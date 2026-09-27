# Set up Side by Side

The Windows prototype is ready for local testing. The Mac build and real
two-computer check are still pending. Keep the original Beamer app closed.

## Windows

1. Build the Windows app following README.md, then open `dist/SideBySide.exe`.
   If you already have the local prototype bundle, its executable is in
   `windows/SideBySide.exe`. It runs without an administrator prompt and creates its own settings under
   `%LOCALAPPDATA%\SideBySide`. Start at logon is off by default.
2. Open **Pairing → Generate pairing key**. The key stays masked until you choose
   Show key. Copy it privately to the Mac; anyone with it can control a paired
   computer while sharing is enabled. Avoid chat messages and cloud clipboards.
3. Note the PC's local IPv4 address shown on that page and port **24830**.
4. If Windows Firewall asks, allow this app on your trusted **Private** network.
   If no prompt appears, use Windows Security → Firewall & network protection →
   Allow an app through firewall → Change settings → Allow another app, select
   this exact executable and allow Private access. Do not enable Public access.
   The app itself does not change firewall rules or network categories.

## Apple silicon Mac (macOS 13+)

1. Clone this repository onto the Mac, or extract a provided source ZIP there.
2. Install the current Python **3.13** installer from
   https://www.python.org/downloads/macos/ if needed.
3. In Terminal, type `cd `, drag the `side-by-side` project folder into the
   window and press Return. Then run `bash Build-Mac.command`.
   This installs dependencies into that folder and builds the app there; it
   does not use sudo, change system security settings, or replace Beamer.
4. Copy `mac_app/dist/SideBySide.app` to your own `~/Applications` folder and
   open it. This personal build is not notarized; if macOS blocks it, use its
   per-app **Privacy & Security → Open Anyway** control after reviewing the
   source. Do not disable Gatekeeper globally.
5. Grant **Accessibility** and **Input Monitoring** to SideBySide in Privacy &
   Security. Quit and reopen it after granting them. Allow Local Network access
   if macOS requests it.
6. Open **Connection**, enter the Windows address, **24830**, and the complete
   lowercase pairing key. Choose **Connect**. Keep both computers on the same
   trusted LAN for this first test.
7. In **Crossing**, arrange the screens to match your desk. Both apps should
   report a connection before trying an edge crossing.

## First hardware check

Use an empty text editor on each machine. Check mouse movement, click, scroll,
typing, modifier release, crossing out and back, and plain-text clipboard in
both directions. Then check the Mac gestures you use. Disconnect Wi-Fi briefly:
input should return locally and reconnect afterward. Check sleep/wake last.
These real-device checks have not yet been performed for this build.

Close-window hides the Windows app to the tray; use **Quit** to end it. You can
turn off either sharing direction in the app. Elevated Windows apps, UAC prompts,
login/lock screens and remote unlocking are outside this prototype's scope.

Changing the key on Windows disconnects the old pairing; enter the replacement
on the Mac. The Copy button clears the current clipboard after one minute if it
is unchanged, but it cannot erase clipboard history or already synced copies.
