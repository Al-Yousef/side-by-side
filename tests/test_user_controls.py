"""Configuration and privilege boundaries on Windows, with OS mutations mocked."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'win_app'))
import app_config
import autostart_win
import firewall_win
import input_injector
import kvm_bridge_win as ui
import secure_transport as tls


class ControlsTests(unittest.TestCase):
    def test_receiver_disabled_setting_survives_startup(self):
        config=app_config.Config('',24830,tls.new_key(),allow_mac_to_drive=False,send_to_mac=False)
        window=SimpleNamespace(_config=config,announcer=Mock(),server=Mock(),_start_sending=Mock())
        ui.WindowsApplication.start(window)
        window.server.start.assert_not_called()

    def test_windows_rejects_weak_pairing_key(self):
        with self.assertRaises(app_config.ConfigError):
            app_config.validate_config(app_config.Config('',24830,'123456'))

    def test_autostart_uses_ordinary_user(self):
        xml=autostart_win.task_xml('C:\\SideBySide.exe','test-user')
        self.assertIn('<RunLevel>LeastPrivilege</RunLevel>',xml)
        self.assertNotIn('HighestAvailable',xml)

    def test_firewall_changes_disabled(self):
        with patch.object(firewall_win,'_powershell') as run:
            with self.assertRaises(RuntimeError): firewall_win.repair('test.exe',24830)
            with self.assertRaises(RuntimeError): firewall_win.trust_network([1])
            run.assert_not_called()

    def test_no_automatic_service_restart(self):
        with patch.object(input_injector.subprocess,'run') as run:
            self.assertFalse(input_injector.release_gameinput_foreground())
            run.assert_not_called()


if __name__=='__main__':unittest.main(verbosity=2)
