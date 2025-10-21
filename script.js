const screen = document.getElementById("screen");
const history = document.getElementById("history");
const keys = document.querySelector(".keys");

let expr = "";         // current expression
let lastResult = null; // last evaluated result

function render() {
  screen.textContent = expr || "0";
}

function append(token) {
  expr += token;
  render();
}

function clearAll() {
  expr = "";
  render();
}

function delOne() {
  expr = expr.slice(0, -1);
  render();
}

function normalizePercent(s) {
  // Replace standalone number% with (number*0.01)
  return s.replace(/(\d+(?:\.\d+)?)%/g, "($1*0.01)");
}

function sanitize(s) {
  // Allow only digits, operators, parentheses, dot, spaces, percent
  if (!/^[\d+\-*/().%\s]+$/.test(s)) throw new Error("Invalid input");
  return s;
}

function safeEval(s) {
  const cleaned = sanitize(normalizePercent(s));
  // Prevent invalid operator sequences like "*/" or ".."
  if (/[/*+\-]{2,}$/.test(cleaned)) throw new Error("Trailing operator");
  // Evaluate using Function for a bit more control than eval
  // eslint-disable-next-line no-new-func
  const val = Function(`"use strict";return (${cleaned});`)();
  if (!isFinite(val)) throw new Error("Invalid result");
  return val;
}

function formatNumber(n) {
  // Fit nicely on screen, keep precision
  const abs = Math.abs(n);
  if (abs !== 0 && (abs >= 1e12 || abs < 1e-6)) return n.toExponential(6);
  // Limit to ~12 significant digits
  const s = Number(n.toPrecision(12)).toString();
  return s;
}

function equals() {
  if (!expr) return;
  try {
    const result = safeEval(expr);
    history.textContent = expr + " =";
    lastResult = result;
    expr = formatNumber(result);
    // flash effect
    screen.style.opacity = "0.8";
    setTimeout(() => (screen.style.opacity = "1"), 90);
    render();
  } catch (e) {
    history.textContent = "";
    expr = "Error";
    render();
    setTimeout(() => { expr = ""; render(); }, 700);
  }
}

// Clicks
keys.addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  const key = b.dataset.key;
  const act = b.dataset.act;
  if (key) append(key);
  else if (act === "ac") clearAll();
  else if (act === "del") delOne();
  else if (act === "eq") equals();
});

// Keyboard
window.addEventListener("keydown", (e) => {
  const k = e.key;
  if (/[\d+\-*/().%]/.test(k)) { append(k); e.preventDefault(); }
  else if (k === "Enter" || k === "=") { equals(); e.preventDefault(); }
  else if (k === "Backspace") { delOne(); e.preventDefault(); }
  else if (k.toLowerCase() === "c") { clearAll(); }
  else if (k === ",") { append("."); e.preventDefault(); }
});

// Start
render();
