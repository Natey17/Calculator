#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import ast, math

# ---------- Safe evaluator ----------
ALLOWED_FUNCS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log10, "ln": math.log
}
ALLOWED_NAMES = {"pi": math.pi, "e": math.e}

class SafeEval(ast.NodeVisitor):
    def __init__(self, names):
        self.names = {**ALLOWED_NAMES, **names}

    def visit_Expression(self, node): return self.visit(node.body)
    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)): return node.value
        raise ValueError("only numbers allowed")
    def visit_Num(self, node):  # py<3.8
        return node.n
    def visit_BinOp(self, node):
        a, b, op = self.visit(node.left), self.visit(node.right), node.op
        if   isinstance(op, ast.Add):  return a + b
        elif isinstance(op, ast.Sub):  return a - b
        elif isinstance(op, ast.Mult): return a * b
        elif isinstance(op, ast.Div):  return a / b
        elif isinstance(op, ast.FloorDiv): return a // b
        elif isinstance(op, ast.Mod):  return a % b
        elif isinstance(op, ast.Pow):  return a ** b
        raise ValueError("operator not allowed")
    def visit_UnaryOp(self, node):
        v, op = self.visit(node.operand), node.op
        if   isinstance(op, ast.UAdd): return +v
        elif isinstance(op, ast.USub): return -v
        raise ValueError("unary operator not allowed")
    def visit_Name(self, node):
        if node.id in self.names: return self.names[node.id]
        raise ValueError(f"name '{node.id}' not allowed")
    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name): raise ValueError("function not allowed")
        f = node.func.id
        if f not in ALLOWED_FUNCS: raise ValueError(f"function '{f}' not allowed")
        if node.keywords: raise ValueError("no keyword args")
        args = [self.visit(a) for a in node.args]
        return ALLOWED_FUNCS[f](*args)
    def generic_visit(self, node):
        forbidden = (
            ast.Assign, ast.Attribute, ast.Subscript, ast.List, ast.Dict, ast.Tuple,
            ast.Lambda, ast.IfExp, ast.Compare, ast.BoolOp, ast.And, ast.Or,
            ast.While, ast.For, ast.If, ast.With, ast.Import, ast.ImportFrom,
            ast.FunctionDef, ast.ClassDef, ast.Module, ast.Expr
        )
        if isinstance(node, forbidden): raise ValueError("syntax not allowed")
        return super().generic_visit(node)

def safe_eval(expr: str, names):
    # allow % as percent of previous number: 50% -> (50*0.01)
    expr = percent_to_mul(expr)
    tree = ast.parse(expr, mode="eval")
    return SafeEval(names).visit(tree)

def percent_to_mul(s: str):
    import re
    return re.sub(r'(\d+(?:\.\d+)?)%', r'(\1*0.01)', s)

def fmt_num(x):
    try:
        if float(x).is_integer():
            return str(int(x))
    except Exception:
        pass
    return f"{float(x):.12g}"

