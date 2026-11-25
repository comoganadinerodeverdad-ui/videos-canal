import json, math, subprocess, wave, sys, random
import numpy as np
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------- args:  mode (long|reel) , name , t0 , t1 , title , subtitle , [testtimes...]
MODE = sys.argv[1]; NAME = sys.argv[2]; FIRST = int(sys.argv[3]); LASTP = int(sys.argv[4]); TESTS = [float(x) for x in sys.argv[5:]]
LONG = MODE == "long"
W, H = (1920, 1080) if LONG else (1080, 1920)
FPS = 30
OFF = 0.0                           # NICO 25-nov: voz y escena desde el fotograma 0
TAIL = 2.5 if LONG else 2.8          # reel closing card
S = min(W, H) / 1080.0
NAVY = (13, 22, 43); NAVY2 = (26, 40, 74); CREAM = (246, 241, 232); MINT = (45, 212, 160)
CORAL = (255, 107, 107); GOLD = (255, 196, 61); BLUE = (96, 165, 250); MUTED = (148, 163, 184); INK = (15, 23, 42)
FD = "/usr/share/fonts/opentype/inter/"
@lru_cache(None)
def F(n, s): return ImageFont.truetype(FD + {"x": "Inter-ExtraBold.otf", "b": "Inter-Bold.otf", "m": "Inter-Medium.otf"}[n], int(s))
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def pop(x): x = max(0, min(1, x)); return 1 + 0.12 * math.sin(x * math.pi) * (1 - x) if x < 1 else 1
def seg(t, a, d=0.45): return ease((t - a) / d)

# ---------- background
@lru_cache(None)
def grad():
    g = np.zeros((H, W, 3), np.float32)
    for i in range(3): g[:, :, i] = np.linspace(NAVY[i], NAVY2[i], H)[:, None]
    return Image.fromarray(g.astype(np.uint8))
random.seed(5); CIR = [(random.random() * W, random.random() * H, random.randint(150, 380) * S, random.random() * 6.28) for _ in range(6)]
def bg(t):
    im = grad().copy(); o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    for x, y, r, ph in CIR:
        cx = x + 40 * math.sin(t * .35 + ph); cy = y + 30 * math.cos(t * .3 + ph)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(96, 165, 250, 14))
    im.paste(o, (0, 0), o); return im

# ---------- text helpers
def T(im, txt, font, cx, cy, fill=CREAM, a=1.0, k=1.0):
    if a <= 0.01 or k < 0.03: return
    b = font.getbbox(txt); w = b[2] - b[0] + 20; h = b[3] - b[1] + 20
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(lay).text((10 - b[0], 10 - b[1]), txt, font=font, fill=fill + (255,))
    if abs(k - 1) > .001: lay = lay.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    im.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)
def fit(txt, n, size, maxw):
    s = size
    while s > 20 and F(n, s).getlength(txt) > maxw: s -= 2
    return F(n, s)
@lru_cache(None)
def panel_img(w, h, fill, r, line=None):
    sc = 3; im = Image.new("RGBA", (w * sc, h * sc), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * sc - 1, h * sc - 1), r * sc, fill=fill, outline=line, width=3 * sc if line else 0)
    return im.resize((w, h), Image.LANCZOS)
def panel(im, cx, cy, w, h, fill=(255, 255, 255, 22), r=28, a=1.0, line=None, k=1.0):
    if a <= .01: return
    w = int(w * k); h = int(h * k); p = panel_img(max(2, w), max(2, h), fill, int(r), line)
    if a < 1: p = p.copy(); p.putalpha(p.getchannel("A").point(lambda v: int(v * a)))
    im.paste(p, (int(cx - w / 2), int(cy - h / 2)), p)

# ---------- icons
def mk(w, h, fn):
    sc = 4; im = Image.new("RGBA", (w * sc, h * sc), (0, 0, 0, 0)); d = ImageDraw.Draw(im); fn(d, w * sc, h * sc)
    return im.resize((w, h), Image.LANCZOS)
@lru_cache(None)
def ic_card(w):
    h = int(w * .64)
    def f(d, W_, H_):
        d.rounded_rectangle((0, 0, W_ - 1, H_ - 1), H_ * .12, fill=(59, 130, 246))
        d.rectangle((0, H_ * .2, W_, H_ * .36), fill=(23, 37, 84))
        d.rounded_rectangle((W_ * .08, H_ * .5, W_ * .26, H_ * .68), H_ * .04, fill=GOLD)
        for i in range(4): d.ellipse((W_ * (.08 + i * .06), H_ * .8, W_ * (.11 + i * .06), H_ * .86), fill=(219, 234, 254))
        d.ellipse((W_ * .66, H_ * .62, W_ * .82, H_ * .88), fill=(255, 107, 107)); d.ellipse((W_ * .76, H_ * .62, W_ * .92, H_ * .88), fill=(255, 196, 61, 230))
    return mk(w, h, f)
@lru_cache(None)
def ic_store(w):
    h = int(w * .9)
    def f(d, W_, H_):
        d.rectangle((W_ * .1, H_ * .42, W_ * .9, H_ * .95), fill=CREAM)
        n = 6
        for i in range(n): d.polygon([(W_ * (.04 + i * .92 / n), H_ * .08), (W_ * (.04 + (i + 1) * .92 / n), H_ * .08), (W_ * (.04 + (i + 1) * .92 / n), H_ * .42), (W_ * (.04 + i * .92 / n), H_ * .42)], fill=CORAL if i % 2 == 0 else CREAM)
        d.rectangle((W_ * .4, H_ * .6, W_ * .6, H_ * .95), fill=(59, 130, 246)); d.rectangle((W_ * .16, H_ * .56, W_ * .34, H_ * .76), fill=(147, 197, 253)); d.rectangle((W_ * .66, H_ * .56, W_ * .84, H_ * .76), fill=(147, 197, 253))
    return mk(w, h, f)
@lru_cache(None)
def ic_bank(w):
    h = int(w * .9)
    def f(d, W_, H_):
        d.polygon([(W_ * .5, H_ * .04), (W_ * .96, H_ * .32), (W_ * .04, H_ * .32)], fill=CREAM)
        for i in range(4): d.rectangle((W_ * (.14 + i * .2), H_ * .38, W_ * (.24 + i * .2), H_ * .78), fill=CREAM)
        d.rectangle((W_ * .06, H_ * .82, W_ * .94, H_ * .94), fill=CREAM); d.ellipse((W_ * .43, H_ * .14, W_ * .57, H_ * .28), fill=GOLD)
    return mk(w, h, f)
