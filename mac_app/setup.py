import os
import sys
from pathlib import Path

from setuptools import setup


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


VERSION = (Path(__file__).resolve().parent.parent / "VERSION").read_text().strip()
BUILD = os.environ.get("SIDEBYSIDE_BUILD", "1")


setup(
    name="SideBySide",
    version=VERSION,
    app=["kvm_bridge_app.py"],
    py_modules=[
        "bridge",
        "clipboard_mac",
        "config",
        "crossing",
        "desktop_mac",
        "gestures",
        "ignored",
        "input_injector_mac",
        "key_codes",
        "keyboard_layout",
        "link_state",
        "media_keys",
        "notch_beam",
        "notch_island",
        "pages",
        "previews",
        "no_unlock",
        "pairing",
        "protocol",
        "secure_transport",
        "receiver",
        "return_edge",
        "settings_store",
        "self_test",
        "theme",
        "tokens",
        "wake",
        "wol",
        "widgets",
        "windows_input",
    ],
    # No Mac ships Hanken Grotesk or B612 Mono. macOS registers anything under
    # ATSApplicationFontsPath before the app runs, so the bundle carries the same files the
    # Windows receiver does rather than a second copy of them.
    data_files=[(
        "Fonts",
        [
            "../win_app/assets/HankenGrotesk-Variable.ttf",
            "../win_app/assets/B612Mono-Regular.ttf",
            "../win_app/assets/B612Mono-Bold.ttf",
            "../win_app/assets/HankenGrotesk-OFL.txt",
            "../win_app/assets/B612Mono-OFL.txt",
        ],
    ), ("", ["../VERSION", "../LICENSE", "../ATTRIBUTION.md"])],
    options={
        "py2app": {
            "argv_emulation": False,
            # cryptography ships a compiled _rust extension plus cffi; py2app's own recipe pulls
            # both in, but naming the package keeps its data files and submodules in the bundle.
            "packages": ["rumps", "cryptography", "cffi"],
            "includes": ["objc", "AppKit", "ApplicationServices", "Quartz"],
            "iconfile": "../SideBySide.icns",
            "plist": {
                "CFBundleDisplayName": "SideBySide",
                "CFBundleIdentifier": "local.sidebyside.desktop",
                "CFBundleName": "SideBySide",
                "CFBundleShortVersionString": VERSION,
                "CFBundleVersion": BUILD,
                "LSMinimumSystemVersion": "13.0",
                "LSUIElement": False,
                "NSHighResolutionCapable": True,
                "NSPrincipalClass": "NSApplication",
                "ATSApplicationFontsPath": "Fonts",
                "NSHumanReadableCopyright": "Copyright 2026 Toby Kalkman",
                "NSLocalNetworkUsageDescription": "SideBySide needs to reach the Windows PC on your local network to forward keyboard and mouse input.",
            },
        }
    },
)
