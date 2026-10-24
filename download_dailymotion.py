#!/usr/bin/env python3
"""Dailymotion の動画・チャンネルを MP4 でダウンロードする。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import yt_dlp

from download_channel import parse_startend

_DAILYMOTION_HOST = re.compile(r"dailymotion\.com", re.IGNORECASE)
_VIDEO_ID = re.compile(r"^x[\da-z]+$", re.IGNORECASE)
_VIDEO_IN_PATH = re.compile(r"/video/(x[\da-z]+)/?$", re.IGNORECASE)
_VIDEO_PATH_INCOMPLETE = re.compile(r"/video/?$", re.IGNORECASE)


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")


def ensure_curl_cffi() -> None:
    """Dailymotion の m3u8 取得に必要（yt-dlp の impersonation）。"""
    try:
        import curl_cffi  # noqa: F401
    except ImportError:
        print(
            "Dailymotion 用に curl_cffi が必要です。次を実行してください:\n"
            "  python -m pip install curl_cffi",
            file=sys.stderr,
        )
        raise SystemExit(1)


def normalize_target(target: str) -> tuple[str, bool]:
    """URL と、チャンネル（プレイリスト）かどうかを返す。"""
    text = target.strip()
    if not text:
        raise argparse.ArgumentTypeError("URL またはチャンネル名を指定してください")

    if _VIDEO_ID.fullmatch(text):
        return f"https://www.dailymotion.com/video/{text}", False

    if not re.match(r"https?://", text, re.IGNORECASE):
        if _DAILYMOTION_HOST.search(text) or text.startswith("www."):
            text = f"https://{text.lstrip('/')}"
        else:
            slug = text.strip("/")
            return f"https://www.dailymotion.com/{slug}/videos", True

    parsed = urlparse(text)
    if not _DAILYMOTION_HOST.search(parsed.netloc):
        raise argparse.ArgumentTypeError(
            f"Dailymotion の URL またはチャンネル名を指定してください: {target}"
        )

    path = parsed.path.rstrip("/")
    if _VIDEO_PATH_INCOMPLETE.search(path):
        raise argparse.ArgumentTypeError(
            "動画 ID が必要です（例: .../video/x5n7kjw または x5n7kjw）"
        )
    if _VIDEO_IN_PATH.search(path):
        return text, False

    if path.endswith("/videos"):
        return f"{parsed.scheme}://{parsed.netloc}{path}", True

    return f"{parsed.scheme}://{parsed.netloc}{path}/videos", True


def build_ydl_opts(
    output_dir: Path,
    *,
    format_spec: str,
    playlist: bool,
    start: Optional[int] = None,
    end: Optional[int] = None,
    cookies_from_browser: Optional[str] = None,
    cookies: Optional[Path] = None,
    overwrite: bool = False,
) -> dict:
    opts: dict = {
        "format": format_spec,
        "merge_output_format": "mp4",
        "outtmpl": str(
            output_dir / "%(uploader)s" / "%(upload_date)s_%(title)s [%(id)s].%(ext)s"
        ),
        "restrictfilenames": False,
        "windowsfilenames": True,
        "ignoreerrors": playlist,
        "quiet": False,
        "noplaylist": not playlist,
        "playlistreverse": False,
    }
    if playlist and start is not None and end is not None:
        opts["playlist_items"] = f"{start + 1}:{end + 1}"
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = tuple(cookies_from_browser.split(":", 1))
    if cookies is not None:
        opts["cookiefile"] = str(cookies)
    if overwrite:
        opts["overwrites"] = True
    return opts


def download(
    targets: list[str],
    output_dir: Path,
    *,
    startend: Optional[tuple[int, int]],
    format_spec: str,
    cookies_from_browser: Optional[str] = None,
    cookies: Optional[Path] = None,
    overwrite: bool = False,
) -> int:
    ensure_curl_cffi()
    output_dir.mkdir(parents=True, exist_ok=True)

    normalized: list[tuple[str, bool]] = [normalize_target(t) for t in targets]
    if startend is not None and len(normalized) != 1:
        raise SystemExit("--startend は対象を 1 つだけ指定したときに使えます")

    start = end = None
    if startend is not None:
        start, end = startend
        url, is_playlist = normalized[0]
        if not is_playlist:
            raise SystemExit("--startend はチャンネル URL 用です（単体動画には不要）")
        normalized = [(url, True)]

    urls = [url for url, _ in normalized]
    playlist = any(is_pl for _, is_pl in normalized)

    opts = build_ydl_opts(
        output_dir,
        format_spec=format_spec,
        playlist=playlist,
        start=start,
        end=end,
        cookies_from_browser=cookies_from_browser,
        cookies=cookies,
        overwrite=overwrite,
    )

    print(f"対象: {len(urls)} 件")
    for url in urls:
        print(f"  {url}")
    if start is not None and end is not None:
        count = end - start + 1
        print(f"範囲: 新しい順の {start}〜{end} 件目（計 {count} 本）")
    elif playlist:
        print("範囲: チャンネル内の全動画")
    print(f"保存先: {output_dir.resolve()}")
    print(f"形式: {format_spec}")
    if cookies_from_browser:
        print(f"Cookie: ブラウザから取得 ({cookies_from_browser})")
    if cookies is not None:
        print(f"Cookie: ファイル {cookies}")
    if overwrite:
        print("既存ファイル: 上書きする")
    print("-" * 60)

    with yt_dlp.YoutubeDL(opts) as ydl:
        code = ydl.download(urls)
    return 0 if code == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dailymotion の動画・チャンネルを MP4 でダウンロードします。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "例:\n"
            "  python download_dailymotion.py x5n7kjw\n"
            "  python download_dailymotion.py nogizaka-channel --startend 0:0\n"
            "  python download_dailymotion.py https://www.dailymotion.com/nogizaka-channel --startend 0:2\n"
            "\n"
            "--startend は download_channel.py と同じ（0 始まり・両端含む）。\n"
            "Dailymotion は curl_cffi が必要です（requirements.txt に含まれます）。"
        ),
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help="動画 URL / ID、またはチャンネル URL・チャンネル名",
    )
    parser.add_argument(
        "--startend",
        type=parse_startend,
        metavar="START:END",
        help="チャンネル動画の範囲（0 始まり・両端含む）。例: 0:0",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("downloads"),
        help="保存先ディレクトリ（既定: downloads）",
    )
    parser.add_argument(
        "-f",
        "--format",
        default="bestvideo*+bestaudio/best",
        help="yt-dlp の -f 相当（既定: 最高画質）",
    )
    parser.add_argument(
        "--cookies-from-browser",
        metavar="BROWSER",
        help="例: chrome / edge / firefox",
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
        help="同名の既存ファイルを上書きする",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cookies_from_browser and args.cookies is not None:
        parser.error("--cookies-from-browser と --cookies は同時に指定できません")
    try:
        return download(
            args.targets,
            args.output,
            startend=args.startend,
            format_spec=args.format,
            cookies_from_browser=args.cookies_from_browser,
            cookies=args.cookies,
            overwrite=args.overwrite,
        )
    except yt_dlp.cookies.CookieLoadError as exc:
        print(f"Cookie 読み込みエラー: {exc}", file=sys.stderr)
        return 1
    except yt_dlp.utils.DownloadError as exc:
        print(f"ダウンロードエラー: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
