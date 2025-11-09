#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import List, Tuple
from copy import deepcopy

GRID_SIZE: int = 9
BOX_SIZE: int = 3

Grid = List[List[int]]

ROOT = Path(__file__).parent.resolve()
PUBLIC_DIR = ROOT / "public"
PUZZLES_DIR = ROOT / "puzzles"
DEFAULT_PUZZLE_ID = os.environ.get("PUZZLE_ID", "easy1")

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}

def in_range(index: int) -> bool:
    return 0 <= index < GRID_SIZE


def is_fixed(givens: Grid, row: int, col: int) -> bool:
    return givens[row][col] != 0


def box_top_left(row: int, col: int) -> Tuple[int, int]:
    return (row // BOX_SIZE) * BOX_SIZE, (col // BOX_SIZE) * BOX_SIZE


def is_valid_placement(grid: Grid, row: int, col: int, value: int) -> bool:
    if not (1 <= value <= 9):
        return False
    if not (in_range(row) and in_range(col)):
        return False

    for col_idx in range(GRID_SIZE):
        if col_idx != col and grid[row][col_idx] == value:
            return False

    for row_idx in range(GRID_SIZE):
        if row_idx != row and grid[row_idx][col] == value:
            return False

    start_row, start_col = box_top_left(row, col)
    for row_idx in range(start_row, start_row + BOX_SIZE):
        for col_idx in range(start_col, start_col + BOX_SIZE):
            if (row_idx != row or col_idx != col) and grid[row_idx][col_idx] == value:
                return False
    return True


def solve_sudoku(givens: Grid) -> Grid | None:
    grid = deepcopy(givens)

    def backtrack() -> bool:
        for row_idx in range(GRID_SIZE):
            for col_idx in range(GRID_SIZE):
                if grid[row_idx][col_idx] == 0:
                    for value in range(1, 10):
                        if is_valid_placement(grid, row_idx, col_idx, value):
                            grid[row_idx][col_idx] = value
                            if backtrack():
                                return True
                            grid[row_idx][col_idx] = 0
                    return False
        return True

    return grid if backtrack() else None


def normalize_grid(grid: Grid) -> Grid:
    if not (isinstance(grid, list) and len(grid) == GRID_SIZE):
        raise ValueError("grid_rows")
    norm: Grid = []
    for row in grid:
        if not (isinstance(row, list) and len(row) == GRID_SIZE):
            raise ValueError("grid_cols")
        norm_row: List[int] = []
        for value in row:
            if not isinstance(value, int) or value < 0 or value > 9:
                raise ValueError("grid_value")
            norm_row.append(value)
        norm.append(norm_row)
    return norm


def load_puzzles() -> dict[str, dict]:
    path = PUZZLES_DIR / f"{DEFAULT_PUZZLE_ID}.json"
    with open(path, "r", encoding="utf-8") as puzzle_file:
        return {DEFAULT_PUZZLE_ID: json.load(puzzle_file)}


PUZZLES = load_puzzles()

PUZZLE_SOLUTIONS: dict[str, Grid] = {}
for pid, puzzle in PUZZLES.items():
    solved = solve_sudoku(puzzle["givens"])
    if solved:
        PUZZLE_SOLUTIONS[pid] = solved
        print(f"[INFO] Solution generated: {pid}")
    else:
        print(f"[WARN] '{pid}' not solvable.")


class SudokuHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status: int, text: str) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/puzzle":
            puzzle = PUZZLES[DEFAULT_PUZZLE_ID]
            return self._send_json(200, {"id": puzzle["id"], "givens": puzzle["givens"]})
        if self._serve_static(path):
            return
        return self._send_text(404, "Not found")

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/validate":
            return self._handle_validate()
        if path == "/api/check":
            return self._handle_check()
        return self._send_text(404, "Not found")

    def _resolve(self, payload):
        pid = payload.get("id", DEFAULT_PUZZLE_ID)
        puzzle = PUZZLES.get(pid)
        solution = PUZZLE_SOLUTIONS.get(pid)
        if not puzzle or solution is None:
            self._send_json(500, {"error": "no_solution"})
            return None
        return puzzle, solution

    def _handle_validate(self):
        payload = self._read_json_body()
        resolved = self._resolve(payload)
        if not resolved:
            return
        puzzle, solution = resolved

        try:
            row = int(payload.get("row", -1))
            col = int(payload.get("col", -1))
            value = int(payload.get("value", 0))
        except (ValueError, TypeError):
            return self._send_json(400, {"error": "bad_request"})

        if not (in_range(row) and in_range(col)):
            return self._send_json(400, {"error": "out_of_range"})
        if is_fixed(puzzle["givens"], row, col):
            return self._send_json(200, {"valid": False, "reason": "fixed_cell"})

        if value == 0:
            return self._send_json(200, {"valid": True})

        expected = solution[row][col]
        return self._send_json(200, {"valid": (value == expected)})

    def _handle_check(self):
        payload = self._read_json_body()
        resolved = self._resolve(payload)
        if not resolved:
            return
        puzzle, solution = resolved

        try:
            client_grid = normalize_grid(payload.get("grid"))
        except Exception:
            return self._send_json(400, {"error": "bad_grid"})

        for row_idx in range(GRID_SIZE):
            for col_idx in range(GRID_SIZE):
                given_value = puzzle["givens"][row_idx][col_idx]
                if given_value and client_grid[row_idx][col_idx] != given_value:
                    return self._send_json(200, {"complete": False, "valid": False})

        all_filled = True
        all_correct = True
        for row_idx in range(GRID_SIZE):
            for col_idx in range(GRID_SIZE):
                value = client_grid[row_idx][col_idx]
                if value == 0:
                    all_filled = False
                elif value != solution[row_idx][col_idx]:
                    all_correct = False

        return self._send_json(200, {"complete": all_filled and all_correct, "valid": all_correct})

    def _serve_static(self, path: str) -> bool:
        target = PUBLIC_DIR / "index.html" if path == "/" else (ROOT / path.lstrip("/")).resolve()
        if not str(target).startswith(str(PUBLIC_DIR.resolve())):
            return False
        if not target.exists() or not target.is_file():
            return False
        ext = target.suffix.lower()
        ctype = CONTENT_TYPES.get(ext, "application/octet-stream")
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        return True


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), SudokuHandler)
    print(f"Server listening on :{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
