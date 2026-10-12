"""Draw Munshi's cast as soft 3D ("clay") SVG avatars: the business owner and six AI workers.

Writes app/assets/avatars/<key>.svg. Pure SVG: radial-gradient shading gives the 3D look.
"""

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "app/assets/avatars"

# key, name, skin, hair colour, hair style, shirt colour, prop
CAST = [
    ("owner", "Kavya", "#C98E6B", "#2B1B14", "bun", "#E9EEF0", "chai"),
    ("researcher", "Riya", "#B7795A", "#1C1310", "long", "#5B7CFA", "magnifier"),
    ("reader", "Arjun", "#D2A07E", "#2E2019", "short", "#2FA36B", "glasses"),
    ("bookkeeper", "Meena", "#A86E4F", "#16100D", "bob", "#E2A23B", "ledger"),
    ("auditor", "Dev", "#8F5A3E", "#110C0A", "short", "#E36A50", "scale"),
    ("collector", "Sana", "#C48563", "#3A231A", "long", "#9B6BD8", "card"),
    ("briefer", "Kabir", "#B07455", "#1F1612", "curly", "#2F9FB0", "clipboard"),
]


def shade(hex_color: str, f: float) -> str:
    """Lighten (f>0) or darken (f<0) a hex colour."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    if f >= 0:
        r, g, b = (int(c + (255 - c) * f) for c in (r, g, b))
    else:
        r, g, b = (int(c * (1 + f)) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def grad(gid: str, base: str) -> str:
    return (f'<radialGradient id="{gid}" cx="35%" cy="30%" r="75%">'
            f'<stop offset="0" stop-color="{shade(base, 0.35)}"/><stop offset="0.6" stop-color="{base}"/>'
            f'<stop offset="1" stop-color="{shade(base, -0.35)}"/></radialGradient>')


def hair(style: str, color: str) -> tuple[str, str]:
    """(behind-head, on-top) shapes."""
    c = "url(#hair)"
    if style == "long":
        return (f'<path d="M50 72 Q48 30 80 26 Q112 30 110 72 L114 118 Q100 108 96 92 L64 92 Q60 108 46 118 Z" fill="{c}"/>',
                f'<path d="M52 66 Q56 34 80 32 Q104 34 108 66 Q96 50 80 48 Q64 50 52 66 Z" fill="{c}"/>')
    if style == "bob":
        return (f'<path d="M50 74 Q48 32 80 28 Q112 32 110 74 L108 96 Q80 104 52 96 Z" fill="{c}"/>',
                f'<path d="M52 66 Q58 34 80 32 Q102 34 108 66 Q92 46 66 52 Z" fill="{c}"/>')
    if style == "bun":
        return (f'<circle cx="80" cy="24" r="13" fill="{c}"/>',
                f'<path d="M52 64 Q56 32 80 30 Q104 32 108 64 Q96 46 80 46 Q64 46 52 64 Z" fill="{c}"/>')
    if style == "curly":
        top = "".join(f'<circle cx="{x}" cy="{y}" r="10" fill="{c}"/>'
                      for x, y in [(58, 50), (68, 40), (80, 36), (92, 40), (102, 50), (62, 46), (98, 46)])
        return ("", top)
    return ("", f'<path d="M53 62 Q56 34 80 32 Q104 34 107 62 Q100 48 80 46 Q60 48 53 62 Z" fill="{c}"/>')


PROPS = {
    "chai": ('<g transform="translate(108 120)"><rect x="0" y="0" width="20" height="22" rx="5" fill="#F4EBDD"/>'
             '<rect x="0" y="0" width="20" height="6" rx="3" fill="#C58B4E"/><path d="M20 6 q8 2 0 12" stroke="#F4EBDD" '
             'stroke-width="3" fill="none"/></g>'),
    "magnifier": ('<g transform="translate(104 108)"><circle cx="12" cy="12" r="11" fill="#DDE8FF" stroke="#1F2B5C" '
                  'stroke-width="4"/><path d="M20 20 L32 32" stroke="#1F2B5C" stroke-width="6" stroke-linecap="round"/></g>'),
    "glasses": ('<g fill="none" stroke="#14231B" stroke-width="3"><circle cx="69" cy="72" r="8"/><circle cx="91" cy="72" r="8"/>'
                '<path d="M77 72 h6"/></g><g transform="translate(104 116)"><rect width="24" height="30" rx="3" fill="#FFFFFF"/>'
                '<path d="M5 8h14M5 14h14M5 20h9" stroke="#9AA7A0" stroke-width="2"/></g>'),
    "ledger": ('<g transform="translate(100 114)"><rect width="32" height="26" rx="4" fill="#7A4A1E"/>'
               '<rect x="3" y="3" width="26" height="20" rx="2" fill="#FFF6E5"/><path d="M8 9h16M8 14h16M8 19h10" '
               'stroke="#B98A4C" stroke-width="2"/></g>'),
    "scale": ('<g transform="translate(100 108)" stroke="#5A3A12" stroke-width="3" fill="none"><path d="M16 0v30M2 8h28"/>'
              '<path d="M2 8 l-5 12 h10 z" fill="#F2B84B"/><path d="M30 8 l-5 12 h10 z" fill="#F2B84B"/>'
              '<path d="M8 32h16"/></g>'),
    "card": ('<g transform="translate(100 118)"><rect width="34" height="22" rx="4" fill="#1E2B26"/>'
             '<rect y="5" width="34" height="5" fill="#4FD18B"/><rect x="4" y="14" width="10" height="4" rx="1" fill="#C9D4CE"/></g>'),
    "clipboard": ('<g transform="translate(102 110)"><rect width="28" height="34" rx="4" fill="#8A5A2B"/>'
                  '<rect x="3" y="5" width="22" height="26" rx="2" fill="#FFFFFF"/><rect x="9" y="1" width="10" height="7" '
                  'rx="2" fill="#C9D4CE"/><path d="M7 15h14M7 20h14M7 25h8" stroke="#9AA7A0" stroke-width="2"/></g>'),
}


def avatar(key, skin, hair_color, style, shirt, prop) -> str:
    behind, top = hair(style, hair_color)
    defs = (grad("skin", skin) + grad("hair", hair_color) + grad("shirt", shirt)
            + '<radialGradient id="shadow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#000" stop-opacity=".35"/>'
              '<stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="160" height="160">
<defs>{defs}</defs>
<ellipse cx="80" cy="152" rx="52" ry="7" fill="url(#shadow)"/>
<path d="M30 152 Q30 112 80 108 Q130 112 130 152 Z" fill="url(#shirt)"/>
<path d="M68 108 Q80 120 92 108" fill="{shade(skin, -0.1)}"/>
<rect x="72" y="92" width="16" height="18" rx="6" fill="{shade(skin, -0.15)}"/>
{behind}
<ellipse cx="80" cy="70" rx="27" ry="30" fill="url(#skin)"/>
<ellipse cx="53" cy="72" rx="5" ry="7" fill="{shade(skin, -0.1)}"/><ellipse cx="107" cy="72" rx="5" ry="7" fill="{shade(skin, -0.1)}"/>
{top}
<ellipse cx="69" cy="73" rx="3.2" ry="3.8" fill="#1B1210"/><ellipse cx="91" cy="73" rx="3.2" ry="3.8" fill="#1B1210"/>
<circle cx="70" cy="72" r="1" fill="#FFFFFF"/><circle cx="92" cy="72" r="1" fill="#FFFFFF"/>
<ellipse cx="62" cy="84" rx="5" ry="3" fill="#E58C7A" opacity=".45"/><ellipse cx="98" cy="84" rx="5" ry="3" fill="#E58C7A" opacity=".45"/>
<path d="M72 86 Q80 93 88 86" stroke="#6B2E22" stroke-width="2.6" fill="none" stroke-linecap="round"/>
{PROPS[prop]}
</svg>'''


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for key, name, skin, hair_color, style, shirt, prop in CAST:
        (OUT / f"{key}.svg").write_text(avatar(key, skin, hair_color, style, shirt, prop), encoding="utf-8")
    print(f"{len(CAST)} avatars -> {OUT}")


if __name__ == "__main__":
    main()
