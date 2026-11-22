# VirtualBox 5.2.30 — Realtek ALC888 identity probe

> **Experimental milestone 0.1.** This is not a complete ALC888 codec emulator.
> It changes the advertised HDA codec vendor/device ID to `10EC:0888` while
> retaining VirtualBox's existing STAC9221 node topology. The purpose is to
> test whether the Windows XP Realtek driver binds to the device and to collect
> the resulting failure mode. It does **not** claim that the Realtek mixer,
> jack sensing, EQ, environment, reverb, or other vendor-specific verbs work.

## What this repository contains

- A source bootstrapper for Oracle's official VirtualBox 5.2.30 source archive.
- A fail-fast patcher for the legacy `HDACodec.cpp` STAC9220 constructor.
- Unit tests for the patcher.
- A Windows GitHub Actions workflow which builds `VBoxDD.dll` on a specially
  prepared **self-hosted Windows runner** and uploads it as an artifact.

The 113 MB upstream source archive is downloaded by the workflow and is not
committed into this small overlay repository.

## Why the workflow uses a self-hosted runner

VirtualBox 5.2.30's Windows build environment is from the Visual Studio 2010
period. The historical toolchain includes Visual Studio 2010 SP1, Windows SDK
7.1 and WDK 7.1, plus the matching kBuild/`kmk` toolchain. A normal
`windows-latest` runner does not provide this environment. Register a Windows
x64 self-hosted runner with the label `vbox52` after preparing those tools.

Set these machine-level environment variables on that runner if the tools are
not in the default locations:

- `VBOX_VC2010`: Visual Studio 2010 `VC` directory.
- `VBOX_WINSDK71`: Windows SDK 7.1 directory.
- `VBOX_WDK71`: Windows Driver Kit 7.1 directory.
- `KBUILD_PATH`: kBuild root containing `footer.kmk` (defaults to the
  `kBuild` directory shipped with the source archive).
- `KMK_EXE`: full path to `kmk.exe` (or make `kmk.exe` available in `PATH`).

The default paths are documented in `scripts/build_windows.ps1`. You may also
need the additional dependencies required by the particular VirtualBox build
target. This workflow intentionally fails early when the core compiler/SDK/
WDK/kBuild prerequisites are missing.

## Run the build

1. Create a new empty GitHub repository for this project. Do not put it in the
   unrelated `OptimePlayer` repository.
2. Upload/push the contents of this directory to its default branch. For a
   local Git checkout, run:

   ```cmd
   git init -b main
   git add .
   git commit -m "Add VirtualBox 5.2.30 ALC888 identity probe"
   git remote add origin https://github.com/Satoshi2310/YOUR-NEW-REPO.git
   git push -u origin main
   ```

   Replace `YOUR-NEW-REPO` with the repository name you create.
3. Prepare a Windows x64 self-hosted GitHub Actions runner and assign it the
   label `vbox52`.
4. In the repository, open **Actions → Build VirtualBox 5.2.30 (ALC888 probe)
   → Run workflow**.
5. Download the `VBoxDD-5.2.30-ALC888-probe` artifact from the successful run.

The workflow does not install or replace VirtualBox on the runner. It only
builds the device DLL and publishes it as an artifact. No GitHub-hosted runner
image currently provides the required VS2010/SDK7.1/WDK7.1 toolchain, so this
workflow intentionally targets your prepared self-hosted runner.

## Installing the artifact for a test

Use a disposable VM and a copy of your existing VirtualBox 5.2.30 installation.
Shut down all VMs and VirtualBox processes before replacing `VBoxDD.dll`. Keep a
backup of the original DLL and be prepared to restore it. Do not replace the
DLL in a working installation without a rollback path.

Configure the VM with HDA and the existing codec selection:

```cmd
VBoxManage modifyvm "XP" --audio dsound --audiocontroller hda --audiocodec stac9221 --audioout on --audioin off
```

The command-line codec selector remains `stac9221`; this first probe changes
the identity returned by the emulated codec internally. The workflow does not
add a new VBoxManage enum value.

## Expected interpretation

- If XP binds the Realtek driver, that only proves the hardware ID matched. The
  driver may still fail to initialize because the emulated nodes and verbs are
  still STAC9221-like.
- If Device Manager reports Code 10, this is not evidence that the patch did
  nothing; it means the identity-only probe is insufficient for the driver's
  initialization sequence.
- RTHDCPL opening successfully is not proof that effects work. EQ, environment,
  reverb and stream playback must be tested independently.

## Next engineering milestone

Implement a real ALC888 codec profile: codec revision and subsystem identity,
Realtek NID/widget topology, connection lists, pin defaults, amp capabilities,
power states, unsolicited responses, and the verb behaviour used by the XP
Realtek driver. The profile must be implemented against the exact 5.2.30 source
and validated by driver/codec traces. This identity probe is only a controlled
starting point for that work.

## Upstream and licensing

The upstream source is Oracle VirtualBox 5.2.30:
<https://download.virtualbox.org/virtualbox/5.2.30/VirtualBox-5.2.30.tar.bz2>

The bootstrapper pins SHA-256 to:
`caf19d4a5310d63e31e564acb24cb63e412c8ce56193a804e38c7dcc8db35609`

The patch is applied to the upstream source only in the build workspace. Keep
VirtualBox's original license notices and comply with the license terms of the
source release when distributing modified binaries or source.
