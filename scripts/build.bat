pyinstaller --noconfirm ^
    --onedir ^
    --name vpype ^
    --add-data="vpype/hpgl_devices.toml;vpype" ^
    --additional-hooks-dir=scripts/hooks ^
    scripts/run_vpype.py