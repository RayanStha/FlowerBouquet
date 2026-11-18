import math
import os
import random
import re
import select
import shutil
import sys
import time

FPS = 24
SPIN_SPEED = 0.6
TILT = 0.30
CAM_DIST = 4.0
MESSAGE = "for you ♥"
FOOTER = "I LOVE YOU!!"       # bottom line, under the message
NUM_HEARTS = 18
SHOW_LETTER = True          # start with a sealed letter that opens into the bouquet
LETTER_TO = "to: you ♥"     # written on the envelope ("" to leave it blank)

WHITE = [244, 248, 251, 254, 255, 231]
PINK = [125, 162, 168, 205, 211, 218, 225]
RED = [52, 88, 124, 160, 196, 203]
PURPLE = [54, 91, 97, 134, 140, 183]
YELLOW = [136, 178, 214, 220, 226, 229]
ORANGE = [130, 166, 202, 208, 214, 216]
GOLD_CENTER = [94, 136, 178, 214, 220]
DARK_CENTER = [52, 58, 94, 130, 136]
SOFT_PINK = [89, 132, 168, 204, 211, 218, 225]
HYD_PINK = [96, 132, 169, 175, 212, 218, 225]
HYD_LILAC = [60, 97, 140, 176, 183, 189, 225]
HYD_BLUE = [18, 25, 32, 69, 75, 111, 153, 189]
HYD_PERIWINKLE = [54, 61, 62, 104, 105, 147, 189]
LILY_THROAT = [64, 106, 149, 150, 192, 193]
STARGAZER = [89, 125, 161, 162, 198, 205]
STARGAZER_EDGE = [175, 182, 218, 224, 225, 231]
ANTHER = [52, 94, 130, 166]
ENVELOPE = [94, 130, 137, 173, 179, 216, 223, 230]
LINER = [89, 125, 168, 175, 211, 218]
SEAL = [52, 88, 125, 161, 197, 204, 211, 218]
AIRMAIL = [167, 230, 68, 230]
GLITTER = [229, 223, 222, 218, 225, 231]
STAR_COLORS = [238, 241, 244, 248, 252]
HINT_COLORS = [175, 182, 218, 225, 231, 225, 218, 182]
PAPER_TEX = "%#&8@"
GREENS = [22, 28, 28, 34, 35, 71, 77, 114]
PAPER = [101, 144, 187, 223, 230, 231]
RIBBON = [88, 125, 161, 197, 204, 211]
HEART_COLORS = [161, 197, 204, 205, 211, 218]
MSG_COLORS = [161, 168, 205, 211, 218, 225, 218, 211, 205, 168]
SHADE = ".:-=+*%@"
PETAL_SHADE = "+*#%"
RESET = "\033[0m"
PIVOT_Y = 0.2

# Flower varieties you can use in BOUQUET below.
DAISIES = {  # petal colors, center colors, number of petals
    "white": (WHITE, GOLD_CENTER, 13),
    "pink": (PINK, GOLD_CENTER, 8),
    "red": (RED, DARK_CENTER, 6),
    "purple": (PURPLE, GOLD_CENTER, 7),
    "yellow": (YELLOW, DARK_CENTER, 12),
    "orange": (ORANGE, DARK_CENTER, 9),
}
TULIPS = {
    "pink": SOFT_PINK,
    "hot pink": PINK,
    "red": RED,
    "yellow": YELLOW,
    "purple": PURPLE,
    "white": WHITE,
    "orange": ORANGE,
}
LILIES = {  # petal middle, petal edge, throat, spot color (or None), stamen color
    "white": (WHITE, WHITE, LILY_THROAT, None, 193),
    "stargazer": (STARGAZER, STARGAZER_EDGE, LILY_THROAT, 89, 225),
    "pink": (SOFT_PINK, PINK, LILY_THROAT, None, 225),
    "tiger": (ORANGE, ORANGE, YELLOW, 52, 223),
}
HYDRANGEAS = {  # each little floret picks one of these palettes
    "pink": [HYD_PINK, HYD_PINK, HYD_LILAC],
    "blue": [HYD_BLUE, HYD_BLUE, HYD_PERIWINKLE],
    "mixed": [HYD_PINK, HYD_BLUE, HYD_LILAC, HYD_PERIWINKLE],
}

# The flowers in the bouquet: (kind, variety). Kinds are daisy, tulip, lily, hydrangea.
# The first one sits on top in the middle; the rest spiral outward and down,
# so entries next to each other in this list end up on different sides.
BOUQUET = [
    ("lily", "white"),
    ("tulip", "pink"),
    ("hydrangea", "pink"),
    ("hydrangea", "blue"),
    ("daisy", "yellow"),
    ("tulip", "pink"),
    ("hydrangea", "pink"),
    ("lily", "stargazer"),
    ("daisy", "white"),
    ("tulip", "red"),
    ("hydrangea", "blue"),
    ("daisy", "purple"),
]

FLOWER_SIZE = {
    "daisy": (0.12, 0.14),
    "tulip": (0.11, 0.11),
    "lily": (0.16, 0.17),
    "hydrangea": (0.14, 0.15),
}
FLORETS = 32

