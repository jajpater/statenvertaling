#!/usr/bin/env python3
"""repareer_versificatie.py — maakt de DutSVV-conversie af.

convert_versification.py hernummert verzen waarvan de [HH:VV]-markering aan
het BEGIN staat. Maar waar de Nederlandse telling één Engels vers in tweeën
deelt, staat de markering MIDDENIN het vers. Zulke verzen moeten gesplitst
worden, niet hernummerd. Gebeurt dat niet, dan blijft het tweede versnummer
leeg: in de Psalmen is dat het opschrift-probleem (vers 1 bevat opschrift én
vers 2, vers 2 is leeg).

Daarnaast komt het omgekeerde één keer voor: twee Engelse verzen die in de
Nederlandse telling één vers zijn, en na conversie hetzelfde nummer dragen.
Die moeten samengevoegd worden.

    python3 repareer_versificatie.py STV.osis.xml STV.osis.xml

Het script is idempotent: een tweede run vindt niets meer te doen.
"""
import re
import sys
from collections import Counter, defaultdict

VERS = re.compile(r'<verse osisID="([^"]+)">(.*?)</verse>', re.S)
MARK = re.compile(r'\s*\[(\d+):(\d+)\]\s*')
NOOT = re.compile(r'<note>.*?</note>', re.S)
CATCH = re.compile(r'<catchWord>(.*?)</catchWord>', re.S)


