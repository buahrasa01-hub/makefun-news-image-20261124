import os, struct, zlib

FONT = {
    "A": ("01110","10001","10001","11111","10001","10001","10001"),
    "B": ("11110","10001","10001","11110","10001","10001","11110"),
    "C": ("01110","10001","10000","10000","10000","10001","01110"),
    "D": ("11110","10001","10001","10001","10001","10001","11110"),
    "E": ("11111","10000","10000","11110","10000","10000","11111"),
    "F": ("11111","10000","10000","11110","10000","10000","10000"),
    "G": ("01110","10001","10000","10111","10001","10001","01110"),
    "H": ("10001","10001","10001","11111","10001","10001","10001"),
    "I": ("11111","00100","00100","00100","00100","00100","11111"),
    "J": ("00111","00010","00010","00010","00010","10010","01100"),
    "K": ("10001","10010","10100","11000","10100","10010","10001"),
    "L": ("10000","10000","10000","10000","10000","10000","11111"),
    "M": ("10001","11011","10101","10101","10001","10001","10001"),
    "N": ("10001","11001","10101","10011","10001","10001","10001"),
    "O": ("01110","10001","10001","10001","10001","10001","01110"),
    "P": ("11110","10001","10001","11110","10000","10000","10000"),
    "Q": ("01110","10001","10001","10001","10101","10010","01101"),
    "R": ("11110","10001","10001","11110","10100","10010","10001"),
    "S": ("01111","10000","10000","01110","00001","00001","11110"),
    "T": ("11111","00100","00100","00100","00100","00100","00100"),
    "U": ("10001","10001","10001","10001","10001","10001","01110"),
    "V": ("10001","10001","10001","10001","10001","01010","00100"),
    "W": ("10001","10001","10001","10101","10101","10101","01010"),
    "X": ("10001","10001","01010","00100","01010","10001","10001"),
    "Y": ("10001","10001","01010","00100","00100","00100","00100"),
    "Z": ("11111","00001","00010","00100","01000","10000","11111"),
    "0": ("01110","10001","10011","10101","11001","10001","01110"),
    "1": ("00100","01100","00100","00100","00100","00100","01110"),
    "2": ("01110","10001","00001","00010","00100","01000","11111"),
    "3": ("11110","00001","00001","01110","00001","00001","11110"),
    "4": ("00010","00110","01010","10010","11111","00010","00010"),
    "5": ("11111","10000","10000","11110","00001","00001","11110"),
    "6": ("01110","10000","10000","11110","10001","10001","01110"),
    "7": ("11111","00001","00010","00100","01000","01000","01000"),
    "8": ("01110","10001","10001","01110","10001","10001","01110"),
    "9": ("01110","10001","10001","01111","00001","00001","01110"),
    ".": ("00000","00000","00000","00000","00000","01100","01100"),
    ",": ("00000","00000","00000","00000","00110","00110","00100"),
    ":": ("00000","01100","01100","00000","01100","01100","00000"),
    ";": ("00000","01100","01100","00000","01100","00100","01000"),
    "!": ("00100","00100","00100","00100","00100","00000","00100"),
    "?": ("01110","10001","00001","00010","00100","00000","00100"),
    "'": ("00100","00100","00000","00000","00000","00000","00000"),
    "-": ("00000","00000","00000","11111","00000","00000","00000"),
    "/": ("00001","00010","00010","00100","01000","01000","10000"),
    "(": ("00010","00100","01000","01000","01000","00100","00010"),
    ")": ("01000","00100","00010","00010","00010","00100","01000"),
    "%": ("11001","11011","00110","01100","11000","10011","00011"),
    "&": ("01100","10010","10100","01000","10101","10010","01101"),
    "+": ("00000","00100","00100","11111","00100","00100","00000"),
    "=": ("00000","00000","11111","00000","11111","00000","00000"),
    "$": ("00100","01111","10100","01110","00101","11110","00100"),
    " ": ("00000","00000","00000","00000","00000","00000","00000"),
}

