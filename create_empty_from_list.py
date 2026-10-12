#!/usr/bin/env python3
"""リストファイルを1行ずつ読み、同じフォルダに中身が空のファイルを作る。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional


def configure_stdio() -> None:
    """cp932 コンソールでも絵文字付きファイル名の表示で止まらないようにする。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")


def create_empty_files(list_path: Path) -> int:
    """各行のファイル名で 0 バイトのファイルを作る。既存ファイルは触らない。"""
    list_path = list_path.resolve()
    if not list_path.is_file():
        print(f"リストが見つかりません: {list_path}", file=sys.stderr)
        return 1

    folder = list_path.parent
    names = list_path.read_text(encoding="utf-8").splitlines()

    created = skipped = 0
    for line_no, raw in enumerate(names, start=1):
        name = raw.strip()
        if not name:
            continue
        if name in {".", ".."} or Path(name).name != name:
            print(f"{line_no}行目をスキップ（ファイル名だけを書いてください）: {name}", file=sys.stderr)
            return 1

        dest = folder / name
        if dest.exists():
            print(f"スキップ（既存）: {name}")
            skipped += 1
            continue

        dest.write_bytes(b"")
        print(f"作成: {name}")
        created += 1

    print("-" * 60)
    print(f"保存先: {folder}")
    print(f"作成: {created} 件 / スキップ: {skipped} 件")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="リストの各行をファイル名として、中身が空のファイルを作ります。",
        epilog=(
            "例:\n"
            '  python create_empty_from_list.py "downloads/Ujan News/dl.txt"'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "list_file",
        nargs="?",
        type=Path,
        default=Path("downloads") / "Ujan News" / "dl.txt",
        help="1行1ファイル名のリスト（既定: downloads/Ujan News/dl.txt）",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)
    return create_empty_files(args.list_file)


if __name__ == "__main__":
    raise SystemExit(main())
