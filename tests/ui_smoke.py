"""Render every Windows page offscreen; never capture hooks or open a listener."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'win_app'))
from PySide6.QtWidgets import QApplication
import kvm_bridge_win as ui
import app_config
import secure_transport

def run():
    app=QApplication.instance() or QApplication([])
    ui.theme.init_fonts(); app.setFont(ui.theme.font(ui.theme.TYPE['body']))
    screenshots=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'test-renders'
    screenshots.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        path=Path(temporary)/'config.json'
        with patch.object(ui.WindowsApplication,'_check_firewall'), \
             patch.object(ui.WindowsApplication,'_check_full_screen'), \
             patch.object(ui.WindowsApplication,'_apply_config',lambda self,cfg:setattr(self,'_config',cfg)):
            window=ui.WindowsApplication(path)
            window.show(); app.processEvents()
            assert not window.server.listening
            assert not path.exists()
            window._toggle_pairing()
            loaded=app_config.load_config(path)
            assert len(secure_transport.key_bytes(loaded.auth_token))==32
            assert window.pair_key.text()==loaded.auth_token
            assert window.pair_key.echoMode()==ui.QLineEdit.EchoMode.Password
            assert not window.server.listening
            for page in ui.pages_win.KEYS:
                window._select_page(page); app.processEvents()
                assert window.grab().save(str(screenshots/f'{page}.png'))
            window.quit(); app.processEvents()
    print('PASS: 7 Windows pages rendered; key generation, persistence and masking verified; no listener/hooks started.')

if __name__=='__main__':run()
