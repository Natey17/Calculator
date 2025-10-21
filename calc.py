#!/usr/bin/env python3
"""
Safe calculator: + - * / // % **, parentheses, ans, math funcs (sqrt,sin,cos,tan,log,ln)
Constants: pi, e. One-shot: `python calc.py -e "2*(3+4)"` or REPL.
"""
import ast, math, argparse, sys

ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
ALLOWED_UNARY = (ast.UAdd, ast.USub)
ALLOWED_FUNCS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log10, "ln": math.log
}
ALLOWED_NAMES = {"pi": math.pi, "e": math.e}

class SafeEval(ast.NodeVisitor):
    def __init__(self, names):
        self.names = {**ALLOWED_NAMES, **names}  # e.g., {"ans": last}

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("only numbers allowed")

    # Py<3.8 compatibility (optional)
    def visit_Num(self, node):  # type: ignore
        return node.n

    def visit_BinOp(self, node):
        left, right = self.visit(node.left), self.visit(node.right)
        op = node.op
        if isinstance(op, ast.Add):   return left + right
        if isinstance(op, ast.Sub):   return left - right
        if isinstance(op, ast.Mult):  return left * right
        if isinstance(op, ast.Div):   return left / right
        if isinstance(op, ast.FloorDiv): return left // right
        if isinstance(op, ast.Mod):   return left % right
        if isinstance(op, ast.Pow):   return left ** right
        raise ValueError("operator not allowed")

    def visit_UnaryOp(self, node):
        val = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd): return +val
        if isinstance(node.op, ast.USub): return -val
        raise ValueError("unary operator not allowed")

    def visit_Name(self, node):
        if node.id in self.names:
            return self.names[node.id]
        raise ValueError(f"name '{node.id}' not allowed")

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise ValueError("function not allowed")
        fname = node.func.id
        if fname not in ALLOWED_FUNCS:
            raise ValueError(f"function '{fname}' not allowed")
        if not (0 < len(node.args) <= 2) or node.keywords:
            raise ValueError("bad function arity")
        args = [self.visit(a) for a in node.args]
        return ALLOWED_FUNCS[fname](*args)

    # Block anything else
    def generic_visit(self, node):
        forbidden = (
            ast.Assign, ast.Attribute, ast.Subscript, ast.List, ast.Dict, ast.Tuple,
            ast.Lambda, ast.IfExp, ast.Compare, ast.BoolOp, ast.And, ast.Or,
            ast.While, ast.For, ast.If, ast.With, ast.Import, ast.ImportFrom,
            ast.FunctionDef, ast.ClassDef, ast.Module, ast.Expr
        )
        if isinstance(node, forbidden):
            raise ValueError("syntax not allowed")
        return super().generic_visit(node)

def safe_eval(expr: str, names):
    tree = ast.parse(expr, mode="eval")
    return SafeEval(names).visit(tree)

def format_num(x):
    # Keep ~12 sig figs, avoid long floats
    try:
        if x == int(x):
            return str(int(x))
    except Exception:
        pass
    s = f"{float(x):.12g}"
    return s

def run_oneshot(expr):
    try:
        val = safe_eval(expr, names={})
        print(format_num(val))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def run_repl():
    print("Calc REPL. Ops: + - * / // % **, funcs: sqrt sin cos tan log ln, consts: pi e, var: ans")
    print("Ctrl+C or Ctrl+D to exit.")
    ans = 0.0
    while True:
        try:
            line = input("> ").strip()
            if not line:
                continue
            val = safe_eval(line, names={"ans": ans})
            ans = float(val)
            print(format_num(ans))
        except (EOFError, KeyboardInterrupt):
            print()
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    ap = argparse.ArgumentParser(description="Safe Python calculator")
    ap.add_argument("-e", "--expr", help='evaluate a single expression, e.g. -e "2*(3+4)"')
    args = ap.parse_args()
    if args.expr:
        run_oneshot(args.expr)
    else:
        run_repl()

if __name__ == "__main__":
    main()
