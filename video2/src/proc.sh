#!/bin/bash
# usage: proc.sh in out mode
in=$1; out=$2; mode=$3
if [ "$mode" = mosaic ]; then
 ffmpeg -loglevel error -y -i "$in" -af "aresample=44100,rubberband=pitch=0.52:formant=shifted,highpass=f=120,lowpass=f=7000,acompressor=threshold=-20dB:ratio=3" -ar 44100 -ac 1 "$out"
else
 ffmpeg -loglevel error -y -i "$in" -filter_complex "[0:a]aresample=44100,asplit=3[a][b][c];[a]rubberband=pitch=0.72:formant=preserved,volume=0.9[m];[b]rubberband=pitch=0.36:formant=shifted,lowpass=f=2500,volume=0.8[l];[c]rubberband=pitch=1.5:formant=preserved,highpass=f=1500,volume=0.18[h];[m][l][h]amix=inputs=3:normalize=0,chorus=0.6:0.9:50|70:0.4|0.32:0.25|0.4:2|1.3,aecho=0.8:0.6:90|180|320:0.35|0.22|0.12,apad=pad_dur=0.6" -ar 44100 -ac 1 "$out"
fi
