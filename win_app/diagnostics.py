"""Opt-in package smoke test. No input hooks, LAN listener or real config writes."""
import concurrent.futures
import json
import os
from pathlib import Path
import socket
import ssl
import tempfile
from unittest.mock import patch


def run(output):
    os.environ['QT_QPA_PLATFORM']='offscreen'
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    import secure_transport as tls
    key=tls.new_key()
    listener=socket.socket(); listener.bind(('127.0.0.1',0)); listener.listen()
    def responder():
        raw,_=listener.accept()
        wrapped=tls.prepare_server(raw,key)
        wrapped.settimeout(3); wrapped.do_handshake()
        with tls.TLSStream(wrapped) as stream:
            assert stream.recv(4)==b'ping'
            stream.sendall(b'pong')
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future=pool.submit(responder)
        with tls.wrap_client(socket.create_connection(listener.getsockname(),timeout=3),key) as stream:
            stream.sendall(b'ping'); assert stream.recv(4)==b'pong'
        future.result(timeout=4)
    listener.close()
    from PySide6.QtWidgets import QApplication
    import kvm_bridge_win as ui
    import app_config
    app=QApplication.instance() or QApplication([])
    ui.theme.init_fonts(); app.setFont(ui.theme.font(ui.theme.TYPE['body']))
    with tempfile.TemporaryDirectory() as temporary:
        path=Path(temporary)/'config.json'
        with patch.object(ui.WindowsApplication,'_check_firewall'), \
             patch.object(ui.WindowsApplication,'_check_full_screen'), \
             patch.object(ui.autostart_win,'is_enabled',return_value=False), \
             patch.object(ui.WindowsApplication,'_apply_config',lambda self,cfg:setattr(self,'_config',cfg)):
            window=ui.WindowsApplication(path)
            window.show(); app.processEvents()
            assert not window.server.listening and not path.exists()
            window._toggle_pairing()
            loaded=app_config.load_config(path)
            assert len(tls.key_bytes(loaded.auth_token))==32
            assert window.pair_key.text()==loaded.auth_token
            assert window.pair_key.echoMode()==ui.QLineEdit.EchoMode.Password
            assert not window.server.listening
            # Render a representative waiting state. It is a preview, not a live Mac connection.
            window._status=ui.ServerState.WAITING
            window._status_detail='Waiting for your Mac'
            window._refresh_window()
            for page in ui.pages_win.KEYS:
                window._select_page(page); app.processEvents()
                assert window.grab().save(str(output/f'{page}.png'))
            window.quit(); app.processEvents()
    report={'ok':True,'tls':'TLSv1.3','openssl':ssl.OPENSSL_VERSION,
            'pages_rendered':len(ui.pages_win.KEYS),'key_generation':'passed',
            'input_hooks_started':False,'lan_listener_started':False,
            'mac_hardware_tested':False}
    (output/'self-test.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report
