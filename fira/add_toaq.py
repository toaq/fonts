from __future__ import annotations

import functools
import os
import sys
from math import atan2, radians
from multiprocessing import Pool
from typing import Any, Callable, List, Optional, Set, Union

import fontforge  # type: ignore
from PIL import Image, ImageDraw, ImageFont  # type: ignore
from psMat import translate, skew, scale, rotate  # type: ignore


# indices of helper glyphs
Y_TAIL = 2
RDESC = 3
Z_TAIL = 4

VY = 0xA761
CAP_VY = 0xA760


def ord_(x: Union[str, int]) -> Union[str, int]:
    return ord(x) if isinstance(x, str) and len(x) == 1 else x


class Font:
    def __init__(self, font: Any) -> None:
        self.font: Any = font
        self.slant: Optional[float] = None
        self.visited: Set[Union[str, int]] = {-1}
        self.inter: bool = "Iqteo" in font.fontname
        self.KERN_TABLE: str = (
            "'kern' Horizontal Kerning lookup 1 per glyph data 0"
            if self.inter
            else "'kern' Horizontal Kerning lookup 2 per glyph data 2"
        )

        # Calculate slant
        slant_dx = self.xmax("ı") - self.be("ı")
        slant_dy = self.ymax("ı") - self.ymin("ı")
        self.slant = atan2(slant_dx, slant_dy)

    @functools.cache
    def get_glyph(self, c: Union[str, int]) -> Optional[Any]:
        try:
            return self.font[ord_(c)]
        except TypeError:
            for g in self.font:
                if self.font[g].unicode == c or self.font[g].glyphname == c:
                    return self.font[g]
        return None

    def get(self, c: Union[str, int]) -> Any:
        glyph = self.get_glyph(c)
        if not glyph:
            raise KeyError(f"get {c}")
        if self.slant is not None and glyph.unicode not in self.visited:
            glyph.transform(skew(-self.slant))
            self.visited.add(glyph.unicode)
        return glyph

    def select(self, src: Union[str, int]) -> None:
        try:
            self.font.selection.select(ord_(src))
        except ValueError:
            self.font.selection.select(("unicode",), ord_(src))

    def copy(self, src: Union[str, int], tgt: Union[str, int]) -> None:
        self.get(src)
        self.select(src)
        self.font.copy()
        self.select(tgt)
        self.font.paste()
        self.visited.add(tgt)

    def add(self, src: Union[str, int], tgt: Union[str, int]) -> None:
        self.get(tgt).foreground += self.get(src).foreground

    def rect(self, c: Union[str, int], *path: float) -> None:
        ct = fontforge.contour(1)
        x1, y1, x2, y2, *rest = path
        rest += [x1, y1, 0.0, 0.0]
        ct.moveTo(x1, y1)
        while len(rest):
            ct.lineTo(x1, y2)
            ct.lineTo(x2, y2)
            x1, y1, x2, y2, *rest = x2, y2, *rest
        ct.closed = True
        # ct.lineTo(x1,y1)
        self.get(c).layers[1] += ct

    def polygon(self, c: Union[str, int], *path: float) -> None:
        ct = fontforge.contour(1)
        x1, y1, *rest = path
        rest += [x1, y1]
        ct.moveTo(x1, y1)
        while len(rest):
            ct.lineTo(x1, y1)
            x1, y1, *rest = rest
        ct.closed = True
        self.get(c).layers[1] += ct

    def xmin(self, c: Union[str, int]) -> float:
        return self.get(c).boundingBox()[0]

    def ymin(self, c: Union[str, int]) -> float:
        return self.get(c).boundingBox()[1]

    def xmax(self, c: Union[str, int]) -> float:
        return self.get(c).boundingBox()[2]

    def ymax(self, c: Union[str, int]) -> float:
        return self.get(c).boundingBox()[3]

    def height(self, c: Union[str, int]) -> float:
        return self.ymax(c) - self.ymin(c)

    def xctr(self, c: Union[str, int]) -> float:
        return (self.xmax(c) + self.xmin(c)) / 2

    def yctr(self, c: Union[str, int]) -> float:
        return (self.ymax(c) + self.ymin(c)) / 2

    def points(self, c: Union[str, int]) -> List[Any]:
        return [p for contour in self.get(c).layers[1] for p in contour]

    # baseline start and end
    def bs(self, c: Union[str, int]) -> float:
        return min([p.x for p in self.points(c) if abs(p.y) < 5] or [0])

    def be(self, c: Union[str, int]) -> float:
        return max([p.x for p in self.points(c) if abs(p.y) < 5] or [1000])

    def crop(self, cp: Union[str, int], *path: float) -> None:
        self.copy(32, 1)
        self.rect(1, *path)
        self.add(1, tgt=cp)
        self.get(cp).intersect()

    def polycrop(self, cp: Union[str, int], *path: float) -> None:
        self.copy(32, 1)
        self.polygon(1, *path)
        self.add(1, tgt=cp)
        self.get(cp).intersect()

    def scaled(self, c: Union[str, int], fx: float, fy: float) -> None:
        g = self.get(c)
        g.unlinkRef()
        dx = self.xctr(c)
        dy = self.yctr(c)
        fg = g.layers[1]
        fg.transform(translate(-dx, -dy))
        fg.transform(scale(fx, fy))
        fg.transform(translate(dx, dy))
        g.layers[1] = fg
        g.correctDirection()

    def hflip(self, c: Union[str, int]) -> None:
        self.scaled(c, -1, 1)

    def vflip(self, c: Union[str, int]) -> None:
        self.scaled(c, 1, -1)

    def make_vy(self, src: Union[str, int], tgt: Union[str, int]) -> None:
        dx = self.be(src) - self.be(2)  # Y_TAIL = 2
        self.get(2).transform(translate(dx, 0))
        self.copy(src, tgt)
        self.add(2, tgt)
        self.get(tgt).removeOverlap()

    def add_rdesc(self, tgt: Union[str, int]) -> None:
        ymint = self.ymin(tgt)
        dy = -self.ymax(3)  # RDESC = 3
        dx = max([p.x for p in self.points(tgt) if abs(p.y - ymint) < 1]) - self.xmax(3)
        self.get(3).transform(translate(dx, dy))
        self.add(3, tgt)
        self.get(tgt).removeOverlap()

    def map_points(self, c: Union[str, int], f: Callable[[Any], Any]) -> None:
        glyph = self.get(c)
        fg = glyph.foreground
        for j, contour in enumerate(fg):
            for i, p in enumerate(contour):
                contour[i] = f(p)
            fg[j] = contour
        glyph.foreground = fg

    def long_rdesc(self, c: Union[str, int]) -> None:
        g = self.get(c)
        otips = [p for p in self.points(c) if p.type == 0 and p.on_curve]
        otips.sort(key=lambda p: p.y)
        xon = sorted([p.x for p in self.points(c) if p.on_curve])
        ix = -1 if self.inter else -2  # stupid
        self.crop(c, -300, -3000, xon[ix], 3000)
        eq_rdesc = [p.x for p in self.points(3) if p.y == self.ymax(RDESC)]
        dx = xon[ix] - max(eq_rdesc)  # ughghgh
        tips = [p for p in self.points(c) if p.type == 0 and p.on_curve]
        tips.sort(key=lambda p: p.y)
        dy = tips[0].y - self.ymax(3)
        self.get(3).transform(translate(dx, dy))
        self.add(3, c)
        self.get(3).transform(translate(0, -tips[0].y))
        self.add(3, c)
        g.removeOverlap()
        g.simplify()
        try:
            sharp_x = self.be(c)
            sharp_y = max(
                [p.y for p in self.points(c) if abs(p.x - sharp_x) < 1 and p.y < 200]
            )
            self.map_points(
                c,
                lambda p: (p.x, otips[1].y) if (p.x, p.y) == (sharp_x, sharp_y) else p,
            )
        except ValueError as e:
            print(self.font, c, "long_rdesc failed", e)

    def stitch(
        self, head: Union[str, int], legs: Union[str, int], tgt: Union[str, int]
    ) -> None:
        LAB = 7
        self.copy(head, tgt)
        self.crop(tgt, 0, 0, 9999, 9999)
        self.copy(legs, LAB)
        self.crop(LAB, 0, -5000, 9999, 0)
        w2 = self.be(tgt) - self.bs(tgt)
        w1 = self.be(LAB) - self.bs(LAB)
        self.get(LAB).transform(scale(w2 / w1, 1))
        self.get(LAB).transform(translate(self.be(tgt) - self.be(LAB), 0))
        self.add(LAB, tgt)
        self.get(LAB).clear()
        self.get(tgt).removeOverlap()

    def dotbelow(self, c: Union[str, int]) -> None:
        g = self.get(c)
        ax_list = [a[2] for a in self.get(c).anchorPoints if a[0] == "Anchor-14"]
        ax = ax_list[0] if ax_list else self.xctr(c)
        self.copy(0x323, 1)
        if self.slant is not None:
            self.get(1).transform(skew(-self.slant))
        self.get(1).transform(translate(ax - self.xctr(1), 0))
        # self.add(1, c)
        g.layers[1] += self.get(1).layers[1]

    def rot(self, c: Union[str, int], deg: float) -> None:
        x, y = self.xctr(c), self.yctr(c)
        self.get(c).transform(translate(-x, -y))
        self.get(c).transform(rotate(radians(deg)))
        self.get(c).transform(translate(x, y))

    def toaqify(self) -> None:
        def make(n: int, name: str) -> int:
            self.font.createChar(n, name)
            return n

        cartouchable = [
            MAMEI := make(0xF16B0, "mamei"),
            MAMEI_CODA := make(0xF16B1, "mamei_coda"),
            BUBUE := make(0xF16B2, "bubue"),
            PIPOQ := make(0xF16B3, "pipoq"),
            FOFUAQ := make(0xF16B4, "fofuaq"),
            NANAQ := make(0xF16B5, "nanaq"),
            DUDEO := make(0xF16B6, "dudeo"),
            TITIEQ := make(0xF16B7, "titieq"),
            ZOZEO := make(0xF16B8, "zozeo"),
            CECOA := make(0xF16B9, "cecoa"),
            SAQSEOQ := make(0xF16BA, "saqseoq"),
            RAIRUA := make(0xF16BB, "rairua"),
            LAOLIQ := make(0xF16BC, "laoliq"),
            NHANHOQ := make(0xF16BD, "nhanhoq"),
            JUJUO := make(0xF16BE, "jujuo"),
            CHICHAO := make(0xF16BF, "chichao"),
            SHOSHIA := make(0xF16C0, "shoshia"),
            WEWA := make(0xF16C1, "wewa"),
            AQAQ := make(0xF16C2, "aqaq"),
            GUGUI := make(0xF16C3, "gugui"),
            KIKUE := make(0xF16C4, "kikue"),
            OAOMO := make(0xF16C5, "oaomo"),
            HEHAQ := make(0xF16C6, "hehaq"),
            PMARK := make(0xF16D2, "deranipmark"),
            QMARK := make(0xF16D3, "deraniqmark"),
            SMARK := make(0xF16D4, "deranismark"),
            RAILAI := make(0xF16DA, "railai"),
            DCNBSP := make(0xF16DB, "deraninbsp"),
            IULAI := make(0xF16CD, "iulai"),
            AILAI := make(0xF16CE, "ailai"),
        ]

        GULAQTEI = make(0xF16CA, "gulaqtei")
        SAQLAQTEI = make(0xF16CB, "saqlaqtei")
        JOLAQTEI = make(0xF16CC, "jolaqtei")
        STOP1 = make(0xF16D5, "deranistop1")
        STOP2 = make(0xF16D6, "deranistop2")
        STOP3 = make(0xF16D7, "deranistop3")
        START_CARTOUCHE = make(0xF16D8, "deranistartcartouche")
        END_CARTOUCHE = make(0xF16D9, "deraniendcartouche")

        bridge = True

        self.copy("y", Y_TAIL)
        self.crop(Y_TAIL, 0, -6000, 6000, 0)
        self.get(Y_TAIL).anchorPoints = []

        self.make_vy("w", VY)
        self.make_vy("W", CAP_VY)

        self.copy("η", RDESC)
        self.crop(RDESC, 0, -6000, 6000, 0)
        self.get(RDESC).anchorPoints = []

        # mamei
        SW = self.ymax("_") - self.ymin("_")
        BW = SW if SW < 50 or self.inter else 0.8 * SW
        self.copy("m", MAMEI)
        if bridge:
            self.rect(MAMEI, self.xmin("m") + SW / 2, 0, self.be("m"), BW)
        self.add_rdesc(MAMEI)
        self.copy("ƿ", MAMEI_CODA)
        self.crop(MAMEI_CODA, 0, 0, 3999, 3999)

        # pipoq
        self.copy("q", PIPOQ)

        # fofuaq
        self.copy("ɿ", FOFUAQ)
        self.add_rdesc(FOFUAQ)

        # nanaq
        self.copy("o", NANAQ)
        self.copy("'", 1)
        self.get(1).transform(translate(-self.xctr(1), -self.yctr(1)))
        self.scaled(1, 0.8, 0.8)
        self.get(1).transform(rotate(radians(-45)))
        if self.inter:
            slant_factor = 35 if self.slant and self.slant > 0.01 else 0
            self.get(1).transform(translate(1100 - slant_factor, 1000))
        else:
            slant_factor = 35 if self.slant and self.slant > 0.01 else 0
            self.get(1).transform(translate(519 - slant_factor, 500))
        self.add(1, NANAQ)
        self.get(NANAQ).width += 50

        # dudeo
        self.copy("ɘ", DUDEO)

        # titieq
        self.copy("U", TITIEQ)
        self.vflip(TITIEQ)

        def f(p):
            x0 = self.xmin("U")
            x1 = self.xmax("U")
            xw = x1 - x0
            if p.x < x0 + xw * 0.4:
                p.x += xw * 0.02
            elif p.x > x1 - xw * 0.4:
                p.x -= xw * 0.02
            return p

        self.map_points(TITIEQ, f)
        self.get(TITIEQ).transform(translate(0, -self.ymin(TITIEQ)))
        self.crop(TITIEQ, 0, self.yctr("o"), 9000, 9000, 400, 0)
        xo = sorted(
            [
                p.x
                for p in self.points("o")
                if p.on_curve and abs(p.y - self.yctr("o")) < SW
            ]
        )
        xU = sorted([p.x for p in self.points(TITIEQ) if p.on_curve])
        if len(xo) >= 2:
            self.get(TITIEQ).transform(translate(xo[-2] - xU[0], 0))
        else:
            print(self.font, "titieq failed!")
        self.add("o", TITIEQ)
        self.get(TITIEQ).removeOverlap()
        self.get(TITIEQ).anchorPoints = [
            (a, b, max(x - SW / 2, 0), y) for a, b, x, y in self.get("o").anchorPoints
        ]
        # print(self.get(TITIEQ).anchorPoints)

        # zozeo
        self.copy("ʝ", Z_TAIL)
        self.get(Z_TAIL).unlinkRef()
        self.get(Z_TAIL).anchorPoints = []
        self.get(Z_TAIL).transform(translate(0, -180 if self.inter else -50))
        self.crop(Z_TAIL, -400, -900, 4000, 0)
        dx = self.be("ɿ") - self.be(Z_TAIL)
        self.get(Z_TAIL).transform(translate(dx, 0))

        self.copy("ɿ", ZOZEO)
        self.add(Z_TAIL, ZOZEO)
        self.get(ZOZEO).removeOverlap()

        # cecoa
        self.copy("c", CECOA)
        if self.inter:
            self.polycrop(
                CECOA,
                -50,
                -50,
                -50,
                self.ymax(CECOA),
                self.xmax(CECOA) * 0.7 + self.xmin(CECOA) * 0.3,
                self.ymax(CECOA),
                self.xctr(CECOA),
                self.yctr(CECOA),
                self.xmax(CECOA),
                self.yctr(CECOA),
                self.xmax(CECOA),
                self.ymin(CECOA),
            )

        # bubue
        if self.inter:
            self.copy(CECOA, BUBUE)
            self.scaled(BUBUE, -1, -1)
        else:
            self.copy("ɔ", BUBUE)

        # saqseoq
        self.copy("o", SAQSEOQ)

        # rairua
        self.copy("n", RAIRUA)
        if bridge:
            self.rect(RAIRUA, self.xmin("η") + SW / 2, 0, self.be("n"), BW)
        self.add_rdesc(RAIRUA)
        self.get(RAIRUA).removeOverlap()

        # laoliq
        self.copy("n", LAOLIQ)
        if bridge:
            self.rect(LAOLIQ, self.xmin("n") + SW / 2, 0, self.be("n"), BW)
        self.get(LAOLIQ).removeOverlap()
        self.dotbelow(LAOLIQ)

        # nhanhoq
        self.copy("ə", NHANHOQ)

        # jujuo
        self.copy("ɷ", JUJUO)
        self.vflip(JUJUO)
        c = self.xctr(JUJUO)
        if self.inter:
            self.crop(JUJUO, 0, 660, 2000, 2000, c, -100, c + 200, 300)
        else:
            self.crop(JUJUO, 0, 190, 2000, 2000, c, -100)

        # chichao
        self.copy("s", CHICHAO)
        self.hflip(CHICHAO)

        # shoshia
        self.copy(CHICHAO, SHOSHIA)
        self.long_rdesc(SHOSHIA)

        # wewa
        self.copy("s", WEWA)

        # aqaq
        self.copy(CECOA, AQAQ)
        self.long_rdesc(AQAQ)

        # gugui
        self.copy("ε", GUGUI)
        if self.inter:
            self.copy(JUJUO, GUGUI)
            self.scaled(GUGUI, -1, -1)

        # kikue
        self.copy(CECOA, KIKUE)
        self.dotbelow(KIKUE)

        # oaomo
        self.copy("·", OAOMO)

        # hehaq
        self.copy(FOFUAQ, HEHAQ)
        self.rect(HEHAQ, self.xmin(HEHAQ) + SW / 2, 0, self.xmax(HEHAQ) + 80, BW)
        self.get(HEHAQ).removeOverlap()

        self.copy(0x0301, GULAQTEI)
        self.get(GULAQTEI).glyphclass = "mark"
        self.copy(0x0303, SAQLAQTEI)
        self.get(SAQLAQTEI).glyphclass = "mark"
        self.font.save(self.font.fontname + ".sfd")
        try:
            self.copy(0x0311, JOLAQTEI)
        except KeyError:
            self.copy(0x0304, JOLAQTEI)
        self.get(JOLAQTEI).glyphclass = "mark"
        self.rot(JOLAQTEI, -25)
        self.get(JOLAQTEI).anchorPoints = [
            (a, b, x + 110, y - 70) for (a, b, x, y) in self.get(JOLAQTEI).anchorPoints
        ]
        for tgt in (IULAI, AILAI):
            self.copy(0x035C, tgt)
            glyph = self.get(tgt)
            l = glyph.layers[1]
            l.transform(translate(200, 0))
            glyph.layers[1] = l
            if self.inter:
                self.scaled(tgt, 0.75, -1.05)
            else:
                self.scaled(tgt, 0.70, -0.80)

        # PMARK
        self.copy(":", PMARK)
        self.scaled(PMARK, 0.8, 0.8)
        # QMARK
        self.copy(PMARK, QMARK)
        # SMARK
        # self.copy("–", SMARK)
        self.copy(",", SMARK)
        self.get(SMARK).transform(translate(200, 0))
        self.add(",", SMARK)
        self.get(SMARK).transform(translate(200, 0))
        self.add(",", SMARK)

        # stops
        self.stitch("]", "}", STOP1)
        self.get(STOP1).transform(translate(150, 0))
        self.copy(STOP1, STOP2)
        self.copy(STOP1, STOP3)
        self.add("·", STOP1)
        S = 200
        self.copy("·", 2)
        if SW > 50:
            self.scaled(2, 0.8, 0.8)
        self.copy(2, 1)
        self.get(1).transform(translate(0, S))
        self.add(2, 1)
        self.get(1).transform(translate(0, -S / 2))
        self.add(1, STOP2)
        self.get(1).transform(translate(0, S + S / 2))
        self.add(2, 1)
        self.get(1).transform(translate(0, -S))
        self.add(1, STOP3)

        # RAILAI
        self.copy("*", RAILAI)

        # DCNBSP
        self.copy("\xa0", DCNBSP)

        # cartouche height
        CH = 1600 if self.inter else 900

        self.copy("\u200b", START_CARTOUCHE)
        self.copy(" ", END_CARTOUCHE)
        ec = self.get(END_CARTOUCHE)
        ec.width = 240
        ct = fontforge.contour(1)
        ct.moveTo(0, CH + SW / 2)
        ct.quadraticTo(180, CH + SW / 2, 180, CH + SW / 2 - 100)
        ct.lineTo(180, 0)
        ec.foreground += ct
        ec.stroke("circular", SW, cap="butt")

        self.visited.add(END_CARTOUCHE)

        langs = ("latn", "dflt"), ("DFLT", "dflt")
        self.font.addLookup(
            "AddCartouche", "gsub_single", ("ignore_marks",), (("cart", langs),)
        )
        self.font.addLookupSubtable("AddCartouche", "AddCartouche1")
        for c in cartouchable:
            base = self.get(c)
            self.font.createChar(-1, cc := base.glyphname + "_c")
            self.copy(c, cc)
            self.rect(cc, 0, CH, base.width, CH + SW)
            self.get(cc).unlinkRef()
            base.addPosSub("AddCartouche1", cc)

        # Cartouche spaces
        self.get(0x20).addPosSub("AddCartouche1", "deraninbsp_c")
        self.get(0xA0).addPosSub("AddCartouche1", "deraninbsp_c")

        # Contextual substitution to start cartouches:
        # Rule: cartouche_start cartouchable @<Cartouchify>

        # Chaining rule:
        # cartouched | cartouchable @<Cartouchify> |

        names = " ".join(self.get(c).glyphname for c in cartouchable)
        names_c = " ".join(self.get(c).glyphname + "_c" for c in cartouchable)
        self.font.addLookup(
            "ContinueCartouche",
            "gsub_contextchain",
            ("ignore_marks",),
            (("rclt", langs),),
        )
        self.font.addContextualSubtable(
            "ContinueCartouche",
            "ContinueCartouche1",
            "class",
            f"1 | 1 @<AddCartouche> |",
            bclasses=(None, names_c),
            mclasses=(
                None,
                names,
            ),
            fclasses=(None,),
        )

        self.font.addLookup(
            "StartCartouche", "gsub_context", ("ignore_marks",), (("rclt", langs),)
        )
        self.font.addContextualSubtable(
            "StartCartouche",
            "StartCartouche1",
            "coverage",
            f"[deranistartcartouche] [{names}] @<AddCartouche>",
        )

        # Kerning
        for mark in "iulai", "ailai", "iulai_c", "ailai_c":
            for fofuaq in "fofuaq", "fofuaq_c":
                self.get(mark).addPosSub(
                    self.KERN_TABLE, fofuaq, -150, 0, 0, 0, 0, 0, 0, 0
                )
                self.get(fofuaq).addPosSub(
                    self.KERN_TABLE, mark, 0, 0, 0, 0, 250, 0, 0, 0
                )

        for k in list(self.visited):
            self.get(k).transform(skew(self.slant))

        self.font.descent = 300
        # fontforge.printSetup("pdf-file", "", 1300, 400)
        # self.font.printSample("fontsample", 60, sample())
        # print("Printed sample:", self.font.fontname)
        self.font.save(self.font.fontname + ".sfd")


