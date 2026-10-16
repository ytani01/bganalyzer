#!/bin/bash
# アイコンの候補（*.svg）を 128px・60px（角を丸めてホーム画面風）・32px・16px で横に並べ、縦に積んだ 1 枚の画像にする
# 使い方: sheet.sh out.png a.svg b.svg ...
set -e
out=$1; shift; tmp=$(mktemp -d); rows=()
for f in "$@"; do n=$(basename "$f" .svg)
  for s in 128 60 32 16; do rsvg-convert -w $s -h $s "$f" -o $tmp/$n-$s.png; done
  for s in 128 60; do r=$((s*22/100)); magick $tmp/$n-$s.png \( +clone -alpha extract -fill black -colorize 100 -fill white -draw "roundrectangle 0,0,$((s-1)),$((s-1)),$r,$r" \) -alpha off -compose CopyOpacity -composite +repage $tmp/$n-$s.png; done
  # -splice は -gravity の向きに入る（north/center だと画像の真ん中に入る）
  magick -background '#d9d9d9' $tmp/$n-{128,60,32,16}.png -bordercolor '#d9d9d9' -border 8x0 -gravity center +append -gravity west -splice 56x0 -font DejaVu-Sans-Bold -pointsize 22 -fill '#222' -annotate +4+0 "$n" -border 0x8 +repage $tmp/row-$n.png
  rows+=($tmp/row-$n.png); done
magick "${rows[@]}" -bordercolor '#d9d9d9' -append -border 10 +repage "$out"
rm -r "$tmp"
