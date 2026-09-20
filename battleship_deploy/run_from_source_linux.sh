#!/usr/bin/env bash
# Запуск игры напрямую из исходников (без сборки бинарника).
# Требуется: python3, python3-tk.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/battleship"
python3 main.py
