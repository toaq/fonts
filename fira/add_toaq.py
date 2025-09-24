import fontforge
import os
import random
import sys
from PIL import Image
from enum import Enum, auto
from math import atan2, radians
from multiprocessing import Pool
from psMat import translate, skew, scale, rotate

def sample():
    return "󱚶󱚲󱛍󱚺 󱚾󱛊󱚹 󱛔 󱛁󱚺󱛋 󱚻󱚲󱛂󱛀󱚲󱛍󱚺 󱛕"
    return "\n\nthe content clause 󱛁󱚺󱛋 󱚾󱚺󱛎󱚹 󱚽󱛊󱚺󱛎󱛃 (ꝡä jaı nháo)"
    return "󱚻󱛌󱚺󱛎󱛃 󱛘󱛄󱛊󱛃󱛍󱚺󱚹󱚺󱛎󱛃󱛙 󱛄󱛋󱚹󱛍󱛃 󱚿󱛃 󱚾󱛊󱚹 󱚲󱛊󱚺󱛂 󱛘󱛄󱛃󱛍󱚺󱚹󱚺󱛎󱛃󱛙 󱛄󱚹 󱚵󱛋󱚺 󱚲󱚺󱛎󱚹 󱚾󱛊󱚹 󱚲󱛊󱚺󱛂 󱛘󱚵󱚹󱛍󱚺󱛎󱛃󱚳󱛃󱛂󱛙 󱛕\nRâo kóacao (kïo cho jí báq koacao kı) nä baı jí báq nıaopoq."
    text = "Fira Sans "
    for v1 in "󱚺󱚴󱚹󱛃󱚲":
        for v2 in "󱚺󱚴󱚹󱛃󱚲":
            if v1 == v2: continue
            c = random.choice("󱚲󱚹󱚿󱚶󱚴󱛃󱛆󱚾󱛄󱚼󱚰󱚵󱚽󱚳󱚻󱚺󱚷󱛁󱚸")
            tone = random.choice("󱛊󱛋󱛌") * random.randint(0,1)
            text += c + tone + v1 + "󱛍" + v2 + random.choice(" 󱛂󱚱  ")
    return text

def ord_(x):
    return ord(x) if isinstance(x, str) and len(x) == 1 else x

