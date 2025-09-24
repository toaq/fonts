import fontforge
import os
import sys
from math import atan2, radians
from psMat import translate, skew, scale, rotate
from enum import Enum, auto
from PIL import Image

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
        select(src); font.copy()
        select(tgt); font.pasteInto()

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
    MAMEI = 0xf16b0; font.createChar(MAMEI, "mamei")
    MAMEI_CODA = 0xf16b1; font.createChar(MAMEI_CODA, "mamei_coda")
    BUBUE = 0xf16b2; font.createChar(BUBUE, "bubue")
    PIPOQ = 0xf16b3; font.createChar(PIPOQ, "pipoq")
    FOFUAQ = 0xf16b4; font.createChar(FOFUAQ, "fofuaq")
    NANAQ = 0xf16b5; font.createChar(NANAQ, "nanaq")
    DUDEO = 0xf16b6; font.createChar(DUDEO, "dudeo")
    TITIEQ = 0xf16b7; font.createChar(TITIEQ, "titieq")
    ZOZEO = 0xf16b8; font.createChar(ZOZEO, "zozeo")
    CECOA = 0xf16b9; font.createChar(CECOA, "cecoa")
    SAQSEOQ = 0xf16ba; font.createChar(SAQSEOQ, "saqseoq")
    RAIRUA = 0xf16bb; font.createChar(RAIRUA, "rairua")
    LAOLIQ = 0xf16bc; font.createChar(LAOLIQ, "laoliq")
    NHANHOQ = 0xf16bd; font.createChar(NHANHOQ, "nhanhoq")
    JUJUO = 0xf16be; font.createChar(JUJUO, "jujuo")
    CHICHAO = 0xf16bf; font.createChar(CHICHAO, "chichao")
    SHOSHIA = 0xf16c0; font.createChar(SHOSHIA, "shoshia")
    WEWA = 0xf16c1; font.createChar(WEWA, "wewa")
    AQAQ = 0xf16c2; font.createChar(AQAQ, "aqaq")
    GUGUI = 0xf16c3; font.createChar(GUGUI, "gugui")
    KIKUE = 0xf16c4; font.createChar(KIKUE, "kikue")
    OAOMO = 0xf16c5; font.createChar(OAOMO, "oaomo")
    HEHAQ = 0xf16c6; font.createChar(HEHAQ, "hehaq")
    GULAQTEI = 0xf16ca; font.createChar(GULAQTEI, "gulaqtei")
    SAQLAQTEI = 0xf16cb; font.createChar(SAQLAQTEI, "saqlaqtei")
    JOLAQTEI = 0xf16cc; font.createChar(JOLAQTEI, "jolaqtei")
    IULAI = 0xf16cd; font.createChar(IULAI, "iulai")
    AILAI = 0xf16ce; font.createChar(AILAI, "ailai")

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
        dy = -ymax(RDESC)
        dx = be(tgt) - xmax(RDESC)
        get(RDESC).transform(translate(dx, dy))
        add(RDESC, tgt)
        get(tgt).removeOverlap()

    # mamei
    SW = ymax("_") - ymin("_")
    BW = SW if SW < 50 else 0.8 * SW
    copy("m", MAMEI)
    if bridge: rect(MAMEI, xmin("m")+SW/2, 0, be("m"), BW)
    add_rdesc(MAMEI)
    copy("ɒ", MAMEI_CODA)

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
    copy(0x0332, IULAI)
    l = get(IULAI).layers[1]
    l.transform(translate(200, 0))
    get(IULAI).layers[1] = l
    copy(0x0332, AILAI)
    get(AILAI).layers[1].transform(translate(90, 0))

    fontforge.printSetup("pdf-file")
    font.printSample("fontsample", 44, "\n\nFira Sans (󱚰󱛊󱚹 :󱚴󱚹󱚻󱚺:)\n\n󱚵󱚲󱛍󱛃 󱚺󱛊󱚲󱛂 󱚶󱛌󱚴 󱚲󱚺 󱛕")

    print("kıosha!", font)

paths = [p for p in os.listdir() if p.endswith(".ttf")]

if len(sys.argv) > 1:
    paths = [sys.argv[1]]
elif not paths:
    import zipfile
    with zipfile.ZipFile("original.dat") as zf:
        zf.extractall(".")
    paths = [p for p in os.listdir() if p.endswith(".ttf")]

for path in paths:
    font = fontforge.open(path)
    font.fontname = font.fontname.replace("FiraSans", "FiraSansToaq")
    toaqify(font)
    font.save("q.sfd")
