#!/usr/bin/env bash
# =========================================================================
#  Сборка автономного бинарника Battleship (Linux)
#  Запускать из папки, где лежит этот файл: ./build_linux.sh
#  Требуется: python3, python3-venv, python3-tk (пакет Tk для python3).
# =========================================================================
set -e

echo "[1/5] Проверка Python и Tk..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "ОШИБКА: python3 не найден. Установите: sudo apt install python3 python3-venv python3-tk"
    exit 1
fi
python3 -c "import tkinter" 2>/dev/null || {
    echo "ОШИБКА: модуль tkinter не найден."
    echo "Установите: sudo apt install python3-tk   (Debian/Ubuntu)"
    echo "            sudo dnf install python3-tkinter  (Fedora)"
    exit 1
}

echo "[2/5] Создание виртуального окружения (.venv_build)..."
python3 -m venv .venv_build
source .venv_build/bin/activate

echo "[3/5] Установка PyInstaller..."
pip install --upgrade pip >/dev/null
pip install pyinstaller

echo "[4/5] Сборка исполняемого файла..."
pyinstaller --noconfirm --onefile --windowed \
    --name battleship \
    --distpath dist_linux \
    --workpath build_linux_tmp \
    battleship/main.py

echo "[5/5] Готово. Исполняемый файл: dist_linux/battleship"
chmod +x dist_linux/battleship

deactivate

cat <<EOF

Готово! Запуск: ./dist_linux/battleship
(config.json и scores.json создаются автоматически рядом с бинарником)

Чтобы добавить ярлык в меню приложений, см. install_linux.sh
или руководство администратора.
EOF