# ---------- UI ----------
class CalcApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculator")
        self.resizable(False, False)

        self.themes = {
            "light": {
                "bg":"#f6f7fb","card":"#ffffff","fg":"#111","muted":"#555",
                "btn":"#f0f2f7","op":"#e4ecff","eq":"#c7f3d9","border":"#dfe3f0"
            },
            "dark": {
                "bg":"#0f1220","card":"#171c2f","fg":"#e8ecf3","muted":"#95a0b8",
                "btn":"#0f1538","op":"#0e1a44","eq":"#1b5e3a","border":"#22294a"
            }
        }
        self.mode = tk.StringVar(value="dark")

        self.expr = tk.StringVar(value="")
        self.last_result = 0.0
        self.history = []  # list of (expr, result)

        self.build_ui()
        self.apply_theme()
        self.bind_events()

    def build_ui(self):
        # Theme toggle
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,0))
        ttk.Label(top, text="Theme:").pack(side="left")
        ttk.Checkbutton(top, text="Dark Mode", variable=self.mode,
                        onvalue="dark", offvalue="light", command=self.apply_theme).pack(side="left", padx=6)

        # Main container
        wrap = ttk.Frame(self)
        wrap.grid(row=1, column=0, padx=10, pady=10)

        # Left: display + keys
        left = ttk.Frame(wrap)
        left.grid(row=0, column=0, sticky="n")

        self.history_line = tk.Label(left, anchor="e", font=("Segoe UI", 10))
        self.history_line.grid(row=0, column=0, columnspan=4, sticky="ew", padx=6, pady=(0,2))

        self.screen = tk.Entry(left, textvariable=self.expr, justify="right", font=("Segoe UI", 20))
        self.screen.grid(row=1, column=0, columnspan=4, sticky="ew", padx=6, pady=(0,8))

        buttons = [
            ("AC","ac"), ("DEL","del"), ("%","%"),   ("÷","/"),
            ("7","7"),  ("8","8"),   ("9","9"),      ("×","*"),
            ("4","4"),  ("5","5"),   ("6","6"),      ("−","-"),
            ("1","1"),  ("2","2"),   ("3","3"),      ("+","+"),
            ("(","("),  ("0","0"),   (")",")"),      ("=","="),
            (".","."),
        ]

        self.btns = []
        r = 2; c = 0
        for label, val in buttons:
            btn = tk.Button(left, text=label, command=lambda v=val: self.on_key(v))
            self.btns.append(btn)
            if label == ".":
                btn.grid(row=r+4, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
            else:
                btn.grid(row=r, column=c, sticky="ew", padx=4, pady=4)
                c += 1
                if c == 4:
                    c = 0; r += 1

        for col in range(4):
            left.grid_columnconfigure(col, weight=1)

        # Right: history list
        right = ttk.Frame(wrap)
        right.grid(row=0, column=1, padx=(10,0), sticky="ns")
        ttk.Label(right, text="History").grid(row=0, column=0, sticky="w")
        self.hlist = tk.Listbox(right, height=15, width=28, activestyle="none")
        self.hlist.grid(row=1, column=0, sticky="ns")
        ttk.Button(right, text="Use Selected", command=self.use_selected).grid(row=2, column=0, pady=6, sticky="ew")
        ttk.Button(right, text="Clear History", command=self.clear_history).grid(row=3, column=0, sticky="ew")

    def apply_theme(self):
        t = self.themes[self.mode.get()]
        self.configure(bg=t["bg"])
        for w in self.winfo_children():
            w.configure(background=t["bg"])
        # cards and borders
        for frame in self.winfo_children():
            for sub in frame.winfo_children():
                try:
                    sub.configure(background=t["bg"], foreground=t["fg"])
                except tk.TclError:
                    pass
        # specific widgets
        self.history_line.configure(bg=t["card"], fg=t["muted"], bd=1, relief="solid", highlightthickness=0)
        self.screen.configure(bg=t["card"], fg=t["fg"], bd=1, relief="solid", insertbackground=t["fg"],
                              highlightthickness=0)
        # buttons
        for b in self.btns:
            txt = b.cget("text")
            bg = t["btn"]; fg = t["fg"]; bd = t["border"]
            if txt in ("÷","×","−","+"): bg = t["op"]
            if txt == "=": bg = t["eq"]
            b.configure(bg=bg, fg=fg, activebackground=bg, activeforeground=fg,
                        relief="raised", bd=1, highlightthickness=0)
        # listbox
        self.hlist.configure(bg=t["card"], fg=t["fg"], bd=1, highlightthickness=0, selectbackground="#448aff")

    def bind_events(self):
        self.bind("<Key>", self.on_keypress)
        self.bind("<Return>", lambda e: self.on_key("="))
        self.bind("<BackSpace>", lambda e: self.on_key("del"))
        self.bind("<Escape>", lambda e: self.on_key("ac"))
        # allow comma as dot
        self.bind(",", lambda e: self.on_key("."))

    # ---------- actions ----------
    def on_keypress(self, e):
        k = e.keysym
        ch = e.char
        if ch and ch in "0123456789.+-*/()%()":
            self.on_key(ch)
        elif k in ("KP_Add","KP_Subtract","KP_Multiply","KP_Divide"):
            m = { "KP_Add":"+","KP_Subtract":"-","KP_Multiply":"*","KP_Divide":"/" }
            self.on_key(m[k])

    def on_key(self, token):
        if token == "ac":
            self.expr.set("")
            self.history_line.config(text="")
            return
        if token == "del":
            self.expr.set(self.expr.get()[:-1])
            return
        if token == "=":
            self.equals()
            return
        # normal append
        self.expr.set(self.expr.get() + token)

    def equals(self):
        s = self.expr.get().strip()
        if not s: return
        try:
            val = safe_eval(s, names={"ans": self.last_result})
            self.last_result = float(val)
            res = fmt_num(self.last_result)
            self.history_line.config(text=f"{s} =")
            self.expr.set(res)
            self.push_history(s, res)
        except Exception as e:
            self.flash_error(str(e))

    def flash_error(self, msg):
        messagebox.showerror("Error", msg)

    def push_history(self, s, res):
        self.history.append((s, res))
        self.hlist.insert(0, f"{s} = {res}")

    def use_selected(self):
        idx = self.hlist.curselection()
        if not idx: return
        item = self.hlist.get(idx[0])
        # put result back into input
        try:
            res = item.split("=", 1)[1].strip()
            self.expr.set(res)
            self.screen.icursor(tk.END)
        except Exception:
            pass

    def clear_history(self):
        self.history.clear()
        self.hlist.delete(0, tk.END)

if __name__ == "__main__":
    app = CalcApp()
    app.mainloop()
