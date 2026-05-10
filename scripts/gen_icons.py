"""Generate all Tauri icon sizes from the SVG source."""
import cairosvg
from PIL import Image
import io
import os

ICON_DIR = "/home/claude/ablab-repo/src-tauri/icons"
SVG_PATH = os.path.join(ICON_DIR, "icon.svg")

# Tauri needs these specific files
sizes = {
    "32x32.png": 32,
    "128x128.png": 128,
    "128x128@2x.png": 256,
    "icon.png": 512,
}

for filename, size in sizes.items():
    out = os.path.join(ICON_DIR, filename)
    cairosvg.svg2png(url=SVG_PATH, write_to=out, output_width=size, output_height=size)
    print(f"  ✓ {filename} ({size}x{size})")

# .ico for Windows (multi-resolution)
ico_path = os.path.join(ICON_DIR, "icon.ico")
ico_sizes = [16, 32, 48, 64, 128, 256]
images = []
for s in ico_sizes:
    png_bytes = cairosvg.svg2png(url=SVG_PATH, output_width=s, output_height=s)
    images.append(Image.open(io.BytesIO(png_bytes)))
images[0].save(ico_path, format='ICO', sizes=[(s, s) for s in ico_sizes], append_images=images[1:])
print(f"  ✓ icon.ico (multi-resolution)")

# .icns for macOS - simplified: just produces a valid 1024 png renamed.
# Real icns generation needs `iconutil` (macOS-only) or `png2icns`.
# GitHub Actions on macos-latest will have iconutil, so locally we ship a placeholder PNG.
# Tauri will accept it for cross-build; for proper icns the GH action will regenerate.
big = cairosvg.svg2png(url=SVG_PATH, output_width=1024, output_height=1024)
icns_placeholder = os.path.join(ICON_DIR, "icon.icns")
# Use png2icns-style fallback - just copy 1024 PNG bytes; Tauri will warn but bundle continues for non-mac targets.
# For proper .icns, contributors building on macOS run `npm run gen-icns`.
with open(icns_placeholder, "wb") as f:
    f.write(big)
print(f"  ✓ icon.icns (PNG placeholder; regenerate on macOS)")

print("\nAll icons generated.")