def toaqify(font):
    def get(c):
        try:
            return font[ord_(c)]
        except:
            for g in font:
                if font[g].unicode == c:
                    return font[g]

    def select(src):
        try: font.selection.select(ord_(src))
        except ValueError: font.selection.select(("unicode",), ord_(src))

    def copy(src, tgt):
        select(src); font.copy()
        select(tgt); font.paste()

    def add(src, tgt):
        get(tgt).foreground += get(src).foreground
        # select(src); font.copy()
        # select(tgt); font.pasteInto()

    def sub(src, tgt):
        copy(src, 1)
        get(1).exclude(get(tgt).layers[1])
        copy(1, tgt)

    def rect(c, x1, y1, x2, y2):

        ct = fontforge.contour(1)
        ct.moveTo(x1,y1)
        ct.lineTo(x1,y2)
        ct.lineTo(x2,y2)
        ct.lineTo(x2,y1)
        ct.lineTo(x1,y1)
        ct.closed = True
        # ct.lineTo(x1,y1)
        get(c).layers[1] += ct

    def xmin(c): return get(c).boundingBox()[0]
    def ymin(c): return get(c).boundingBox()[1]
    def xmax(c): return get(c).boundingBox()[2]
    def ymax(c): return get(c).boundingBox()[3]
    def height(c): return ymax(c) - ymin(c)
    def xctr(c): return (xmax(c) + xmin(c)) / 2
    def yctr(c): return (ymax(c) + ymin(c)) / 2

    def points(c):
        return [p for contour in get(c).layers[1] for p in contour]

    # baseline start and end
    def bs(c): return min([p.x for p in points(c) if abs(p.y) < 1])
    def be(c): return max([p.x for p in points(c) if abs(p.y) < 1])

    def clip(cp, x1, y1, x2, y2):
        copy(32, 1)
        rect(1, x1, y1, x2, y2)
        add(1, tgt=cp)
        get(cp).intersect()

    def flip(c, fx, fy):
        g = get(c)
        g.unlinkRef()
        dx = xctr(c)
        dy = yctr(c)
        fg = g.layers[1]
        fg.transform(skew(-slant))
        fg.transform(translate(-dx, -dy))
        fg.transform(scale(fx, fy))
        fg.transform(translate(dx, dy))
        fg.transform(skew(slant))
        g.layers[1] = fg
        g.correctDirection()

    def hflip(c): flip(c, -1, 1)
    def vflip(c): flip(c, 1, -1)

    slant_dx = xmax("ı") - be("ı")
    slant_dy = ymax("ı") - ymin("ı")
    slant = atan2(slant_dx, slant_dy)

    # helper glyphs
    Y_TAIL = 2
    RDESC = 3
    Z_TAIL = 4

    VY = 0xa761
    CAP_VY = 0xa760
    def make(n, name): font.createChar(n, name); return n

    MAMEI = make(0xf16b0, "mamei")
    MAMEI_CODA = make(0xf16b1, "mamei_coda")
    BUBUE = make(0xf16b2, "bubue")
    PIPOQ = make(0xf16b3, "pipoq")
    FOFUAQ = make(0xf16b4, "fofuaq")
    NANAQ = make(0xf16b5, "nanaq")
    DUDEO = make(0xf16b6, "dudeo")
    TITIEQ = make(0xf16b7, "titieq")
    ZOZEO = make(0xf16b8, "zozeo")
    CECOA = make(0xf16b9, "cecoa")
    SAQSEOQ = make(0xf16ba, "saqseoq")
    RAIRUA = make(0xf16bb, "rairua")
    LAOLIQ = make(0xf16bc, "laoliq")
    NHANHOQ = make(0xf16bd, "nhanhoq")
    JUJUO = make(0xf16be, "jujuo")
    CHICHAO = make(0xf16bf, "chichao")
    SHOSHIA = make(0xf16c0, "shoshia")
    WEWA = make(0xf16c1, "wewa")
    AQAQ = make(0xf16c2, "aqaq")
    GUGUI = make(0xf16c3, "gugui")
    KIKUE = make(0xf16c4, "kikue")
    OAOMO = make(0xf16c5, "oaomo")
    HEHAQ = make(0xf16c6, "hehaq")
    GULAQTEI = make(0xf16ca, "gulaqtei")
    SAQLAQTEI = make(0xf16cb, "saqlaqtei")
    JOLAQTEI = make(0xf16cc, "jolaqtei")
    IULAI = make(0xf16cd, "iulai")
    AILAI = make(0xf16ce, "ailai")
    PMARK = make(0xf16d2, "deranipmark")
    QMARK = make(0xf16d3, "deraniqmark")
    SMARK = make(0xf16d4, "deranismark")
    STOP1 = make(0xf16d5, "deranistop1")
    STOP2 = make(0xf16d6, "deranistop2")
    STOP3 = make(0xf16d7, "deranistop3")
    START_CARTOUCHE = make(0xf16d8, "deranistartcartouche")
    END_CARTOUCHE = make(0xf16d9, "deraniendcartouche")
    RAILAI = make(0xf16da, "railai")
    DCNBSP = make(0xf16db, "deraninbsp")

    bridge = True

    copy("y", Y_TAIL)
    clip(Y_TAIL, 0, -600, 600, 0)
    get(Y_TAIL).anchorPoints = []

    def make_vy(src, tgt):
        dx = be(src) - be(Y_TAIL)
        get(Y_TAIL).transform(translate(dx, 0))
        copy(src, tgt)
        add(Y_TAIL, tgt)
        get(tgt).removeOverlap()

    make_vy("w", VY)
    make_vy("W", CAP_VY)

    copy("η", RDESC)
    clip(RDESC, 0, -600, 600, 0)
    get(RDESC).anchorPoints = []

    def add_rdesc(tgt):
        ymint = ymin(tgt)
        dy = -ymax(RDESC)
        dx = max([p.x for p in points(tgt) if abs(p.y-ymint) < 1]) - xmax(RDESC)
        get(RDESC).transform(translate(dx, dy))
        add(RDESC, tgt)
        get(tgt).removeOverlap()

    # mamei
    SW = ymax("_") - ymin("_")
    BW = SW if SW < 50 else 0.8 * SW
    copy("m", MAMEI)
    if bridge: rect(MAMEI, xmin("m")+SW/2, 0, be("m"), BW)
    add_rdesc(MAMEI)
    copy("ƿ", MAMEI_CODA)
    clip(MAMEI_CODA, 0, 0, 999, 999)

    # bubue
    copy("ɔ", BUBUE)

    # pipoq
    copy("q", PIPOQ)

    # fofuaq
    copy("ɿ", FOFUAQ)
    add_rdesc(FOFUAQ)

    # nanaq
    # copy("´", 1)
    # get(1).anchorPoints = []
    # dx = xctr("o") - xctr(1) + height("o") * slant_dx / slant_dy
    # dy = -90
    # get(1).transform(translate(dx, dy))
    # copy(1, NANAQ)
    # add("o", NANAQ)
    copy("ohorn", NANAQ)

    # dudeo
    copy("ɘ", DUDEO)

    # titieq
    copy("d", TITIEQ)

    # zozeo
    try:
        copy("jcrossedtaildotless", Z_TAIL)
    except ValueError:
        copy("jcrossedtail", Z_TAIL)
    get(Z_TAIL).anchorPoints = []
    clip(Z_TAIL, -400, -400, 400, 50)
    get(Z_TAIL).transform(translate(0, -50))
    dx = be("ɿ") - be(Z_TAIL)
    get(Z_TAIL).transform(translate(dx, 0))
    copy("ɿ", ZOZEO)
    add(Z_TAIL, ZOZEO)
    get(ZOZEO).removeOverlap()

    # cecoa
    copy("c", CECOA)

    # saqseoq
    copy("o", SAQSEOQ)

    # rairua
    copy("n", RAIRUA)
    if bridge: rect(RAIRUA, xmin("η")+SW/2, 0, be("n"), BW)
    add_rdesc(RAIRUA)
    get(RAIRUA).removeOverlap()

    # laoliq
    def dotbelow(c):
        g = get(c)
        g.layers[1].transform(skew(-slant))
        ax = next(a[2] for a in get(c).anchorPoints if a[0] == "Anchor-14")
        copy("dotbelowcomb", 1)
        get(1).transform(skew(-slant))
        get(1).transform(translate(ax - xctr(1), 0))
        # add(1, c)
        g.layers[1] += get(1).layers[1]
        g.layers[1].transform(skew(slant))

    copy("n", LAOLIQ)
    if bridge: rect(LAOLIQ, xmin("n")+SW/2, 0, be("n"), BW)
    get(LAOLIQ).removeOverlap()
    dotbelow(LAOLIQ)

    # TODO underdot

    # nhanhoq
    copy("ə", NHANHOQ)

    # jujuo
    copy("ω", JUJUO)
    vflip(JUJUO)
    copy(32, 1)

    ct = fontforge.contour(1)
    xs = sorted({int(p.x) for p in points(JUJUO) if p.y <= 0})
    ct.moveTo(0,300)
    ct.lineTo(0,900)
    ct.lineTo(900,900)
    ct.lineTo(900,0)
    ct.lineTo(xs[-2],0)
    ct.lineTo(xs[-2],300)
    ct.closed = True
    get(1).layers[1] = ct
    get(1).transform(skew(slant))
    add(1, JUJUO)
    get(JUJUO).intersect()

    # chichao
    copy("s", CHICHAO)
    hflip(CHICHAO)
    get(CHICHAO).transform(translate(0, 0))

    def long_rdesc(c):
        g = get(c)
        g.transform(skew(-slant))
        get(RDESC).transform(skew(-slant))
        otips = [p for p in points(c) if p.type == 0 and p.on_curve]
        otips.sort(key=lambda p: p.y)
        xon = sorted([p.x for p in points(c) if p.on_curve])
        clip(c, 0, -999, xon[-2], 999)
        dx = xon[-2] - max([p.x for p in points(RDESC) if p.y == ymax(RDESC)])
        tips = [p for p in points(c) if p.type == 0 and p.on_curve]
        tips.sort(key=lambda p: p.y)
        dy = tips[0].y - ymax(RDESC)
        get(RDESC).transform(translate(dx, dy))
        add(RDESC, c)
        get(RDESC).transform(translate(0, -tips[0].y))
        add(RDESC, c)
        g.removeOverlap()
        g.simplify()
        sharp_x = be(c)
        sharp_y = max([p.y for p in points(c) if abs(p.x-sharp_x)<1 and p.y < 200])
        fg = g.layers[1]
        for (j, contour) in enumerate(fg):  # oroooo
            for (i, p) in enumerate(contour):
                if (p.x,p.y) == (sharp_x,sharp_y):
                    p.y = otips[1].y
                    contour[i] = p
                    break
            fg[j] = contour
        g.layers[1] = fg
        get(RDESC).transform(skew(slant))
        g.transform(skew(slant))

    # shoshia
    copy(CHICHAO, SHOSHIA)
    long_rdesc(SHOSHIA)

    # wewa
    copy("s", WEWA)

    # aqaq
    copy("c", AQAQ)
    long_rdesc(AQAQ)

    # gugui
    copy("ε", GUGUI)

    # kikue
    copy("c", KIKUE)
    dotbelow(KIKUE)

    # oaomo
    copy("·", OAOMO)

    # hehaq
    copy(FOFUAQ, HEHAQ)
    get(HEHAQ).transform(skew(-slant))
    rect(HEHAQ, xmin(HEHAQ)+SW/2, 0, xmax(HEHAQ) + 80, BW)
    get(HEHAQ).transform(skew(slant))
    get(HEHAQ).removeOverlap()

    def rot(c, deg):
        x, y = xctr(c), yctr(c)
        get(c).transform(translate(-x, -y))
        get(c).transform(rotate(radians(deg)))
        get(c).transform(translate(x, y))

    copy(0x0301, GULAQTEI)
    copy(0x0303, SAQLAQTEI)
    # rot(SAQLAQTEI, -15)
    copy(0x0311, JOLAQTEI)
    # rot(JOLAQTEI, 15)
    for tgt in (IULAI, AILAI):
        copy(0x035c, tgt)
        l = get(tgt).layers[1]
        l.transform(translate(200, 0))
        get(tgt).layers[1] = l
        flip(tgt, 0.8, -0.8)

    # PMARK
    copy(":", PMARK)
    # QMARK
    copy(":", QMARK)
    # SMARK
    copy(",", SMARK)
    get(SMARK).transform(translate(200, 0))
    add(",", SMARK)
    get(SMARK).transform(translate(200, 0))
    add(",", SMARK)

    # stops
    copy("|", STOP1)
    add_rdesc(STOP1)
    get(STOP1).transform(translate(150, 0))
    copy(STOP1, STOP2)
    copy(STOP1, STOP3)
    add("·", STOP1)
    add(":", STOP2)
    add(":", STOP3)
    add("·", STOP3)

    # cartouches (not rendered)
    copy("\u200b", START_CARTOUCHE)
    copy("\u200b", END_CARTOUCHE)

    # RAILAI
    copy("*", RAILAI)

    # DCNBSP
    copy("\xa0", DCNBSP)

    font.descent = 300
    fontforge.printSetup("pdf-file", "", 1300, 400)
    font.printSample("fontsample", 60, sample())
    print("Printed sample:", font.fontname)

paths = [p for p in os.listdir() if p.endswith(".ttf")]

if len(sys.argv) > 1:
    paths = [sys.argv[1]]
elif not paths:
    import zipfile
    with zipfile.ZipFile("original.dat") as zf:
        zf.extractall(".")
    paths = [p for p in os.listdir() if p.endswith(".ttf")]

def convert(path):
    font = fontforge.open(path)
    font.fontname = font.fontname.replace("FiraSans", "FiraSansToaq")
    toaqify(font)
    if font.fontname == "FiraSansToaq-Regular": font.save("q.sfd")

if __name__ == "__main__":
    with Pool(8) as p:
        p.map(convert, paths)
