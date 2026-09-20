@echo off
REM Запуск игры напрямую из исходников (без сборки exe).
REM Требуется Python 3.9+ с Tkinter (входит в стандартную установку с python.org).
cd /d "%~dp0battleship"
python main.py
pause