# Letter animation timeline, in seconds after the click.
SEAL_POP = 0.15
FLAP_OPEN = (0.3, 1.2)
GLITTER_TIME = (0.9, 2.0)
DISSOLVE_START = 1.4
BLOOM_START, BLOOM_TIME = 2.0, 1.6
LETTER_GONE = 3.8
FLAP_DEPTH = 0.56

MOUSE_ON = "\033[?1000h\033[?1006h"
MOUSE_OFF = "\033[?1000l\033[?1006l"
SGR_MOUSE = re.compile(rb"\x1b\[<(\d+);\d+;\d+([Mm])")
X10_MOUSE = re.compile(rb"\x1b\[M(.)..", re.S)

_L = (-0.45, 0.6, 0.66)
_n = math.sqrt(sum(v * v for v in _L))
LX, LY, LZ = (v / _n for v in _L)


def norm(v):
    m = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
    return (v[0] / m, v[1] / m, v[2] / m)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def basis(axis):
    helper = (0.0, 1.0, 0.0) if abs(axis[1]) < 0.9 else (1.0, 0.0, 0.0)
    u = norm(cross(helper, axis))
    return u, cross(axis, u)


def add(p, d, k):
    return (p[0] + d[0] * k, p[1] + d[1] * k, p[2] + d[2] * k)


def clamp01(b):
    return min(0.999, max(0.0, b))


def make_florets(rnd, palettes):
    golden = math.pi * (3 - math.sqrt(5))
    out = []
    for i in range(FLORETS):
        y = 1 - 2 * (i + 0.5) / FLORETS
        r = math.sqrt(1 - y * y)
        a = i * golden + rnd.uniform(-0.2, 0.2)
        out.append((r * math.cos(a), y, r * math.sin(a), rnd.choice(palettes), rnd.uniform(-0.25, 0.25)))
    return out


def build_scene():
    rnd = random.Random(21)
    pts = []
    neck = (0.0, -0.12, 0.0)

    C, D = (0.0, 0.12, 0.0), 0.64
    N = len(BOUQUET)
    golden = math.pi * (3 - math.sqrt(5))
    heads = []
    for i in range(N):
        el = math.radians(88 - 60 * math.sqrt(i / max(1, N - 1)))
        az = i * golden
        d = (math.cos(el) * math.cos(az), math.sin(el), math.cos(el) * math.sin(az))
        pos = add(C, d, D * rnd.uniform(0.92, 1.05))
        heads.append((pos, norm(d)))

    flowers = []
    for idx, (pos, axis) in enumerate(heads):
        base = add(pos, axis, -0.03)
        for j in range(70):
            t = j / 69
            p = (base[0] + (neck[0] - base[0]) * t, base[1] + (neck[1] - base[1]) * t,
                 base[2] + (neck[2] - base[2]) * t)
            pts.append((p[0], p[1], p[2], axis[0], 0.0, axis[2], GREENS, -0.15, True, None))

        kind, variety = BOUQUET[idx]
        spec = {"daisy": DAISIES, "tulip": TULIPS, "lily": LILIES, "hydrangea": HYDRANGEAS}[kind][variety]
        R = rnd.uniform(*FLOWER_SIZE[kind])
        extra = make_florets(rnd, spec) if kind == "hydrangea" else None
        flowers.append((pos, kind, spec, R, rnd.uniform(0, 6.28), extra))

    for i in range(8):
        a = (i + 0.4) / 8 * 2 * math.pi
        c, s = math.cos(a), math.sin(a)
        base = (0.26 * c, 0.30, 0.26 * s)
        d = norm((c, 0.15, s))
        side = (-s, 0.0, c)
        n = norm(cross(side, d))
        L, W = 0.30, 0.07
        for ti in range(32):
            t = ti / 31
            for wi in range(-5, 6):
                w = wi / 5
                curl = 0.025 * w * w
                p = (base[0] + d[0] * L * t + side[0] * W * math.sin(math.pi * t) * w + n[0] * curl,
                     base[1] + d[1] * L * t - 0.10 * t * t + n[1] * curl,
                     base[2] + d[2] * L * t + side[2] * W * math.sin(math.pi * t) * w + n[2] * curl)
                rib = -0.25 if wi == 0 else 0.0
                pts.append((p[0], p[1], p[2], n[0], n[1], n[2], GREENS, rib, True, None))

    y0, y1, r0, r1 = -0.20, 0.30, 0.06, 0.36
    k = (r1 - r0) / (y1 - y0)
    rings = 50
    for i in range(rings):
        t = i / (rings - 1)
        r = r0 + (r1 - r0) * t
        count = max(8, int(170 * r))
        for j in range(count):
            ph = (j + rnd.random()) / count * 2 * math.pi
            c, s = math.cos(ph), math.sin(ph)
            y = y0 + (y1 - y0) * t
            if t > 0.9:
                y += 0.03 * math.sin(9 * ph)
            fold = 0.3 * (abs(math.sin(5 * ph)) - 0.6)
            nn = norm((c, -k, s))
            pts.append((r * c, y, r * s, nn[0], nn[1], nn[2], PAPER, fold, False, None))

    for i in range(7):
        a = i / 7 * 2 * math.pi
        sx, sz = 0.025 * math.cos(a), 0.025 * math.sin(a)
        for j in range(40):
            t = j / 39
            pts.append((sx * (1 + 1.2 * t), -0.20 - 0.30 * t, sz * (1 + 1.2 * t),
                        math.cos(a), 0.0, math.sin(a), GREENS, -0.1, True, None))

    by = -0.12
    br = r0 + k * (by - y0) + 0.01
    for j in range(90):
        ph = j / 90 * 2 * math.pi
        for dy in (-0.012, 0.0, 0.012):
            pts.append((br * math.cos(ph), by + dy, br * math.sin(ph),
                        math.cos(ph), 0.0, math.sin(ph), RIBBON, 0.0, False, None))
    knot = (0.0, by, br + 0.01)
    for side in (-1, 1):
        for j in range(70):
            a = j / 70 * 2 * math.pi
            lx = side * (0.07 + 0.07 * math.cos(a))
            ly = 0.04 * math.sin(a) + 0.02 * (0.07 + 0.07 * math.cos(a)) / 0.14
            for fill in (1.0, 0.7):
                pts.append((knot[0] + lx * fill, knot[1] + ly * fill, knot[2] + 0.01,
                            side * 0.3, 0.2, 0.93, RIBBON, 0.1, True, None))
        for j in range(30):
            t = j / 29
            pts.append((knot[0] + side * 0.06 * t, knot[1] - 0.15 * t, knot[2] + 0.015,
                        side * 0.2, 0.0, 0.98, RIBBON, -0.05 + 0.05 * math.sin(t * 9), True, None))
    for dx in (-0.01, 0.0, 0.01):
        pts.append((dx, by, knot[2] + 0.02, 0, 0, 1, RIBBON, 0.2, True, "@"))

    babies = []
    for _ in range(90):
        a = rnd.random() * 2 * math.pi
        el = rnd.uniform(0.3, 1.4)
        rr = rnd.uniform(0.40, 0.58)
        babies.append((rr * math.cos(a) * math.cos(el), C[1] + rr * math.sin(el),
                       rr * math.sin(a) * math.cos(el), rnd.uniform(0, 6.28)))

    sparkles = []
    for _ in range(30):
        a = rnd.random() * 2 * math.pi
        rr = rnd.uniform(0.75, 0.95)
        sparkles.append((rr * math.cos(a), rnd.uniform(-0.3, 1.0), rr * math.sin(a),
                         rnd.uniform(0, 6.28), rnd.uniform(1.5, 4.0)))

    return pts, flowers, babies, sparkles