W = H = 1024
PAPER, INK, NAVY, WHITE = (250,246,235), (20,20,28), (16,32,64), (255,255,255)
canvas = []

def fill_rect(x, y, w, h, color):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    span = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        canvas[yy][x0 * 3:x1 * 3] = span

def draw_rect_outline(x, y, w, h, color):
    fill_rect(x, y, w, 1, color)
    fill_rect(x, y + h - 1, w, 1, color)
    fill_rect(x, y, 1, h, color)
    fill_rect(x + w - 1, y, 1, h, color)

def fill_circle(cx, cy, r, color):
    for dy in range(-r, r + 1):
        span = int((r * r - dy * dy) ** 0.5)
        fill_rect(cx - span, cy + dy, span * 2 + 1, 1, color)

def text_width(s, scale):
    return len(s) * 6 * scale - scale if s else 0

def draw_text(x, y, s, scale, color):
    for i, ch in enumerate(s.upper()):
        glyph = FONT.get(ch, FONT[" "])
        gx0 = x + i * 6 * scale
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    fill_rect(gx0 + gx * scale, y + gy * scale, scale, scale, color)

def write_png(path, rows):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    raw = b"".join(b"\x00" + bytes(row) for row in rows)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def draw_panel_base(x, y, w, h):
    fill_rect(x, y, w, h, (255, 255, 255))
    fill_rect(x, y, w, 1, INK)
    fill_rect(x, y + h - 1, w, 1, INK)
    fill_rect(x, y, 1, h, INK)
    fill_rect(x + w - 1, y, 1, h, INK)

