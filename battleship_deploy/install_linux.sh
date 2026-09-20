#!/usr/bin/env bash
# =========================================================================
#  Установка "Морского боя" для текущего пользователя Linux.
#  Собирает бинарник (если ещё не собран), копирует его в ~/.local/bin
#  и добавляет ярлык в меню приложений.
#  Запуск: ./install_linux.sh
# =========================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "dist_linux/battleship" ]; then
    echo "Бинарник не найден, собираю..."
    ./build_linux.sh
fi

INSTALL_DIR="$HOME/.local/share/battleship"
BIN_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$HOME/.local/share/applications"

cp dist_linux/battleship "$INSTALL_DIR/battleship"
chmod +x "$INSTALL_DIR/battleship"
ln -sf "$INSTALL_DIR/battleship" "$BIN_DIR/battleship"

cat > "$HOME/.local/share/applications/battleship.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Морской бой
Comment=Игра "Морской бой" против компьютера
Exec=$INSTALL_DIR/battleship
Terminal=false
Categories=Game;
EOF

echo "Установка завершена."
echo "Запуск из терминала: battleship  (если ~/.local/bin есть в PATH)"
echo "Либо найдите «Морской бой» в меню приложений."
