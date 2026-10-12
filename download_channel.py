#!/usr/bin/env python3
"""指定 YouTube チャンネルから動画を新しい順に MP4 でダウンロードする。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import yt_dlp


def parse_startend(value: str) -> tuple[int, int]:
    """`--startend START:END` を 0 始まり・両端含む範囲として解釈する。"""
    match = re.fullmatch(r"(\d+):(\d+)", value.strip())
    if not match:
        raise argparse.ArgumentTypeError(
            "--startend は START:END 形式です（例: 0:2）"
        )
    start, end = int(match.group(1)), int(match.group(2))
    if start > end:
        raise argparse.ArgumentTypeError(
            f"START は END 以下である必要があります: {start}:{end}"
        )
    return start, end


def normalize_channel_url(channel: str) -> str:
    """チャンネル指定を /videos タブ URL に正規化する（新しい順・通常動画のみ）。"""
    text = channel.strip()
    if re.fullmatch(r"@[\w.-]+", text):
        return f"https://www.youtube.com/{text}/videos"

    if not re.match(r"https?://", text, re.IGNORECASE):
        if text.startswith("UC") and len(text) >= 20:
            return f"https://www.youtube.com/channel/{text}/videos"
        if text.startswith("@"):
            return f"https://www.youtube.com/{text}/videos"
        return f"https://www.youtube.com/@{text}/videos"

    parsed = urlparse(text)
    path = parsed.path.rstrip("/")

    for suffix in ("/videos", "/shorts", "/streams", "/playlists", "/community", "/about"):
        if path.endswith(suffix):
            path = path[: -len(suffix)]
            break

    return f"{parsed.scheme}://{parsed.netloc}{path}/videos"


def build_ydl_opts(
    output_dir: Path,
    start: Optional[int],
    end: Optional[int],
    *,
    cookies_from_browser: Optional[str] = None,
    cookies: Optional[Path] = None,
    overwrite: bool = False,
) -> dict:
    opts: dict = {
        "format": (
            "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/"
            "bv*+ba/b"
        ),
        "merge_output_format": "mp4",
        "outtmpl": str(output_dir / "%(uploader)s" / "%(upload_date)s_%(title)s [%(id)s].%(ext)s"),
        "restrictfilenames": False,
        "windowsfilenames": True,
        "ignoreerrors": True,
        "no_warnings": False,
        "quiet": False,
        "noplaylist": False,
        # /videos は新しい順。プレイリスト全体を逆順にしない。
        "playlistreverse": False,
        # YouTube の JS チャレンジ解決（deno + yt-dlp-ejs / GitHub）
        "js_runtimes": {"deno": {}},
        "remote_components": {"ejs:github"},
    }
    if start is not None and end is not None:
        # ユーザー指定は 0 始まり・両端含む → yt-dlp は 1 始まり・両端含む
        opts["playlist_items"] = f"{start + 1}:{end + 1}"
    if cookies_from_browser:
        # 例: chrome / edge / firefox / chrome:Profile 1
        opts["cookiesfrombrowser"] = tuple(cookies_from_browser.split(":", 1))
    if cookies is not None:
        opts["cookiefile"] = str(cookies)
    # Cookie 利用時の tv_downgraded 系不具合回避
    # https://github.com/yt-dlp/yt-dlp/issues/17389
    if cookies_from_browser or cookies is not None:
        opts["extractor_args"] = {
            "youtube": {"player_client": ["default", "web_embedded"]},
        }
    if overwrite:
        opts["overwrites"] = True
    return opts


def download(
    channel: str,
    startend: Optional[tuple[int, int]],
    output_dir: Path,
    *,
    cookies_from_browser: Optional[str] = None,
    cookies: Optional[Path] = None,
    overwrite: bool = False,
) -> int:
    url = normalize_channel_url(channel)
    output_dir.mkdir(parents=True, exist_ok=True)

    start = end = None
    if startend is not None:
        start, end = startend

    opts = build_ydl_opts(
        output_dir,
        start,
        end,
        cookies_from_browser=cookies_from_browser,
        cookies=cookies,
        overwrite=overwrite,
    )

    print(f"チャンネル: {url}")
    if start is not None and end is not None:
        count = end - start + 1
        print(f"範囲: 新しい順の {start}〜{end} 件目（計 {count} 本）")
    else:
        print("範囲: 全動画（新しい順）")
    print(f"保存先: {output_dir.resolve()}")
    if cookies_from_browser:
        print(f"Cookie: ブラウザから取得 ({cookies_from_browser})")
    if cookies is not None:
        print(f"Cookie: ファイル {cookies}")
    if overwrite:
        print("既存ファイル: 上書きする")
    print("-" * 60)

    with yt_dlp.YoutubeDL(opts) as ydl:
        code = ydl.download([url])
    return 0 if code == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "指定した YouTube チャンネルから、新しい順に動画を MP4 でダウンロードします。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "例:\n"
            "  python download_channel.py @YouTube --startend 0:2\n"
            "  python download_channel.py @YouTube --startend 0:0 --cookies-from-browser chrome\n"
            "  python download_channel.py https://www.youtube.com/@YouTube -o downloads\n"
            "  python download_channel.py UCBR8-60-B28hp2BmDPdNTC4 --startend 0:0\n"
            "\n"
            "--startend 0:2 は、新しい順の 0〜2 件目（最新 3 本）をダウンロードします。\n"
            "YouTube のボット判定が出るときは --cookies-from-browser を付けてください。"
        ),
    )
    parser.add_argument(
        "channel",
        help="チャンネル URL / @ハンドル / チャンネル ID",
    )
    parser.add_argument(
        "--startend",
        type=parse_startend,
        metavar="START:END",
        help="新しい順のインデックス範囲（0 始まり・両端含む）。例: 0:2",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("downloads"),
        help="保存先ディレクトリ（既定: downloads）",
    )
    parser.add_argument(
        "--cookies-from-browser",
        metavar="BROWSER",
        help=(
            "ログイン済みブラウザから Cookie を読む。"
            "例: chrome / edge / firefox / chrome:Profile 1"
        ),
    )
    parser.add_argument(
        "--cookies",
        type=Path,
        metavar="FILE",
        help="Netscape 形式の cookies.txt",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="同名の既存ファイルを上書きする（空のプレースホルダ置換用）",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cookies_from_browser and args.cookies is not None:
        parser.error("--cookies-from-browser と --cookies は同時に指定できません")
    try:
        return download(
            args.channel,
            args.startend,
            args.output,
            cookies_from_browser=args.cookies_from_browser,
            cookies=args.cookies,
            overwrite=args.overwrite,
        )
    except yt_dlp.cookies.CookieLoadError as exc:
        print(f"Cookie 読み込みエラー: {exc}", file=sys.stderr)
        print(
            "Chrome / Edge は起動中だと Cookie DB をロックします。\n"
            "  1) 対象ブラウザを完全に終了してから再実行する\n"
            "  2) または Firefox を使う: --cookies-from-browser firefox\n"
            "  3) または cookies.txt を渡す: --cookies cookies.txt",
            file=sys.stderr,
        )
        return 1
    except yt_dlp.utils.DownloadError as exc:
        print(f"ダウンロードエラー: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
