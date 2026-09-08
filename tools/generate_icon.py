# -*- coding: utf-8 -*-
"""
Generates the CAD Viewer application icon (assets/icon.ico, assets/icon.png).

This is a one-off developer utility (not required at runtime). Re-run it with
`python tools/generate_icon.py` if you want to tweak the icon's look.
"""
import math
import os

from PIL import Image, ImageDraw

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
SIZE = 256


def iso(x, y, z, cx, cy, scale):
    """Simple isometric projection for a unit-cube-ish wireframe box."""
    sx = (x - z) * math.cos(math.radians(30))
    sy = (x + z) * math.sin(math.radians(30)) - y
    return (cx + sx * scale, cy + sy * scale)


def build_icon() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background: rounded square, dark slate gradient (matches the app's viewport theme)
    pad = 10
    radius = 48
    top_color = (58, 66, 78)
    bottom_color = (30, 34, 41)
    bg = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    for yy in range(pad, SIZE - pad):
        t = (yy - pad) / (SIZE - 2 * pad)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        bg_draw.line([(pad, yy), (SIZE - pad, yy)], fill=(r, g, b, 255))

    mask = Image.new("L", (SIZE, SIZE), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([pad, pad, SIZE - pad, SIZE - pad], radius=radius, fill=255)
    img.paste(bg, (0, 0), mask)

    # Isometric wireframe box: represents CAD/3D-geometry viewing
    cx, cy = SIZE / 2, SIZE / 2 + 8
    scale = 62

    top = [iso(-1, 1, -1, cx, cy, scale), iso(1, 1, -1, cx, cy, scale),
           iso(1, 1, 1, cx, cy, scale), iso(-1, 1, 1, cx, cy, scale)]
    left = [iso(-1, 1, 1, cx, cy, scale), iso(-1, 1, -1, cx, cy, scale),
            iso(-1, -1, -1, cx, cy, scale), iso(-1, -1, 1, cx, cy, scale)]
    right = [iso(1, 1, -1, cx, cy, scale), iso(1, 1, 1, cx, cy, scale),
             iso(1, -1, 1, cx, cy, scale), iso(1, -1, -1, cx, cy, scale)]

    accent = (64, 196, 200)
    draw.polygon(top, fill=(*accent, 235))
    draw.polygon(left, fill=(int(accent[0] * 0.55), int(accent[1] * 0.55), int(accent[2] * 0.55), 235))
    draw.polygon(right, fill=(int(accent[0] * 0.75), int(accent[1] * 0.75), int(accent[2] * 0.75), 235))

    edge_color = (18, 22, 26, 255)
    edge_width = 6
    for face in (top, left, right):
        draw.line(face + [face[0]], fill=edge_color, width=edge_width, joint="curve")

    # Wireframe diagonals across the top face to emphasize the "mesh/tessellation" idea
    mesh_color = (18, 22, 26, 160)
    mid_top = [( (top[0][0] + top[1][0]) / 2, (top[0][1] + top[1][1]) / 2 ),
               ( (top[2][0] + top[3][0]) / 2, (top[2][1] + top[3][1]) / 2 )]
    mid_side = [( (top[1][0] + top[2][0]) / 2, (top[1][1] + top[2][1]) / 2 ),
                ( (top[3][0] + top[0][0]) / 2, (top[3][1] + top[0][1]) / 2 )]
    draw.line(mid_top, fill=mesh_color, width=3)
    draw.line(mid_side, fill=mesh_color, width=3)

    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    icon = build_icon()

    png_path = os.path.join(OUT_DIR, "icon.png")
    icon.save(png_path)

    ico_path = os.path.join(OUT_DIR, "icon.ico")
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon.save(ico_path, format="ICO", sizes=sizes)

    print(f"Wrote {png_path}")
    print(f"Wrote {ico_path}")


if __name__ == "__main__":
    main()
