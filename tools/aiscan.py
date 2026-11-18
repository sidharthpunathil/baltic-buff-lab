"""AI-marks scanner.
Layer A (watermarks-remover's deterministic layer): invisible Unicode, exotic spaces, bidi, tag chars.
Layer B (humanizer + copywriting tell lists): dashes, contrast reveals, stock phrases, AI vocabulary.
Usage: python3 -I aiscan.py [--clean] FILE...   (--clean fixes Layer A only; prose tells are fixed by hand)
"""
import re
import sys
import unicodedata

INVISIBLE = {
    **{c: "zero-width/format" for c in range(0x200B, 0x2010)},
    **{c: "bidi control" for c in list(range(0x202A, 0x202F)) + list(range(0x2066, 0x206A))},
    **{c: "word joiner/invisible op" for c in range(0x2060, 0x2065)},
    0xFEFF: "BOM / zero-width no-break",
    0x00AD: "soft hyphen",
    0x180E: "mongolian vowel separator",
    **{c: "unicode tag char" for c in range(0xE0000, 0xE0080)},
    **{c: "variation selector" for c in range(0xFE00, 0xFE10)},
}
SPACES = {0x00A0: "no-break space", 0x202F: "narrow nbsp", 0x205F: "math space", 0x3000: "ideographic space",
          **{c: "typographic space" for c in range(0x2000, 0x200B)}}

TELLS = [
    (r"—|–", "dash (em/en)"),
    (r"\bnot (just|only|merely)\b", "not-just contrast"),
    (r"\b(it'?s|it’s|this is) not\b[^.]{0,60}\b(it'?s|it’s)\b", "it's-not-X-it's-Y"),
    (r"\b(delve|tapestry|testament|pivotal|seamless(ly)?|robust|unlock|streamline|leverage|showcas\w*|underscor\w*|meticulous\w*|vibrant|intricate|landscape|crucial|game-?changer|elevate)\b", "AI vocabulary"),
    (r"\b(let'?s dive|here'?s the thing|in today'?s|at its core|the real question|it'?s worth noting|in conclusion|whether you'?re)\b", "stock phrase"),
    (r"\b(serves as|stands as|boasts)\b", "copula avoidance"),
    (r"\?\s*(Honestly|The result|The answer)\b|\bThe result\?", "self-answered question"),
    (r"!", "exclamation"),
    (r"\b(I hope this helps|let me know|Great question|Certainly)\b", "chatbot residue"),
]


def strip_markup(s):
    s = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"`[^`]*`", " ", s)  # inline code
    s = re.sub(r"```.*?```", " ", s, flags=re.S)
    return s


def scan(path, clean=False):
    raw = open(path, encoding="utf-8").read()
    hits = []
    out = []
    for i, ch in enumerate(raw):
        cp = ord(ch)
        if cp in INVISIBLE:
            hits.append(("A", f"U+{cp:04X} {INVISIBLE[cp]}", raw[max(0, i - 20):i + 20]))
            if clean:
                continue
        elif cp in SPACES:
            hits.append(("A", f"U+{cp:04X} {SPACES[cp]}", raw[max(0, i - 20):i + 20]))
            if clean:
                out.append(" ")
                continue
        out.append(ch)
    if clean and hits:
        open(path, "w", encoding="utf-8").write("".join(out))
    if unicodedata.normalize("NFC", raw) != raw:
        hits.append(("A", "not NFC-normalized", ""))
    prose = strip_markup(raw) if path.endswith((".html", ".md")) else ""
    for line in prose.splitlines():
        for pat, name in TELLS:
            for m in re.finditer(pat, line, flags=re.I):
                if name == "exclamation" and re.search(r"(!=|!\[|<!)", line):
                    continue
                hits.append(("B", name, line.strip()[:110]))
    return hits


if __name__ == "__main__":
    clean = "--clean" in sys.argv
    total = 0
    for p in [a for a in sys.argv[1:] if a != "--clean"]:
        h = scan(p, clean)
        total += len(h)
        if h:
            print(f"\n## {p} ({len(h)})")
            for layer, what, ctx in h:
                print(f"  [{layer}] {what}: {ctx!r}")
    print(f"\nTOTAL findings: {total}{' (layer A cleaned)' if clean else ''}")
