#!/usr/bin/env bash
# Build both promo videos from source.
#   requirements: node + playwright (Chromium), ffmpeg, python3 with numpy scipy pyloudnorm
#   setup once  : (cd video/src && npm install) ; pip install numpy scipy pyloudnorm
set -euo pipefail
cd "$(dirname "$0")"
WORK="${WORK:-$(mktemp -d)}"
OUT=..

python3 music.py "$WORK/bgm.wav"

encode () {  # $1=w $2=h $3=name
  rm -rf "$WORK/frames_$3"
  node render.js "$1" "$2" "$WORK/frames_$3" 30 36 4
  ffmpeg -y -v error -framerate 30 -i "$WORK/frames_$3/f%05d.png" -i "$WORK/bgm.wav" \
    -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
    -c:v libx264 -preset slow -crf 18 -profile:v high -level 4.2 -g 60 \
    -c:a aac -b:a 192k -ar 44100 -movflags +faststart -shortest \
    "$OUT/jobhunt_promo_$3.mp4"
  echo "wrote $OUT/jobhunt_promo_$3.mp4"
}

encode 1920 1080 16x9
encode 1080 1920 9x16
