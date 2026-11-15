"""Typeset the user's circular brand badge with Vietnamese-capable fonts."""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent


def make_logo():
    size = 1024
    canvas = Image.new('RGBA', (size, size))
    d = ImageDraw.Draw(canvas)
    d.ellipse((10, 10, 1014, 1014), fill='#29133e', outline='#eac86a', width=14)
    d.ellipse((164, 164, 860, 860), outline='#eac86a', width=6)
    portrait = Image.open(ROOT/'assets/logo-portrait-base.png').convert('RGBA').resize((680, 680), Image.Resampling.LANCZOS)
    canvas.alpha_composite(portrait, (172, 172))
    font = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf', 85)

    def arc(value, radius, bottom=False):
        advances = [font.getlength(c) for c in value]
        total = sum(advances)
        position = -total/2
        for char, width in zip(value, advances):
            angle = (position+width/2)/radius
            position += width
            if not char.strip():
                continue
            glyph = Image.new('RGBA', (180, 180))
            gd = ImageDraw.Draw(glyph)
            gd.text((90, 90), char, font=font, anchor='mm', fill='#fff1bd')
            degrees = math.degrees(angle)
            glyph = glyph.rotate(degrees if bottom else -degrees, Image.Resampling.BICUBIC, expand=True)
            x = size/2+radius*math.sin(angle)
            y = size/2+radius*math.cos(angle)*(1 if bottom else -1)
            canvas.alpha_composite(glyph, (round(x-glyph.width/2), round(y-glyph.height/2)))

    arc('Tiếng Anhh', 426)
    arc('Cùng Minh', 426, bottom=True)
    # Gold separators at the horizontal edges.
    d = ImageDraw.Draw(canvas)
    for x in (86, 938):
        d.ellipse((x-12, 500, x+12, 524), fill='#eac86a')
    target = ROOT/'assets/logo-tieng-anhh-cung-minh.png'
    canvas.save(target)
    print(target)


if __name__ == '__main__':
    make_logo()