@lru_cache(None)
def ic_person(w):
    h = int(w * 1.1)
    def f(d, W_, H_):
        d.ellipse((W_ * .3, H_ * .02, W_ * .7, H_ * .42), fill=CREAM); d.rounded_rectangle((W_ * .12, H_ * .48, W_ * .88, H_ * 1.2), W_ * .3, fill=CREAM)
    return mk(w, h, f)
@lru_cache(None)
def ic_coin(w):
    def f(d, W_, H_):
        d.ellipse((0, 0, W_ - 1, H_ - 1), fill=GOLD); d.ellipse((W_ * .12, H_ * .12, W_ * .88, H_ * .88), outline=(217, 150, 20), width=int(W_ * .06))
        fnt = ImageFont.truetype(FD + "Inter-ExtraBold.otf", int(W_ * .5)); d.text((W_ / 2, H_ / 2), "€", font=fnt, fill=(180, 110, 10), anchor="mm")
    return mk(w, w, f)
def put(im, ic, cx, cy, a=1.0, k=1.0):
    if a <= .01 or k < .03: return
    if abs(k - 1) > .001: ic = ic.resize((max(1, int(ic.width * k)), max(1, int(ic.height * k))), Image.LANCZOS)
    if a < 1: ic = ic.copy(); ic.putalpha(ic.getchannel("A").point(lambda v: int(v * a)))
    im.paste(ic, (int(cx - ic.width / 2), int(cy - ic.height / 2)), ic)
def line(im, p0, p1, col, wd, k=1.0, dash=False):
    x = p0[0] + (p1[0] - p0[0]) * k; y = p0[1] + (p1[1] - p0[1]) * k
    d = ImageDraw.Draw(im)
    if not dash: d.line([p0, (x, y)], fill=col, width=int(wd))
    else:
        L = math.hypot(x - p0[0], y - p0[1]); n = int(L // (30 * S))
        for i in range(0, n, 2):
            a = i / max(1, n); b = min(1, (i + 1) / max(1, n)); d.line([(p0[0] + (x - p0[0]) * a, p0[1] + (y - p0[1]) * a), (p0[0] + (x - p0[0]) * b, p0[1] + (y - p0[1]) * b)], fill=col, width=int(wd))
    if k > .97 and not dash:
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); r = 26 * S
        d.polygon([p1, (p1[0] - r * math.cos(ang - .45), p1[1] - r * math.sin(ang - .45)), (p1[0] - r * math.cos(ang + .45), p1[1] - r * math.sin(ang + .45))], fill=col)
def esp(x, dec=2):  # 23.34 -> "23,34"
    return f"{x:.{dec}f}".replace(".", ",")

# ---------- layout zones
CX = W / 2
TOP = H * (0.10 if LONG else 0.09)
BOT = H * (0.76 if LONG else 0.72)       # content must end above captions
def cap_y(): return H * (0.89 if LONG else 0.745)


# =============== TIMELINE (voz acelerada x1.12) ===============
SPD = 1.12; LEAD = 0.30
raw = json.load(open("/home/claude/audios/asr_cuenta.json"))
P = [dict(st=p["st"] / SPD, d=p["d"] / SPD, text=p["text"]) for p in raw]
X = lambda i: P[i]["st"]
E = lambda i: P[i]["st"] + P[i]["d"]
CLEAN = {1: "Y aun así,", 3: "Hoy te explico cómo,", 10: "Los bancos pagan de media un 0,26 % por tu cuenta.", 12: "Y cobran un 7,46 % por un crédito al consumo.",
 13: "¿De dónde salen esas cifras?", 14: "Según el Banco Central Europeo, en marzo de 2026, los bancos de la zona euro",
 15: "pagaban de media un 0,26 % por los depósitos a la vista de los hogares, es decir, por las cuentas corrientes.", 17: "Y cuánto cobran por prestar",
 19: "El tipo medio de los créditos al consumo era del 7,46 %.", 21: "Un 0,26 % frente a un 7,46 %.", 27: "10.000 euros en una cuenta al 0,26 %",
 29: "Prestados al 7,46 % serían unos 746.", 41: "Un 0,2 % en débito", 42: "y un 0,3 % en crédito de consumo.",
 44: "Los grandes bancos españoles ganaron unos 34.000 millones de euros en 2025,", 45: "un 7 % más que el año anterior,", 4: "con datos oficiales."}
GROUPS = {10: (10, 11), 15: (15, 16), 21: (21, 22, 23), 42: (42, 43)}
SKIP = {11, 16, 22, 23, 43, 25, 53}
D = []
for i in range(58):
    if i in SKIP: continue
    g = GROUPS.get(i, (i,)); D.append(dict(st=X(i), d=E(g[-1]) - X(i), text=CLEAN.get(i, P[i]["text"]).replace(" %", "%"), i=i))
def esp_n(v, dec=0): return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
def lerp(a, b, k): return a + (b - a) * k

# =============== extra icons ===============
@lru_cache(None)
def ic_doc(w):
    h = int(w * 1.25)
    def f(d, W_, H_):
        d.rounded_rectangle((0, 0, W_ - 1, H_ - 1), W_ * .08, fill=CREAM)
        for i in range(5): d.rounded_rectangle((W_ * .15, H_ * (.16 + i * .15), W_ * (.85 if i != 4 else .55), H_ * (.16 + i * .15 + .06)), 8, fill=(148, 163, 184))
        d.rounded_rectangle((W_ * .15, H_ * .16, W_ * .5, H_ * .22), 8, fill=(59, 130, 246))
    return mk(w, h, f)
@lru_cache(None)
def ic_eu(w):
    h = int(w * .67)
    def f(d, W_, H_):
        d.rounded_rectangle((0, 0, W_ - 1, H_ - 1), H_ * .06, fill=(0, 51, 153))
        for i in range(12):
            a = i / 12 * 2 * math.pi; cx_ = W_ / 2 + H_ * .32 * math.sin(a); cy_ = H_ / 2 - H_ * .32 * math.cos(a); pts = []
            for j in range(10):
                r = H_ * (.075 if j % 2 == 0 else .03); aa = j * math.pi / 5; pts.append((cx_ + r * math.sin(aa), cy_ - r * math.cos(aa)))
            d.polygon(pts, fill=(255, 204, 0))
    return mk(w, h, f)
def check(im, cx, cy, r, col, a=1.0):
    if a <= .01: return
    o = Image.new("RGBA", (int(r * 3), int(r * 3)), (0, 0, 0, 0)); d = ImageDraw.Draw(o); c = r * 1.5
    d.ellipse((c - r, c - r, c + r, c + r), fill=col + (int(255 * a),))
    d.line([(c - r * .45, c + r * .02), (c - r * .1, c + r * .38), (c + r * .5, c - r * .32)], fill=INK + (int(255 * a),), width=max(3, int(r * .22)), joint="curve")
    im.paste(o, (int(cx - c), int(cy - c)), o)
def statcard(im, cx, cy, w, h, label, val, col, a, k=1.0, vs=150, ls=36):
    if a <= .01: return
    panel(im, cx, cy, w, h, (255, 255, 255, 26), 34, a, col + (255,), k)
    T(im, label, fit(label, "b", ls * S, w * .9), cx, cy - h * .30, MUTED, a)
    T(im, val, fit(val, "x", min(vs * S, h * .55), w * .9), cx, cy + h * .12, col, a, k)
def two(im, t, t0, l1, l2, y, c1=CREAM, c2=MINT, s1=104, s2=112, gap=118, a=1.0, mw=.9):
    T(im, l1, fit(l1, "x", s1 * S, W * mw), CX, y, c1, seg(t, t0, .25) * a, pop((t - t0) / .35))
    T(im, l2, fit(l2, "x", s2 * S, W * mw), CX, y + gap * S, c2, seg(t, t0 + .2, .25) * a, pop((t - t0 - .2) / .35))
def src(im, txt, y, a=1.0): T(im, txt, fit(txt, "m", 28 * S, W * .88), CX, y, MUTED, a * .95)

# =============== ESCENAS ===============
def scene_A(im, t):
    dx = (270 if LONG else 235) * S; cy = H * (.29 if LONG else .27); isz = int((330 if LONG else 300) * S)
    put(im, ic_card(isz), CX - dx, cy + 8 * math.sin(t * 2), seg(t, X(0), .3), pop((t - X(0)) / .5))
    if t > X(0) + .5:
        panel(im, CX - dx, cy + isz * .52, 190 * S, 74 * S, (45, 212, 160, 240), 22, seg(t, X(0) + .5, .25), None, pop((t - X(0) - .5) / .3))
        T(im, "0 €", F("x", 52 * S), CX - dx, cy + isz * .52, INK, seg(t, X(0) + .5, .25))
    if t >= X(1) - .1:
        put(im, ic_bank(isz), CX + dx, cy + 8 * math.sin(t * 2 + 1), seg(t, X(1) - .1, .3), pop((t - X(1) + .1) / .5))
    if t >= X(2):
        for j in range(4):
            ph = ((t - X(2)) * .45 + j / 4) % 1.0
            x = lerp(CX - dx + isz * .35, CX + dx - isz * .35, ph); y = cy - 70 * S * math.sin(math.pi * ph)
            put(im, ic_coin(int(58 * S)), x, y, min(1, seg(t, X(2), .3)))
    y1 = H * (.60 if LONG else .47)
    if t < X(1): two(im, t, X(0), "TU CUENTA", "ES GRATIS", y1, CREAM, MINT)
    elif t < X(3): two(im, t, X(1), "Y AUN ASÍ", "EL BANCO GANA", y1, CREAM, CORAL, a=1.0) if t < X(2) else two(im, t, X(1), "Y AUN ASÍ", "EL BANCO GANA", y1, CREAM, CORAL)
    else:
        a = seg(t, X(3), .3); two(im, t, X(3), "CÓMO LO HACE", "DATOS OFICIALES", y1, GOLD, CREAM, 96, 78, 110)
        if t > X(4) + .3:
            panel(im, CX, y1 + 235 * S, W * (.50 if LONG else .78), 76 * S, (255, 255, 255, 30), 26, seg(t, X(4) + .3, .3), GOLD + (255,))
            T(im, "BCE · Reglamento UE 2015/751", fit("BCE · Reglamento UE 2015/751", "b", 36 * S, W * (.46 if LONG else .72)), CX, y1 + 235 * S, CREAM, seg(t, X(4) + .3, .3))

def scene_B(im, t):
    yt = H * (.17 if not LONG else .16)
    if t < X(8) - .1:
        fade = 1 - seg(t, X(8) - .45, .35)
        two(im, t, X(5), "UNA IDEA", "QUE LO CAMBIA TODO", yt, GOLD, CREAM, 100, 66, 100, fade)
        cy = H * (.43 if not LONG else .50)
        if t > X(5) + .3:
            kc = seg(t, X(5) + .3, .3) * (1 - seg(t, X(7) - .1, .25))
            put(im, ic_card(int(340 * S)), CX, cy, kc, pop((t - X(5) - .3) / .45))
            if kc > .01 and t > X(6) - .1:
                dv = ImageDraw.Draw(im); r = 150 * S
                kx = ease((t - X(6) - .2) / .3)
                dv.line([(CX - r, cy - r * .8), (CX - r + 2 * r * kx, cy - r * .8 + 1.6 * r * kx)], fill=CORAL, width=int(18 * S))
                ka = seg(t, X(6), .3)
                T(im, "TU CUENTA NO ES", F("x", 50 * S), CX, cy + 230 * S, CORAL, kc * fade * ka); T(im, "EL PRODUCTO", F("x", 70 * S), CX, cy + 300 * S, CORAL, kc * fade * ka)
        if t > X(7) - .1:
            a = seg(t, X(7) - .1, .3) * fade
            put(im, ic_coin(int(300 * S)), CX, cy, a, pop((t - X(7) + .1) / .5))
            T(im, "TU DINERO", F("x", 76 * S), CX, cy + 230 * S, MINT, a); T(im, "SÍ ES EL PRODUCTO", F("x", 56 * S), CX, cy + 300 * S, CREAM, a)
        return
    a = seg(t, X(8) - .1, .35)
    ny = H * (.30 if not LONG else .38); isz = int((190 if not LONG else 230) * S)
    xs = [W * .2, W * .5, W * .8]
    nodes = [(ic_person(int(isz * .62)), "TÚ", X(8)), (ic_bank(isz), "BANCO", X(8) + .3), (ic_store(isz), "PERSONAS Y EMPRESAS", X(9))]
    for (ic, lab, t0), x in zip(nodes, xs):
        k = seg(t, t0 - .1, .35); put(im, ic, x, ny + 6 * math.sin(t * 1.8 + x), k, pop((t - t0 + .1) / .45))
        T(im, lab, fit(lab, "x", 36 * S, W * .27), x, ny + isz * .62, CREAM, k)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pad = isz * .62
    k1 = ease((t - X(8) - .4) / .7); line(ov, (xs[0] + pad * .45, ny), (xs[1] - pad * .55, ny), MINT + (255,), 9 * S, k1)
    T(ov, "tu nómina", F("b", 34 * S), (xs[0] + xs[1]) / 2, ny - 70 * S, MINT, seg(t, X(8) + .6, .3))
    k2 = ease((t - X(9) - .3) / .8); line(ov, (xs[1] + pad * .55, ny), (xs[2] - pad * .6, ny), GOLD + (255,), 9 * S, k2)
    T(ov, "préstamos", F("b", 34 * S), (xs[1] + xs[2]) / 2, ny - 70 * S, GOLD, seg(t, X(9) + .4, .3))
    for (xa, xb, st_, on) in ((xs[0] + pad * .45, xs[1] - pad * .55, X(8) + .6, k1), (xs[1] + pad * .55, xs[2] - pad * .6, X(9) + .5, k2)):
        if on > .95:
            for j in range(2):
                ph = ((t - st_) * .6 + j * .5) % 1.0; put(ov, ic_coin(int(46 * S)), lerp(xa, xb, ph), ny, 1)
    im.paste(ov, (0, 0), ov)
    ty = H * (.50 if not LONG else .62)
    T(im, "El banco usa tu dinero", F("x", 52 * S), CX, ty, CREAM, seg(t, X(9) - .2, .3) * a)
    tp = X(9) + P[9]["d"] * .70
    if t > tp:
        panel(im, CX, ty + 105 * S, W * (.62 if LONG else .80), 90 * S, (45, 212, 160, 240), 28, seg(t, tp, .3), None, pop((t - tp) / .4))
        T(im, "y a ti no te cobra nada", F("x", 46 * S), CX, ty + 105 * S, INK, seg(t, tp, .3))

def scene_C(im, t):
    cwid = W * (.36 if LONG else .78); chh = (380 if LONG else 360) * S
    # C1 : las dos cifras
    if t < X(13) + .1:
        fade = 1 - seg(t, X(13) - .15, .3)
        pos = [(W * .27, H * .50), (W * .73, H * .50)] if LONG else [(CX, H * .385), (CX, H * .60)]
        two(im, t, X(10) - .3, "TU BANCO", "PAGA vs COBRA", H * (.17 if not LONG else .16), CREAM, GOLD, 84, 100, 105, fade)
        for (lab, v, col, t0, dec), (x, y) in zip((("PAGAN POR TU CUENTA", .26, MINT, X(10), 2), ("COBRAN POR UN CRÉDITO", 7.46, CORAL, X(12), 2)), pos):
            k = seg(t, t0 - .1, .3); q = ease((t - t0 - .1) / .6)
            statcard(im, x, y, cwid, chh, lab, esp(v * q, dec) + " %", col, k * fade, pop((t - t0 + .1) / .45), 190 if not LONG else 150, 40)
        return
    # C2 : fuente BCE
    if t < X(20) - .1:
        fade = 1 - seg(t, X(20) - .45, .35)
        yh = H * (.18 if not LONG else .16)
        if t < X(14) - .05:
            two(im, t, X(13) - .1, "¿DE DÓNDE", "SALEN ESAS CIFRAS?", H * (.25 if not LONG else .30), CREAM, GOLD, 100, 76, 112, 1 - seg(t, X(14) - .35, .3)); return
        T(im, "DATOS DEL BCE", F("x", 80 * S), CX, yh, GOLD, seg(t, X(14) - .1, .3) * fade, pop((t - X(14) + .1) / .4))
        T(im, "Banco Central Europeo · marzo 2026", fit("Banco Central Europeo · marzo 2026", "b", 40 * S, W * .86), CX, yh + 85 * S, CREAM, seg(t, X(14), .3) * fade)
        T(im, "bancos de la zona euro", F("m", 34 * S), CX, yh + 140 * S, MUTED, seg(t, X(14) + 1.8, .3) * fade)
        pos = [(W * .27, H * .52), (W * .73, H * .52)] if LONG else [(CX, H * .395), (CX, H * .575)]
        hh = (330 if LONG else 215) * S
        statcard(im, *pos[0], cwid, hh, "CUENTAS CORRIENTES · lo que pagan", "0,26 %", MINT, seg(t, X(15), .3) * fade, pop((t - X(15)) / .45), 130, 32)
        if t < X(19): statcard(im, *pos[1], cwid, hh, "CRÉDITOS AL CONSUMO · lo que cobran", "? %", GOLD, seg(t, X(17), .3) * fade, pop((t - X(17)) / .45), 130, 32)
        else: statcard(im, *pos[1], cwid, hh, "CRÉDITOS AL CONSUMO · lo que cobran", "7,46 %", CORAL, seg(t, X(19) - .1, .2) * fade, pop((t - X(19)) / .45), 130, 32)
        src(im, "Fuente: BCE, estadísticas de tipos de interés bancarios (MIR)", H * (.672 if not LONG else .80), seg(t, X(15), .4) * fade)
        return
    # C3 : la diferencia
    T(im, "FÍJATE EN LA DIFERENCIA", fit("FÍJATE EN LA DIFERENCIA", "x", 72 * S, W * .9), CX, H * (.17 if not LONG else .17), GOLD, seg(t, X(20), .3), pop((t - X(20)) / .4))
    x0 = W * (.10 if not LONG else .18); bw = W * (.62 if not LONG else .56)
    yb = [H * (.31 if not LONG else .36), H * (.47 if not LONG else .56)]
    for (lab, v, col, t0, y) in (("Lo que pagan por tu cuenta", .26, MINT, X(21) + .3, yb[0]), ("Lo que cobran por un crédito", 7.46, CORAL, X(23) + .1, yb[1])):
        k = ease((t - t0) / 1.0); a = seg(t, t0 - .4, .3)
        T(im, lab, F("b", 38 * S), x0 + F("b", 38 * S).getlength(lab) / 2, y - 52 * S, CREAM, a)
        panel(im, x0 + bw / 2, y + 30 * S, bw, 56 * S, (255, 255, 255, 25), 28, a)
        wv = max(14, bw * (v / 7.46) * k)
        if k > .02:
            panel(im, x0 + wv / 2, y + 30 * S, wv, 56 * S, col + (255,), 28, 1)
            tx = esp(v * k, 2) + " %"; fs = F("x", 64 * S); T(im, tx, fs, x0 + wv + 24 * S + fs.getlength(tx) / 2, y + 28 * S, col)
    if t > X(23) + 1.6:
        panel(im, CX, H * (.595 if not LONG else .72), W * (.56 if LONG else .78), 96 * S, (255, 196, 61, 240), 28, seg(t, X(23) + 1.6, .3), None, pop((t - X(23) - 1.6) / .4))
        T(im, "unas 29 veces más", F("x", 58 * S), CX, H * (.595 if not LONG else .72), INK, seg(t, X(23) + 1.6, .3))
    src(im, "Fuente: BCE, tipos de interés bancarios (MIR), marzo 2026, zona euro", H * (.672 if not LONG else .80), seg(t, X(21), .4))

def scene_D(im, t):
    yt = H * (.17 if not LONG else .16)
    if t < X(26) + .15:      # fórmula del margen
        fade = 1 - seg(t, X(26) - .25, .3)
        T(im, "MARGEN DE INTERESES", fit("MARGEN DE INTERESES", "x", 78 * S, W * .9), CX, yt, GOLD, seg(t, X(24), .3) * fade, pop((t - X(24)) / .4))
        toks = [("7,46 %", CORAL, X(24) + 1.7, "cobra"), ("–", CREAM, X(24) + 2.2, ""), ("0,26 %", MINT, X(24) + .5, "paga"), ("=", CREAM, X(24) + 3.4, ""), ("MARGEN", GOLD, X(24) + 3.7, "")]
        order = [2, 1, 0, 3, 4]
        toks = [toks[2], toks[1], toks[0], toks[3], toks[4]]
        toks = [("7,46 %", CORAL, X(24) + 1.7, "cobra"), ("–", CREAM, X(24) + 2.2, ""), ("0,26 %", MINT, X(24) + .5, "paga"), ("=", CREAM, X(24) + 3.4, ""), ("MARGEN", GOLD, X(24) + 3.7, "")]
        fs = 70
        while fs > 30:
            f_ = F("x", fs * S); tot = sum(f_.getlength(x[0]) for x in toks) + 4 * 46 * S
            if tot <= W * .86: break
            fs -= 2
        f_ = F("x", fs * S); x = CX - tot / 2; yy = H * (.36 if not LONG else .42)
        for txt, col, t0, sub in toks:
            w_ = f_.getlength(txt); cxx = x + w_ / 2
            T(im, txt, f_, cxx, yy, col, seg(t, t0, .3) * fade, pop((t - t0) / .4))
            if sub: T(im, sub, F("b", 34 * S), cxx, yy + 80 * S, MUTED, seg(t, t0 + .2, .3) * fade)
            x += w_ + 46 * S
        return
    if t < X(30) - .05:      # ejemplo 10.000 €
        fade = 1 - seg(t, X(30) - .35, .3)
        T(im, "UN EJEMPLO", F("x", 64 * S), CX, yt, GOLD, seg(t, X(26), .3) * fade)
        T(im, "10.000 €", fit("10.000 €", "x", (230 if not LONG else 170) * S, W * .84), CX, H * (.26 if not LONG else .30), CREAM, seg(t, X(27), .3) * fade, pop((t - X(27)) / .5))
        pos = [(W * .27, H * .56), (W * .73, H * .56)] if LONG else [(CX, H * .42), (CX, H * .575)]
        hh = (300 if LONG else 260) * S; wc = W * (.40 if LONG else .78)
        statcard(im, *pos[0], wc, hh, "EN TU CUENTA · al 0,26 %", "26 € al año", MINT, seg(t, X(28) - .1, .3) * fade, pop((t - X(28) + .1) / .45), 130 if not LONG else 90, 38)
        statcard(im, *pos[1], wc, hh, "PRESTADOS · al 7,46 %", "746 € al año", CORAL, seg(t, X(29) - .1, .3) * fade, pop((t - X(29) + .1) / .45), 130 if not LONG else 90, 38)
        src(im, "10.000 × 0,26 % = 26 €   ·   10.000 × 7,46 % = 746 €", H * (.672 if not LONG else .80), seg(t, X(29) + 1.0, .3) * fade)
        return
    two(im, t, X(30) - .3, "PERO OJO", "ES SOLO UN EJEMPLO", yt, CORAL, CREAM, 110, 62, 105)
    T(im, "NO TODO EL MARGEN", F("x", 60 * S), CX, H * (.35 if not LONG else .40), GOLD, seg(t, X(32), .3), pop((t - X(32)) / .4))
    T(im, "ES BENEFICIO", F("x", 84 * S), CX, H * (.35 if not LONG else .40) + 85 * S, GOLD, seg(t, X(32) + .3, .3), pop((t - X(32) - .3) / .4))
    items = [("COSTES", X(33)), ("RESERVAS", X(34)), ("PRÉSTAMOS QUE NO SE DEVUELVEN", X(34) + 1.7)]
    for j, (lab, t0) in enumerate(items):
        if LONG: cxp = W * (.20 + .30 * j); cyp = H * .62; wp = W * .27
        else: cxp = CX; cyp = H * (.50 + j * .095); wp = W * .76
        a = seg(t, t0, .3); panel(im, cxp, cyp, wp, 84 * S, (255, 255, 255, 30), 24, a, GOLD + (255,), pop((t - t0) / .4))
        T(im, lab, fit(lab, "x", 44 * S, wp * .88), cxp, cyp, CREAM, a)

def scene_E(im, t):
    yt = H * (.17 if not LONG else .16)
    if t < X(36) - .05:
        T(im, "SEGUNDA VÍA", F("x", 120 * S), CX, H * (.32 if not LONG else .40), GOLD, seg(t, X(35), .25), pop((t - X(35)) / .4)); return
    if t < X(39) - .05:
        fade = 1 - seg(t, X(39) - .4, .3)
        two(im, t, X(36) - .1, "LAS COMISIONES", "QUE NO VES", yt, CREAM, GOLD, 96, 104, 112, fade)
        if not LONG:
            isz = int(190 * S); ys = [H * .32, H * .465, H * .61]; lx = CX - 230 * S
            nodes = [(ic_person(int(isz * .62)), "TÚ", X(36)), (ic_store(isz), "COMERCIO", X(37)), (ic_bank(isz), "BANCO", X(38))]
            for (ic, lab, t0), y in zip(nodes, ys):
                k = seg(t, t0 - .2, .35) * fade; put(im, ic, CX, y + 6 * math.sin(t * 1.8 + y), k, pop((t - t0 + .2) / .45)); T(im, lab, F("x", 42 * S), lx, y, CREAM, k)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gp = isz * .58
            k1 = ease((t - X(37) - .2) / .6); line(ov, (CX, ys[0] + gp * .6), (CX, ys[1] - gp), MUTED + (255,), 9 * S, k1)
            T(ov, "pagas el precio", F("m", 34 * S), CX + 250 * S, (ys[0] + ys[1]) / 2, MUTED, seg(t, X(37) + .4, .3))
            k2 = ease((t - X(38) - .1) / .7); line(ov, (CX, ys[1] + gp), (CX, ys[2] - gp), CORAL + (255,), 13 * S, k2)
            T(ov, "COMISIÓN", F("x", 42 * S), CX + 250 * S, (ys[1] + ys[2]) / 2, CORAL, seg(t, X(38) + .5, .3))
            if k2 > .95:
                ph = ((t - X(38) - .8) * .55) % 1.0; put(ov, ic_coin(int(56 * S)), CX, lerp(ys[1] + gp, ys[2] - gp, ph), 1)
            im.paste(ov, (0, 0), ov)
            tn = X(38) + 1.9
            if t > tn:
                T(im, "NO TÚ", F("x", 80 * S), CX - 250 * S, (ys[0] + ys[1]) / 2, CORAL, seg(t, tn, .3) * fade, pop((t - tn) / .4))
            return
        ny = H * (.46 if not LONG else .50); isz = int((200 if not LONG else 240) * S); xs = [W * .2, W * .5, W * .8]
        nodes = [(ic_person(int(isz * .62)), "TÚ", X(36)), (ic_store(isz), "COMERCIO", X(37)), (ic_bank(isz), "BANCO", X(38))]
        for (ic, lab, t0), x in zip(nodes, xs):
            k = seg(t, t0 - .2, .35) * fade; put(im, ic, x, ny + 6 * math.sin(t * 1.8 + x), k, pop((t - t0 + .2) / .45)); T(im, lab, F("x", 38 * S), x, ny + isz * .62, CREAM, k)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pad = isz * .62
        a1 = (xs[0] + pad * .45, xs[1] - pad * .6); a2 = (xs[1] + pad * .6, xs[2] - pad * .6)
        k1 = ease((t - X(37) - .2) / .6); line(ov, (a1[0], ny), (a1[1], ny), MUTED + (255,), 8 * S, k1)
        T(ov, "pagas el precio", F("m", 30 * S), (a1[0] + a1[1]) / 2, ny - 62 * S, MUTED, seg(t, X(37) + .4, .3))
        k2 = ease((t - X(38) - .1) / .7); line(ov, (a2[0], ny), (a2[1], ny), CORAL + (255,), 12 * S, k2)
        T(ov, "COMISIÓN", F("x", 34 * S), (a2[0] + a2[1]) / 2, ny - 62 * S, CORAL, seg(t, X(38) + .5, .3))
        if k2 > .95:
            ph = ((t - X(38) - .8) * .55) % 1.0; put(ov, ic_coin(int(52 * S)), lerp(a2[0], a2[1], ph), ny, 1)
        im.paste(ov, (0, 0), ov)
        tn = X(38) + 1.9
        if t > tn:
            panel(im, CX, ny + isz * .62 + 120 * S, W * .5, 96 * S, (255, 107, 107, 235), 28, seg(t, tn, .3) * fade, None, pop((t - tn) / .4))
            T(im, "LO PAGA EL COMERCIO, NO TÚ", fit("LO PAGA EL COMERCIO, NO TÚ", "x", 34 * S, W * .46), CX, ny + isz * .62 + 120 * S, INK, seg(t, tn, .3) * fade)
        return
    panel(im, CX, yt + 10 * S, W * (.62 if LONG else .86), 100 * S, (255, 196, 61, 240), 28, seg(t, X(39), .3), None, pop((t - X(39)) / .4))
    T(im, "TASA DE INTERCAMBIO", fit("TASA DE INTERCAMBIO", "x", 62 * S, W * (.58 if LONG else .80)), CX, yt + 10 * S, INK, seg(t, X(39), .3))
    T(im, "UE · límite máximo", F("b", 42 * S), CX, yt + 105 * S, CREAM, seg(t, X(40), .3))
    fl = seg(t, X(40) - .1, .3) * (1 - seg(t, X(41) - .35, .3))
    if fl > .01:
        put(im, ic_eu(int(360 * S)), CX, H * (.40 if not LONG else .48), fl, pop((t - X(40) + .1) / .5))
        T(im, "DESDE 2015", F("x", 96 * S), CX, H * (.40 if not LONG else .48) + 230 * S, GOLD, fl * seg(t, X(40) + .8, .3))
    pos = [(W * .27, H * .52), (W * .73, H * .52)] if LONG else [(CX, H * .385), (CX, H * .545)]
    hh = (340 if LONG else 280) * S; wc = W * (.36 if LONG else .78)
    statcard(im, *pos[0], wc, hh, "DÉBITO", "0,2 %", MINT, seg(t, X(41), .3), pop((t - X(41)) / .45), 190 if not LONG else 140, 40)
    statcard(im, *pos[1], wc, hh, "CRÉDITO DE CONSUMO", "0,3 %", GOLD, seg(t, X(42), .3), pop((t - X(42)) / .45), 190 if not LONG else 140, 40)
    T(im, "como máximo, del importe del pago", fit("como máximo, del importe del pago", "m", 38 * S, W * .86), CX, H * (.648 if not LONG else .76), CREAM, seg(t, X(43) + 1.0, .3))
    src(im, "Fuente: Reglamento (UE) 2015/751", H * (.678 if not LONG else .81), seg(t, X(41), .4))

def scene_F(im, t):
    yt = H * (.17 if not LONG else .16)
    two(im, t, X(44) - .1, "LOS GRANDES BANCOS", "ESPAÑOLES", yt, CREAM, MINT, 80, 80, 90)
    q = ease((t - X(44) - .4) / 3.2); v = 34000 * q
    T(im, esp_n(v), F("x", (230 if not LONG else 250) * S), CX, H * (.40 if not LONG else .42), GOLD, seg(t, X(44) + .3, .3), pop((t - X(44) - .3) / .5))
    T(im, "millones de euros", F("b", 52 * S), CX, H * (.49 if not LONG else .60), CREAM, seg(t, X(44) + 1.0, .3))
    T(im, "beneficio en 2025 · cifra aproximada", F("m", 36 * S), CX, H * (.535 if not LONG else .67), MUTED, seg(t, X(44) + 1.4, .3))
    if t > X(45):
        panel(im, CX, H * (.60 if not LONG else .75), W * (.36 if LONG else .56), 100 * S, (45, 212, 160, 240), 28, seg(t, X(45), .3), None, pop((t - X(45)) / .4))
        T(im, "+7 % vs 2024", F("x", 56 * S), CX, H * (.60 if not LONG else .75), INK, seg(t, X(45), .3))
    src(im, "Fuente: resultados anuales de los bancos (vía EFE)", H * (.675 if not LONG else .82), seg(t, X(46), .4))

def scene_G(im, t):
    y1 = H * (.30 if not LONG else .32)
    if t < X(48) - .1:
        fade = 1 - seg(t, X(48) - .4, .3)
        T(im, "NO ES PARA", F("x", 84 * S), CX, y1, CREAM, seg(t, X(47) - .1, .3) * fade, pop((t - X(47) + .1) / .4))
        T(im, "DESCONFIAR", F("x", 120 * S), CX, y1 + 125 * S, CORAL, seg(t, X(47) + .3, .3) * fade, pop((t - X(47) - .3) / .4))
        tn = X(47) + P[47]["d"] * .5
        if t > tn:
            panel(im, CX, y1 + 285 * S, W * (.50 if LONG else .80), 100 * S, (45, 212, 160, 240), 28, seg(t, tn, .3) * fade, None, pop((t - tn) / .4))
            T(im, "NEGOCIO LEGAL Y REGULADO", fit("NEGOCIO LEGAL Y REGULADO", "x", 46 * S, W * (.46 if LONG else .74)), CX, y1 + 285 * S, INK, seg(t, tn, .3) * fade)
        return
    two(im, t, X(48) - .1, "ES PARA QUE SEPAS", "CÓMO FUNCIONA", y1, CREAM, GOLD, 74, 106, 120)

def scene_H(im, t):
    yt = H * (.17 if not LONG else .16)
    two(im, t, X(49) - .1, "UNA COSA PARA", "HACER HOY", yt, CREAM, GOLD, 80, 108, 112)
    if t > X(50) - .2:
        put(im, ic_doc(int(190 * S)), CX, H * (.36 if not LONG else .37), seg(t, X(50) - .2, .3), pop((t - X(50) + .2) / .45))
        T(im, "MIRA TU CONTRATO", fit("MIRA TU CONTRATO", "x", 66 * S, W * .9), CX, H * (.36 if not LONG else .37) + 170 * S, CREAM, seg(t, X(50), .3))
    rows = [("¿Qué interés te paga tu cuenta?", X(51)), ("¿Qué comisiones tiene?", X(52))]
    for j, (lab, t0) in enumerate(rows):
        yy = H * (.57 + j * .085 if not LONG else .68 + j * .10); a = seg(t, t0, .3); wp = W * (.74 if not LONG else .50)
        panel(im, CX, yy, wp, 76 * S, (255, 255, 255, 30), 26, a, MINT + (255,), pop((t - t0) / .4))
        check(im, CX - wp / 2 + 48 * S, yy, 22 * S, MINT, a)
        T(im, lab, fit(lab, "b", 38 * S, wp * .78), CX + 24 * S, yy, CREAM, a)

def scene_I(im, t):
    T(im, "Esto es información,", F("x", 54 * S), CX, H * (.20 if not LONG else .22), CREAM, seg(t, X(54), .3))
    T(im, "no asesoramiento financiero", fit("no asesoramiento financiero", "x", 54 * S, W * .9), CX, H * (.20 if not LONG else .22) + 72 * S, MUTED, seg(t, X(55) - .3, .3))
    if t > X(56) - .1:
        two(im, t, X(56) - .1, "¿QUÉ NEGOCIO", "ANALIZO AHORA?", H * (.38 if not LONG else .42), CREAM, MINT, 96, 104, 112)
    if t > X(57) - .1:
        panel(im, CX, H * (.60 if not LONG else .72), W * (.52 if LONG else .82), 100 * S, (255, 196, 61, 240), 28, seg(t, X(57) - .1, .3), None, pop((t - X(57) + .1) / .4))
        T(im, "Escríbelo en comentarios", fit("Escríbelo en comentarios", "x", 52 * S, W * (.48 if LONG else .76)), CX, H * (.60 if not LONG else .72), INK, seg(t, X(57) - .1, .3))

def scenes(im, t):
    if t < X(5) - .05: scene_A(im, t)
    elif t < X(10) - .05: scene_B(im, t)
    elif t < X(24) - .05: scene_C(im, t)
    elif t < X(35) - .05: scene_D(im, t)
    elif t < X(44) - .05: scene_E(im, t)
    elif t < X(47) - .05: scene_F(im, t)
    elif t < X(49) - .05: scene_G(im, t)
    elif t < X(54) - .05: scene_H(im, t)
    else: scene_I(im, t)

# =============== subtítulos palabra a palabra ===============
def captions(im, t):
    cur = None
    for p in D:
        if p["st"] - .05 <= t < p["st"] + p["d"] + .35: cur = p
    if not cur: return
    allw = cur["text"].split(); f = F("x", 50 * S); maxw = W * (.80 if LONG else .66)
    wts = [len(w) + 2 for w in allw]; tot = sum(wts); acc = 0; tall = []
    for ww in wts: tall.append((cur["st"] + cur["d"] * acc / tot, cur["st"] + cur["d"] * (acc + ww) / tot)); acc += ww
    CH = 9 if LONG else 6
    chunks = [(i, min(i + CH, len(allw))) for i in range(0, len(allw), CH)]
    if len(chunks) > 1 and chunks[-1][1] - chunks[-1][0] < 3: chunks[-2] = (chunks[-2][0], chunks[-1][1]); chunks.pop()
    ci = 0
    for k_, (a_, b_) in enumerate(chunks):
        if t >= tall[a_][0] - .02: ci = k_
    a_, b_ = chunks[ci]; words = allw[a_:b_]; times = tall[a_:b_]
    lines = []; ln = []; wl = 0; sp = f.getlength(" ")
    for i, w_ in enumerate(words):
        l = f.getlength(w_)
        if ln and wl + sp + l > maxw: lines.append(ln); ln = []; wl = 0
        ln.append(i); wl += l + (sp if len(ln) > 1 else 0)
    if ln: lines.append(ln)
    lh = 72 * S; ytop = cap_y() - lh / 2 - (len(lines) - 1) * lh / 2
    panel(im, CX, ytop + len(lines) * lh / 2, maxw + 50 * S, len(lines) * lh + 30 * S, (8, 14, 30, 150), 26)
    lay = Image.new("RGBA", (W, int(len(lines) * lh + 20)), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); base = lh * 0.72
    for r_, li in enumerate(lines):
        tw = sum(f.getlength(words[i]) for i in li) + sp * (len(li) - 1); x = CX - tw / 2
        for i in li:
            col = MINT if times[i][0] <= t < times[i][1] else (CREAM if t >= times[i][1] else (148, 163, 184))
            dd.text((x, 10 + r_ * lh + base), words[i], font=f, fill=col + (255,), anchor="ls"); x += f.getlength(words[i]) + sp
    im.paste(lay, (0, int(ytop)), lay)

def brand(im): T(im, "CÓMO GANA DINERO DE VERDAD", F("x", 30 * S), CX, H * .095 if not LONG else H * .045, MUTED, .9)
def progress(im, t, a, b):
    ImageDraw.Draw(im).rectangle((0, H - 8 * S, W * min(1, (t - a) / max(.01, b - a)), H), fill=MINT)

def closing(im, t):
    panel(im, CX, H * .47, W * .84, 640 * S, (255, 255, 255, 24), 40, seg(t, 0, .35), MINT + (255,))
    mw = W * .72
    T(im, "¿Qué negocio analizo ahora?", fit("¿Qué negocio analizo ahora?", "x", 60 * S, mw), CX, H * .47 - 190 * S, MINT, seg(t, 0, .35))
    T(im, "Díselo en comentarios", fit("Díselo en comentarios", "b", 48 * S, mw), CX, H * .47 - 100 * S, CREAM, seg(t, .25, .35))
    T(im, "Envíaselo a quien crea que", fit("Envíaselo a quien crea que", "b", 44 * S, mw), CX, H * .47 + 20 * S, GOLD, seg(t, .5, .35))
    T(im, "su cuenta es gratis", fit("su cuenta es gratis", "x", 54 * S, mw), CX, H * .47 + 90 * S, GOLD, seg(t, .6, .35))
    T(im, "Información, no asesoramiento financiero", fit("Información, no asesoramiento financiero", "m", 28 * S, mw), CX, H * .47 + 205 * S, MUTED, seg(t, .8, .35))
    T(im, "Voz generada con IA", F("m", 28 * S), CX, H * .47 + 250 * S, MUTED, seg(t, .8, .35))

# =============== rango ===============
if MODE == "long": FIRSTP, LASTP2 = 0, 57
else: FIRSTP, LASTP2 = FIRST, LASTP
T0 = 0.0 if FIRSTP == 0 else X(FIRSTP) - .03
T1 = 153.72 if LASTP2 == 57 else E(LASTP2) + .22
TOTAL = (T1 - T0) + TAIL
def frame(tt):
    t = T0 + tt                       # tiempo de audio
    if t > T1 and not LONG:
        im = bg(tt); closing(im, t - T1); brand(im); return im
    tv = min(t + LEAD, 1e9 if LONG else T1)        # las imágenes se adelantan 0,3 s a la voz
    im = bg(tt); scenes(im, tv); captions(im, min(t, T1)); brand(im); progress(im, t, T0, T1 + (TAIL if LONG else 0)); return im
if TESTS:
    for q in TESTS: frame(q).convert("RGB").save(f"test_{NAME}_{q}.png")
    sys.exit()

# =============== audio ===============
SR = 44100
def rd(f):
    r = wave.open(f); return np.frombuffer(r.readframes(r.getnframes()), dtype=np.int16).astype(np.float32) / 32768
v = rd("narr_fast.wav")[int(T0 * SR):int(T1 * SR)]
n = int(TOTAL * SR); v = np.pad(v, (0, max(0, n - len(v))))[:n]
tt = np.arange(n) / SR; BPM = 84; beat = 60 / BPM
ch = [[196, 246.94, 293.66], [164.81, 207.65, 246.94], [220, 261.63, 329.63], [174.61, 220, 261.63]]
mus = np.zeros(n, dtype=np.float32)
for i in range(int(TOTAL / beat) + 1):
    bar = (i // 4) % 4; s = int(i * beat * SR); L = int(beat * SR * 1.9)
    if s >= n: break
    sg = slice(s, min(n, s + L)); k = np.arange(sg.stop - sg.start) / SR; env = np.exp(-k * 1.4)
    for fr in ch[bar]: mus[sg] += 0.05 * np.sin(2 * np.pi * fr * k) * env
    mus[sg] += 0.035 * np.sin(2 * np.pi * ch[bar][i % 3] * 2 * k) * np.exp(-k * 5)
    if i % 2 == 0:
        kk = np.arange(min(int(0.16 * SR), n - s)) / SR; mus[s:s + len(kk)] += 0.20 * np.sin(2 * np.pi * (48 + 60 * np.exp(-kk * 30)) * kk) * np.exp(-kk * 14)
env = np.abs(v); k = int(.15 * SR); env = np.convolve(env, np.ones(k) / k, mode="same"); env = np.clip(env / 0.12, 0, 1)
mus = mus * (0.8 - 0.55 * env)
mus *= np.minimum(1, (TOTAL - tt) / 1.6) * np.minimum(1, tt / .15)
sfx = np.zeros(n, dtype=np.float32)
def add(t0, x):
    s = int((t0 - T0) * SR)
    if s < 0: return
    x = x[:max(0, n - s)]; sfx[s:s + len(x)] += x
def popf(f0=700):
    k = np.arange(int(.12 * SR)) / SR; return (0.14 * np.sin(2 * np.pi * (f0 * np.exp(-k * 14)) * k) * np.exp(-k * 28)).astype(np.float32)
def whoosh():
    k = np.arange(int(.3 * SR)) / SR; x = np.random.randn(len(k)) * np.sin(np.pi * k / .3) ** 2
    return (0.05 * np.convolve(x, np.ones(40) / 40, mode="same")).astype(np.float32)
np.random.seed(3)
for p in D:
    if T0 <= p["st"] <= T1: add(max(T0, p["st"] - .1) , whoosh())
for tp in (X(2), X(6), X(7), X(10), X(12), X(15), X(19), X(23), X(24) + 3.7, X(28), X(29), X(32), X(41), X(42), X(44) + .3, X(45), X(51), X(52), X(56)):
    if T0 + .1 <= tp <= T1: add(tp, popf(800))
add(T1 + .1, (0.12 * (np.sin(2 * np.pi * 1046 * np.arange(int(1.2 * SR)) / SR) + .5 * np.sin(2 * np.pi * 1568 * np.arange(int(1.2 * SR)) / SR)) * np.exp(-np.arange(int(1.2 * SR)) / SR * 3)).astype(np.float32))
mix = v * 0.95 + mus + sfx; mix = mix / np.abs(mix).max() * 0.9
wv = wave.open(f"mezcla_{NAME}.wav", "wb"); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((mix * 32767).astype(np.int16).tobytes()); wv.close()
pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", f"mezcla_{NAME}.wav",
    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", str(TOTAL), f"{NAME}.mp4"], stdin=subprocess.PIPE)
for i in range(int(TOTAL * FPS)): pr.stdin.write(frame(i / FPS).convert("RGB").tobytes())
pr.stdin.close(); pr.wait(); print("ok", NAME, round(TOTAL, 2))