def update_hearts(hearts, dt):
    while len(hearts) < NUM_HEARTS:
        hearts.append([random.random(), 1.0 + random.random(), random.uniform(0.03, 0.08),
                       random.uniform(0, 6.28), random.choice(HEART_COLORS)])
    for h in hearts:
        h[1] -= h[2] * dt
        if h[1] < 0:
            h[0], h[1], h[4] = random.random(), 1.0, random.choice(HEART_COLORS)


def draw_daisy(plot, fx, fy, zt, rx, ry, dim, rot, spec):
    pal, cpal, n_pet = spec
    for row in range(int(fy - ry) - 1, int(fy + ry) + 2):
        dy = (row + 0.5 - fy) / ry
        for col in range(int(fx - rx) - 1, int(fx + rx) + 2):
            dx = (col + 0.5 - fx) / rx
            s = math.sqrt(dx * dx + dy * dy)
            if s > 1.0:
                continue
            if s < 0.3:
                b = clamp01(0.55 - 0.35 * dx - 0.35 * dy + dim)
                plot(col, row, zt + 0.06, "@" if s < 0.17 else "o", cpal[int(b * len(cpal))])
                continue
            ph = math.atan2(dy, dx)
            reach = 0.32 + 0.68 * abs(math.cos(n_pet * (ph + rot) / 2)) ** 0.7
            if s > reach:
                continue
            edge = -0.22 if s > reach - 0.14 else 0.0
            b = clamp01(0.62 - 0.22 * dx - 0.28 * dy + 0.12 * s + edge + dim)
            plot(col, row, zt + 0.04 * (1 - s),
                 PETAL_SHADE[int(b * len(PETAL_SHADE))], pal[int(b * len(pal))])


def draw_tulip(plot, fx, fy, zt, rx, ry, dim, pal):
    for row in range(int(fy - ry) - 1, int(fy + ry) + 2):
        dy = (row + 0.5 - fy) / ry
        v = (1 - dy) / 2
        if v < 0 or v > 1:
            continue
        hw = 0.62 * math.sin(math.pi * 0.5 * min(1.0, v * 1.5 + 0.05))
        if hw <= 0:
            continue
        for col in range(int(fx - rx) - 1, int(fx + rx) + 2):
            dx = (col + 0.5 - fx) / rx
            if abs(dx) > hw:
                continue
            xn = dx / hw
            if v > 0.72 + 0.28 * math.cos(1.5 * math.pi * xn) ** 2:
                continue
            seam = -0.25 if abs(abs(xn) - 0.33) < 0.12 and v > 0.3 else 0.0
            b = clamp01(0.55 - 0.3 * xn + 0.1 * v + seam + dim)
            plot(col, row, zt + 0.03, PETAL_SHADE[int(b * len(PETAL_SHADE))], pal[int(b * len(pal))])


