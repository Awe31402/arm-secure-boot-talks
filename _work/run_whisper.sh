#!/bin/bash
# Download audio (YouTube, one at a time, 60 s apart) and transcribe with whisper turbo.
# Usage: run_whisper.sh NN:ID [NN:ID ...]
cd "$(dirname "$0")"
for item in "$@"; do
  nn=${item%%:*}; id=${item#*:}
  if [ -s txt/$nn.txt ]; then echo "SKIP $nn"; continue; fi
  a=$(ls audio/$id.* 2>/dev/null | grep -v '\.part$' | head -1)
  if [ -z "$a" ]; then
    yt-dlp -q -f bestaudio -o "audio/%(id)s.%(ext)s" "https://www.youtube.com/watch?v=$id" 2>&1 | grep -E 'ERROR' && { echo "AUDIO_FAIL $nn $id"; sleep 60; continue; }
    a=$(ls audio/$id.* 2>/dev/null | grep -v '\.part$' | head -1)
    sleep 60
  fi
  [ -z "$a" ] && { echo "AUDIO_FAIL $nn $id"; continue; }
  whisper "$a" --model turbo --language en --device cuda --condition_on_previous_text False --output_dir whisper --output_format all --verbose False >/dev/null 2>whisper/$id.err \
    || { echo "WHISPER_FAIL $nn $id"; continue; }
  python3 -I vtt2txt.py whisper/$id.vtt txt/$nn.txt && echo "DONE $nn $id $(wc -l < txt/$nn.txt) lines"
done
echo ALL_FINISHED
