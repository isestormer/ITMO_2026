import tkinter as tk
from tkinter import ttk, colorchooser, messagebox

import config as cfg
import scores as scores_mod
from logic import Board, ComputerPlayer, EMPTY, SHIP, MISS, HIT


class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_data = cfg.load_config()
        self.title("Морской бой")
        self.geometry(f"{self.config_data['window_width']}x{self.config_data['window_height']}")
        self.resizable(False, False)
        self.configure(bg=self.config_data["bg_color"])
        self._build_ui()

    def _build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        font_big = (self.config_data["font_family"], self.config_data["font_size"] + 12, "bold")
        font_btn = (self.config_data["font_family"], self.config_data["font_size"] + 2)

        title = tk.Label(
            self, text="МОРСКОЙ БОЙ", font=font_big,
            bg=self.config_data["bg_color"], fg="white",
        )
        title.pack(pady=60)

        btn_frame = tk.Frame(self, bg=self.config_data["bg_color"])
        btn_frame.pack()

        buttons = [
            ("Играть", self.open_game),
            ("Настройки", self.open_settings),
            ("Рекорды", self.open_scores),
            ("Выход", self.destroy),
        ]
        for text, command in buttons:
            b = tk.Button(
                btn_frame, text=text, font=font_btn, width=18, command=command,
                bg="white", activebackground="#e0e0e0",
            )
            b.pack(pady=8)

    def refresh(self):
        self.config_data = cfg.load_config()
        self.geometry(f"{self.config_data['window_width']}x{self.config_data['window_height']}")
        self.configure(bg=self.config_data["bg_color"])
        self._build_ui()

    def open_game(self):
        GameWindow(self, self.config_data)

    def open_settings(self):
        SettingsWindow(self)

    def open_scores(self):
        ScoresWindow(self)


class SettingsWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_app = master
        self.title("Настройки")
        self.geometry("420x560")
        self.resizable(False, False)
        self.config_data = cfg.load_config()
        self.color_vars = {}
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        tk.Label(self, text="Имя игрока:").grid(row=0, column=0, sticky="w", **pad)
        self.name_var = tk.StringVar(value=self.config_data["player_name"])
        tk.Entry(self, textvariable=self.name_var).grid(row=0, column=1, **pad)

        tk.Label(self, text="Ширина окна:").grid(row=1, column=0, sticky="w", **pad)
        self.width_var = tk.IntVar(value=self.config_data["window_width"])
        tk.Spinbox(self, from_=700, to=1600, textvariable=self.width_var, width=10).grid(row=1, column=1, **pad)

        tk.Label(self, text="Высота окна:").grid(row=2, column=0, sticky="w", **pad)
        self.height_var = tk.IntVar(value=self.config_data["window_height"])
        tk.Spinbox(self, from_=500, to=1200, textvariable=self.height_var, width=10).grid(row=2, column=1, **pad)

        tk.Label(self, text="Кол-во кораблей (1-10):").grid(row=3, column=0, sticky="w", **pad)
        self.ships_var = tk.IntVar(value=self.config_data["ship_count"])
        tk.Spinbox(self, from_=1, to=10, textvariable=self.ships_var, width=10).grid(row=3, column=1, **pad)

        tk.Label(self, text="Сложность:").grid(row=4, column=0, sticky="w", **pad)
        self.diff_var = tk.StringVar(value=self.config_data["difficulty"])
        ttk.Combobox(
            self, textvariable=self.diff_var, state="readonly",
            values=["easy", "medium", "hard"], width=10,
        ).grid(row=4, column=1, **pad)

        tk.Label(self, text="Размер клетки поля:").grid(row=5, column=0, sticky="w", **pad)
        self.cell_var = tk.IntVar(value=self.config_data["cell_size"])
        tk.Spinbox(self, from_=20, to=50, textvariable=self.cell_var, width=10).grid(row=5, column=1, **pad)

        tk.Label(self, text="Шрифт:").grid(row=6, column=0, sticky="w", **pad)
        self.font_var = tk.StringVar(value=self.config_data["font_family"])
        ttk.Combobox(
            self, textvariable=self.font_var, state="readonly",
            values=["Arial", "Helvetica", "Times New Roman", "Courier New"], width=15,
        ).grid(row=6, column=1, **pad)

        tk.Label(self, text="Размер шрифта:").grid(row=7, column=0, sticky="w", **pad)
        self.font_size_var = tk.IntVar(value=self.config_data["font_size"])
        tk.Spinbox(self, from_=8, to=24, textvariable=self.font_size_var, width=10).grid(row=7, column=1, **pad)

        color_row = 8
        for key, label in (
            ("bg_color", "Цвет фона"),
            ("ship_color", "Цвет корабля"),
            ("hit_color", "Цвет попадания"),
            ("miss_color", "Цвет промаха"),
        ):
            tk.Label(self, text=label + ":").grid(row=color_row, column=0, sticky="w", **pad)
            self.color_vars[key] = tk.StringVar(value=self.config_data[key])
            swatch = tk.Label(self, textvariable=self.color_vars[key], width=10, relief="solid")
            swatch.grid(row=color_row, column=1, sticky="w", **pad)

            def make_picker(k=key, sw=swatch):
                def pick():
                    result = colorchooser.askcolor(color=self.color_vars[k].get())
                    if result and result[1]:
                        self.color_vars[k].set(result[1])
                        sw.configure(bg=result[1])
                return pick

            swatch.configure(bg=self.config_data[key])
            swatch.bind("<Button-1>", lambda e, p=make_picker(): p())
            color_row += 1

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=color_row, column=0, columnspan=2, pady=20)
        tk.Button(btn_frame, text="Сохранить", command=self.save, width=14).pack(side="left", padx=6)
        tk.Button(btn_frame, text="По умолчанию", command=self.reset_defaults, width=14).pack(side="left", padx=6)

    def save(self):
        self.config_data.update({
            "player_name": self.name_var.get().strip() or "Игрок",
            "window_width": self.width_var.get(),
            "window_height": self.height_var.get(),
            "ship_count": self.ships_var.get(),
            "difficulty": self.diff_var.get(),
            "cell_size": self.cell_var.get(),
            "font_family": self.font_var.get(),
            "font_size": self.font_size_var.get(),
        })
        for key, var in self.color_vars.items():
            self.config_data[key] = var.get()

        cfg.save_config(self.config_data)
        messagebox.showinfo("Настройки", "Настройки сохранены.")
        self.master_app.refresh()
        self.destroy()

    def reset_defaults(self):
        self.config_data = cfg.DEFAULT_CONFIG.copy()
        self.destroy()
        SettingsWindow(self.master_app)


class ScoresWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Рекорды")
        self.geometry("420x400")
        self.resizable(False, False)

        tk.Label(self, text="Лучшие результаты (победы, меньше ходов — лучше)",
                 font=("Arial", 11, "bold")).pack(pady=10)

        columns = ("place", "name", "moves", "date")
        tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        tree.heading("place", text="#")
        tree.heading("name", text="Игрок")
        tree.heading("moves", text="Ходов")
        tree.heading("date", text="Дата")
        tree.column("place", width=30, anchor="center")
        tree.column("name", width=140)
        tree.column("moves", width=70, anchor="center")
        tree.column("date", width=140, anchor="center")
        tree.pack(padx=10, pady=10, fill="both", expand=True)

        best = scores_mod.best_scores(15)
        if not best:
            tk.Label(self, text="Пока нет завершённых побед.").pack()
        for i, rec in enumerate(best, start=1):
            tree.insert("", "end", values=(i, rec["name"], rec["moves"], rec["date"]))


class GameWindow(tk.Toplevel):
    def __init__(self, master, config_data):
        super().__init__(master)
        self.master_app = master
        self.cfg = config_data
        self.title("Морской бой — игра")
        self.resizable(False, False)
        self.configure(bg=self.cfg["bg_color"])

        self.size = self.cfg["board_size"]
        self.cell = self.cfg["cell_size"]
        self.fleet = cfg.fleet_for_count(self.cfg["ship_count"])

        self.player_board = Board(self.size)
        self.computer_board = Board(self.size)
        self.computer = ComputerPlayer(self.size, self.cfg["difficulty"])

        self.player_moves = 0
        self.game_over = False

        self._new_layout()
        self._build_ui()

    def _new_layout(self):
        self.player_board = Board(self.size)
        self.computer_board = Board(self.size)
        self.player_board.place_ships_randomly(self.fleet)
        self.computer_board.place_ships_randomly(self.fleet)
        self.computer = ComputerPlayer(self.size, self.cfg["difficulty"])
        self.player_moves = 0
        self.game_over = False

    def _build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        font_lbl = (self.cfg["font_family"], self.cfg["font_size"] + 2, "bold")

        top = tk.Frame(self, bg=self.cfg["bg_color"])
        top.pack(pady=10)
        self.status_var = tk.StringVar(value="Ваш ход! Стреляйте по правому полю.")
        tk.Label(top, textvariable=self.status_var, font=font_lbl,
                 bg=self.cfg["bg_color"], fg="white").pack()

        boards_frame = tk.Frame(self, bg=self.cfg["bg_color"])
        boards_frame.pack(padx=20, pady=10)

        left = tk.Frame(boards_frame, bg=self.cfg["bg_color"])
        left.grid(row=0, column=0, padx=20)
        tk.Label(left, text="Ваше поле", font=font_lbl,
                 bg=self.cfg["bg_color"], fg="white").pack()
        self.player_canvas = tk.Canvas(
            left, width=self.size * self.cell, height=self.size * self.cell,
            bg="#dfe7f5", highlightthickness=1, highlightbackground="black",
        )
        self.player_canvas.pack()

        right = tk.Frame(boards_frame, bg=self.cfg["bg_color"])
        right.grid(row=0, column=1, padx=20)
        tk.Label(right, text="Поле противника", font=font_lbl,
                 bg=self.cfg["bg_color"], fg="white").pack()
        self.enemy_canvas = tk.Canvas(
            right, width=self.size * self.cell, height=self.size * self.cell,
            bg="#dfe7f5", highlightthickness=1, highlightbackground="black",
        )
        self.enemy_canvas.pack()
        self.enemy_canvas.bind("<Button-1>", self.on_enemy_click)

        bottom = tk.Frame(self, bg=self.cfg["bg_color"])
        bottom.pack(pady=10)
        tk.Button(bottom, text="Новая игра", command=self.restart).pack(side="left", padx=6)
        tk.Button(bottom, text="В меню", command=self.back_to_menu).pack(side="left", padx=6)

        self.draw_boards()

    def draw_boards(self):
        self._draw_board(self.player_canvas, self.player_board, reveal=True)
        self._draw_board(self.enemy_canvas, self.computer_board, reveal=False)

    def _draw_board(self, canvas, board, reveal):
        canvas.delete("all")
        c = self.cell
        sunk_cells = board.ship_cells_of_sunk_ships()
        for y in range(board.size):
            for x in range(board.size):
                x0, y0 = x * c, y * c
                x1, y1 = x0 + c, y0 + c
                state = board.grid[y][x]
                color = "#dfe7f5"
                if state == SHIP and reveal:
                    color = self.cfg["ship_color"]
                elif state == HIT or (x, y) in sunk_cells:
                    color = self.cfg["hit_color"]
                elif state == MISS:
                    color = self.cfg["miss_color"]
                canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="#8899aa")

    def on_enemy_click(self, event):
        if self.game_over:
            return
        x = event.x // self.cell
        y = event.y // self.cell
        if not (0 <= x < self.size and 0 <= y < self.size):
            return

        result = self.computer_board.shoot(x, y)
        if result == "repeat":
            self.status_var.set("Вы уже стреляли сюда. Выберите другую клетку.")
            return

        self.player_moves += 1
        self.draw_boards()

        if result == "sunk":
            self.status_var.set("Потопили корабль! Стреляйте ещё раз.")
        elif result == "hit":
            self.status_var.set("Попадание! Стреляйте ещё раз.")
        else:
            self.status_var.set("Промах. Ход противника...")

        if self.computer_board.all_sunk():
            self.finish_game(won=True)
            return

        if result == "miss":
            self.after(600, self.computer_turn)

    def computer_turn(self):
        if self.game_over:
            return
        while True:
            x, y = self.computer.choose_shot()
            result = self.player_board.shoot(x, y)
            self.computer.register_result((x, y), result)
            self.draw_boards()
            if self.player_board.all_sunk():
                self.finish_game(won=False)
                return
            if result == "miss":
                self.status_var.set("Компьютер промахнулся. Ваш ход!")
                break
            else:
                self.status_var.set("Компьютер попал! Он стреляет ещё раз...")

    def finish_game(self, won):
        self.game_over = True
        name = self.cfg["player_name"]
        if won:
            scores_mod.add_result(name, "win", self.player_moves)
            messagebox.showinfo("Победа!", f"Поздравляем, {name}! Вы потопили весь флот за {self.player_moves} ходов.")
        else:
            scores_mod.add_result(name, "loss", self.player_moves)
            messagebox.showinfo("Поражение", "Компьютер потопил все ваши корабли. Попробуйте снова!")
        self.status_var.set("Игра окончена. Нажмите «Новая игра» или «В меню».")

    def restart(self):
        self._new_layout()
        self.draw_boards()
        self.status_var.set("Новая игра! Ваш ход.")

    def back_to_menu(self):
        self.destroy()
