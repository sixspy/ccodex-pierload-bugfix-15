"""统计业务源码行数（不含 vendor / tests / Docker / README）。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "tests",
    "scripts",
    ".git",
    "data",
}
SKIP_NAMES = {"vue.global.prod.js", "README.md", "Dockerfile"}
SKIP_SUFFIX = {".md"}


def iter_files():
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        parts = set(p.relative_to(ROOT).parts)
        if parts & SKIP_PARTS:
            continue
        if p.name in SKIP_NAMES or p.name.startswith("_build"):
            continue
        if p.suffix in SKIP_SUFFIX:
            continue
        if p.suffix in {".py", ".js", ".html", ".css", ".json"}:
            if p.suffix == ".json" and "fixtures" not in p.parts:
                continue
            yield p


def main() -> None:
    total = 0
    by_ext: dict[str, int] = {}
    for p in sorted(iter_files()):
        n = len(p.read_text(encoding="utf-8").splitlines())
        total += n
        by_ext[p.suffix] = by_ext.get(p.suffix, 0) + n
    print("业务 LOC 合计:", total)
    for ext, n in sorted(by_ext.items()):
        print(f"  {ext}: {n}")
    print("达标:" if total >= 3000 else "未达标（须 >= 3000）", total >= 3000)


if __name__ == "__main__":
    main()