def convert(path: str) -> str:
    font = fontforge.open(path)
    font.fontname = font.fontname.replace("FiraSans", "FiraSansToaq")
    font.fontname = font.fontname.replace("Inter", "Iqteo")
    Font(font).toaqify()
    return font.fontname + ".sfd"


def patch_font(path: str) -> None:
    if "Italic" not in path:
        return
    normal_path = path.replace("Italic", "").replace("-.", "-Regular.")
    italic = fontforge.open(path)
    normal = fontforge.open(normal_path)

    def find(font: Any, name: str) -> Optional[Any]:
        for g in font:
            if font[g].glyphname == name:
                return font[g]
        return None

    for base in "dudeo", "nhanhoq", "pipoq":
        for suffix in ("", "_c"):
            name = base + suffix
            ng = find(normal, name)
            ig = find(italic, name)
            ng.foreground = ig.foreground
            ng.transform(skew(-0.14))
            ng.width -= 60
            normal.save(normal_path)


def export_font(path: str) -> None:
    font = fontforge.open(path)
    font.generate(path.replace(".sfd", ".ttf"))


def is_input_ttf(path: str) -> bool:
    return (
        path.startswith("FiraSans-") or path.startswith("Inter-")
    ) and path.endswith(".ttf")


def inputs() -> List[str]:
    return [p for p in os.listdir() if is_input_ttf(p)]


