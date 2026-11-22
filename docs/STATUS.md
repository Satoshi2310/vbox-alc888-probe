# Engineering status

## Implemented in this overlay

- Download the official VirtualBox 5.2.30 source archive.
- Verify the Oracle-published SHA-256 before extraction.
- Locate the legacy HDA codec source and patch exactly one vendor ID and one
  device ID assignment.
- Fail instead of guessing if the source layout or expected assignments differ.
- Build `VBoxDD` on a Windows self-hosted runner and upload `VBoxDD.dll`.

## Not implemented / not verified

- A real Realtek ALC888 node graph.
- Realtek-specific pin default configuration and subsystem ID.
- Realtek vendor-specific verbs, coefficients, GPIO, unsolicited responses,
  jack detection, or power management.
- XP driver successful initialization, audio playback, capture, or effects.
- A full VirtualBox installer.
- An actual GitHub Actions run. The project has to be imported into a new
  repository and executed on a runner with the historical toolchain.
