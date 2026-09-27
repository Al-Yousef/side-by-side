"""Exercise the packaged Mac runtime without live keys, hooks or LAN access."""
from __future__ import annotations

import json
import logging
import platform
import ssl
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch


def check_tls(key):
    import secure_transport

    client_in, client_out, server_in, server_out = [ssl.MemoryBIO() for _ in range(4)]
    client = secure_transport.context(key, server=False).wrap_bio(
        client_in, client_out, server_side=False)
    server = secure_transport.context(key, server=True).wrap_bio(
        server_in, server_out, server_side=True)
    client_done = server_done = False
    for _ in range(20):
        try:
            if not client_done:
                client.do_handshake()
                client_done = True
        except ssl.SSLWantReadError:
            pass
        flight = client_out.read()
        if flight:
            server_in.write(flight)
        try:
            if not server_done:
                server.do_handshake()
                server_done = True
        except ssl.SSLWantReadError:
            pass
        flight = server_out.read()
        if flight:
            client_in.write(flight)
        if client_done and server_done:
            break
    assert client_done and server_done, "Bundled TLS-PSK handshake did not finish"
    assert client.version() == server.version() == "TLSv1.3"
    for sender, outgoing, incoming, receiver in (
        (client, client_out, server_in, server),
        (server, server_out, client_in, client),
    ):
        sender.write(b"SideBySide packaged transport check")
        incoming.write(outgoing.read())
        assert receiver.read() == b"SideBySide packaged transport check"
    return client.version()


def run(output_directory, ui):
    import AppKit
    import secure_transport

    output = Path(output_directory).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    AppKit.NSApplication.sharedApplication()
    ui.theme.init_fonts()
    key = secure_transport.new_key()
    tls_version = check_tls(key)
    rendered = []
    with tempfile.TemporaryDirectory(prefix="sidebyside-self-test-") as temporary:
        store = ui.SettingsStore(Path(temporary) / "config.json")
        raw = ui.config_to_raw(ui.editable_default_config())
        raw.update(host="127.0.0.1", auth_token=key,
                   send_to_windows=False, allow_windows_to_drive=False)
        cfg = store.save(raw)
        assert store.load().auth_token == key
        assert stat.S_IMODE(store.path.stat().st_mode) == 0o600
        assert stat.S_IMODE(store.path.parent.stat().st_mode) == 0o700
        controller = ui.WakingController(cfg, logger=logging.getLogger("self-test"))
        # ControlWindow.refresh can retry capture when permissions are granted.
        # Keep this mode inert even on a Mac already authorized for the app.
        with patch.object(ui, "accessibility_granted", return_value=False), \
             patch.object(ui, "input_monitoring_granted", return_value=False), \
             patch.object(controller, "start_input_capture") as capture:
            window = ui.ControlWindow.alloc().initWithController_settingsStore_logger_(
                controller, store, logging.getLogger("self-test"))
            try:
                assert isinstance(window.token_field, AppKit.NSSecureTextField)
                assert window.token_field.stringValue() == key
                assert window.token_boxes[1].isHidden()
                for width, height in ((900, 640), (640, 540)):
                    window.window.setContentSize_(AppKit.NSMakeSize(width, height))
                    window.windowDidResize_(None)
                    for page in ui.pages.KEYS:
                        window._select_page(page)
                        view = window.window.contentView()
                        view.layoutSubtreeIfNeeded()
                        actual = view.bounds().size
                        assert abs(actual.width - width) < 1 and abs(actual.height - height) < 1, (
                            f"{page}: content shrank to {actual.width}x{actual.height} "
                            f"inside a {width}x{height} window")
                        bitmap = view.bitmapImageRepForCachingDisplayInRect_(view.bounds())
                        assert bitmap is not None, f"Cannot render {page}"
                        view.cacheDisplayInRect_toBitmapImageRep_(view.bounds(), bitmap)
                        data = bitmap.representationUsingType_properties_(AppKit.NSPNGFileType, {})
                        name = f"{page}-{width}x{height}.png"
                        assert data is not None and data.writeToFile_atomically_(str(output / name), True)
                        rendered.append(name)
                capture.assert_not_called()
                assert not controller.started and not controller.threads
                assert controller.sock is None and controller.event_tap is None
            finally:
                window.window.orderOut_(None)
                window.window.setDelegate_(None)
                window.window.close()
    report = {
        "python": platform.python_version(),
        "architecture": platform.machine(),
        "macos": platform.mac_ver()[0],
        "openssl": ssl.OPENSSL_VERSION,
        "tls": tls_version,
        "has_psk": ssl.HAS_PSK,
        "pages_rendered": rendered,
        "key_masked": True,
        "settings_mode": "0600",
        "live_settings_used": False,
        "input_hooks_started": False,
        "network_sockets_opened": False,
        "clipboard_accessed": False,
    }
    (output / "self-test.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0