def compress_originals() -> None:
    import zipfile

    paths = inputs()
    # Bundle all the ttf files in "paths" into a zip file and save it as "original.dat".
    with zipfile.ZipFile("original.dat", "w") as zf:
        for path in paths:
            zf.write(path, path)
    # Verify that the zip file contains all the ttf files.
    with zipfile.ZipFile("original.dat") as zf:
        assert set(zf.namelist()) == set(paths)
    # Remove the original files.
    for path in paths:
        os.remove(path)
    print(f"moved {len(paths)} ttf files into original.dat")


def extract_originals() -> None:
    import zipfile

    with zipfile.ZipFile("original.dat") as zf:
        zf.extractall(".")
    return inputs()


if __name__ == "__main__":
    if not os.path.exists("ttf"):
        os.makedirs("ttf")
    os.chdir("ttf")
    paths = inputs()
    flags = [x for x in sys.argv[1:] if x.startswith("--")]

    if "--compress" in flags:
        compress_originals()
        exit()

    paths = (
        [x for x in sys.argv[1:] if not x.startswith("--")]
        or inputs()
        or extract_originals()
        or exit("no paths found")
    )

    with Pool(8) as p:
        saved = p.map(convert, paths)
        print("patching")
        p.map(patch_font, saved)
        print("exporting")
        p.map(export_font, saved)

    if "--preview" in flags:
        print("previewing")
        # Save a sample image to "sample.png"
        im = Image.new("RGB", (800, 500), "#886688")
        draw = ImageDraw.Draw(im)
        iqteo = ImageFont.truetype("Iqteo-Regular.ttf", 100)
        firasans = ImageFont.truetype("FiraSansToaq-Regular.ttf", 120)
        draw.text((50, 50), "󱛃󱚲󱛍󱚺󱛂󱚷󱚸󱚶󱚹󱛍󱚲", font=iqteo, fill="white")
        draw.text((50, 200), "󱛃󱚲󱛍󱚺󱛂󱚷󱚸󱚶󱚹󱛍󱚲", font=firasans, fill="white")
        im.save("sample.png")
