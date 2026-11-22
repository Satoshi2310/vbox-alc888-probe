#!/usr/bin/env python3
"""Download and verify the official VirtualBox 5.2.30 source archive."""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import sys
import tarfile
import urllib.request

SOURCE_URL = (
    "https://download.virtualbox.org/virtualbox/5.2.30/"
    "VirtualBox-5.2.30.tar.bz2"
)
SOURCE_SHA256 = "caf19d4a5310d63e31e564acb24cb63e412c8ce56193a804e38c7dcc8db35609"
ARCHIVE_NAME = "VirtualBox-5.2.30.tar.bz2"


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_archive(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".download")
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "vbox-alc888-probe-source-bootstrap/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response, tmp.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        actual = sha256_file(tmp)
        if actual.lower() != SOURCE_SHA256:
            raise RuntimeError(
                f"SHA-256 mismatch for {ARCHIVE_NAME}: expected {SOURCE_SHA256}, got {actual}"
            )
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def safe_extract(archive: pathlib.Path, destination: pathlib.Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    base = destination.resolve()
    with tarfile.open(archive, mode="r:bz2") as tf:
        members = tf.getmembers()
        for member in members:
            target = (destination / member.name).resolve()
            if target != base and base not in target.parents:
                raise RuntimeError(f"Unsafe path in source archive: {member.name}")
        # Python 3.12's data filter also blocks link-based path traversal.
        tf.extractall(destination, filter="data")


def locate_source_root(extraction_dir: pathlib.Path) -> pathlib.Path:
    candidates = list(extraction_dir.rglob("configure.vbs"))
    candidates = [p.parent for p in candidates if (p.parent / "Version.kmk").is_file()]
    if len(candidates) != 1:
        raise RuntimeError(
            "Expected exactly one VirtualBox source root containing configure.vbs "
            f"and Version.kmk, found {len(candidates)}"
        )
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", required=True, help="Directory used for the source archive and extraction")
    args = parser.parse_args()

    dest = pathlib.Path(args.dest).resolve()
    archive = dest / ARCHIVE_NAME
    extraction = dest / "source"

    if not archive.is_file() or sha256_file(archive).lower() != SOURCE_SHA256:
        print(f"Downloading {SOURCE_URL}", flush=True)
        download_archive(archive)
    else:
        print("Using cached archive with matching SHA-256", flush=True)

    root = locate_source_root(extraction) if extraction.exists() else None
    if root is None:
        if extraction.exists():
            import shutil
            shutil.rmtree(extraction)
        print("Extracting authenticated source archive...", flush=True)
        safe_extract(archive, extraction)
        root = locate_source_root(extraction)

    print(f"VirtualBox source root: {root}")
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as output:
            output.write(f"source_root={root}\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # surfaced as a clear workflow failure
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
