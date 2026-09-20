@echo off
REM =====================================================================
REM  Сборка Battleship.exe (Windows)
REM  Запускать из папки, где лежит этот файл (build_windows.bat).
REM  Требуется: Python 3.9+ установленный и добавленный в PATH.
REM =====================================================================

setlocal

echo [1/5] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден в PATH.
    echo Установите Python с https://www.python.org/downloads/windows/
    echo и отметьте галочку "Add python.exe to PATH" при установке.
    pause
    exit /b 1
)

echo [2/5] Создание виртуального окружения (.venv_build)...
python -m venv .venv_build
call .venv_build\Scripts\activate.bat

echo [3/5] Установка PyInstaller...
python -m pip install --upgrade pip >nul
python -m pip install pyinstaller

echo [4/5] Сборка исполняемого файла...
pyinstaller --noconfirm --onefile --windowed ^
    --name Battleship ^
    --distpath dist_windows ^
    --workpath build_windows_tmp ^
    battleship\main.py

echo [5/5] Готово. Исполняемый файл находится в dist_windows\Battleship.exe
echo Скопируйте dist_windows\Battleship.exe на клиентскую машину и запустите.
echo (config.json и scores.json будут созданы автоматически рядом с exe
echo  при первом запуске.)

call .venv_build\Scripts\deactivate.bat
pause
