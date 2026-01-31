# yt-dlp

Command-line tool for downloading videos and audio from YouTube and other sites.

## Overview

yt-dlp is a youtube-dl fork with additional features:

- **Multi-site support** - YouTube, Vimeo, Twitter, and 1000+ sites
- **Format selection** - Choose quality, codec, container
- **Playlist support** - Download entire playlists
- **Metadata** - Embed thumbnails, subtitles, chapters
- **Performance** - Parallel downloads, aria2c integration

## Installation

### macOS

```bash
brew install yt-dlp
```

### Linux

```bash
# pip
pip install yt-dlp

# Or download binary
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp
```

### Verify

```bash
yt-dlp --version
```

### Update

```bash
yt-dlp -U
```

## Basic Usage

### Download Video

```bash
# Default best quality
yt-dlp "https://www.youtube.com/watch?v=VIDEO_ID"

# Specify output name
yt-dlp -o "%(title)s.%(ext)s" URL
```

### Download Audio Only

```bash
# Best audio, convert to mp3
yt-dlp -x --audio-format mp3 URL

# Best audio, keep original format
yt-dlp -x URL

# Specific audio quality
yt-dlp -x --audio-format mp3 --audio-quality 0 URL  # Best
yt-dlp -x --audio-format mp3 --audio-quality 5 URL  # Medium
```

### Download Playlist

```bash
# Entire playlist
yt-dlp PLAYLIST_URL

# Specific range
yt-dlp --playlist-start 1 --playlist-end 10 PLAYLIST_URL

# Specific items
yt-dlp --playlist-items 1,3,5-7 PLAYLIST_URL
```

## Format Selection

### List Available Formats

```bash
yt-dlp -F URL
```

Output example:
```
ID   EXT  RESOLUTION  FPS  │  FILESIZE   TBR   PROTO  VCODEC        ACODEC
─────────────────────────────────────────────────────────────────────────────
140  m4a  audio only       │   3.45MiB  130k  https  audio only    mp4a.40.2
251  webm audio only       │   3.22MiB  124k  https  audio only    opus
137  mp4  1920x1080   30   │  45.32MiB 1155k  https  avc1.640028   video only
248  webm 1920x1080   30   │  32.45MiB  827k  https  vp9           video only
```

### Select Specific Format

```bash
# By format ID
yt-dlp -f 137+140 URL

# Best video + best audio
yt-dlp -f "bestvideo+bestaudio" URL

# Best mp4
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]" URL

# Maximum resolution
yt-dlp -f "bestvideo[height<=1080]+bestaudio" URL
```

### Common Format Options

```bash
# Best quality overall
yt-dlp -f "bestvideo+bestaudio/best" URL

# Best mp4 (no re-encoding needed)
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]" URL

# 720p or lower
yt-dlp -f "bestvideo[height<=720]+bestaudio/best[height<=720]" URL

# Prefer AV1 codec
yt-dlp -f "bestvideo[vcodec^=av01]+bestaudio/best" URL
```

## Configuration File

### Location

| Platform | Path |
|----------|------|
| Linux/macOS | `~/.config/yt-dlp/config` |
| macOS alt | `~/Library/Application Support/yt-dlp/config` |
| Windows | `%APPDATA%\yt-dlp\config` |

### Example Configuration

```bash
# ~/.config/yt-dlp/config

# Output template
-o ~/Videos/%(uploader)s/%(title)s.%(ext)s

# Format selection
-f bestvideo[height<=1080]+bestaudio/best

# Embed metadata
--embed-thumbnail
--embed-metadata
--embed-chapters
--embed-subs

# Subtitles
--write-auto-subs
--sub-langs en,no

# Rate limiting (be nice to servers)
--limit-rate 10M

# Archive (don't re-download)
--download-archive ~/.local/share/yt-dlp/archive.txt

# Sponsorblock
--sponsorblock-mark all
```

### Per-Site Configuration

```bash
# For specific extractors
--extractor-args "youtube:player_client=android"
```

## Output Templates

### Available Variables