def line_char(th):
    d = math.degrees(th) % 180
    if d < 22.5 or d >= 157.5:
        return "-"
    if d < 67.5:
        return "\\"
    if d < 112.5:
        return "|"
    return "/"


def draw_lily(plot, fx, fy, zt, rx, ry, dim, rot, spec):
    mid_pal, edge_pal, throat_pal, spot, filament = spec
    sixth = math.pi / 3
    for row in range(int(fy - ry) - 1, int(fy + ry) + 2):
        dy = (row + 0.5 - fy) / ry
        for col in range(int(fx - rx) - 1, int(fx + rx) + 2):
            dx = (col + 0.5 - fx) / rx
            s = math.sqrt(dx * dx + dy * dy)
            if s > 1.0:
                continue
            light = 0.62 - 0.22 * dx - 0.28 * dy + dim
            if s < 0.15:
                b = clamp01(light - 0.1)
                plot(col, row, zt + 0.05, PETAL_SHADE[int(b * len(PETAL_SHADE))],
                     throat_pal[int(b * len(throat_pal))])
                continue
            ph = math.atan2(dy, dx) - rot
            k = round(ph / sixth)
            a = ph - k * sixth
            inner = k % 2 == 1
            u = s * math.cos(a) / (0.9 if inner else 1.0)
            if u >= 1.0:
                continue
            w = (0.22 if inner else 0.17) * math.sin(math.pi * u ** 0.55)
            v = abs(s * math.sin(a))
            if v > w:
                continue
            frac = v / w
            groove = -0.22 if frac < 0.16 and u > 0.2 else 0.0
            rim = -0.15 if frac > 0.82 else 0.0
            b = clamp01(light + 0.12 * (1 - frac) + groove + rim + (0.05 if inner else 0.0))
            if u < 0.24:
                pal = throat_pal
            elif frac < 0.55:
                pal = mid_pal
            else:
                pal = edge_pal
            ch = PETAL_SHADE[int(b * len(PETAL_SHADE))]
            color = pal[int(b * len(pal))]
            if spot is not None and 0.22 < u < 0.62 and frac < 0.75:
                h = (int(u * 11) * 73856093) ^ (int(frac * 4) * 19349663) ^ ((k % 6) * 83492791)
                if h % 5 == 0:
                    ch, color = "%", spot
            plot(col, row, zt + 0.04 * (1 - s), ch, color)

    for i in range(7):
        pistil = i == 6
        th = rot + (0.25 if pistil else (i + 0.5) * sixth + 0.15 * math.sin(i * 2.3))
        reach = 0.3 if pistil else 0.4 + 0.05 * math.sin(i * 1.7)
        c, s = math.cos(th), math.sin(th)
        mid = reach - 0.12
        plot(int(fx + c * mid * rx), int(fy + s * mid * ry), zt + 0.08, line_char(th), filament)
        tip_col, tip_row = int(fx + c * reach * rx), int(fy + s * reach * ry)
        if pistil:
            plot(tip_col, tip_row, zt + 0.09, "*", 149)
        else:
            b = clamp01(0.6 - 0.3 * c - 0.3 * s + dim)
            plot(tip_col, tip_row, zt + 0.09, "o", ANTHER[int(b * len(ANTHER))])


def draw_hydrangea(plot, fx, fy, zt, rx, ry, dim, R, florets, view):
    ca, sa, ct, st = view
    depth = R * 0.7
    body = florets[0][3]
    for row in range(int(fy - ry * 0.85) - 1, int(fy + ry * 0.85) + 2):
        dy = (row + 0.5 - fy) / ry
        for col in range(int(fx - rx * 0.85) - 1, int(fx + rx * 0.85) + 2):
            dx = (col + 0.5 - fx) / rx
            s2 = (dx * dx + dy * dy) / 0.72
            if s2 > 1.0:
                continue
            nz = math.sqrt(1 - s2)
            b = clamp01(0.12 + 0.25 * max(0.0, -dx * LX - dy * LY + nz * LZ) + dim)
            plot(col, row, zt + depth * 0.55 * nz, ":", body[int(b * len(body))])

    size = 0.32
    frx, fry = size * rx, size * ry
    for px, py, pz, pal, frot in florets:
        xr = px * ca - pz * sa
        zr = px * sa + pz * ca
        yt = py * ct - zr * st
        zv = py * st + zr * ct
        if zv < -0.2:
            continue
        shade = 0.36 + 0.58 * max(0.0, xr * LX + yt * LY + zv * LZ) + dim
        ccx, ccy = fx + xr * 0.8 * rx, fy - yt * 0.8 * ry
        rl = math.sqrt(xr * xr + yt * yt) or 1.0
        rdx, rdy = xr / rl, yt / rl
        squash = max(0.35, zv)
        fz = zt + depth * (0.8 * zv + 0.25)
        for row in range(int(ccy - fry) - 1, int(ccy + fry) + 2):
            uy = -(row + 0.5 - ccy) / fry
            for col in range(int(ccx - frx) - 1, int(ccx + frx) + 2):
                ux = (col + 0.5 - ccx) / frx
                a = (ux * rdx + uy * rdy) / squash
                c = -ux * rdy + uy * rdx
                r = math.sqrt(a * a + c * c)
                if r > 1.0:
                    continue
                reach = 0.4 + 0.6 * abs(math.cos(2 * (math.atan2(c, a) + frot)))
                if r > reach:
                    continue
                b = clamp01(shade + 0.12 * (1 - r) - (0.2 if r > reach - 0.25 else 0.0))
                plot(col, row, fz, PETAL_SHADE[int(b * len(PETAL_SHADE))], pal[int(b * len(pal))])
        if zv > 0.15:
            b = clamp01(shade + 0.3)
            plot(int(ccx), int(ccy), fz + 0.01, "o", pal[int(b * len(pal))])


