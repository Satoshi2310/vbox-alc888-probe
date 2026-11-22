# XP validation plan for the identity probe

1. Preserve the original VirtualBox 5.2.30 installation and VM configuration.
2. Replace only `VBoxDD.dll` in a disposable copy of VirtualBox; keep a backup.
3. Start a Windows XP VM configured with HDA.
4. Record the codec hardware ID shown by Device Manager or a hardware-ID tool.
   The intended codec ID is `HDAUDIO\\FUNC_01&VEN_10EC&DEV_0888`.
5. Install the matching Realtek XP HDA package and record the exact device
   status/error code. Do not infer success from the driver installer finishing.
6. Capture VirtualBox HDA/codec logs while the driver starts. Save the XP
   Device Manager status and the log together.
7. If the driver starts, test playback, mute/volume, reboot persistence, and
   only then test the Realtek control panel and effects one at a time.

A Code 10 result is expected to remain possible because this milestone still
presents the STAC9221 node map. The next implementation step must be based on
actual driver verb traffic and ALC888 documentation, not merely further ID
changes.
