# YouTube チャンネル MP4 ダウンローダー

指定した YouTube チャンネルから、**新しい順**に動画を **MP4** でダウンロードします。

## 必要条件

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/)（動画・音声のマージ用）
- `yt-dlp`

```bash
pip install -r requirements.txt
```

## 使い方

```bash
# 最新 0〜2 件目（最新 3 本）をダウンロード
python download_channel.py @UjanNews-Yt --startend 0:2
# ダウンロードできない場合は、クッキーをchromeからダウンロードして以下のコマンド
python download_channel.py @UjanNews-Yt --startend 0:2 --cookies cookies.txt

# チャンネル URL を指定
python download_channel.py https://www.youtube.com/@YouTube --startend 0:0

# 保存先を変更
python download_channel.py @YouTube --startend 0:2 -o my_videos

# 範囲指定なし → チャンネルの全通常動画
python download_channel.py @YouTube


# ファイルの内容を無くして、ファイル名のみ残す
# 確認だけ（変更なし）
python truncate_nonempty_mp4.py "downloads/Ujan News"

# 本当に空にする
python truncate_nonempty_mp4.py "downloads/Ujan News" --execute


```

### `--startend START:END`

| 指定 | 意味 |
|------|------|
| `0:0` | 最新 1 本だけ |
| `0:2` | 最新から 0・1・2 件目（計 3 本） |
| `3:5` | 新しい順の 4〜6 本目 |

インデックスは **0 始まり・両端含む** です。チャンネルの「動画」タブ（新しい順）と同じ並びです。

## 補足

- `/videos` タブ相当を対象にするため、Shorts / ライブは含まれません。
- ファイルは `downloads/<チャンネル名>/<投稿日>_<タイトル> [<ID>].mp4` に保存されます。
