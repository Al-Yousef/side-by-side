# SideBySide hardware test

Status on 27 September 2026: the Mac app builds and launches. Its packaged UI,
TLS checks and 87 focused tests pass. All physical two-computer checks below
are pending until observed on your Mac and Windows PC.

## Connect the computers

1. Open SideBySide from your personal Applications folder on the Mac.
2. On its Permissions page, use Grant for Accessibility and Input Monitoring.
   Enable SideBySide in each corresponding System Settings list, then relaunch
   SideBySide. Allow Local Network if requested. The app should say both
   permissions are granted and input capture is ready.
3. Keep the Windows app open on the same trusted LAN. Allow its exact executable
   through Windows Firewall on Private networks if needed.
4. Generate the pairing key in Windows SideBySide if it has none. Enter it
   directly in the Mac Connection page with the Windows IPv4 address and port
   24830. Keep it masked. Do not put it in chat, screenshots or test reports.
5. Click Connect. Confirm a connection on both computers and enable both sharing
   directions. In Crossing, put the Windows screen on the correct side of the Mac.
6. Open a blank TextEdit document on Mac and blank Notepad on Windows. Close
   other input-sharing apps. Know how to return: the default Mac shortcut is
   double-tap Right Option; the SideBySide menu also offers a return control.

## Test each direction

First use the Mac's physical keyboard and trackpad to drive Windows. Then return
locally and use the PC's physical keyboard and mouse to drive the Mac. Returning
the Mac's pointer home is not proof that the PC's own input can drive the Mac.

| Check | Procedure | Mac to Windows | Windows to Mac |
|---|---|---|---|
| Mouse | Move across the destination screen; left-click, right-click, double-click and select text by dragging. | Pending | Pending |
| Keyboard | Type `SideBySide test 123 !?`, Enter, arrows and Backspace. Hold a letter briefly to test repeat. | Pending | Pending |
| Shortcuts | Test select-all, copy, paste and undo in the blank editor. In semantic mode, Mac Command maps to Windows Ctrl and Windows Ctrl maps to Mac Command. | Pending | Pending |
| Scrolling | Scroll a long test document vertically and horizontally where supported. | Pending | Pending |
| Crossing | Cross the configured edge, then return through the facing edge. Repeat five times, including a slow push. | Pending | Pending |
| Text clipboard | Copy `from Mac 123` locally, cross and paste on Windows. Then copy `from Windows 456` locally, cross and paste on Mac. Transfer occurs at input handoff. | Pending | Pending |
| Image clipboard | Copy a small non-sensitive test image, cross and paste in Paint or Preview as appropriate. Repeat in reverse. | Pending | Pending |
| Reconnect | While redirected in a blank editor, briefly disconnect that computer's network. Confirm input returns locally. Restore it, wait for connection, then cross again. | Pending | Pending |
| Held-key release | Repeat a disconnect while holding Shift in the blank editor. Release it and verify subsequent local typing is lowercase and no mouse button remains held. | Pending | Pending |
| Direction controls | Disable one sharing direction and confirm that direction stops while the other remains usable. Re-enable it. | Pending | Pending |
| Restart | Quit and reopen one app. Confirm it reconnects without replacing the key. Repeat for the other app. | Pending | Pending |
| Sleep/wake | Sleep and manually wake one computer; unlock it locally and confirm reconnection. Repeat for the other computer. | Pending | Pending |

## Gestures

Mac-to-Windows: in a browser with disposable tabs, try two-finger scrolling,
pinch zoom and page back/forward gestures. Separately try any configured
three/four-finger desktop gestures and record whether they act on Windows,
remain local or do nothing. They use platform-specific capture paths and need
individual results. Smart magnify is currently a reserved no-op.

Windows-to-Mac native trackpad gestures are not implemented in this prototype.
Record that as unsupported, not passed. Mouse-wheel scrolling is tested above.

For any failure, report only the direction, action, expected result, actual
result and approximate time. Do not include pairing keys, configuration-file
contents or clipboard contents beyond the synthetic test strings above.