| Variable | Description |
|----------|-------------|
| `%(title)s` | Video title |
| `%(id)s` | Video ID |
| `%(ext)s` | File extension |
| `%(uploader)s` | Channel name |
| `%(upload_date)s` | Upload date (YYYYMMDD) |
| `%(playlist)s` | Playlist name |
| `%(playlist_index)s` | Position in playlist |
| `%(duration)s` | Duration in seconds |

### Template Examples

```bash
# Organized by channel
-o "%(uploader)s/%(title)s.%(ext)s"

# With date
-o "%(upload_date)s - %(title)s.%(ext)s"

# Playlist organized
-o "%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s"

# Clean filename
-o "%(title).100s.%(ext)s"  # Limit to 100 chars
```

## Common Recipes

### Download Best Quality Video

```bash
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
  --merge-output-format mp4 \
  URL
```

### Download Podcast/Music

```bash
yt-dlp -x \
  --audio-format mp3 \
  --audio-quality 0 \
  --embed-thumbnail \
  --embed-metadata \
  -o "%(title)s.%(ext)s" \
  URL
```

### Archive YouTube Channel

```bash
yt-dlp \
  --download-archive archive.txt \
  -f "bestvideo[height<=1080]+bestaudio/best" \
  --write-info-json \
  --write-thumbnail \
  --write-subs \
  -o "%(uploader)s/%(upload_date)s - %(title)s.%(ext)s" \
  "https://www.youtube.com/@CHANNEL/videos"
```

### Download with Subtitles

```bash
yt-dlp \
  --write-subs \
  --write-auto-subs \
  --sub-langs "en,no" \
  --embed-subs \
  URL
```

### Download Thumbnail Only

```bash
yt-dlp --write-thumbnail --skip-download URL
```

### Batch Download from File

Create `urls.txt`:
```
https://www.youtube.com/watch?v=VIDEO1
https://www.youtube.com/watch?v=VIDEO2
https://www.youtube.com/watch?v=VIDEO3
```

```bash
yt-dlp -a urls.txt
```

### Download with SponsorBlock

```bash
# Mark sponsored segments
yt-dlp --sponsorblock-mark all URL

# Remove sponsored segments
yt-dlp --sponsorblock-remove sponsor,intro,outro URL
```

### Download Private/Age-Restricted

```bash
# With cookies
yt-dlp --cookies-from-browser firefox URL

# Or export cookies
yt-dlp --cookies cookies.txt URL
```

## Advanced Options

### Rate Limiting

```bash
# Limit download speed
yt-dlp --limit-rate 5M URL

# Sleep between downloads (playlist)
yt-dlp --sleep-interval 5 --max-sleep-interval 30 PLAYLIST
```

### Using External Downloader

```bash
# Use aria2c for faster downloads
yt-dlp --downloader aria2c --downloader-args aria2c:"-x 16 -s 16" URL
```

### Proxy

```bash
yt-dlp --proxy socks5://127.0.0.1:1080 URL
```

### Geo-Bypass

```bash
yt-dlp --geo-bypass-country NO URL
```

## Troubleshooting

### Video Unavailable

```bash
# Try different client
yt-dlp --extractor-args "youtube:player_client=android" URL

# Use cookies for authentication
yt-dlp --cookies-from-browser chrome URL
```

### Slow Downloads

```bash
# Use aria2c
yt-dlp --downloader aria2c URL

# Or concurrent fragments
yt-dlp -N 4 URL
```

### Age-Restricted Content

```bash
# Requires authentication
yt-dlp --cookies-from-browser firefox URL
```

### Update yt-dlp

```bash
# Self-update
yt-dlp -U

# Or via package manager
brew upgrade yt-dlp
pip install -U yt-dlp
```

## Useful Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Quick audio download
alias yta='yt-dlp -x --audio-format mp3 --audio-quality 0'

# Best video
alias ytv='yt-dlp -f "bestvideo[height<=1080]+bestaudio/best"'

# Playlist audio
alias ytpa='yt-dlp -x --audio-format mp3 -o "%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s"'

# List formats
alias ytf='yt-dlp -F'
```

## See Also

- [Modern Replacements](modern-replacements.md) - CLI tool alternatives
- [Archives](archives.md) - File compression
