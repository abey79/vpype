@Rem call from project directory, first argument must be version string

pyinstaller --noconfirm --onedir ^
    --name vpype --icon="scripts/vpype.ico" ^
    --add-data="vpype/hpgl_devices.toml;vpype" ^
    --additional-hooks-dir=scripts/hooks ^
    scripts/run_vpype.py

makensis /V4 /DVERSION="%1" scripts/installer_win.nsi
