@Rem call from project directory, first argument must be version string

pyinstaller --noconfirm --onedir ^
    --name vpype --icon="scripts/vpype.ico" ^
    --add-data="vpype/vpype_config.toml;vpype" ^
    --add-data="vpype_viewer/shaders;vpype_viewer/shaders" ^
    --add-data="vpype_viewer/resources;vpype_viewer/resources" ^
    --add-data="vpype_viewer/qtviewer/resources;vpype_viewer/qtviewer/resources" ^
    --additional-hooks-dir=scripts/hooks ^
    scripts/run_vpype.py

@Rem makensis /V4 /DVERSION="%1" scripts/installer_win.nsi
