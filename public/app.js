let puzzleId = "easy1";
let givens = [];
let grid = Array.from({ length: 9 }, () => Array(9).fill(0));
let hasWon = false;

const $ = (sel) => document.querySelector(sel);

async function load() {
  const res = await fetch("/api/puzzle");
  const data = await res.json();
  puzzleId = data.id;
  givens = data.givens;
  grid = JSON.parse(JSON.stringify(givens));
  render();
}

function render() {
  const root = $("#grid");
  root.classList.add("board");
  root.innerHTML = "";
  buildBoard(root);
}

function buildBoard(root) {
  for (let br = 0; br < 3; br++) {
    for (let bc = 0; bc < 3; bc++) {
      const block = document.createElement("div");
      block.className = "block";
      for (let innerRow = 0; innerRow < 3; innerRow++) {
        for (let innerCol = 0; innerCol < 3; innerCol++) {
          const row = br * 3 + innerRow;
          const col = bc * 3 + innerCol;
          block.appendChild(createCell(row, col));
        }
      }
      root.appendChild(block);
    }
  }
}

function createCell(row, col) {
  const input = document.createElement("input");
  input.type = "text";
  input.inputMode = "numeric";
  input.maxLength = 1;
  input.autocomplete = "off";
  input.className = "cell";

  if (givens[row][col] !== 0) {
    input.value = givens[row][col];
    input.disabled = true;
    input.classList.add("fixed");
  } else {
    input.value = grid[row][col] || "";
    input.addEventListener("input", (event) => onInput(row, col, event.target));
    input.addEventListener("blur", (event) => {
      if (!event.target.value) event.target.classList.remove("ok", "err");
    });
  }
  return input;
}

function sanitizeValue(str) {
  const value = Number(str.replace(/[^1-9]/g, ""));
  return value || 0;
}

async function onInput(row, col, inputEl) {
  if (hasWon) return;
  const value = sanitizeValue(inputEl.value);
  inputEl.value = value || "";
  grid[row][col] = value;

  if (!value) {
    inputEl.classList.remove("ok", "err");
    return;
  }

  try {
    const res = await fetch("/api/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: puzzleId, row, col, value: grid[row][col] }),
    });
    const data = await res.json();
    inputEl.classList.remove("ok", "err");
    inputEl.classList.add(data.valid ? "ok" : "err");

    if (data.valid) {
      try {
        const res2 = await fetch("/api/check", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: puzzleId, grid }),
        });
        const chk = await res2.json();
        if (chk.complete && chk.valid) {
          showWin();
          hasWon = true;
        }
      } catch (_) {
        // ignore; keep validation styling intact
      }
    }
  } catch (err) {
    inputEl.classList.remove("ok", "err");
  }
}

function showWin() {
  const banner = $("#win-banner");
  if (!banner) return;
  banner.hidden = false;
  setTimeout(() => (banner.hidden = true), 4000);
  disableBoard();
}

function disableBoard() {
  document
    .querySelectorAll("#grid input.cell")
    .forEach((inp) => (inp.disabled = true));
}

document.addEventListener("DOMContentLoaded", load);