def new_canvas(cols, rows):
    return ([[" "] * cols for _ in range(rows)], [[0] * cols for _ in range(rows)],
            [[-1e9] * cols for _ in range(rows)])


def make_plot(canvas, view_rows):
    chars, colors, zbuf = canvas
    cols = len(chars[0])

    def plot(col, row, z, ch, color):
        if 0 <= row < view_rows and 0 <= col < cols and z > zbuf[row][col]:
            zbuf[row][col] = z
            chars[row][col] = ch
            colors[row][col] = color

    return plot


def draw_hearts(plot, hearts, t, cols, view_rows):
    for x, y, _, phase, color in hearts:
        col = int((x + 0.015 * math.sin(t * 1.2 + phase)) * cols) % cols
        plot(col, int(y * view_rows), -50, "♥", color)


def draw_bouquet(plot, scene, t, cols, view_rows, grow=1.0, anchor_row=None):
    pts, flowers, babies, sparkles = scene
    full = max(1.0, min((view_rows - 2) / 1.45, (cols - 2) / 2.7))
    scale = max(0.3, full * grow)
    sx_scale = scale * 2.0
    cx = cols / 2
    cy = 1 + 0.78 * full
    if anchor_row is not None and grow < 1.0:
        cy = anchor_row + (cy - anchor_row) * max(0.0, grow)

    ang = t * SPIN_SPEED + 3.0 * (1 - min(1.0, max(0.0, grow))) ** 2
    ca, sa = math.cos(ang), math.sin(ang)
    ct, st = math.cos(TILT), math.sin(TILT)

    def project(x, y, z):
        xr = x * ca - z * sa
        zr = x * sa + z * ca
        yp = y - PIVOT_Y
        yt = yp * ct - zr * st
        zt = yp * st + zr * ct
        f = CAM_DIST / (CAM_DIST - zt)
        return int(cx + xr * f * sx_scale), int(cy - yt * f * scale), zt

    def project_f(x, y, z):
        xr = x * ca - z * sa
        zr = x * sa + z * ca
        yp = y - PIVOT_Y
        yt = yp * ct - zr * st
        zt = yp * st + zr * ct
        f = CAM_DIST / (CAM_DIST - zt)
        return cx + xr * f * sx_scale, cy - yt * f * scale, zt, f

    for x, y, z, nx, ny, nz, pal, tone, two_sided, override in pts:
        col, row, zt = project(x, y, z)
        nxr = nx * ca - nz * sa
        nzr = nx * sa + nz * ca
        nyt = ny * ct - nzr * st
        nzt = ny * st + nzr * ct
        dot = nxr * LX + nyt * LY + nzt * LZ
        if two_sided and dot < 0:
            dot = -dot * 0.55
        b = 0.25 + 0.75 * max(0.0, dot) + tone
        b = min(0.999, max(0.0, b))
        if override == "P":
            ch = PETAL_SHADE[int(b * len(PETAL_SHADE))]
        else:
            ch = override or SHADE[int(b * len(SHADE))]
        plot(col, row, zt, ch, pal[int(b * len(pal))])

    view = (ca, sa, ct, st)
    for (x, y, z), kind, spec, R, seed, extra in flowers:
        fx, fy, zt, f = project_f(x, y, z)
        rx, ry = R * f * sx_scale, R * f * scale
        dim = -0.4 * (1 - min(1.0, max(0.0, (zt + 0.6) / 1.2)))
        rot = seed + ang * 0.7
        if kind == "daisy":
            draw_daisy(plot, fx, fy, zt, rx, ry, dim, rot, spec)
        elif kind == "tulip":
            draw_tulip(plot, fx, fy, zt, rx, ry, dim, spec)
        elif kind == "lily":
            draw_lily(plot, fx, fy, zt, rx, ry, dim, rot, spec)
        elif kind == "hydrangea":
            draw_hydrangea(plot, fx, fy, zt, rx, ry, dim, R, extra, view)

    for x, y, z, phase in babies:
        col, row, zt = project(x, y, z)
        star = math.sin(t * 2 + phase) > 0.6
        plot(col, row, zt + 0.02, "*" if star else "·", 231 if star else 255)

    for x, y, z, phase, speed in sparkles:
        col, row, zt = project(x, y, z)
        tw = math.sin(t * speed + phase)
        if tw > 0.85:
            plot(col, row, zt, "*", 231)
        elif tw > 0.4:
            plot(col, row, zt, "+", 225)
        elif tw > 0.0:
            plot(col, row, zt, "·", 218)