def kaal(xml: str) -> str:
    """Leestekst zonder tags, voor het matchen van catchWords."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", xml)).strip().lower()


def verdeel_noten(segmenten: list[str]) -> list[str]:
    """Noten staan achteraan het oorspronkelijke vers. Hang elke noot aan het
    segment waarin zijn catchWord voorkomt; lukt dat niet, laat hem staan."""
    noten = NOOT.findall(segmenten[-1])
    if not noten or len(segmenten) < 2:
        return segmenten
    romp = [NOOT.sub("", s) for s in segmenten]
    teksten = [kaal(s) for s in romp]
    bij = [[] for _ in segmenten]
    for noot in noten:
        cw = CATCH.search(noot)
        doel = len(segmenten) - 1
        if cw:
            naald = kaal(cw.group(1)).rstrip(" ,;:.")
            for i, t in enumerate(teksten):
                if naald and naald in t:
                    doel = i
                    break
        bij[doel].append(noot)
    return [romp[i].rstrip() + "".join(bij[i]) for i in range(len(segmenten))]


def splits_verzen(inhoud: str):
    """Splitst verzen met een markering middenin. Geeft (nieuwe inhoud,
    verplaatsingen) waarbij verplaatsingen de segmenten zijn die in een ander
    hoofdstuk thuishoren: {(boek, hoofdstuk): [(versnr, xml), ...]}."""
    verplaats = defaultdict(list)
    gesplitst = 0

    def vervang(m):
        nonlocal gesplitst
        oid, lijf = m.group(1), m.group(2)
        marks = list(MARK.finditer(lijf))
        marks = [x for x in marks if x.start() > 0]
        if not marks:
            return m.group(0)
        gesplitst += 1
        boek, hfd, _ = oid.rsplit(".", 2)

        stukken, grenzen = [], [0] + [x.start() for x in marks] + [len(lijf)]
        for i in range(len(grenzen) - 1):
            begin = grenzen[i]
            if i > 0:
                begin = marks[i - 1].end()
            stukken.append(lijf[begin:grenzen[i + 1]])
        stukken = verdeel_noten(stukken)

        uit = [f'<verse osisID="{oid}">{stukken[0]}</verse>']
        for i, x in enumerate(marks, start=1):
            nieuw_hfd, nieuw_vers = str(int(x.group(1))), str(int(x.group(2)))
            xml = f'<verse osisID="{boek}.{nieuw_hfd}.{nieuw_vers}">{stukken[i]}</verse>'
            if nieuw_hfd == hfd:
                uit.append(xml)
            else:
                verplaats[(boek, nieuw_hfd)].append((int(nieuw_vers), xml))
        return "".join(uit)

    return VERS.sub(vervang, inhoud), verplaats, gesplitst


def voeg_in(inhoud: str, verplaats: dict) -> tuple[str, int]:
    """Zet verplaatste verzen vooraan in het juiste hoofdstuk."""
    n = 0
    for (boek, hfd), items in verplaats.items():
        kop = f'<chapter osisID="{boek}.{hfd}">'
        i = inhoud.find(kop)
        if i < 0:
            print(f"  LET OP: hoofdstuk {boek}.{hfd} niet gevonden", file=sys.stderr)
            continue
        i += len(kop)
        for _, xml in sorted(items):
            inhoud = inhoud[:i] + xml + inhoud[i:]
            n += 1
    return inhoud, n


def voeg_samen(inhoud: str) -> tuple[str, int]:
    """Twee opeenvolgende verzen met hetzelfde osisID worden één vers."""
    ids = VERS.findall(inhoud)
    dubbel = {k for k, c in Counter(i for i, _ in ids).items() if c > 1}
    n = 0
    for oid in sorted(dubbel):
        patroon = re.compile(
            rf'<verse osisID="{re.escape(oid)}">(.*?)</verse>\s*'
            rf'<verse osisID="{re.escape(oid)}">(.*?)</verse>', re.S)

        def samen(m):
            nonlocal n
            n += 1
            eerste = m.group(1).rstrip()
            noten = NOOT.findall(eerste)
            romp = NOOT.sub("", eerste).rstrip()
            return f'<verse osisID="{oid}">{romp} {m.group(2).lstrip()}{"".join(noten)}</verse>'

        inhoud, k = patroon.subn(samen, inhoud)
        while k:
            inhoud, k = patroon.subn(samen, inhoud)
    return inhoud, n


def controleer(inhoud: str) -> None:
    ids = [i for i, _ in VERS.findall(inhoud)]
    dubbel = [k for k, c in Counter(ids).items() if c > 1]
    per = defaultdict(list)
    for i in ids:
        b, c, v = i.rsplit(".", 2)
        per[(b, int(c))].append(int(v))
    gaten = [(b, c, sorted(set(range(1, max(v) + 1)) - set(v))) for (b, c), v in per.items()
             if set(range(1, max(v) + 1)) - set(v)]
    rest = len([1 for _, lijf in VERS.findall(inhoud)
                if any(m.start() > 0 for m in MARK.finditer(lijf))])
    leeg = [i for i, lijf in VERS.findall(inhoud) if not kaal(NOOT.sub("", lijf))]
    print(f"\ncontrole: {len(ids)} verzen")
    print(f"  dubbele osisID's:        {len(dubbel)} {sorted(dubbel)[:5] if dubbel else ''}")
    print(f"  hoofdstukken met gaten:  {len(gaten)} {gaten[:5] if gaten else ''}")
    print(f"  resterende markeringen:  {rest}")
    print(f"  lege verzen:             {len(leeg)} {leeg[:5] if leeg else ''}")


def main() -> int:
    bron = sys.argv[1] if len(sys.argv) > 1 else "STV.osis.xml"
    doel = sys.argv[2] if len(sys.argv) > 2 else "STV.osis.xml"
    inhoud = open(bron, encoding="utf-8").read()
    print(f"gelezen: {bron} ({len(inhoud)/1e6:.1f} MB)")

    inhoud, verplaats, n_split = splits_verzen(inhoud)
    inhoud, n_verpl = voeg_in(inhoud, verplaats)
    inhoud, n_samen = voeg_samen(inhoud)

    print(f"  gesplitste verzen:            {n_split}")
    print(f"  naar ander hoofdstuk verhuisd:{n_verpl}")
    print(f"  samengevoegde verzen:         {n_samen}")
    controleer(inhoud)

    open(doel, "w", encoding="utf-8").write(inhoud)
    print(f"\ngeschreven: {doel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
