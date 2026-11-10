import sys
import tkinter as tk

from sympy import (
    symbols, Eq, sqrt, sin, cos, tan, log, pi, E, exp, Abs,
    diff, integrate, solve, simplify, expand, factor, limit, oo,
    Integer, Float,
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application, convert_xor,
)


# ============ 想改大小，只改这两行 ============
WINDOW_W = 340          # 宽
WINDOW_H = 453          # 高（保持 H = W * 4 / 3 就是 3:4）
# ============================================

# ============ 想改输入/输出字号，改这两个 ============
ENTRY_FONT_SIZE  = 15   # 上方输入框字号
RESULT_FONT_SIZE = 12   # 下方结果字号
# ===================================================


def _enable_dpi_awareness():
    """Windows 上关闭系统 DPI 缩放，避免窗口被悄悄放大/缩小。"""
    if sys.platform != "win32":
        return
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(2)   # 2 = per-monitor DPI aware
    except Exception:
        try:
            from ctypes import windll
            windll.user32.SetProcessDPIAware()
        except Exception:
            pass


# ---------- 配色 ----------
BG         = "#1b1b1f"
BAR_BG     = "#25252b"
DISPLAY_BG = "#111114"
FG         = "#f2f2f2"
DIM        = "#8a8a94"
GREEN      = "#7ee787"

NUM_BG, NUM_FG = "#2c2c31", "#f2f2f2"
FN_BG,  FN_FG  = "#232327", "#d1d1d6"
OP_BG,  OP_FG  = "#3a3a42", "#ff9f0a"
EQ_BG,  EQ_FG  = "#0a84ff", "#ffffff"
CLR_BG, CLR_FG = "#3a2b2b", "#ff6b6b"

STYLE = {
    "num": (NUM_BG, NUM_FG),
    "fn":  (FN_BG,  FN_FG),
    "op":  (OP_BG,  OP_FG),
    "eq":  (EQ_BG,  EQ_FG),
    "clr": (CLR_BG, CLR_FG),
}

# ---------- SymPy 环境 ----------
x, y, n = symbols("x y n")

LOCAL_DICT = {
    "x": x, "y": y, "n": n,
    "pi": pi, "e": E, "E": E, "oo": oo,
    "sin": sin, "cos": cos, "tan": tan, "exp": exp, "abs": Abs,
    "sqrt": sqrt, "ln": log, "log": log,
    "diff": diff, "integrate": integrate, "solve": solve,
    "simplify": simplify, "expand": expand, "factor": factor,
    "limit": limit,
}

TRANSFORMS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

COMMAND_PREFIXES = ("solve(", "diff(", "integrate(", "limit(",
                    "simplify(", "factor(", "expand(")

BTN_LAYOUT = [
    [("C", "clear", "clr"), ("⌫", "back", "clr"), ("(", "ins:(", "fn"),
     (")", "ins:)", "fn"), ("^", "ins:^", "fn"), ("√", "ins:sqrt(", "fn")],

    [("sin", "ins:sin(", "fn"), ("cos", "ins:cos(", "fn"), ("tan", "ins:tan(", "fn"),
     ("ln", "ins:ln(", "fn"), ("log", "ins:log(", "fn"), ("π", "ins:pi", "fn")],

    [("7", "ins:7", "num"), ("8", "ins:8", "num"), ("9", "ins:9", "num"),
     ("÷", "ins:/", "op"), ("x", "ins:x", "fn"), ("e", "ins:e", "fn")],

    [("4", "ins:4", "num"), ("5", "ins:5", "num"), ("6", "ins:6", "num"),
     ("×", "ins:*", "op"), ("d/dx", "ins:diff(", "fn"), ("∫", "ins:integrate(", "fn")],

    [("1", "ins:1", "num"), ("2", "ins:2", "num"), ("3", "ins:3", "num"),
     ("−", "ins:-", "op"), ("slv", "ins:solve(", "fn"), ("simp", "ins:simplify(", "fn")],

    [("0", "ins:0", "num"), (".", "ins:.", "num"), ("+", "ins:+", "op"),
     ("fct", "ins:factor(", "fn"), ("=", "equals", "eq", 2)],
]


