@ECHO OFF
CD "%USERPROFILE%\VLC_Rich"
CALL .\vlc_rich\Scripts\activate.bat
pythonw.exe vlc_rich.pyw /p <vlc_interface_password>
@ECHO ON
