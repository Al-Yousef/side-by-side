# Continue the macOS build and validation

SideBySide is an experimental Beamer-derived Windows/Mac mouse and keyboard
sharing app. Its interface and gesture code are retained while the connection
uses mandatory authenticated TLS. Windows checks have passed. The Mac app has
now built and launched on an Apple silicon Mac running macOS 26.6.2; physical
pairing/input checks remain.
Clone this repository and work from its root directory.

## Already done on Windows, 27 September 2026

- Forked Beamer tag v1.3.3 / commit
  `387aeff00f52a9eea65d8ba734a814e511f5019e`; retained GPL and attribution.
- Named the independent prototype SideBySide 0.1.0, with separate settings and
  TCP port 24830.
- Added identical `secure_transport.py` copies to both platforms: mandatory
  TLS 1.3, 256-bit random PSK, no tickets/early data or plaintext fallback.
- Receiver and both senders use that transport. The inherited inner framing
  itself remains replayable outside TLS; never expose it on a raw connection.
- Replaced six-digit pairing with manually transferred 64-character lowercase
  key. Generate on Windows, enter on Mac Connection page with the PC's IPv4.
- No discovery service, administrator default, firewall repair, service
  restart or lock-screen unlock. Live configuration files are ignored by Git.
- Focused tests passed; see VALIDATION.md. Mac sender was exercised with
  native APIs faked on Windows. This is **not** a real Mac gesture/UI test.
- Built the Windows exe and kept the full source. Windows settings are stored
  in `%LOCALAPPDATA%\SideBySide`; Mac uses `~/Library/Application Support/SideBySide`.

## Mac progress, 27 September 2026

- Python.org 3.13.15 / OpenSSL 3.0.21, TLS-PSK available, ARM64 execution.
- Built and launched the standalone bundle; saved `requirements-mac.lock`.
- Fixed the native content view shrinking below the requested window width.
- Corrected an obsolete short-code instruction on Pairing.
- Added `--self-test OUTPUT_DIRECTORY`: temporary synthetic settings, masked
  key field, 0600 file permissions, 14 page renders and in-memory TLS 1.3
  exchange in both directions. No live settings, input hooks, LAN sockets or
  clipboard access. The build runs it and verifies local signature integrity.
- Permission grants, authenticated LAN pairing and all physical input tests
  remain unverified. Resume with [HARDWARE-TEST.md](HARDWARE-TEST.md).

## Continue here

1. Inspect README.md, SETUP.md, SECURITY.md and this source before building.
   Check `python3.13` and `ssl.HAS_PSK`. Build-Mac.command uses the official
   framework interpreter by default; SIDEBYSIDE_PYTHON can select another
   known Python 3.13+ with PSK support. No sudo is needed for the project build.
2. Run `bash Build-Mac.command`. Resolve actual Mac dependency/build issues.
   Save the Mac dependency lock only after a successful installation. Do not
   downgrade transport requirements or re-enable Beamer's network pairing.
3. The artifact should be `mac_app/dist/SideBySide.app`. Check the built bundle
   imports `ssl`/`secure_transport` and supports TLS-PSK. Launch the actual app,
   inspect UI sizing, then guide the user through Accessibility, Input
   Monitoring and any Local Network permission prompt. No global Gatekeeper
   disable or removal of unrelated app permissions is needed.
4. Transfer the generated Windows pairing key privately between the paired
   machines. Never paste it into a chat or logs. Discover the
   current Windows address from the Windows app; no fixed IP is assumed here.
5. Test both actual machines: connection, mouse, buttons, scrolling, typing,
   Cmd/Ctrl mapping, crossing and return, gestures, clipboard, disconnect
   recovery, modifiers released on disconnect, sleep/wake, direction switches.
   Use blank editors and user-owned test content. Record what really passed.
6. Fix observed issues and update VALIDATION.md. Do not claim fully working,
   audited, signed or notarized until those separate facts are established.

Useful focused checks (run separately to isolate platform module imports):

```
python tests/test_secure_link.py
python tests/test_mac_transport.py
cd mac_app
python -m unittest discover -s tests -p test_gestures.py -v
```

The inherited full test suite still contains assumptions about the removed
Beamer pairing protocol and privileged features; the passing subset is
documented. See SECURITY.md for the current transport design and limitations.
