#!/usr/bin/env python3
"""Apply a deliberately limited Realtek ALC888 identity probe to VBox HDA."""
from __future__ import annotations

import argparse
import difflib
import pathlib
import re
import sys

OLD_CODEC = "HDACodec.cpp"
NEW_CODEC = "DevHdaCodec.cpp"


def _replace_one(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=0, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Expected exactly one {label} assignment; found {count}")
    return updated


def _check_already_patched(text: str, vendor_pattern: str, device_pattern: str) -> bool:
    marker_count = text.count("VBOX_ALC888_IDENTITY_PROBE")
    if marker_count == 0:
        return False
    vendor_ok = re.search(vendor_pattern, text, flags=re.MULTILINE) is not None
    device_ok = re.search(device_pattern, text, flags=re.MULTILINE) is not None
    if marker_count != 1 or not vendor_ok or not device_ok:
        raise RuntimeError("Found an incomplete or inconsistent ALC888 identity patch")
    return True


def patch_legacy(text: str) -> str:
    if _check_already_patched(
        text,
        r"^[ \t]*pThis->u16VendorId[ \t]*=[ \t]*0x10EC;.*VBOX_ALC888_IDENTITY_PROBE",
        r"^[ \t]*pThis->u16DeviceId[ \t]*=[ \t]*0x0888;",
    ):
        return text
    updated = _replace_one(
        text,
        r"^([ \t]*pThis->u16VendorId[ \t]*=[ \t]*)0x8384([ \t]*;[^\r\n]*)$",
        r"\g<1>0x10EC; /* Realtek ALC888 identity probe: VBOX_ALC888_IDENTITY_PROBE */",
        "STAC vendor ID",
    )
    updated = _replace_one(
        updated,
        r"^([ \t]*pThis->u16DeviceId[ \t]*=[ \t]*)0x7680([ \t]*;[^\r\n]*)$",
        r"\g<1>0x0888; /* Realtek ALC888 identity probe */",
        "STAC device ID",
    )
    return updated


def patch_modern(text: str) -> str:
    if _check_already_patched(
        text,
        r"^[ \t]*pCfg->idVendor[ \t]*=[ \t]*0x10EC;.*VBOX_ALC888_IDENTITY_PROBE",
        r"^[ \t]*pCfg->idDevice[ \t]*=[ \t]*0x0888;",
    ):
        return text
    updated = _replace_one(
        text,
        r"^([ \t]*pCfg->idVendor[ \t]*=[ \t]*)0x8384([ \t]*;[^\r\n]*)$",
        r"\g<1>0x10EC; /* Realtek ALC888 identity probe: VBOX_ALC888_IDENTITY_PROBE */",
        "STAC vendor ID",
    )
    updated = _replace_one(
        updated,
        r"^([ \t]*pCfg->idDevice[ \t]*=[ \t]*)0x7680([ \t]*;[^\r\n]*)$",
        r"\g<1>0x0888; /* Realtek ALC888 identity probe */",
        "STAC device ID",
    )
    return updated


def find_codec_file(source_root: pathlib.Path) -> pathlib.Path:
    audio_dir = source_root / "src" / "VBox" / "Devices" / "Audio"
    candidates = [audio_dir / OLD_CODEC, audio_dir / NEW_CODEC]
    found = [p for p in candidates if p.is_file()]
    if len(found) != 1:
        raise RuntimeError(
            "Could not uniquely identify the HDA codec source. Expected one of "
            f"{OLD_CODEC} or {NEW_CODEC} in {audio_dir}; found: "
            + (", ".join(p.name for p in found) if found else "none")
        )
    return found[0]


def patch_file(path: pathlib.Path) -> pathlib.Path:
    original_bytes = path.read_bytes()
    try:
        original = original_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"Codec source is not UTF-8 text: {path}") from exc

    patched = patch_legacy(original) if path.name == OLD_CODEC else patch_modern(original)
    if patched == original:
        print(f"Already patched: {path}")
        return path

    path.write_text(patched, encoding="utf-8", newline="")
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        patched.splitlines(keepends=True),
        fromfile=f"a/{path.name}",
        tofile=f"b/{path.name}",
    )
    patch_path = path.parents[4] / "alc888-identity-probe.patch"
    patch_path.write_text("".join(diff), encoding="utf-8", newline="")
    print(f"Patched {path}")
    print(f"Patch diff: {patch_path}")
    return patch_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=pathlib.Path)
    args = parser.parse_args()
    root = args.source_root.resolve()
    if not (root / "configure.vbs").is_file():
        raise RuntimeError(f"Not a VirtualBox source root: {root}")
    codec_file = find_codec_file(root)
    patch_file(codec_file)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
