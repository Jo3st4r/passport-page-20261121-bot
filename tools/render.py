"""Render the passport spread for the Republic of Veskar.

Draws a complete invented passport spread (data page + visas/stamps page)
for a fictional North Atlantic island republic, using only PIL primitives.
Fully deterministic: fixed geometry, fixed colours, fixed-seed paper grain.
No network, no timestamps, no randomness beyond a fixed seed.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024

PAPER = (243, 236, 215)
PAPER_DARK = (232, 222, 194)
NAVY = (30, 58, 92)
NAVY_SOFT = (52, 84, 122)
INK = (34, 32, 26)
GREY = (96, 92, 80)
STAMP_RED = (126, 47, 38)
STAMP_BLUE = (44, 79, 124)
STAMP_GREEN = (46, 93, 67)
STAMP_PURPLE = (91, 58, 110)
GUILLOCHE = (208, 194, 158)
SKIN = (217, 181, 150)
SKIN_DARK = (198, 160, 128)
HAIR = (46, 38, 32)
SLATE = (46, 61, 78)
SWEATER = (58, 76, 96)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    path = os.path.join(FONT_DIR, name)
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


SERIF = "DejaVuSerif.ttf"
SERIF_B = "DejaVuSerif-Bold.ttf"
SANS = "DejaVuSans.ttf"
SANS_B = "DejaVuSans-Bold.ttf"
MONO = "DejaVuSansMono.ttf"


def text_center(draw, cx, y, s, fnt, fill):
    w = draw.textlength(s, font=fnt)
    draw.text((cx - w / 2, y), s, font=fnt, fill=fill)
    return w


def text_spaced(draw, cx, y, s, fnt, fill, spacing=3):
    """Draw text with extra letter spacing, centred on cx."""
    widths = [draw.textlength(ch, font=fnt) for ch in s]
    total = sum(widths) + spacing * (len(s) - 1)
    x = cx - total / 2
    for ch, wd in zip(s, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += wd + spacing


def wrap_text(draw, text, fnt, max_width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- MRZ helpers
def _mrz_value(ch):
    if ch == "<":
        return 0
    if ch.isdigit():
        return int(ch)
    return ord(ch) - 55  # A=10 ... Z=35


def mrz_check(field):
    total = 0
    for i, ch in enumerate(field):
        total += _mrz_value(ch) * (7, 3, 1)[i % 3]
    return str(total % 10)


def build_mrz():
    """Return (line1, line2) for holder Ingrid Marie Halvorsen, Veskar."""
    surname = "HALVORSEN"
    given = "INGRID<MARIE"
    line1 = ("P<VSK" + surname + "<<" + given).ljust(44, "<")
    doc = "VK483917<"
    doc_cd = mrz_check(doc)
    dob = "880314"
    dob_cd = mrz_check(dob)
    exp = "360202"
    exp_cd = mrz_check(exp)
    personal = "<" * 14  # optional-data field, positions 29-42
    personal_cd = mrz_check(personal)  # position 43
    # composite check digit, position 44, over positions 1-10, 14-20, 22-43
    composite = mrz_check(doc + doc_cd + dob + dob_cd + exp + exp_cd
                          + personal + personal_cd)
    line2 = (doc + doc_cd + "VSK" + dob + dob_cd + "F" + exp + exp_cd
             + personal + personal_cd + composite)
    assert len(line1) == 44 and len(line2) == 44, (line1, line2)
    return line1, line2


# ---------------------------------------------------------------- coat of arms
def draw_arms(draw, cx, top, scale=1.0):
    """Small line-art coat of arms: shield, puffin over three waves, star."""
    w, h = int(64 * scale), int(78 * scale)
    x0, y0 = cx - w // 2, top
    # star above shield
    star_cx, star_cy, r = cx, y0 + int(7 * scale), int(7 * scale)
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((star_cx + rr * math.cos(ang), star_cy + rr * math.sin(ang)))
    draw.polygon(pts, outline=NAVY, fill=NAVY)
    # shield outline
    sy = y0 + int(16 * scale)
    sh = h - int(16 * scale)
    shield = [
        (x0, sy),
        (x0 + w, sy),
        (x0 + w, sy + int(sh * 0.62)),
        (cx, sy + sh),
        (x0, sy + int(sh * 0.62)),
    ]
    draw.polygon(shield, outline=NAVY, width=2)
    # puffin: body ellipse, white belly, beak, eye
    bx, by = cx, sy + int(sh * 0.30)
    draw.ellipse([bx - 15, by - 13, bx + 15, by + 13], fill=(250, 250, 246),
                 outline=NAVY, width=2)
    draw.ellipse([bx - 8, by - 2, bx + 8, by + 13], fill=(250, 250, 246))
    draw.polygon([(bx + 12, by - 6), (bx + 24, by - 1), (bx + 12, by + 3)],
                 fill=(198, 84, 44), outline=NAVY)
    draw.ellipse([bx + 4, by - 9, bx + 8, by - 5], fill=NAVY)
    # three waves
    for k in range(3):
        wy = sy + int(sh * 0.62) + k * 7
        pts = []
        for xx in range(x0 + 8, x0 + w - 6, 4):
            pts.append((xx, wy + 2.5 * math.sin((xx - x0) / 9.0 + k)))
        draw.line(pts, fill=NAVY_SOFT, width=2)


# ---------------------------------------------------------------- portrait
def draw_portrait(base, x, y, w, h):
    """Flat-illustration passport portrait of a North Atlantic islander."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # background: pale blue-grey gradient + faint dots
    for yy in range(h):
        t = yy / max(1, h - 1)
        col = tuple(int(a + (b - a) * t) for a, b in zip((205, 214, 220), (168, 180, 190)))
        d.line([(0, yy), (w, yy)], fill=col + (255,))
    for yy in range(6, h, 9):
        for xx in range(6, w, 9):
            d.point((xx, yy), fill=(150, 162, 172, 90))
    cx = w // 2
    # shoulders / knitted sweater
    d.pieslice([cx - 78, h - 96, cx + 78, h + 60], 180, 360, fill=SWEATER)
    d.rectangle([cx - 78, h - 52, cx + 78, h], fill=SWEATER)
    for yy in range(h - 46, h - 4, 9):  # knit rows
        d.line([(cx - 70, yy), (cx + 70, yy)], fill=(72, 92, 114, 255), width=1)
    # collar V
    d.polygon([(cx - 22, h - 62), (cx + 22, h - 62), (cx, h - 34)],
              fill=(228, 226, 218))
    # neck
    d.rectangle([cx - 13, h - 108, cx + 13, h - 62], fill=SKIN_DARK)
    # ears
    d.ellipse([cx - 40, h - 158, cx - 28, h - 138], fill=SKIN)
    d.ellipse([cx + 28, h - 158, cx + 40, h - 138], fill=SKIN)
    # face
    d.ellipse([cx - 34, h - 178, cx + 34, h - 102], fill=SKIN)
    # hair: shoulder-length, framing the face
    d.pieslice([cx - 40, h - 190, cx + 40, h - 108], 180, 360, fill=HAIR)
    d.ellipse([cx - 40, h - 168, cx - 26, h - 96], fill=HAIR)
    d.ellipse([cx + 26, h - 168, cx + 40, h - 96], fill=HAIR)
    d.polygon([(cx - 40, h - 150), (cx - 30, h - 176), (cx - 18, h - 160)],
              fill=HAIR)
    d.polygon([(cx + 40, h - 150), (cx + 30, h - 176), (cx + 18, h - 160)],
              fill=HAIR)
    # brows, eyes, nose, mouth (muted, minimal)
    d.line([(cx - 22, h - 146), (cx - 8, h - 148)], fill=HAIR, width=2)
    d.line([(cx + 8, h - 148), (cx + 22, h - 146)], fill=HAIR, width=2)
    d.ellipse([cx - 19, h - 141, cx - 11, h - 134], fill=(38, 32, 28))
    d.ellipse([cx + 11, h - 141, cx + 19, h - 134], fill=(38, 32, 28))
    d.line([(cx, h - 138), (cx - 2, h - 122)], fill=SKIN_DARK, width=2)
    d.line([(cx - 9, h - 114), (cx + 9, h - 114)], fill=(150, 84, 72), width=2)
    base.alpha_composite(img, (x, y))


