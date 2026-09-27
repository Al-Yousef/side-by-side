# Validation: 27 September 2026

Environment: Windows 11, Python 3.13.15, OpenSSL 3.0.21, PySide6 6.11.1.
Exact Windows package versions are in requirements-windows.lock.

## Passed: 68 focused tests

| Check | Count | Evidence |
|---|---:|---|
| TLS / receiver regressions | 11 | tests/test_secure_link.py |
| Real Windows sender + shared receiver, fake devices | 27 | win_app/tests/test_sender.py |
| Mac sender over real TLS, native APIs faked | 1 | tests/test_mac_transport.py |
| User controls and privilege boundaries | 5 | tests/test_user_controls.py |
| Inherited Mac gesture translation logic | 24 | mac_app/tests/test_gestures.py |

The TLS tests include valid pairing, bad keys, legacy plaintext rejection,
replaying captured TLS records into a fresh connection, simultaneous 1 MiB
traffic in each direction, timeouts, closing a blocked read, reconnecting after
rejection, and input/clipboard delivery to fake handlers. Four shared modules
are checked byte-for-byte across both apps.

The Windows sender tests exercise keyboard forwarding, clipboard, screen
arrangement, edge/corner switching, return and stale-disconnect handling over
the actual transport. The controls tests check that a saved receiver-off
setting remains off on startup, short keys are refused, scheduled startup uses
LeastPrivilege, and automatic firewall/service changes cannot run.

Seven Windows pages rendered successfully offscreen. Key generation,
persistence and masking passed using a temporary config. No native input
hooks or LAN listeners were enabled in that UI test. Both source trees passed
Python compilation. A Windows PE manifest inspection confirmed `asInvoker`.

## Packaged executable: passed

The final unsigned Windows executable exited with code 0 from `--self-test`.
It loaded its bundled Qt libraries, rendered all seven pages, generated and
saved a masked pairing key in temporary settings, and completed an authenticated
TLS 1.3 loopback exchange using bundled OpenSSL 3.0.21. The machine-readable
result is `windows/self-test.json`. Input hooks and LAN listeners stayed off.

Packaging initially picked up incompatible ICU/Windows runtime DLLs from
unrelated media tools on this host's PATH. The spec now restricts DLL discovery
to its Python environment and Windows, and rejects external DLL sources. The
corrected executable passed its packaged self-test. No Windows or Beamer
installation was altered to fix that conflict.

## Mac build and native checks: passed

Environment: Apple silicon ARM64, macOS 26.6.2, Python.org 3.13.15,
OpenSSL 3.0.21 with TLS-PSK, PyObjC 12.2.2 and py2app 0.28.10.
Exact dependencies are in requirements-mac.lock; `pip check` passed.

87 focused tests passed on this Mac:

| Check | Count | Evidence |
|---|---:|---|
| TLS / receiver regressions | 11 | tests/test_secure_link.py |
| Mac sender over real loopback TLS, fake input devices | 1 | tests/test_mac_transport.py |
| Gesture translation | 24 | mac_app/tests/test_gestures.py |
| Mac key, click and pointer planning | 13 | mac_app/tests/test_input_injector_mac.py |
| Fake pasteboard and real AppKit PNG/TIFF conversion | 6 | mac_app/tests/test_clipboard_mac.py |
| Edge, corner, notch and resistance logic | 31 | mac_app/tests/test_crossing.py |
| Cursor association restored when settings change during redirect | 1 | mac_app/tests/test_update_config_redirecting.py |

The standalone bundle launched and its native Permissions page was inspected.
The packaged `--self-test OUTPUT_DIRECTORY` passed, exercising bundled TLS 1.3
PSK exchange in both directions through memory BIOs, synthetic settings saved
with mode 0600, a masked pairing-key field and seven AppKit pages at both
900x640 and 640x540 points. It starts no input hooks, opens no sockets and does
not use the live settings or clipboard. Reports and page images are generated
under `mac_app/dist/self-test/`, excluded from Git.

Native rendering exposed a content view that collapsed to its fitting width
while the window frame retained its requested width. Binding its width to the
window content layout guide corrected this; the packaged test now asserts the
actual content dimensions after layout on every page. Pairing's obsolete
short-code instruction was also corrected.

`codesign --verify --deep --strict` passed for the locally ad-hoc-signed bundle.
This does not establish Developer ID signing, notarization or a security audit.
The production secure transport, framing and receiver modules are unchanged.

## Remaining

Accessibility/Input Monitoring grants, authenticated LAN pairing, real
mouse/keyboard and Mac-to-Windows gestures across both physical computers,
actual LAN latency, clipboard images across the LAN, multi-monitor scaling,
sleep/wake and reconnects still need device testing. Native Windows-to-Mac
trackpad gestures are not implemented (`input_injector_mac.inject_gesture`
explicitly ignores them); ordinary scrolling is a separate supported path.
See HARDWARE-TEST.md for the pending matrix. No public signing, notarization,
dependency-wide security audit or independent security review has been performed.

The complete inherited upstream test suite was not run; some tests deliberately
expect the removed pairing and privileged behaviors. Passing the focused tests
does not establish overall security or hardware compatibility.
