@echo off
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Building EthosSoundCreator.exe ...
pyinstaller --onefile --windowed ^
    --name EthosSoundCreator ^
    --collect-all customtkinter ^
    --collect-all soundfile ^
    --hidden-import google.cloud.texttospeech ^
    app.py

echo.
echo Done. Executable is in dist\EthosSoundCreator.exe
pause