def scene1(x, y, w, h):
    fill_rect(x + w*18//100, y + h*32//100, w*64//100, h*48//100, (200, 200, 192))
    fill_rect(x + w*42//100, y + h*10//100, w*16//100, h*4//100, (132, 132, 124))
    fill_rect(x + w*34//100, y + h*14//100, w*32//100, h*4//100, (132, 132, 124))
    fill_rect(x + w*26//100, y + h*18//100, w*48//100, h*5//100, (132, 132, 124))
    fill_rect(x + w*18//100, y + h*23//100, w*64//100, h*5//100, (132, 132, 124))
    fill_rect(x + w*26//100, y + h*42//100, w*6//100, h*30//100, (230, 230, 222))
    fill_rect(x + w*47//100, y + h*42//100, w*6//100, h*30//100, (230, 230, 222))
    fill_rect(x + w*68//100, y + h*42//100, w*6//100, h*30//100, (230, 230, 222))
    gold = (212, 175, 55)
    fill_rect(x + w*48//100, y + h*27//100, w*4//100, h*18//100, gold)
    fill_rect(x + w*39//100, y + h*29//100, w*22//100, h*3//100, gold)
    fill_rect(x + w*37//100, y + h*32//100, w*8//100, h*3//100, gold)
    fill_rect(x + w*39//100, y + h*35//100, w*4//100, h*4//100, gold)
    fill_rect(x + w*55//100, y + h*32//100, w*8//100, h*3//100, gold)
    fill_rect(x + w*57//100, y + h*35//100, w*4//100, h*4//100, gold)
    fill_rect(x + w*74//100, y + h*70//100, w*9//100, h*11//100, (30, 30, 35))
    fill_rect(x + w*76//100, y + h*72//100, w*5//100, h*7//100, (35, 145, 75))
    fill_rect(x + w*12//100, y + h*78//100, w*12//100, h*8//100, (115, 72, 40))
    fill_rect(x + w*20//100, y + h*84//100, w*12//100, h*3//100, (115, 72, 40))

def scene2(x, y, w, h):
    fill_rect(x, y + h//2, w, h - h//2, (58, 126, 166))
    fill_rect(x, y + h*20//100, w*20//100, h*80//100, (205, 171, 116))
    fill_rect(x + w*80//100, y + h*15//100, w*20//100, h*85//100, (205, 171, 116))
    fill_rect(x + w*24//100, y + h*57//100, w*24//100, h*8//100, (35, 41, 48))
    fill_rect(x + w*27//100, y + h*52//100, w*13//100, h*5//100, (190, 55, 50))
    fill_rect(x + w*42//100, y + h*48//100, w*5//100, h*9//100, (235, 235, 225))
    fill_rect(x + w*58//100, y + h*68//100, w*23//100, h*7//100, (35, 41, 48))
    fill_rect(x + w*61//100, y + h*63//100, w*12//100, h*5//100, (190, 55, 50))
    fill_rect(x + w*75//100, y + h*59//100, w*5//100, h*9//100, (235, 235, 225))
    mx, my, mr = x + w*53//100, y + h*71//100, max(3, w//55)
    fill_circle(mx, my, mr, (20, 20, 20))
    fill_rect(mx - mr - 5, my - 1, 6, 2, (20, 20, 20))
    fill_rect(mx + mr - 1, my - 1, 6, 2, (20, 20, 20))
    fill_rect(mx - 1, my - mr - 5, 2, 6, (20, 20, 20))
    fill_rect(mx - 1, my + mr - 1, 2, 6, (20, 20, 20))
    fill_circle(x + w*30//100, y + h*42//100, max(3, w//40), (130, 130, 130))
    fill_circle(x + w*37//100, y + h*36//100, max(4, w//35), (150, 150, 150))
    fill_circle(x + w*31//100, y + h*31//100, max(3, w//45), (115, 115, 115))

def scene3(x, y, w, h):
    fill_rect(x, y, w, h, (10, 18, 38))
    fill_rect(x, y + h*62//100, w, h - h*62//100, (20, 42, 70))
    fill_circle(x + w*82//100, y + h*18//100, max(8, w//18), (225, 222, 190))
    fill_rect(x + w*8//100, y + h*55//100, w*42//100, h*9//100, (92, 98, 104))
    fill_rect(x + w*13//100, y + h*48//100, w*10//100, h*7//100, (190, 90, 55))
    fill_rect(x + w*25//100, y + h*50//100, w*11//100, h*5//100, (65, 115, 150))
    fill_rect(x + w*55//100, y + h*58//100, w*28//100, h*5//100, (115, 120, 126))
    fill_rect(x + w*58//100, y + h*63//100, w*24//100, h*5//100, (80, 84, 90))
    fill_rect(x + w*22//100, y + h*16//100, w*6//100, h*4//100, (35, 38, 44))
    fill_rect(x + w*17//100, y + h*15//100, w*16//100, 2, (35, 38, 44))
    fill_rect(x + w*19//100, y + h*20//100, w*12//100, 2, (35, 38, 44))
    fill_rect(x + w*24//100, y + h*18//100, w*2//100, h*2//100, (245, 210, 70))
    fill_rect(x + w*46//100, y + h*24//100, w*6//100, h*4//100, (35, 38, 44))
    fill_rect(x + w*41//100, y + h*23//100, w*16//100, 2, (35, 38, 44))
    fill_rect(x + w*43//100, y + h*28//100, w*12//100, 2, (35, 38, 44))
    fill_rect(x + w*48//100, y + h*26//100, w*2//100, h*2//100, (245, 210, 70))
    fill_rect(x + w*70//100, y + h*12//100, w*6//100, h*4//100, (35, 38, 44))
    fill_rect(x + w*65//100, y + h*11//100, w*16//100, 2, (35, 38, 44))
    fill_rect(x + w*67//100, y + h*16//100, w*12//100, 2, (35, 38, 44))
    fill_rect(x + w*72//100, y + h*14//100, w*2//100, h*2//100, (245, 210, 70))

def scene4(x, y, w, h):
    fill_rect(x, y + h*55//100, w, h*45//100, (214, 188, 140))
    fill_rect(x + w*42//100, y + h*12//100, w*16//100, h*55//100, (28, 52, 92))
    fill_rect(x + w*46//100, y + h*17//100, w*2//100, h*2//100, (245, 210, 70))
    fill_rect(x + w*55//100, y + h*17//100, w*2//100, h*2//100, (245, 210, 70))
    fill_rect(x + w*46//100, y + h*24//100, w*2//100, h*2//100, (245, 210, 70))
    fill_rect(x + w*55//100, y + h*24//100, w*2//100, h*2//100, (245, 210, 70))
    fill_rect(x + w*46//100, y + h*31//100, w*2//100, h*2//100, (245, 210, 70))
    fill_circle(x + w*50//100, y + h*8//100, max(4, w//60), (135, 135, 135))
    fill_circle(x + w*56//100, y + h*5//100, max(3, w//70), (155, 155, 155))
    fill_circle(x + w*45//100, y + h*5//100, max(3, w//75), (115, 115, 115))
    fill_rect(x + w*50//100, y + h*86//100, w*12//100, h*3//100, (55, 52, 48))
    fill_rect(x + w*60//100, y + h*83//100, w*16//100, h*3//100, (55, 52, 48))
    fill_rect(x + w*74//100, y + h*80//100, w*14//100, h*3//100, (55, 52, 48))
    fill_rect(x + w*84//100, y + h*74//100, w*6//100, h*8//100, (245, 245, 240))
    fill_rect(x + w*90//100, y + h*78//100, w*5//100, h*7//100, (245, 245, 240))
    fill_rect(x + w*81//100, y + h*80//100, w*4//100, h*5//100, (245, 245, 240))

def scene5(x, y, w, h):
    fill_rect(x + w*6//100, y + h*20//100, w*66//100, h*48//100, (198, 196, 184))
    fill_rect(x + w*6//100, y + h*12//100, w*66//100, h*2//100, (200, 45, 45))
    fill_rect(x + w*6//100, y + h*14//100, w*66//100, h*2//100, (245, 245, 238))
    fill_rect(x + w*6//100, y + h*16//100, w*66//100, h*2//100, (200, 45, 45))
    fill_rect(x + w*6//100, y + h*18//100, w*66//100, h*2//100, (245, 245, 238))
    fill_rect(x + w*24//100, y + h*27//100, w*30//100, h*5//100, NAVY)
    fill_rect(x, y + h*68//100, w, h*32//100, (95, 95, 100))
    fill_rect(x + w*76//100, y + h*24//100, w*20//100, h*38//100, (135, 135, 130))
    fill_rect(x + w*82//100, y + h*30//100, 2, h*18//100, (55, 55, 55))
    fill_rect(x + w*87//100, y + h*42//100, w*5//100, 2, (55, 55, 55))
    fill_circle(x + w*82//100, y + h*20//100, max(4, w//50), (135, 135, 135))
    fill_circle(x + w*88//100, y + h*15//100, max(3, w//60), (155, 155, 155))
    fill_circle(x + w*78//100, y + h*13//100, max(3, w//65), (115, 115, 115))
    fill_rect(x, y + h*69//100, w, h*2//100, (245, 210, 55))
    fill_rect(x + w*6//100, y + h*69//100, w*4//100, h*2//100, (25, 25, 25))
    fill_rect(x + w*34//100, y + h*69//100, w*4//100, h*2//100, (25, 25, 25))
    fill_rect(x + w*62//100, y + h*69//100, w*4//100, h*2//100, (25, 25, 25))
    fill_rect(x + w*70//100, y + h*62//100, w*22//100, h*8//100, (40, 80, 160))
    fill_rect(x + w*78//100, y + h*59//100, w*7//100, h*2//100, (245, 245, 230))

def scene6(x, y, w, h):
    fill_rect(x + w*5//100, y + h*8//100, w*90//100, h*84//100, WHITE)
    fill_rect(x + w*10//100, y + h*70//100, w*12//100, h*5//100, (40, 155, 80))
    fill_rect(x + w*21//100, y + h*56//100, w*12//100, h*5//100, (40, 155, 80))
    fill_rect(x + w*32//100, y + h*42//100, w*12//100, h*5//100, (40, 155, 80))
    fill_rect(x + w*43//100, y + h*28//100, w*12//100, h*5//100, (40, 155, 80))
    fill_rect(x + w*55//100, y + h*32//100, w*12//100, h*5//100, (200, 50, 50))
    fill_rect(x + w*66//100, y + h*44//100, w*12//100, h*5//100, (200, 50, 50))
    fill_rect(x + w*77//100, y + h*56//100, w*12//100, h*5//100, (200, 50, 50))
    fill_rect(x + w*86//100, y + h*68//100, w*8//100, h*5//100, (200, 50, 50))
    fill_rect(x + w*8//100, y + h*15//100, w*9//100, h*6//100, (40, 155, 80))
    fill_rect(x + w*10//100, y + h*80//100, w*18//100, h*5//100, (145, 145, 145))
    fill_rect(x + w*30//100, y + h*80//100, w*18//100, h*5//100, (145, 145, 145))
    fill_rect(x + w*50//100, y + h*80//100, w*18//100, h*5//100, (145, 145, 145))
    fill_rect(x + w*70//100, y + h*80//100, w*18//100, h*5//100, (145, 145, 145))
    fill_rect(x + w*75//100, y + h*24//100, w*12//100, h*4//100, (200, 50, 50))
    fill_rect(x + w*78//100, y + h*28//100, w*6//100, h*4//100, (200, 50, 50))
    fill_rect(x + w*80//100, y + h*32//100, w*2//100, h*4//100, (200, 50, 50))
    fill_rect(x + w*80//100, y + h*36//100, w*2//100, h*10//100, (200, 50, 50))

def scene7(x, y, w, h):
    fill_rect(x + w*18//100, y + h*45//100, w*64//100, h*12//100, (35, 33, 38))
    fill_rect(x + w*12//100, y + h*57//100, w*76//100, h*10//100, (145, 95, 55))
    fill_rect(x + w*49//100, y + h*23//100, w*2//100, h*20//100, (212, 175, 55))
    fill_rect(x + w*41//100, y + h*25//100, w*18//100, h*2//100, (212, 175, 55))
    fill_rect(x + w*39//100, y + h*28//100, w*6//100, h*2//100, (212, 175, 55))
    fill_rect(x + w*40//100, y + h*30//100, w*4//100, h*3//100, (212, 175, 55))
    fill_rect(x + w*55//100, y + h*28//100, w*6//100, h*2//100, (212, 175, 55))
    fill_rect(x + w*56//100, y + h*30//100, w*4//100, h*3//100, (212, 175, 55))
    flag_colors = [(200, 50, 50), (40, 150, 80), (50, 90, 190), (225, 180, 45), (225, 120, 40), (135, 70, 165), (40, 160, 160), (245, 245, 235)]
    for i, color in enumerate(flag_colors):
        px = x + w*6//100 + i*w*11//100
        fill_rect(px, y + h*7//100, 2, h*12//100, (95, 75, 55))
        fill_rect(px + 1, y + h*7//100, w*5//100, h*5//100, color)

def scene8(x, y, w, h):
    fill_rect(x, y, w, h, (10, 20, 45))
    fill_rect(x + w*44//100, y + h*30//100, w*12//100, h*34//100, WHITE)
    fill_rect(x + w*47//100, y + h*23//100, w*6//100, h*3//100, WHITE)
    fill_rect(x + w*46//100, y + h*26//100, w*8//100, h*3//100, WHITE)
    fill_rect(x + w*45//100, y + h*29//100, w*10//100, h*3//100, WHITE)
    fill_rect(x + w*39//100, y + h*52//100, w*5//100, h*12//100, WHITE)
    fill_rect(x + w*56//100, y + h*52//100, w*5//100, h*12//100, WHITE)
    fill_rect(x + w*44//100, y + h*64//100, w*12//100, h*4//100, (245, 135, 35))
    fill_rect(x + w*46//100, y + h*68//100, w*8//100, h*4//100, (245, 135, 35))
    fill_rect(x + w*48//100, y + h*72//100, w*4//100, h*4//100, (245, 135, 35))
    fill_circle(x + w*44//100, y + h*81//100, max(4, w//30), (130, 130, 130))
    fill_circle(x + w*53//100, y + h*84//100, max(5, w//25), (150, 150, 150))
    fill_circle(x + w*38//100, y + h*86//100, max(4, w//32), (110, 110, 110))
    fill_rect(x + w*7//100, y + h*10//100, w*15//100, h*7//100, (115, 120, 130))
    fill_rect(x + w*11//100, y + h*7//100, w*7//100, h*4//100, (170, 175, 185))
    fill_rect(x + w*2//100, y + h*11//100, w*5//100, h*4//100, (45, 75, 130))
    fill_rect(x + w*22//100, y + h*11//100, w*5//100, h*4//100, (45, 75, 130))
    fill_rect(x + w*9//100, y + h*85//100, w*6//100, h*4//100, (200, 50, 50))
    fill_rect(x + w*16//100, y + h*85//100, w*6//100, h*4//100, (40, 150, 80))

def wrap_lines(s, scale, max_w):
    lines = []
    for word in s.split():
        if not lines:
            lines = [word]
        elif text_width(lines[-1] + " " + word, scale) <= max_w:
            lines[-1] += " " + word
        elif len(lines) < 2:
            lines.append(word)
        else:
            break
    return lines[:2]

def draw_tag(x, y, label, color):
    fill_rect(x, y, text_width(label, 1) + 12, 16, color)
    draw_text(x + 6, y + 4, label, 1, WHITE)

def draw_leads_14():
    w, h = 239, 216
    leads = [
        (scene1, "USA", (180, 30, 30), "HUAWEI GUILTY ON 10 OF 12 COUNTS", "Jury convicts on trade secrets and bank fraud; racketeering charge fails"),
        (scene2, "GULF", (20, 60, 120), "FOUR TANKERS HIT MINES IN HORMUZ", "Iran says strait to close further; maritime centre says claims unconfirmed"),
        (scene3, "UKRAINE", (150, 110, 0), "KYIV DRONE STRIKES HIT RUSSIAN SHIPS", "Sparta II towed; corvette hit off Libya; Poland cites breach"),
        (scene4, "YEMEN", (30, 120, 60), "HOUTHIS 60 KM FROM ADEN", "Riyadh tower hit again, 11 wounded; Britain sanctions Houthi officials"),
    ]
    for i, (scene, label, color, headline, caption) in enumerate(leads):
        x, y = 16 + i * 251, 112
        draw_panel_base(x, y, w, h)
        scene(x + 4, y + 4, w - 8, 92)
        draw_tag(x + 4, y + 100, label, color)
        for j, line in enumerate(wrap_lines(headline, 2, w - 12)):
            draw_text(x + 6, y + 122 + j * 18, line, 2, INK)
        for j, line in enumerate(wrap_lines(caption, 1, w - 12)):
            draw_text(x + 6, y + 168 + j * 10, line, 1, INK)

def draw_leads_58():
    w, h = 239, 216
    leads = [
        (scene5, "COLOMBIA", (200, 90, 20), "25 HELD HOSTAGE IN CARTAGENA STORE", "Five women freed; car bomb in Villavicencio injures 23"),
        (scene6, "MARKETS", (110, 40, 140), "NVIDIA SLIDES 6% AS RALLY FADES", "Nasdaq down 1.5%; Seoul rebounds 6%, Nikkei up 3.9%; tariffs loom"),
        (scene7, "WORLD", (0, 120, 120), "14 NATIONS BACK ICJ GENOCIDE RULING", "Court finds Myanmar responsible over Rohingya in 2017"),
        (scene8, "SPACE", (20, 40, 90), "CHINA LAUNCHES SHENZHOU-24", "First foreign astronaut aboard China's Tiangong station"),
    ]
    for i, (scene, label, color, headline, caption) in enumerate(leads):
        x, y = 16 + i * 251, 336
        draw_panel_base(x, y, w, h)
        scene(x + 4, y + 4, w - 8, 92)
        draw_tag(x + 4, y + 100, label, color)
        for j, line in enumerate(wrap_lines(headline, 2, w - 12)):
            draw_text(x + 6, y + 122 + j * 18, line, 2, INK)
        for j, line in enumerate(wrap_lines(caption, 1, w - 12)):
            draw_text(x + 6, y + 168 + j * 10, line, 1, INK)

BRIEFS = [
    "TURKIYE - Air Force helicopter crashes, 5 crew killed in Eskisehir",
    "LIBYA - Haftar visits Turkey for first time, to meet Erdogan",
    "ISRAEL - Strike kills Hamas internal security chief Nahel in Gaza",
    "IRAQ - Baghdad orders federal control of Kurdish oilfields",
    "YEMEN - Saudi strikes on buses, trucks leave 25 dead or missing",
    "GAZA - Meningitis epidemic alert as cases hit 272 in October",
    "CONGO - Plane missing as rebels claim shootdown in South Kivu",
    "VIETNAM - Hanoi restaurant blast kills 6, injures at least 10",
    "MALAYSIA - To return thousands of migrants to Myanmar in Dec",
    "KOREA - Russian jets enter air defence zone; fighters scrambled",
    "BANGLADESH - Exiled Hasina plans return home on Dec 16",
    "INDONESIA - Prabowo names two candidates to replace VP Gibran",
    "CHINA - Official sentenced to death for spying for foreign state",
    "NATO - Rutte vows defence vs space threat as Russia denies report",
    "MEXICO - US drone helped capture El Chapo Isidro; Mexico to try him",
    "HAITI - Bukele names 3 Salvadoran soldiers killed in mission",
    "CANADA - Pentagon rebukes Ottawa over defence, F-35 review",
    "USA - Megaspeed, firm in Nvidia scandal, added to blacklist",
    "UKRAINE - Zelensky urges four-party talks with Russia, US, EU",
    "USA - Consumer confidence jumps to 103.3, highest in 2 years",
    "USA - Trump set to unveil new tariffs after capacity probe",
    "TECH - Microsoft declares 'Code Red' after historic outage",
    "CHINA - Politburo member Chen Jining probed in graft crackdown",
    "USA - Trump nominates NC prosecutor O'Neill as federal judge",
    "PACIFIC - Solomon Islands picks Australia as security partner",
    "SPORT - Senegal regains Africa Cup title after court appeal",
    "SPORT - FIFA names 2031 Women's World Cup co-hosts: US, Mexico",
]

def draw_briefs():
    draw_text(16, 566, "ALSO ON TUESDAY 24 NOVEMBER 2026", 2, INK)
    for i, brief in enumerate(BRIEFS):
        while text_width(brief, 1) > 484:
            brief = brief[:-1]
        x = 16 if i < 14 else 524
        row = i if i < 14 else i - 14
        draw_text(x, 600 + row * 26, brief, 1, INK)

def draw_footer():
    fill_rect(16, 976, 992, 1, INK)
    text = "SOURCES: REUTERS - AP - AFP - CNN - 24 NOVEMBER 2026"
    draw_text((W - text_width(text, 1)) // 2, 992, text, 1, INK)

def main():
    global canvas
    canvas = [bytearray(bytes(PAPER) * W) for _ in range(H)]
    fill_rect(0, 0, 1024, 1024, PAPER)
    fill_rect(0, 0, 1024, 104, NAVY)
    title = "THE WORLD IN ONE IMAGE"
    draw_text((W - text_width(title, 6)) // 2, 12, title, 6, WHITE)
    date = "TUESDAY 24 NOVEMBER 2026"
    draw_text((W - text_width(date, 4)) // 2, 58, date, 4, WHITE)
    subline = "35 STORIES - 6 REGIONS"
    draw_text((W - text_width(subline, 1)) // 2, 92, subline, 1, WHITE)
    draw_leads_14()
    draw_leads_58()
    draw_briefs()
    draw_footer()
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    write_png(out + "/entry.png", canvas)

if __name__ == "__main__":
    main()