# ---------------------------------------------------------------- stamps
def circular_stamp(base, cx, cy, r, top_text, center_lines, color, angle):
    """Round immigration stamp: double circle, straight centred lines."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    col = color + (215,)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=3)
    d.ellipse([cx - r + 9, cy - r + 9, cx + r - 9, cy + r - 9], outline=col, width=1)
    lines = [top_text] + list(center_lines)
    y = cy - (len(lines) - 1) * 21 // 2 - 6
    for i, line in enumerate(lines):
        size = 13 if i == 0 else 12
        text_center(d, cx, y, line, font(SANS_B, size), col)
        y += 21
        if i == 0:
            d.line([(cx - 26, y - 3), (cx + 26, y - 3)], fill=col, width=1)
    layer = layer.rotate(angle, resample=Image.BICUBIC, center=(cx, cy))
    base.alpha_composite(layer)


def rect_stamp(base, x, y, w, h, lines, color, angle, font_size=15):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    col = color + (215,)
    cx, cy = x + w // 2, y + h // 2
    d.rounded_rectangle([x, y, x + w, y + h], radius=6, outline=col, width=3)
    d.rounded_rectangle([x + 5, y + 5, x + w - 5, y + h - 5], radius=4,
                        outline=col, width=1)
    yy = cy - (len(lines) - 1) * (font_size + 5) // 2 - 4
    for line in lines:
        text_center(d, cx, yy, line, font(SANS_B, font_size), col)
        yy += font_size + 5
    layer = layer.rotate(angle, resample=Image.BICUBIC, center=(cx, cy))
    base.alpha_composite(layer)


# ---------------------------------------------------------------- page build
def render():
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(img)

    # paper grain (fixed seed -> deterministic)
    rng = random.Random(20261121)
    grain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grain)
    for _ in range(2600):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, H - 1)
        gd.point((x, y), fill=(120, 100, 60, rng.randint(6, 16)))
    img.alpha_composite(grain)

    # guilloche: faint sine waves across both pages
    for yy in range(48, H - 40, 15):
        pts = [(x, yy + 4 * math.sin(x / 55.0 + yy / 40.0)) for x in range(34, 991, 6)]
        d.line(pts, fill=GUILLOCHE, width=1)

    # outer frame + gutter
    d.rectangle([24, 24, 1000, 1000], outline=NAVY, width=3)
    d.rectangle([30, 30, 994, 994], outline=NAVY, width=1)
    d.line([(512, 30), (512, 994)], fill=NAVY, width=2)
    d.line([(515, 30), (515, 994)], fill=(120, 120, 110), width=1)

    # ================= LEFT PAGE: DATA PAGE =================
    draw_arms(d, 270, 46)
    text_center(d, 270, 132, "REPUBLIC OF VESKAR", font(SERIF_B, 29), NAVY)
    text_spaced(d, 270, 166, "LÝÐVELDIÐ VESKAR", font(SANS, 13), NAVY_SOFT, spacing=4)
    text_center(d, 270, 190, "PASSPORT  ·  VEGABRÉF", font(SERIF_B, 19), NAVY)
    d.line([(60, 218), (480, 218)], fill=NAVY, width=2)

    # photo
    px, py, pw, ph = 60, 234, 150, 188
    d.rectangle([px - 3, py - 3, px + pw + 3, py + ph + 3], outline=NAVY, width=2)
    draw_portrait(img, px, py, pw, ph)
    # small embossed seal fully inside the photo's bottom-right corner
    seal_cx, seal_cy, seal_r = px + pw - 26, py + ph - 26, 24
    seal = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seal)
    scol = STAMP_BLUE + (190,)
    sd.ellipse([seal_cx - seal_r, seal_cy - seal_r, seal_cx + seal_r, seal_cy + seal_r],
               outline=scol, width=2)
    sd.ellipse([seal_cx - seal_r + 5, seal_cy - seal_r + 5,
                seal_cx + seal_r - 5, seal_cy + seal_r - 5], outline=scol, width=1)
    sd.text((seal_cx, seal_cy), "VK", font=font(SANS_B, 14), fill=scol, anchor="mm")
    img.alpha_composite(seal)

    # holder fields, right of the photo
    fx = 232
    fields = [
        ("SURNAME / ÆTTARNAFN", "HALVORSEN"),
        ("GIVEN NAMES / FORNÖFN", "INGRID MARIE"),
        ("NATIONALITY / RÍKISFANG", "VESKARI"),
        ("DATE OF BIRTH / FÆÐINGARDAGUR", "14 MAR 1988"),
        ("PLACE OF BIRTH / FÆÐINGARSTAÐUR", "KALDVIK"),
        ("SEX / KYN", "F"),
    ]
    fy = 236
    for label, value in fields:
        d.text((fx, fy), label, font=font(SANS, 10), fill=GREY)
        d.text((fx, fy + 13), value, font=font(SANS_B, 15), fill=INK)
        fy += 31
    d.line([(fx - 10, 232), (fx - 10, fy - 8)], fill=NAVY_SOFT, width=1)  # thin rule

    # second field row, full width
    d.line([(60, 448), (480, 448)], fill=NAVY, width=1)
    d.text((60, 460), "PASSPORT NO. / VEGABRÉFSNÚMER", font=font(SANS, 10), fill=GREY)
    d.text((60, 473), "VK 483 917", font=font(SANS_B, 16), fill=INK)
    d.text((280, 460), "DATE OF EXPIRY / GILDISTÍMI", font=font(SANS, 10), fill=GREY)
    d.text((280, 473), "02 FEB 2036", font=font(SANS_B, 16), fill=INK)
    d.text((60, 508), "DATE OF ISSUE / ÚTGÁFUDAGUR", font=font(SANS, 10), fill=GREY)
    d.text((60, 521), "02 FEB 2026", font=font(SANS_B, 16), fill=INK)
    d.text((280, 508), "AUTHORITY / ÚTGÁFANDI", font=font(SANS, 10), fill=GREY)
    d.text((280, 521), "PASSPORT OFFICE", font=font(SANS_B, 14), fill=INK)

    # signature
    d.text((60, 566), "Ingrid M. Halvorsen", font=font(SERIF, 22), fill=INK)
    d.line([(60, 594), (300, 594)], fill=NAVY_SOFT, width=1)
    d.text((60, 600), "SIGNATURE OF HOLDER / UNDIRSKRIFT", font=font(SANS, 9), fill=GREY)

    # machine-readable zone
    d.line([(60, 640), (480, 640)], fill=NAVY, width=1)
    line1, line2 = build_mrz()
    d.text((60, 652), line1, font=font(MONO, 15), fill=INK)
    d.text((60, 674), line2, font=font(MONO, 15), fill=INK)

    # observations box: the seafarer detail
    d.rounded_rectangle([60, 716, 480, 806], radius=4, outline=NAVY, width=1)
    d.text((72, 726), "OBSERVATIONS / ATHUGASEMDIR", font=font(SANS_B, 11), fill=NAVY)
    obs = ("HOLDER IS A REGISTERED SEAFARER. "
           "CREW PERMIT No. C-2214. EMPLOYMENT ABOARD "
           "FISHING VESSELS REQUIRES A SEPARATE PERMIT.")
    lines = wrap_text(d, obs, font(SANS, 12), 396)
    yy = 746
    for ln in lines:
        d.text((72, yy), ln, font=font(SANS, 12), fill=INK)
        yy += 16

    # faint "VK" watermarks filling the empty bottom of each page
    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wm)
    wd.text((270, 890), "VK", font=font(SERIF_B, 110), fill=NAVY + (16,),
            anchor="mm")
    wd.text((754, 925), "VK", font=font(SERIF_B, 80), fill=NAVY + (16,),
            anchor="mm")
    img.alpha_composite(wm)

    # left page number
    d.text((270, 968), "1", font=font(SANS, 11), fill=GREY, anchor="mm")

    # ================= RIGHT PAGE: VISAS & STAMPS =================
    text_center(d, 754, 52, "VISAS", font(SERIF_B, 24), NAVY)
    text_spaced(d, 754, 84, "VEGABRÉF · ÁRITANIR", font(SANS, 12), NAVY_SOFT, spacing=3)
    d.line([(548, 112), (960, 112)], fill=NAVY, width=2)

    # Ostara visitor visa sticker
    vx, vy, vw, vh = 548, 130, 412, 118
    d.rectangle([vx, vy, vx + vw, vy + vh], outline=NAVY, width=2,
                fill=(226, 232, 238))
    d.rectangle([vx + 5, vy + 5, vx + vw - 5, vy + vh - 5], outline=NAVY_SOFT, width=1)
    # Ostara flag: three vertical bands
    fx0, fy0 = vx + 16, vy + 18
    for i, col in enumerate([(46, 93, 67), (198, 164, 84), (30, 58, 92)]):
        d.rectangle([fx0 + i * 14, fy0, fx0 + i * 14 + 13, fy0 + 82], fill=col)
    d.rectangle([fx0, fy0, fx0 + 42, fy0 + 82], outline=NAVY, width=1)
    tx = vx + 74
    d.text((tx, vy + 14), "KINGDOM OF OSTARA", font=font(SANS_B, 16), fill=NAVY)
    d.text((tx, vy + 36), "VISITOR VISA — 30 DAYS", font=font(SANS, 13), fill=INK)
    d.text((tx, vy + 56), "ISSUED AT KALDVIK  22 APR 2026", font=font(SANS, 12), fill=INK)
    d.text((tx, vy + 74), "VALID 01 MAY — 31 OCT 2026", font=font(SANS, 12), fill=INK)
    d.text((tx, vy + 92), "VISA No. OS-22914", font=font(SANS, 12), fill=INK)

    # circular stamps: Aurelia arrival + Ostara entry
    circular_stamp(img, 652, 348, 72, "AURELIA",
                   ["PORT MERIDIAN", "ARRIVED", "12 MAY 2026"], STAMP_RED, -8)
    circular_stamp(img, 856, 348, 72, "OSTARA",
                   ["BORDER CONTROL", "ENTRY", "03 JUN 2026"], STAMP_GREEN, 6)

    # Ternmark entry + departure pair
    rect_stamp(img, 548, 452, 196, 74, ["TERNMARK", "ENTRY", "19 AUG 2026"],
               STAMP_BLUE, -4)
    rect_stamp(img, 764, 452, 196, 74, ["TERNMARK", "DEPARTED", "28 AUG 2026"],
               STAMP_BLUE, 5)

    # Veskar re-entry + landing-fee stamp
    circular_stamp(img, 800, 636, 60, "VESKAR",
                   ["KALDVIK", "ENTRY", "05 SEP 2026"], NAVY, -5)
    rect_stamp(img, 548, 606, 150, 66, ["LANDING FEE", "40 KR — PAID"],
               STAMP_PURPLE, 8, font_size=13)

    # conditions box: the telling paperwork detail
    d.rounded_rectangle([548, 736, 960, 872], radius=4, outline=NAVY, width=1)
    d.text((562, 748), "CONDITIONS OF ISSUE", font=font(SANS_B, 12), fill=NAVY)
    cond = ("The holder must register with the Harbourmaster within "
            "48 hours of landing in any Veskari port. Employment aboard "
            "fishing vessels requires a separate Crew Permit. This "
            "passport remains the property of the Republic of Veskar.")
    lines = wrap_text(d, cond, font(SANS, 12), 384)
    yy = 770
    for ln in lines:
        d.text((562, yy), ln, font=font(SANS, 12), fill=INK)
        yy += 17
    d.text((562, 838), "FEE STAMP: LANDING FEE 40 KR — SEE STAMP ABOVE.",
           font=font(SANS, 10), fill=GREY)

    # right page number
    d.text((754, 968), "2", font=font(SANS, 11), fill=GREY, anchor="mm")

    return img.convert("RGB")
