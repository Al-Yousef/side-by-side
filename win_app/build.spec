from pathlib import Path
import os
import sys


source_dir = Path(SPECPATH)

# This desktop host can put PDF/image-tool DLL folders on PATH. Those contain
# older ucrtbase/ICU libraries that must never shadow Windows' own runtime.
# Limit dependency discovery to this Python installation and Windows itself.
if os.name == "nt":
    windows_dir = Path(os.environ["SystemRoot"])
    os.environ["PATH"] = os.pathsep.join(map(str, [
        Path(sys.prefix), Path(sys.prefix) / "Scripts", Path(sys.base_prefix),
        windows_dir / "System32", windows_dir,
    ]))

analysis = Analysis(
    [str(source_dir / "kvm_bridge_win.py")],
    pathex=[str(source_dir)],
    binaries=[],
    datas=[(str(source_dir / "SideBySide.ico"), "."), (str(source_dir / "assets"), "assets"), (str(source_dir.parent / "VERSION"), "."), (str(source_dir.parent / "LICENSE"), "."), (str(source_dir.parent / "ATTRIBUTION.md"), ".")],
    hiddenimports=["cryptography"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PIL", "pystray", "tkinter", "numpy", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.Qt3DCore", "PySide6.QtMultimedia"],
    noarchive=False,
)

if os.name == "nt":
    allowed = [Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(),
               windows_dir.resolve(), source_dir.resolve()]
    unexpected = [source for _, source, _ in analysis.binaries
                  if not any(Path(source).resolve().is_relative_to(root) for root in allowed)]
    if unexpected:
        raise RuntimeError("Unexpected external DLLs in build: " + ", ".join(unexpected))

python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="SideBySideDebug" if os.environ.get("SIDEBYSIDE_CONSOLE") else "SideBySide",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=bool(os.environ.get("SIDEBYSIDE_CONSOLE")),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(source_dir / "SideBySide.ico"),
    # Run as the signed-in user; elevated windows and secure desktop are unsupported.
    uac_admin=False,
)
