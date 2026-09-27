#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [[ "$(uname -s)" != Darwin ]]; then
  echo "Run this script on your Mac."
  exit 1
fi
PYTHON="${SIDEBYSIDE_PYTHON:-/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13}"
if [[ ! -x "$PYTHON" ]]; then
  echo "Install Python 3.13 from python.org first, or set SIDEBYSIDE_PYTHON to its executable."
  exit 1
fi
"$PYTHON" -c 'import sys,ssl; assert sys.version_info >= (3,13) and ssl.HAS_PSK, "Python 3.13+ with TLS-PSK is required"'
"$PYTHON" -m venv .venv-mac
.venv-mac/bin/python -m pip install -r requirements-mac.lock
.venv-mac/bin/python -m pip check
.venv-mac/bin/python tests/test_secure_link.py
.venv-mac/bin/python tests/test_mac_transport.py
cd mac_app
../.venv-mac/bin/python -m unittest discover -s tests -p test_gestures.py
../.venv-mac/bin/python setup.py py2app
dist/SideBySide.app/Contents/MacOS/SideBySide --self-test "$PWD/dist/self-test"
/usr/bin/codesign --verify --deep --strict dist/SideBySide.app
echo "Built mac_app/dist/SideBySide.app. Copy it to ~/Applications, then open it."
echo "Grant Accessibility and Input Monitoring to SideBySide, then reopen the app."
