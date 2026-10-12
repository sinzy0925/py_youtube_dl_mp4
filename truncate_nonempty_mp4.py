#!/usr/bin/env python3
"""指定フォルダ内の .mp4 で、中身があるファイルだけ 0 バイトにする（ファイル名は残す）。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")


def truncate_nonempty_mp4(folder: Path, dry_run: bool) -> int:
    folder = folder.resolve()
    if not folder.is_dir():
        print(f"フォルダが見つかりません: {folder}", file=sys.stderr)
        return 1

    mp4s = sorted(folder.glob("*.mp4"))
    if not mp4s:
        print(f".mp4 がありません: {folder}")
        return 0

    truncated = skipped_empty = 0
    for path in mp4s:
        size = path.stat().st_size
        if size == 0:
            skipped_empty += 1
            continue
        if dry_run:
            print(f"[dry-run] 空にする: {path.name}  ({size:,} bytes)")
        else:
            path.open("wb").close()
            print(f"空にした: {path.name}  (was {size:,} bytes)")
        truncated += 1

    print("-" * 60)
    print(f"対象フォルダ: {folder}")
    print(f".mp4 合計: {len(mp4s)} / もともと空: {skipped_empty} / 処理: {truncated}")
    if dry_run and truncated:
        print("※ 実際に空にするには --execute を付けて再実行してください。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="中身がある .mp4 だけ 0 バイトにし、ファイル名だけ残します。",
        epilog=(
            "例:\n"
            '  python truncate_nonempty_mp4.py "downloads/Ujan News"          # 確認のみ\n'
            '  python truncate_nonempty_mp4.py "downloads/Ujan News" --execute'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "folder",
        nargs="?",
        type=Path,
        default=Path("downloads") / "Ujan News",
        help="対象フォルダ（既定: downloads/Ujan News）",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="実際にファイルを空にする（省略時は dry-run）",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)
    return truncate_nonempty_mp4(args.folder, dry_run=not args.execute)


if __name__ == "__main__":
    raise SystemExit(main())
