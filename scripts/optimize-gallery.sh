#!/usr/bin/env bash
#
# optimize-gallery.sh — resize gallery source images and generate WebP + AVIF variants.
#
# For every JPEG/PNG in assets/gallery/, this script:
#   1. Resizes so the longest edge is at most MAX_EDGE px (never upscales).
#   2. Re-encodes the JPEG fallback at quality Q_JPEG.
#   3. Writes a .webp variant (quality Q_WEBP).
#   4. Writes a .avif variant (quality Q_AVIF).
#
# It is idempotent: variants are only (re)built when the source is newer than
# the variant, so re-running is cheap. Safe to run locally or in CI.
#
# Requires ImageMagick 7 (`magick`) with WebP + AVIF delegates.
#
# Usage:  scripts/optimize-gallery.sh [gallery_dir]
set -euo pipefail

GALLERY_DIR="${1:-assets/gallery}"
MAX_EDGE="${MAX_EDGE:-1000}"   # longest edge cap (px)
Q_JPEG="${Q_JPEG:-80}"
Q_WEBP="${Q_WEBP:-80}"
Q_AVIF="${Q_AVIF:-55}"         # AVIF is perceptually strong at lower numbers

if ! command -v magick >/dev/null 2>&1; then
  echo "ERROR: ImageMagick 'magick' not found." >&2
  exit 1
fi

shopt -s nullglob nocaseglob
sources=("$GALLERY_DIR"/*.jpg "$GALLERY_DIR"/*.jpeg "$GALLERY_DIR"/*.png)
shopt -u nocaseglob

if [ ${#sources[@]} -eq 0 ]; then
  echo "No source images found in $GALLERY_DIR"
  exit 0
fi

newer_than() { # $1 newer than $2 ? (or $2 missing)
  [ ! -f "$2" ] || [ "$1" -nt "$2" ]
}

for src in "${sources[@]}"; do
  base="${src%.*}"
  ext="${src##*.}"
  # Skip anything that is itself already a generated variant
  case "$ext" in webp|avif) continue;; esac

  echo "• $src"

  # 1) Resize + re-encode the JPEG/PNG fallback in place (longest edge <= MAX_EDGE, no upscale).
  magick "$src" -auto-orient -strip -resize "${MAX_EDGE}x${MAX_EDGE}>" -quality "$Q_JPEG" "$src"

  # 2) WebP
  webp="${base}.webp"
  if newer_than "$src" "$webp"; then
    magick "$src" -strip -quality "$Q_WEBP" "$webp"
    echo "    -> $(basename "$webp")"
  fi

  # 3) AVIF
  avif="${base}.avif"
  if newer_than "$src" "$avif"; then
    magick "$src" -strip -quality "$Q_AVIF" "$avif"
    echo "    -> $(basename "$avif")"
  fi
done

echo "Done. Variants written next to each source in $GALLERY_DIR."
