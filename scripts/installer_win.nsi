;vpype Windows installer script

!define APPNAME vpype

;Must be defined by caller
;!define VERSION 1.2.0a0


!include "MUI2.nsh"


;--------------------------------
;General

;Name and file
Name "${APPNAME}"
OutFile "..\dist\vpype-${VERSION}-setup.exe"
Unicode True

;Default installation folder
InstallDir "$LOCALAPPDATA\${APPNAME}"

;Get installation folder from registry if available
InstallDirRegKey HKCU "Software\${APPNAME}" ""

;Request application privileges for Windows Vista
RequestExecutionLevel user

;--------------------------------
;Interface Settings

!define MUI_ABORTWARNING

;--------------------------------
;Pages

Var StartMenuFolder

!define MUI_ICON "installer.ico"
!define MUI_UNICON "uninstaller.ico"

!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "headerimage.bmp"
!define MUI_HEADERIMAGE_RIGHT

!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY

!define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\${APPNAME}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "vpype"

!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

!insertmacro MUI_PAGE_INSTFILES


!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

!insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "vpype Software" SecVpype
    SetOutPath $INSTDIR\vpype
    File /r "..\dist\vpype\*"

    SetOutPath $INSTDIR
    File "vpype.ico"
    File "uninstaller.ico"

    ;Create vpype shell path script
    FileOpen $0 $INSTDIR\vpype_shell.bat w
    FileWrite $0 "@echo off$\r$\n"
    FileWrite $0 'set "PATH=$INSTDIR\vpype;%PATH%"$\r$\n'
    FileClose $0

    ;Store installation folder
    WriteRegStr HKCU "Software\${APPNAME}" "" $INSTDIR

    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application

    ;Create shortcuts
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Uninstall vpype.lnk" "$INSTDIR\Uninstall.exe"

    ;Create vpype shell with path
    ReadEnvStr $0 COMSPEC
    SetOutPath $PROFILE
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\vpype Shell.lnk" "$0" '/k "$INSTDIR\vpype_shell.bat"' "$INSTDIR\vpype.ico"

    !insertmacro MUI_STARTMENU_WRITE_END

    ;Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ;Support add/remove programs
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
        "DisplayName" "vpype - The Swiss-Army-knife command-line tool for plotter vector graphics"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
        "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
        "QuietUninstallString" "$\"$INSTDIR\Uninstall.exe$\" /S"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
        "DisplayIcon" "$\"$INSTDIR\uninstaller.ico$\""
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
	WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
SectionEnd

Function .onInit
    ;Make the base section mandatory
    SectionSetFlags ${SecVpype} 17
FunctionEnd

Section "vpype Shell Desktop Shortcut" SecDesktop
    SetShellVarContext current
    ReadEnvStr $0 COMSPEC
    SetOutPath $PROFILE
    CreateShortcut "$DESKTOP\vpype Shell.lnk" "$0" '/k "$INSTDIR\vpype_shell.bat"' "$INSTDIR\vpype.ico"
SectionEnd

;--------------------------------
;Descriptions

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecVpype} "The complete vpype software distribution."
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "A Desktop shortcut to the vpype shell."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section "Uninstall"
  RMDir /r $INSTDIR\vpype
  Delete $INSTDIR\vpype.ico
  Delete $INSTDIR\uninstaller.ico
  Delete "$INSTDIR\vpype_shell.bat"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"

  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder

  Delete "$DESKTOP\vpype Shell.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\vpype Shell.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall vpype.lnk"
  RMDir "$SMPROGRAMS\$StartMenuFolder"


  DeleteRegKey /ifempty HKCU "Software\${APPNAME}"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd