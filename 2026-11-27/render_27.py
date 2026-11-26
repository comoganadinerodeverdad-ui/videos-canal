"""Reels del viernes 27-nov-2026 (La pizarra de Nico).
Uso: python3 render_27.py ig|tt  [t_prueba ...]   (con tiempos de prueba solo guarda PNG)
Voz: Piper (es-carlfm-x-low). Etiqueta: Voz generada con IA.
Zonas seguras: nada en el 8,5 % superior, nada pasado el 87 % por la derecha, nada desde el 78 % hacia abajo.
"""
import math, random, subprocess, sys, wave
import numpy as np
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

MODE = sys.argv[1]; TESTS = [float(x) for x in sys.argv[2:]]
W, H, FPS = 1080, 1920, 30
XL, XR = 40, 930           # margen izquierdo / derecho (87 % = 939)
YT, YB = 170, 1490         # arriba (8,5 % = 163) / abajo (78 % = 1497)
CX = (XL + XR) // 2
NAVY = (13, 22, 43); NAVY2 = (26, 40, 74); CREAM = (246, 241, 232); MINT = (45, 212, 160)
CORAL = (255, 107, 107); GOLD = (255, 196, 61); BLUE = (96, 165, 250); MUTED = (148, 163, 184); INK = (15, 23, 42)
FD = "/usr/share/fonts/opentype/inter/"
@lru_cache(None)
def F(n, s): return ImageFont.truetype(FD + {"x": "Inter-ExtraBold.otf", "b": "Inter-Bold.otf", "m": "Inter-Medium.otf"}[n], int(s))
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def A(t, a, d=.4): return ease((t - a) / d)

@lru_cache(None)
def grad():
    g = np.zeros((H, W, 3), np.float32)
    for i in range(3): g[:, :, i] = np.linspace(NAVY[i], NAVY2[i], H)[:, None]
    return Image.fromarray(g.astype(np.uint8))
random.seed(7); CIR = [(random.random() * W, random.random() * H, random.randint(150, 380), random.random() * 6.28) for _ in range(6)]
def bg(t):
    im = grad().copy(); o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    for x, y, r, ph in CIR:
        cx = x + 40 * math.sin(t * .35 + ph); cy = y + 30 * math.cos(t * .3 + ph)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(96, 165, 250, 14))
    im.paste(o, (0, 0), o); return im

def T(im, txt, font, cx, cy, fill=CREAM, a=1.0, k=1.0, anchor="c"):
    if a <= .01 or k < .03: return
    b = font.getbbox(txt); w = b[2] - b[0] + 20; h = b[3] - b[1] + 20
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(lay).text((10 - b[0], 10 - b[1]), txt, font=font, fill=fill + (255,))
    if abs(k - 1) > .001: lay = lay.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
    if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    x = cx - lay.width / 2 if anchor == "c" else cx
    im.paste(lay, (int(x), int(cy - lay.height / 2)), lay)
def fit(txt, n, size, maxw):
    s = size
    while s > 20 and F(n, s).getlength(txt) > maxw: s -= 2
    return F(n, s)
@lru_cache(None)
def panel_img(w, h, fill, r, line=None):
    sc = 3; im = Image.new("RGBA", (w * sc, h * sc), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * sc - 1, h * sc - 1), r * sc, fill=fill, outline=line, width=4 * sc if line else 0)
    return im.resize((w, h), Image.LANCZOS)
def panel(im, cx, cy, w, h, fill=(255, 255, 255, 24), r=28, a=1.0, line=None, k=1.0):
    if a <= .01: return
    w = int(w * k); h = int(h * k); p = panel_img(max(2, w), max(2, h), fill, int(r), line)
    if a < 1: p = p.copy(); p.putalpha(p.getchannel("A").point(lambda v: int(v * a)))
    im.paste(p, (int(cx - w / 2), int(cy - h / 2)), p)
def mk(w, h, fn):
    sc = 4; im = Image.new("RGBA", (w * sc, h * sc), (0, 0, 0, 0)); d = ImageDraw.Draw(im); fn(d, w * sc, h * sc)
    return im.resize((w, h), Image.LANCZOS)
def put(im, ic, cx, cy, a=1.0, k=1.0):
    if a <= .01 or k < .03: return
    if abs(k - 1) > .001: ic = ic.resize((max(1, int(ic.width * k)), max(1, int(ic.height * k))), Image.LANCZOS)
    if a < 1: ic = ic.copy(); ic.putalpha(ic.getchannel("A").point(lambda v: int(v * a)))
    im.paste(ic, (int(cx - ic.width / 2), int(cy - ic.height / 2)), ic)

@lru_cache(None)
def ic_lemon(w):
    h = int(w * .8)
    def f(d, W_, H_):
        d.ellipse((W_ * .08, H_ * .12, W_ * .92, H_ * .92), fill=GOLD)
        d.polygon([(W_ * .02, H_ * .52), (W_ * .12, H_ * .42), (W_ * .14, H_ * .62)], fill=GOLD)
        d.polygon([(W_ * .98, H_ * .52), (W_ * .88, H_ * .42), (W_ * .86, H_ * .62)], fill=GOLD)
        d.ellipse((W_ * .5, H_ * .02, W_ * .8, H_ * .26), fill=MINT)
    return mk(w, h, f)
@lru_cache(None)
def ic_lupa(w):
    def f(d, W_, H_):
        d.ellipse((W_ * .05, W_ * .05, W_ * .65, W_ * .65), outline=CREAM, width=int(W_ * .08))
        d.line([(W_ * .56, W_ * .56), (W_ * .93, W_ * .93)], fill=CREAM, width=int(W_ * .11))
    return mk(w, w, f)
@lru_cache(None)
def ic_sobre(w):
    h = int(w * .66)
    def f(d, W_, H_):
        d.rounded_rectangle((0, 0, W_ - 1, H_ - 1), H_ * .08, fill=CREAM)
        d.polygon([(0, 0), (W_ / 2, H_ * .58), (W_, 0)], fill=(226, 218, 200))
        d.line([(0, H_ - 1), (W_ * .38, H_ * .45)], fill=(226, 218, 200), width=int(H_ * .02))
        d.line([(W_, H_ - 1), (W_ * .62, H_ * .45)], fill=(226, 218, 200), width=int(H_ * .02))
    return mk(w, h, f)

def seg_wrap(segs, fr, fb, maxw):
    words = []
    for txt, bold in segs:
        for wd in txt.split(" "):
            if not wd: continue
            if wd[0] in ",;:." and words: words[-1] = (words[-1][0] + wd, words[-1][1])
            else: words.append((wd, bold))
    lines, cur, cw = [], [], 0
    for wd, bold in words:
        L = (fb if bold else fr).getlength(wd + " ")
        if cur and cw + L > maxw: lines.append(cur); cur, cw = [], 0
        cur.append((wd, bold)); cw += L
    if cur: lines.append(cur)
    return lines
def draw_lines(im, lines, fr, fb, x, cy, lh, hl=1.0, a=1.0):
    y0 = cy - lh * (len(lines) - 1) / 2
    for i, ln in enumerate(lines):
        xx = x
        for wd, bold in ln:
            f = fb if bold else fr
            col = (MINT if bold else CREAM) if hl > 0 else CREAM
            if bold and hl < 1: col = tuple(int(CREAM[k] + (MINT[k] - CREAM[k]) * hl) for k in range(3))
            T(im, wd, f, xx, y0 + i * lh, col, a, anchor="l")
            xx += f.getlength(wd + " ") + 0

def caption(im, txt, a=1.0):
    f = fit(txt, "b", 40, XR - XL - 20)
    T(im, txt, f, CX, 1420, MUTED, a)
def header(im):
    T(im, "LA PIZARRA DE NICO", F("x", 30), CX, 205, MUTED)

# ---------------------------------------------------------------- IG ------
IG_SENT = [
    ("Soy profe de sexto y enseño los conectores con una espía y un limón.", "Soy profe de sexto y enseño los conectores con una espía y un limón."),
    ("La agente Lía recibe un sobre sin remitente.", "La agente Lía recibe un sobre sin remitente."),
    ("Pero su informe llega desordenado: ocho frases mezcladas.", "Pero su informe llega desordenado: ocho frases mezcladas."),
    ("Cada frase lleva una pista: primero, entonces, por eso, finalmente.", "Cada frase lleva una pista: primero, entonces, por eso, finalmente."),
    ("Las parejas escriben solo las letras en el orden correcto.", "Las parejas escriben solo las letras en el orden correcto."),
    ("La última palabra del informe es la clave del tesoro.", "La última palabra del informe es la clave del tesoro."),
    ("Es una de las tres estaciones de mi misión de agentes secretos para Lengua.", "Es una de las tres estaciones de mi misión de agentes secretos para Lengua."),
    ("¿Quieres la ficha? Escribe AGENTE en comentarios.", "¿Quieres la ficha? Escribe agente en comentarios."),
]
CARDS = [
    ("A", [("Por eso", 1), (", acercó el papel a una lámpara para calentarlo un poco.", 0)]),
    ("B", [("Finalmente", 1), (", guardó el mensaje y salió en busca del tesoro.", 0)]),
    ("C", [("Hace unos días", 1), (", la agente Lía recibió un sobre sin remitente.", 0)]),
    ("D", [("Poco a poco", 1), (", aparecieron unas letras de color marrón.", 0)]),
    ("E", [("Dentro encontró un papel en blanco; ", 0), ("sin embargo", 1), (", olía a limón.", 0)]),
    ("F", [("Después", 1), (" de leerlas, Lía sonrió: eran las instrucciones de su nueva misión.", 0)]),
    ("G", [("Primero", 1), (", lo abrió con mucho cuidado, ", 0), ("porque", 1), (" podía ser una trampa.", 0)]),
    ("H", [("Entonces", 1), (" recordó que el zumo de limón sirve como tinta invisible.", 0)]),
]
def ig_scene(im, i, t, dur, caps):
    d = ImageDraw.Draw(im)
    if i == 0:
        T(im, "Conectores", F("x", 150), CX, 520); T(im, "con un espía", F("x", 120), CX, 680, MINT)
        put(im, ic_lemon(330), CX - 170, 1030, 1, 1 + .04 * math.sin(t * 4)); put(im, ic_lupa(300), CX + 190, 1000, 1, 1 + .04 * math.cos(t * 4))
        T(im, "Lengua · 6.º de Primaria", F("b", 44), CX, 1250, MUTED)
    elif i == 1:
        k = .85 + .15 * ease(t / .5); put(im, ic_sobre(640), CX, 760, 1, k)
        T(im, "SIN REMITENTE", F("x", 84), CX, 1120, CORAL, A(t, .3)); T(im, "La agente Lía", F("b", 54), CX, 1240, CREAM, A(t, .5))
    elif i in (2, 3):
        base = 1.0 if i == 2 else .55
        for n, (let, segs) in enumerate(CARDS):
            a = A(t, .08 * n, .3) if i == 2 else 1.0
            y = 290 + n * 146 + (1 - ease(a)) * 40
            panel(im, CX, y, XR - XL, 132, (255, 255, 255, 26 if i == 2 else 14), 26, a=min(1, a))
            d.ellipse((XL + 20, y - 36, XL + 92, y + 36), fill=BLUE if i == 2 else (60, 90, 140)); T(im, let, F("x", 44), XL + 56, y, NAVY)
            fr, fb = F("m", 34), F("x", 34)
            lines = seg_wrap([(s, b) for s, b in segs], fr, fb, XR - XL - 150)
            hl = 1.0 if i == 2 else (0.5 + .5 * math.sin(t * 7 + n)) if i == 3 else .6
            draw_lines(im, lines, fr, fb, XL + 120, y, 42, hl, a=min(1, a) * (1 if i == 2 else .9))
        if i == 3:
            T(im, "primero · entonces · por eso · finalmente", fit("primero · entonces · por eso · finalmente", "x", 44, XR - XL), CX, 1420, MINT, A(t, .2))
    elif i == 4:
        T(im, "Escriben solo", F("x", 90), CX, 520); T(im, "las letras,", F("x", 90), CX, 630, MINT); T(im, "en orden", F("x", 90), CX, 740)
        panel(im, CX, 1000, 840, 230, (246, 241, 232, 240), 30, a=A(t, .1))
        n_f = min(8, int(t * 2.2)); txt = "-".join(["?"] * n_f + ["_"] * (8 - n_f))
        T(im, txt, fit(txt, "x", 80, 780), CX, 1000, INK, A(t, .1)); T(im, "en el cuaderno", F("b", 46), CX, 1190, MUTED, A(t, .3))
    elif i == 5:
        T(im, "La última palabra", F("x", 78), CX, 520); T(im, "del informe =", F("x", 78), CX, 620)
        T(im, "la clave del tesoro", F("x", 78), CX, 720, MINT)
        for n in range(6):
            panel(im, CX - 5 * 70 + n * 140, 1000, 120, 150, (246, 241, 232, 235), 20, a=A(t, .2 + .08 * n, .3))
            T(im, "?", F("x", 90), CX - 5 * 70 + n * 140, 1000, INK, A(t, .3 + .08 * n, .3))
        put(im, ic_lupa(240), CX, 1260, A(t, .6), 1)
    elif i == 6:
        names = [("A", "Archivos clasificados", "Autónoma"), ("B", "Contraseña de voz", "Con la AL"), ("C", "Documento desordenado", "Con la PT")]
        for n, (l, nm, who) in enumerate(names):
            y = 520 + n * 270; hi = n == 2
            panel(im, CX, y, XR - XL - 20, 230, (45, 212, 160, 60) if hi else (255, 255, 255, 24), 30, a=A(t, .15 * n, .35), line=MINT if hi else None)
            d.ellipse((XL + 50, y - 55, XL + 160, y + 55), fill=MINT if hi else BLUE); T(im, l, F("x", 70), XL + 105, y, NAVY)
            T(im, nm, fit(nm, "x", 52, 600), XL + 200, y - 22, CREAM, A(t, .15 * n, .35), anchor="l"); T(im, who, F("m", 38), XL + 200, y + 40, MUTED, A(t, .15 * n, .35), anchor="l")
        T(im, "Misión Agente Secreto", F("x", 56), CX, 1330, GOLD, A(t, .5))
    else:
        T(im, "¿Quieres", F("x", 110), CX, 480); T(im, "la ficha?", F("x", 110), CX, 610, MINT)
        panel(im, CX, 890, 760, 200, MINT + (255,), 40, k=1 + .03 * math.sin(t * 5))
        T(im, "Escribe AGENTE", F("x", 82), CX, 890, NAVY); T(im, "en comentarios", F("b", 50), CX, 1040, CREAM)
        T(im, "Estación C · informe desordenado (conectores)", fit("Estación C · informe desordenado (conectores)", "m", 38, XR - XL), CX, 1160, MUTED)
        T(im, "Decreto 66/2022 · Lengua 6.º · criterio 5.1", fit("Decreto 66/2022 · Lengua 6.º · criterio 5.1", "m", 36, XR - XL), CX, 1250, MUTED)
        T(im, "Voz generada con IA", F("b", 34), CX, 1330, MUTED)

# ---------------------------------------------------------------- TikTok ---
TT_SENT = [
    ("Descifra esto antes de que acabe el reel.", "Descifra esto antes de que acabe el ril."),
    ("Cada número es una letra: uno, la A; dos, la B.", "Cada número es una letra: uno, la a; dos, la be."),
    ("Pista: es lo primero que dice un agente al llegar.", "Pista: es lo primero que dice un agente al llegar."),
    ("Tres, dos, uno. Y la respuesta: HOLA AGENTE.", "Tres, dos, uno. Y la respuesta: hola, agente."),
    ("En mi clase de sexto, cada pareja escribe uno con tres conectores y dos tildes.", "En mi clase de sexto, cada pareja escribe uno con tres conectores y dos tildes."),
    ("Luego lo cifra y otra pareja lo descifra.", "Luego lo cifra y otra pareja lo descifra."),
    ("¿Quieres el alfabeto secreto? Escribe CLAVE en comentarios.", "¿Quieres el alfabeto secreto? Escribe clave en comentarios."),
]
ALPHA = list("ABCDEFGHIJKLMNÑOPQRSTUVWXYZ")
def code_row(im, codes, y, a=1.0, size=100):
    T(im, codes, fit(codes, "x", size, XR - XL), CX, y, GOLD, a)
def tt_scene(im, i, t, dur):
    d = ImageDraw.Draw(im)
    if i == 0:
        T(im, "DESCIFRA", F("x", 130), CX, 460); T(im, "ESTO", F("x", 130), CX, 600, MINT)
        panel(im, CX, 960, XR - XL, 380, (255, 255, 255, 28), 36)
        code_row(im, "8-16-12-1", 880, 1, 110); code_row(im, "1-7-5-14-21-5", 1040, 1, 110)
        w = (XR - XL - 80) * max(0, 1 - t / 3.3); d.rounded_rectangle((XL + 40, 1230, XL + 40 + max(4, w), 1250), 10, fill=CORAL)
    elif i == 1:
        for n in range(12):
            r, c = divmod(n, 4); x = CX - 300 + c * 200; y = 520 + r * 250
            hi = n < 2
            panel(im, x, y, 170, 210, (45, 212, 160, 70) if hi else (255, 255, 255, 24), 24, a=A(t, .08 * n, .3), line=MINT if hi else None)
            T(im, ALPHA[n] if n < 14 else "", F("x", 80), x, y - 40, CREAM, A(t, .08 * n, .3)); T(im, str(n + 1), F("x", 70), x, y + 55, GOLD, A(t, .08 * n, .3))
        T(im, "1 = A   ·   2 = B   ·   3 = C ...", F("x", 50), CX, 1330, MUTED, A(t, .5))
    elif i == 2:
        put(im, ic_lupa(300), CX, 560, 1, 1 + .04 * math.sin(t * 5))
        T(im, "PISTA", F("x", 120), CX, 850, MINT); T(im, "lo primero que", F("b", 62), CX, 1010); T(im, "dice un agente", F("b", 62), CX, 1090); T(im, "al llegar", F("b", 62), CX, 1170)
    elif i == 3:
        cd = dur * .5
        if t < cd:
            n = 3 - int(t / (cd / 3)); k = 1 + .25 * (1 - ease((t % (cd / 3)) / .25))
            T(im, str(n), F("x", 420), CX, 760, MINT, 1, k)
            T(im, "8-16-12-1  /  1-7-5-14-21-5", fit("8-16-12-1  /  1-7-5-14-21-5", "x", 56, XR - XL), CX, 1180, GOLD)
        else:
            u = t - cd
            words = [("HOLA", [8, 16, 12, 1]), ("AGENTE", [1, 7, 5, 14, 21, 5])]
            for r, (wd, nums) in enumerate(words):
                y = 640 + r * 400
                for n, (ch, nu) in enumerate(zip(wd, nums)):
                    cw = 118 if r == 1 else 150; x = CX - cw * (len(wd) - 1) / 2 + n * cw
                    a = A(u, (r * len(words[0][0]) + n) * .1, .3)
                    T(im, str(nu), F("x", 64), x, y - 90, GOLD, a); T(im, ch, F("x", 120), x, y + 30, MINT, a, 1 + .15 * (1 - a))
    elif i == 4:
        T(im, "En 6.º", F("x", 110), CX, 480)
        for n, (big, sm) in enumerate([("3", "conectores"), ("2", "tildes")]):
            y = 800 + n * 330; panel(im, CX, y, 760, 270, (255, 255, 255, 28), 36, a=A(t, .2 + .25 * n, .35))
            T(im, big, F("x", 190), CX - 250, y, MINT, A(t, .2 + .25 * n, .35)); T(im, sm, F("x", 82), CX - 120, y, CREAM, A(t, .2 + .25 * n, .35), anchor="l")
    elif i == 5:
        for n, (lb, sub, x) in enumerate([("Pareja 1", "cifra", CX - 250), ("Pareja 2", "descifra", CX + 250)]):
            a = A(t, .3 * n, .4)
            panel(im, x, 800, 400, 420, (255, 255, 255, 28), 36, a=a); T(im, lb, F("x", 60), x, 640, CREAM, a)
            put(im, ic_sobre(240), x, 800, a); T(im, sub, F("x", 64), x, 960, MINT, a)
        if t > .5:
            ln = ease((t - .5) / .5); d.line([(CX - 30, 800), (CX - 30 + 60 * ln, 800)], fill=GOLD, width=14)
        T(im, "8-16-12-1  1-7-5-14-21-5", fit("8-16-12-1  1-7-5-14-21-5", "x", 56, XR - XL), CX, 1200, GOLD, A(t, .8))
    else:
        T(im, "¿Quieres el", F("x", 100), CX, 480); T(im, "alfabeto secreto?", fit("alfabeto secreto?", "x", 100, XR - XL), CX, 610, MINT)
        panel(im, CX, 900, 760, 200, MINT + (255,), 40, k=1 + .03 * math.sin(t * 5))
        T(im, "Escribe CLAVE", F("x", 82), CX, 900, NAVY); T(im, "en comentarios", F("b", 50), CX, 1050, CREAM)
        T(im, "Misión Agente Secreto · Lengua 6.º", fit("Misión Agente Secreto · Lengua 6.º", "m", 38, XR - XL), CX, 1190, MUTED)
        T(im, "Voz generada con IA", F("b", 34), CX, 1270, MUTED)

# ---------------------------------------------------------------- audio -----
def synth(sents, tag):
    from piper import PiperVoice
    v = PiperVoice.load("/tmp/w/voz/es-carlfm-x-low.onnx"); out = []; durs = []; sr = None
    for k, (_, spoken) in enumerate(sents):
        fn = f"/tmp/w/{tag}_{k}.wav"
        with wave.open(fn, "wb") as w: v.synthesize_wav(spoken, w)
        with wave.open(fn) as w: sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16)
        out.append(a); durs.append(len(a) / sr)
    return out, durs, sr

def main():
    sents, scene, tail, name = (IG_SENT, ig_scene, 1.6, "reel_instagram_conectores") if MODE == "ig" else (TT_SENT, tt_scene, 1.6, "reel_tiktok_alfabeto")
    out, durs, sr = synth(sents, MODE)
    gap = int(.18 * sr); pieces = []; starts = []; pos = 0
    for k, a in enumerate(out):
        starts.append(pos / sr); pieces.append(a); pos += len(a)
        if k < len(out) - 1: pieces.append(np.zeros(gap, np.int16)); pos += gap
    audio = np.concatenate(pieces + [np.zeros(int(tail * sr), np.int16)]); total = len(audio) / sr
    ends = starts[1:] + [total]
    with wave.open(f"/tmp/w/{MODE}_all.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(audio.tobytes())
    print("duración", round(total, 2), "frases", [round(x, 1) for x in starts])
    def frame(t):
        im = bg(t).convert("RGBA"); header(im)
        i = max(k for k in range(len(starts)) if starts[k] <= t + 1e-6)
        lt = t - starts[i]; dur = ends[i] - starts[i]
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if MODE == "ig": scene(lay, i, lt, dur, None); dy = {0: 170, 1: 140, 5: 130, 6: 40}.get(i, 0)
        else: scene(lay, i, lt, dur); dy = {0: 130, 1: 110, 2: 150, 3: 80, 4: 120, 5: 150}.get(i, 0)
        im.paste(lay, (0, dy), lay)
        if i < len(sents) - 1 or True:
            cap = sents[i][0]
            if i < len(sents) - 1: caption(im, cap if len(cap) < 52 else cap[:cap.rfind(" ", 0, 52)] + "…", 1) if False else None
        return im.convert("RGB")
    if TESTS:
        for tt in TESTS: frame(tt).save(f"/tmp/w/test_{MODE}_{tt}.png"); print("ok", tt)
        return
    import os; os.makedirs("/home/claude/videos-canal/2026-11-27", exist_ok=True)
    dst = f"/home/claude/videos-canal/2026-11-27/{name}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", f"/tmp/w/{MODE}_all.wav",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.3f}", "-movflags", "+faststart", dst], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for f in range(n): p.stdin.write(frame(f / FPS).tobytes())
    p.stdin.close(); p.wait(); frame(0).save(f"/home/claude/videos-canal/2026-11-27/{name}_portada.png"); print("hecho", dst)
main()
