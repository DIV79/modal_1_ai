@echo off
title GEMINI AI - Build Standalone Windows Executable
color 0B

echo ====================================================
echo   ✦ GEMINI AI Standalone Executable Builder ✦
echo ====================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/3] Ensuring dependencies and PyInstaller are installed...
pip install pyinstaller sounddevice numpy SpeechRecognition pyttsx3 requests pillow --quiet

echo.
echo [2/3] Building ARIA.exe using PyInstaller...
echo       This may take 1-2 minutes, please wait...
echo.

python -m PyInstaller --clean ARIA.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed! Check the output above.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo  [SUCCESS] ARIA.exe has been built successfully!
echo  Location: dist\ARIA.exe
echo ====================================================
echo.
pause
