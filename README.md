# Side by Side 0.1.0

An experimental personal fork of **Beamer 1.3.3** by Toby Kalkman, keeping its
desktop interface, edge crossing, keyboard sharing, clipboard handling and Mac
gesture code. Original project: https://github.com/kalkman-code/beamer.
See [ATTRIBUTION.md](ATTRIBUTION.md) and [LICENSE](LICENSE).

This first build adds mandatory authenticated **TLS 1.3**, a randomly generated
256-bit pairing key, separate settings and TCP port **24830**, and ordinary-user
Windows execution. Six-digit network pairing, UDP discovery, automatic firewall
changes, service restarts and lock-screen unlocking are disabled.

**Status:** Windows executable tested locally; Mac app built and launched on
Apple silicon with macOS 26.6.2. The packaged Mac UI and TLS checks pass.
Permissions, pairing and physical two-computer input tests are still pending.
Mac-to-Windows gesture translation is implemented; native Windows-to-Mac
trackpad gestures are not implemented. This is not an independently audited
security release.

Start with [SETUP.md](SETUP.md). Test evidence and limitations are in
[VALIDATION.md](VALIDATION.md). Security design is in [SECURITY.md](SECURITY.md).

## Build

This repository contains source. Build the apps locally; no signed or notarized
release is available from this repository yet.

```sh
git clone https://github.com/Al-Yousef/side-by-side.git
cd side-by-side
```

Use Python 3.13+ with `ssl.HAS_PSK` (the official Python.org 3.13 installers work
for the tested Windows runtime; the Mac script checks its runtime before build).

- Windows: `powershell -File build-windows.ps1 -Python <python313.exe>`.
- Mac: `bash Build-Mac.command` from Terminal after installing Python 3.13.

Windows output: `dist/SideBySide.exe`. Mac output: `mac_app/dist/SideBySide.app`.
For continuing the Mac validation work, see [MAC-HANDOFF.md](MAC-HANDOFF.md).

The Windows and Mac dependency locks record their verified build environments.
`Build-Mac.command` installs `requirements-mac.lock`, runs the focused transport
and gesture tests, builds the app, runs its packaged self-test and verifies the
bundle's local code-signature integrity. This is local ad-hoc signing, not a
Developer ID signature or notarization. See [HARDWARE-TEST.md](HARDWARE-TEST.md)
for the remaining physical checks.

## Development checks

Run `python tests/test_secure_link.py` for TLS, replay and receiver regressions.
On Windows, run `python tests/ui_smoke.py <output-folder>` for the offscreen UI.
From `win_app`, `python -m unittest discover -s tests -p test_sender.py -v`
exercises the real sender/receiver transport with fake input devices.

Other inherited tests still include old Beamer pairing, privilege and plaintext
transport assumptions; they are not a passing all-project test suite for this
fork. The executed subset is listed in VALIDATION.md. Historical upstream
documentation is retained in `upstream-docs/` for provenance only.