class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()

        # 1) 先藏起来，避免中间过程闪一下
        self.withdraw()

        self.title("SymPy")
        self.configure(bg=BG)

        self._pin = True
        self._drag_x = self._drag_y = 0

        self.expr_var = tk.StringVar()
        self.res_var = tk.StringVar()

        # 2) 建完所有控件
        self._build_titlebar()
        self._build_display()
        self._build_buttons()
        self._bind_keys()

        # 3) 控件的自然尺寸算完，再设窗口属性
        self.update_idletasks()
        self._apply_window_style()

        # 4) 最后才显示
        self.deiconify()
        self.after(150, self.entry.focus_force)

    # ---------- 窗口样式：无边框 + 置顶 + 固定尺寸 ----------
    def _apply_window_style(self):
        W, H = WINDOW_W, WINDOW_H
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()

        # 只在窗口真的装不下时才缩，留足余量
        max_w, max_h = int(sw * 0.6), int(sh * 0.8)
        if W > max_w or H > max_h:
            k = min(max_w / W, max_h / H)
            W, H = int(W * k), int(H * k)

        x_pos = max(0, sw - W - 32)
        y_pos = max(0, min(56, sh - H - 40))

        self.overrideredirect(True)
        self.resizable(False, False)
        self.geometry(f"{W}x{H}+{x_pos}+{y_pos}")
        self.attributes("-topmost", self._pin)
        self.update_idletasks()

    # ---------- 顶部拖动条 ----------
    def _build_titlebar(self):
        bar = tk.Frame(self, bg=BAR_BG, height=24)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        title = tk.Label(bar, text="SymPy", font=("Segoe UI", 9),
                         bg=BAR_BG, fg=DIM, padx=10)
        title.pack(side="left", fill="y")

        close = tk.Label(bar, text="✕", font=("Segoe UI", 9),
                         bg=BAR_BG, fg=DIM, padx=10, cursor="hand2")
        close.pack(side="right", fill="y")
        close.bind("<Button-1>", lambda e: self.destroy())
        close.bind("<Enter>", lambda e: close.configure(fg="#ff6b6b"))
        close.bind("<Leave>", lambda e: close.configure(fg=DIM))

        pin = tk.Label(bar, text="钉", font=("Segoe UI", 9),
                       bg=BAR_BG, fg=GREEN, padx=8, cursor="hand2")
        pin.pack(side="right", fill="y")
        pin.bind("<Button-1>", lambda e: self._toggle_pin(pin))

        for w in (bar, title):
            w.bind("<Button-1>", self._start_move)
            w.bind("<B1-Motion>", self._on_move)

    def _start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_move(self, event):
        nx = self.winfo_x() + event.x - self._drag_x
        ny = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{nx}+{ny}")

    def _toggle_pin(self, label):
        self._pin = not self._pin
        self.attributes("-topmost", self._pin)
        label.configure(fg=GREEN if self._pin else DIM)

    # ---------- 显示区 ----------
    def _build_display(self):
        frame = tk.Frame(self, bg=DISPLAY_BG, padx=10, pady=8)
        frame.pack(fill="x", padx=6, pady=(6, 3))

        self.entry = tk.Entry(
            frame, textvariable=self.expr_var,
            font=("Consolas", ENTRY_FONT_SIZE), bg=DISPLAY_BG, fg=FG,
            insertbackground=FG, bd=0, relief="flat", justify="right",
        )
        self.entry.pack(fill="x", ipady=4)

        self.result_label = tk.Label(
            frame, textvariable=self.res_var,
            font=("Consolas", RESULT_FONT_SIZE), bg=DISPLAY_BG, fg=GREEN,
            anchor="e", justify="right", wraplength=WINDOW_W - 40,
        )
        self.result_label.pack(fill="x", pady=(6, 0))

    # ---------- 按钮区 ----------
    def _build_buttons(self):
        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        cols = 6
        for c in range(cols):
            frame.columnconfigure(c, weight=1, uniform="btn")
        for r in range(len(BTN_LAYOUT)):
            frame.rowconfigure(r, weight=1, uniform="btn")

        for r, row in enumerate(BTN_LAYOUT):
            c = 0
            for item in row:
                text, action, kind = item[0], item[1], item[2]
                span = item[3] if len(item) > 3 else 1
                bg, fg = STYLE[kind]

                btn = tk.Button(
                    frame, text=text, font=("Segoe UI", 9, "bold"),
                    bg=bg, fg=fg, bd=0, relief="flat", cursor="hand2",
                    activebackground="#4a4a55", activeforeground="#ffffff",
                    takefocus=0,
                    command=lambda a=action: self._on_click(a),
                )
                btn.grid(row=r, column=c, columnspan=span,
                         sticky="nsew", padx=1, pady=1)
                c += span

    def _bind_keys(self):
        self.bind("<Return>", lambda e: self.evaluate())
        self.bind("<KP_Enter>", lambda e: self.evaluate())
        self.bind("<Escape>", lambda e: self._clear())
        self.bind("<Control-q>", lambda e: self.destroy())
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        if event.widget is self:
            self.result_label.configure(wraplength=max(100, event.width - 40))

    # ---------- 交互 ----------
    def _on_click(self, action):
        if action == "clear":
            self._clear()
        elif action == "back":
            self.expr_var.set(self.expr_var.get()[:-1])
        elif action == "equals":
            self.evaluate()
        elif action.startswith("ins:"):
            self._insert(action[4:])

    def _insert(self, text):
        self.entry.focus_set()
        self.entry.icursor("end")
        self.entry.insert("insert", text)

    def _clear(self):
        self.expr_var.set("")
        self.res_var.set("")
        self.entry.focus_set()

    # ---------- 计算 ----------
    def _parse(self, s):
        return parse_expr(s, local_dict=LOCAL_DICT,
                          transformations=TRANSFORMS)

    def _is_equation(self, s):
        if s.startswith(COMMAND_PREFIXES):
            return False
        if any(op in s for op in ("==", "<=", ">=", "!=")):
            return False
        return "=" in s

    def evaluate(self):
        raw = self.expr_var.get().strip()
        if not raw:
            return
        try:
            if self._is_equation(raw):
                left, right = raw.split("=", 1)
                res = solve(Eq(self._parse(left), self._parse(right)), x)
            else:
                res = self._parse(raw)
        except Exception as exc:
            self.res_var.set("错误：" + str(exc).split("\n")[0])
            return

        self.res_var.set(self._format(res))

    def _format(self, res):
        is_seq = isinstance(res, (list, tuple, set))
        items = list(res) if is_seq else [res]

        exact = "[" + ", ".join(str(i) for i in items) + "]" if is_seq else str(res)

        approx, need = [], False
        for it in items:
            if isinstance(it, (Integer, Float)):
                approx.append(str(it))
                continue
            try:
                v = it.evalf(10)
                if v.is_number:
                    approx.append(str(v))
                    need = True
                else:
                    approx.append(None)
            except Exception:
                approx.append(None)

        if need and all(a is not None for a in approx):
            a_str = "[" + ", ".join(approx) + "]" if is_seq else approx[0]
            return f"{exact}   ≈   {a_str}"
        return exact


if __name__ == "__main__":
    _enable_dpi_awareness()
    Calculator().mainloop()