def hash01(a, b, salt=0):
    n = (a * 374761393 + b * 668265263 + salt * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_out_back(x):
    x = min(1.0, max(0.0, x)) - 1
    return 1 + 2.70158 * x ** 3 + 1.70158 * x ** 2


def build_intro():
    rnd = random.Random(7)
    burst = []
    for _ in range(46):
        a = rnd.uniform(0, 2 * math.pi)
        burst.append((math.cos(a), math.sin(a), rnd.uniform(8, 20), rnd.uniform(0.5, 1.0),
                      rnd.choice("♥♥*+·"), rnd.choice(SEAL[3:])))
    glitter = []
    for _ in range(70):
        glitter.append((rnd.uniform(0.25, 0.75), rnd.uniform(*GLITTER_TIME), rnd.uniform(-12, 12),
                        rnd.uniform(-28, -14), rnd.uniform(0.9, 1.5), rnd.choice("*+·♥*"),
                        rnd.choice(GLITTER)))
    stars = [(rnd.random(), rnd.random(), rnd.uniform(0, 6.28), rnd.uniform(0.8, 2.5))
             for _ in range(45)]
    return burst, glitter, stars


def letter_layout(cols, view_rows):
    W = max(16, min(cols - 2, int(min(cols * 0.62, (view_rows - 6) * 2.6))))
    H = max(7, int(W / 3.1))
    x0 = (cols - W) // 2
    y0 = max(1, (view_rows - H) // 2 + H // 5)
    return x0, y0, W, H


def draw_seg(put, xa, ya, xb, yb, z, color):
    dx, dy = xb - xa, yb - ya
    ratio = dy / dx if dx else 99.0
    if abs(ratio) < 0.2:
        ch = "-"
    elif abs(ratio) > 2.5:
        ch = "|"
    else:
        ch = "\\" if ratio > 0 else "/"
    n = int(max(abs(dx), abs(dy))) + 1
    for i in range(n + 1):
        k = i / n
        put(int(xa + dx * k), int(ya + dy * k), z, ch, color)


def in_heart(x, y):
    q = x * x + y * y - 1
    return q * q * q - x * x * y * y * y <= 0


def draw_heart(put, xc, yc, hw, z, pal):
    hh = hw / 2
    halo = 1.22
    for row in range(int(yc - hh * 1.7) - 1, int(yc + hh * 1.7) + 2):
        y = -(row + 0.5 - yc) / hh + 0.15
        for col in range(int(xc - hw * 1.6) - 1, int(xc + hw * 1.6) + 2):
            x = (col + 0.5 - xc) / hw
            if in_heart(x, y):
                b = clamp01(0.5 - 0.2 * x + 0.25 * y)
                ch = "*" if (x + 0.45) ** 2 + (y - 0.6) ** 2 < 0.05 else ("@" if b > 0.3 else "%")
                put(col, row, z, ch, pal[int(b * len(pal))] if ch != "*" else 225)
            elif in_heart(x / halo, (y - 0.15) / halo + 0.15):
                put(col, row, z - 1, " ", 0)


def draw_stars(plot, stars, t, cols, view_rows):
    for fx, fy, phase, speed in stars:
        tw = math.sin(t * speed + phase)
        if tw < 0.2:
            continue
        ch = "*" if tw > 0.92 else ("+" if tw > 0.7 else "·")
        plot(int(fx * cols), int(fy * view_rows), -40, ch,
             STAR_COLORS[int((tw - 0.2) / 0.81 * len(STAR_COLORS))])


def draw_letter(plot, t, s, cols, view_rows, intro):
    """The sealed envelope. s is seconds since it was clicked (None while still closed)."""
    burst, glitter, _ = intro
    x0, y0, W, H = letter_layout(cols, view_rows)
    xc = x0 + W / 2
    kx, ky = W / 78, H / 25
    p = 0.0 if s is None else smoothstep((s - FLAP_OPEN[0]) / (FLAP_OPEN[1] - FLAP_OPEN[0]))
    tip = FLAP_DEPTH * math.cos(math.pi * p)
    dis = None if s is None else s - DISSOLVE_START
    top, span = y0 - H * FLAP_DEPTH, H * (1 + FLAP_DEPTH)

    def put(col, row, z, ch, color):
        # Once dissolving, every cell of the envelope breaks off (top first) and floats up as glitter.
        if dis is None or dis < 0:
            plot(col, row, z, ch, color)
            return
        tau = dis - 0.8 * min(1.0, max(0.0, (row - top) / span)) - 0.3 * hash01(col, row, 1)
        if tau < 0:
            plot(col, row, z, ch, color)
            return
        h2, h3 = hash01(col, row, 2), hash01(col, row, 3)
        life = 0.6 + 0.5 * h2
        if tau >= life:
            return
        k = tau / life
        if k > 0.2:
            ch = "*" if k < 0.5 else ("+" if k < 0.75 else "·")
            color = GLITTER[int(h3 * len(GLITTER))]
        x = col + ((col - xc) * 1.2 + (h2 - 0.5) * 24 * kx) * tau
        y = row - (10 + 16 * h3) * ky * tau + 8 * ky * tau * tau
        plot(int(x), int(y), z + 60, ch, color)

    for r in range(H):
        v = (r + 0.5) / H
        row = y0 + r
        for c in range(W):
            col = x0 + c
            if r == 0 or r == H - 1 or c < 2 or c >= W - 2:
                put(col, row, 100, "/", AIRMAIL[((c + r) // 2) % 4])
                continue
            u = (c + 0.5) / W
            tri = 1 - abs(2 * u - 1)
            n = hash01(c, r, 4)
            ch = PAPER_TEX[int(hash01(c, r, 5) * len(PAPER_TEX))]
            b = 0.5 + 0.2 * (1 - v) - 0.12 * u + 0.12 * (n - 0.5)
            if tip > 0 and v < tip * tri:
                b += 0.08 - 0.3 * math.sin(math.pi * p)
            elif p > 0 and v < FLAP_DEPTH * 0.9 * tri:
                b = 0.08 + 0.2 * v / (FLAP_DEPTH * 0.9)
                ch = ":"
            elif tip > 0 and v < tip * tri + 0.08:
                b -= 0.2
            put(col, row, 100, ch, ENVELOPE[int(clamp01(b) * len(ENVELOPE))])

    seam = ENVELOPE[2]
    meet = y0 + H * 0.64
    draw_seg(put, x0 + 2, y0 + H - 1, xc, meet, 101, seam)
    draw_seg(put, x0 + W - 3, y0 + H - 1, xc, meet, 101, seam)
    if p > 0.3:
        inner = y0 + H * FLAP_DEPTH * 0.9
        draw_seg(put, x0 + 2, y0 + 1, xc, inner, 101, seam)
        draw_seg(put, x0 + W - 3, y0 + 1, xc, inner, 101, seam)

    if LETTER_TO and len(LETTER_TO) + 4 < W * 0.45:
        row = y0 + int(H * 0.8)
        start = int(xc - len(LETTER_TO) / 2)
        for i in range(-2, len(LETTER_TO) + 2):
            ch = LETTER_TO[i] if 0 <= i < len(LETTER_TO) else " "
            put(start + i, row, 101, ch, 224)

    if tip >= 0:
        tip_row = y0 + tip * H
        draw_seg(put, x0 + 1, y0, xc, tip_row, 103, ENVELOPE[1])
        draw_seg(put, x0 + W - 2, y0, xc, tip_row, 103, ENVELOPE[1])
    else:
        up = -tip * H
        for r_up in range(int(up) + 1):
            depth = (r_up + 0.5) / up
            for c in range(W):
                if depth > 1 - abs(2 * (c + 0.5) / W - 1):
                    continue
                n = hash01(c, r_up, 6)
                ch = "♥" if n > 0.94 else PAPER_TEX[int(hash01(c, r_up, 7) * len(PAPER_TEX))]
                b = clamp01(0.3 + 0.4 * (1 - depth) + 0.12 * (n - 0.5))
                put(x0 + c, y0 - 1 - r_up, 102, ch, LINER[int(b * len(LINER))])
        draw_seg(put, x0 + 1, y0 - 1, xc, y0 - up, 103, LINER[1])
        draw_seg(put, x0 + W - 2, y0 - 1, xc, y0 - up, 103, LINER[1])

    if s is None or s < SEAL_POP + 0.1:
        beat = abs(math.sin(t * 2.6)) ** 6
        swell = 1 + 0.1 * beat if s is None else 1 + 2.5 * s
        draw_heart(put, xc, y0 + tip * H, max(2.5, W * 0.095) * swell, 105, SEAL)

    if s is None:
        return
    tau = s - SEAL_POP
    yc = y0 + FLAP_DEPTH * H
    for dx, dy, speed, life, ch, color in burst:
        if 0 <= tau < life:
            plot(int(xc + dx * speed * 2 * kx * tau), int(yc + (dy * speed * tau + 6 * tau * tau) * ky),
                 170, ch if tau < life * 0.7 else "·", color)
    for u, begin, vx, vy, life, ch, color in glitter:
        g = s - begin
        if 0 <= g < life:
            plot(int(x0 + u * W + vx * kx * g), int(y0 + 1 + (vy * g + 15 * g * g) * ky),
                 160, ch if g < life * 0.75 else "·", color)


def write_text(canvas, row, text, palette, shift=0):
    chars, colors, _ = canvas
    cols = len(chars[0])
    start = max(0, (cols - len(text)) // 2)
    for i, ch in enumerate(text):
        if start + i < cols:
            chars[row][start + i] = ch
            colors[row][start + i] = palette[(i + shift) % len(palette)]


def canvas_to_ansi(canvas):
    chars, colors, _ = canvas
    lines = []
    for rc, rcol in zip(chars, colors):
        last = -1
        parts = []
        for ch, color in zip(rc, rcol):
            if ch != " " and color != last:
                last = color
                parts.append(f"\033[38;5;{last}m")
            parts.append(ch)
        lines.append("".join(parts))
    return "\033[H" + "\n".join(lines) + RESET


def render_frame(scene, intro, t, s, cols, rows, hearts, hint=""):
    """One frame. s = seconds since the letter was opened, or None while it's still sealed."""
    canvas = new_canvas(cols, rows)
    view_rows = rows - 2
    plot = make_plot(canvas, view_rows)
    draw_hearts(plot, hearts, t, cols, view_rows)
    letter = intro is not None and (s is None or s < LETTER_GONE)
    if letter:
        draw_stars(plot, intro[2], t, cols, view_rows)
    if s is not None and s >= BLOOM_START:
        _, y0, _, H = letter_layout(cols, view_rows)
        grow = ease_out_back((s - BLOOM_START) / BLOOM_TIME)
        draw_bouquet(plot, scene, t, cols, view_rows, grow, y0 + H * 0.5)
    if letter:
        draw_letter(plot, t, s, cols, view_rows, intro)

    shift = int(t * 6)
    if s is None:
        write_text(canvas, rows - 2, hint, HINT_COLORS, shift)
    elif s > BLOOM_START + 0.8:
        write_text(canvas, rows - 2, MESSAGE, MSG_COLORS, shift)
    write_text(canvas, rows - 1, FOOTER, [211])
    return canvas_to_ansi(canvas)


def render(scene, t, cols, rows, hearts):
    return render_frame(scene, None, t, 1e9, cols, rows, hearts)


class Input:
    """Non-blocking clicks and key presses. Clicks need a terminal with mouse reporting."""

    def __init__(self):
        self.kind = None
        self.saved = None
        try:
            if os.name == "nt":
                import msvcrt
                self.msvcrt = msvcrt
                self.kind = "keys"
            elif sys.stdin.isatty():
                import termios
                import tty
                self.termios = termios
                self.fd = sys.stdin.fileno()
                self.saved = termios.tcgetattr(self.fd)
                tty.setcbreak(self.fd)
                sys.stdout.write(MOUSE_ON)
                self.kind = "mouse"
        except Exception:
            self.kind = None

    @property
    def hint(self):
        if self.kind == "mouse":
            return "click the letter (or press any key) to open ♥"
        if self.kind == "keys":
            return "press any key to open ♥"
        return "opening… ♥"

    def poll(self):
        """True if there was a click or key press since the last call."""
        if self.kind == "keys":
            hit = False
            while self.msvcrt.kbhit():
                self.msvcrt.getwch()
                hit = True
            return hit
        if self.kind != "mouse":
            return False
        data = b""
        while select.select([self.fd], [], [], 0)[0]:
            chunk = os.read(self.fd, 1024)
            if not chunk:
                break
            data += chunk
        if not data:
            return False
        clicks = [b for b, kind in SGR_MOUSE.findall(data) if kind == b"M" and int(b) < 64]
        old_clicks = [b for b in X10_MOUSE.findall(data) if (b[0] - 32) & 3 != 3 and b[0] - 32 < 64]
        keys = X10_MOUSE.sub(b"", SGR_MOUSE.sub(b"", data))
        return bool(clicks or old_clicks or keys)

    def mouse_off(self):
        if self.kind == "mouse":
            sys.stdout.write(MOUSE_OFF)

    def close(self):
        self.mouse_off()
        if self.saved is not None:
            self.termios.tcsetattr(self.fd, self.termios.TCSADRAIN, self.saved)


def main():
    if os.name == "nt":
        os.system("")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    scene = build_scene()
    intro = build_intro()
    hearts = []
    inp = Input()
    sys.stdout.write("\033[?25l\033[2J")
    start = last = time.perf_counter()
    opened_at = None if SHOW_LETTER else -1e6
    last_size = None
    try:
        while True:
            now = time.perf_counter()
            dt, last = now - last, now
            t = now - start
            clicked = inp.poll()
            if opened_at is None and (clicked or (inp.kind is None and t > 3.0)):
                opened_at = t
                inp.mouse_off()
            size = shutil.get_terminal_size((80, 30))
            cols, rows = max(20, size.columns - 1), max(12, size.lines - 1)
            if (cols, rows) != last_size:
                sys.stdout.write("\033[2J")
                last_size = (cols, rows)
            update_hearts(hearts, dt)
            s = None if opened_at is None else t - opened_at
            sys.stdout.write(render_frame(scene, intro, t, s, cols, rows, hearts, inp.hint))
            sys.stdout.flush()
            wait = 1 / FPS - (time.perf_counter() - now)
            if wait > 0:
                time.sleep(wait)
    except KeyboardInterrupt:
        pass
    finally:
        inp.close()
        sys.stdout.write(RESET + "\033[?25h\033[2J\033[H")
        print("\033[38;5;205m♥\033[0m")


if __name__ == "__main__":
    main()
