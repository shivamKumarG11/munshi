"""Visual building blocks for the Munshi app: theme CSS, logos, 3D tiles, worker floor."""

import base64
import re
from decimal import Decimal
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"


def _data_uri(name: str) -> str:
    path = ASSETS / name
    mime = {".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp"}[path.suffix]
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


LOGO = {
    "neatlogs": _data_uri("neatlogs.png"),
    "entire": _data_uri("entire.svg"),
    "crustdata": _data_uri("crustdata.svg"),
    "dodo": _data_uri("dodo-payments.webp"),
}


def inr(x, sign: bool = False) -> str:
    """Indian digit grouping: 1,41,600."""
    x = Decimal(str(x))
    neg = x < 0
    s = str(abs(x).quantize(Decimal("1")))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        s = f"{head},{tail}"
    prefix = "−" if neg else ("+" if sign else "")
    return f"{prefix}₹{s}"


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500&family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
:root { --bg:#0E1613; --tile:#1A2621; --tile2:#22322B; --edge:#0B110E; --ink:#EEF3EF; --muted:#A9B8B0;
        --green:#4FD18B; --green-edge:#2E8F5C; --amber:#F2B84B; --amber-bg:#2E2715; --red:#FF8C7A; --red-bg:#3A1D19; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] { background: var(--bg) !important; color: var(--ink); }
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] div, [data-testid="stAppViewContainer"] span:not([data-testid="stIconMaterial"]),
[data-testid="stAppViewContainer"] button, [data-testid="stAppViewContainer"] input, [data-testid="stAppViewContainer"] label { font-family: 'IBM Plex Sans', system-ui, sans-serif; }
[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
[data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stAppDeployButton"], [data-testid="stMainMenu"] { display: none !important; }
[data-testid="stNavSectionHeader"], [data-testid="stTopNavLinkContainer"] a span { font-size: 15px; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 4.2rem; max-width: 1240px; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; color: var(--ink) !important; letter-spacing: -0.01em; }
.mono { font-family: 'IBM Plex Mono', monospace !important; }
.muted { color: var(--muted); }
.hero { text-align:center; padding: 18px 0 6px; }
.hero h1 { font-size: 58px; line-height: 1.05; margin: 0 0 12px; }
.hero p { font-size: 19px; color: var(--muted); margin: 0; }
.center { text-align:center; }
.title { font-family:'Space Grotesk',sans-serif; font-size: 38px; font-weight: 700; margin: 6px 0 4px; }
.sub { font-size: 17px; color: var(--muted); margin: 0 0 18px; }
.floor-wrap { perspective: 1400px; display:flex; justify-content:center; padding: 30px 0 10px; }
.floor { transform: rotateX(22deg); transform-style: preserve-3d; display:flex; align-items:flex-end; gap:16px;
         padding: 36px 40px 50px; border-radius: 28px; background:#15201C;
         box-shadow: 0 2px 0 #24332D inset, 0 40px 80px rgba(0,0,0,.55); }
.worker { display:flex; flex-direction:column; align-items:center; gap:9px; width:112px; }
.block { width:92px; height:92px; border-radius:22px; background:var(--tile2); border-bottom:8px solid #13201A;
         display:flex; align-items:center; justify-content:center; box-shadow:0 16px 24px rgba(0,0,0,.45); transition: all .3s; }
.block.amber { background:#2A2616; border-bottom-color:#17140A; }
.block.done { box-shadow: 0 0 0 3px var(--green), 0 16px 24px rgba(0,0,0,.45); }
.block.active { box-shadow: 0 0 0 3px var(--amber), 0 0 30px rgba(242,184,75,.45); transform: translateY(-8px); }
.block.final { width:108px; height:108px; background:var(--green); border-bottom:10px solid var(--green-edge);
               flex-direction:column; box-shadow:0 20px 36px rgba(79,209,139,.35); color:#0E1613; }
.wname { font-weight:600; font-size:15px; }
.wnote { font-size:12px; color:var(--muted); text-align:center; }
.chip { display:inline-flex; align-items:center; gap:6px; padding:4px 8px; border-radius:6px; background:#2B3A34; font-size:11px; color:var(--ink); }
.chip.light { background:var(--ink); color:#0E1613; font-weight:700; letter-spacing:.04em; }
.chip img { height:11px; }
.arrow { margin-bottom:70px; }
.tile { padding:24px; border-radius:22px; background:var(--tile); border-bottom:9px solid var(--edge);
        box-shadow:0 22px 34px rgba(0,0,0,.45); }
.tile.tilt { transform: perspective(1200px) rotateX(8deg); }
.tile .label { font-size:15px; color:var(--muted); }
.tile .big { font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:32px; margin-top:6px; white-space:nowrap; }
.tile.red { background:var(--red-bg); border-bottom-color:#1E0D0B; } .tile.red .big { color:var(--red); }
.tile.amber { background:var(--amber-bg); border-bottom-color:#17130A; } .tile.amber .big { color:var(--amber); }
.tile.green { background:var(--green); border-bottom-color:var(--green-edge); color:#0E1613; }
.tile.green .label { color:#0E1613; font-weight:600; }
.pills { display:flex; justify-content:center; gap:12px; flex-wrap:wrap; }
.pill { display:flex; align-items:center; gap:10px; padding:10px 14px; border-radius:14px; background:var(--tile);
        border-bottom:4px solid var(--edge); font-weight:600; font-size:14px; }
.dot { width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; color:#0E1613; }
.dot.g { background:var(--green); } .dot.a { background:var(--amber); } .dot.w { background:#3A4C45; color:var(--ink); }
.gap-row { display:flex; align-items:center; justify-content:center; gap:22px; flex-wrap:wrap; perspective:1400px; }
.cause { width:340px; padding:16px 18px; border-radius:18px; background:var(--amber-bg); border-bottom:7px solid #17130A;
         display:flex; align-items:center; gap:14px; box-shadow:0 18px 30px rgba(0,0,0,.45); margin-bottom:12px; }
.cause .amt { font-family:'IBM Plex Mono',monospace; font-size:19px; color:var(--amber); min-width:88px; }
.footer-note { display:flex; align-items:center; justify-content:center; gap:10px; color:var(--muted); font-size:14px; padding:14px 0; }
.footer-note img { width:22px; height:22px; border-radius:6px; }
.why { padding:22px; border-radius:20px; background:var(--ink); color:#0E1613; border-bottom:8px solid var(--muted); }
.why .h { font-family:'Space Grotesk',sans-serif; font-size:24px; font-weight:700; line-height:1.2; margin:6px 0 14px; }
.why .k { font-size:12px; font-weight:600; color:#3E4A44; letter-spacing:.05em; }
.why .step { display:flex; gap:10px; align-items:center; font-size:15px; margin:8px 0; }
.why .n { width:26px; height:26px; border-radius:8px; background:#0E1613; color:var(--ink); display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; }
.why .warn { padding:12px; border-radius:12px; background:#FBF1DC; color:#6B4708; font-size:14px; margin-top:12px; }
.card { padding:24px; border-radius:22px; background:var(--tile); border-bottom:9px solid var(--edge);
        box-shadow:0 22px 32px rgba(0,0,0,.42); margin-bottom:8px; }
.card .tag { display:inline-block; padding:5px 10px; border-radius:8px; font-size:13px; font-weight:600; }
.tag.g { background:#22322B; color:#8FE3B5; } .tag.r { background:var(--red-bg); color:var(--red); } .tag.a { background:#3A3018; color:var(--amber); }
.card .who { font-family:'Space Grotesk',sans-serif; font-size:24px; font-weight:700; margin:12px 0 2px; }
.card .what { font-size:14px; color:var(--muted); }
.card .amt { font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:32px; margin-top:10px; }
.bar { height:12px; border-radius:6px; }
.vs { display:grid; grid-template-columns:1fr 1fr; gap:24px; perspective:1400px; }
.vs .side { padding:26px; border-radius:24px; }
.vs .v1 { background:#2A1714; border-bottom:10px solid #160B09; transform: rotateY(6deg); }
.vs .v2 { background:var(--green); color:#0E1613; border-bottom:10px solid var(--green-edge); transform: rotateY(-6deg); }
.vs .nums { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:14px; }
.vs .num { font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:28px; }
.vs .v1 .num { color:var(--red); } .vs .v1 .cap { color:#F3B4A9; font-size:13px; } .vs .v2 .cap { font-size:13px; font-weight:600; }
/* Streamlit widgets in the dark theme */
.stButton > button[kind="primary"] { background: var(--green); color:#0E1613; border:0; font-weight:700; border-radius:14px;
        padding: 0.7rem 1.4rem; box-shadow: 0 6px 0 var(--green-edge); }
.stButton > button p, [data-testid="stLinkButton"] p { font-size: 16px !important; font-weight: 700 !important; }
.stButton > button[kind="secondary"] p { font-weight: 500 !important; }
.spacer { height: 22px; }
.stButton > button[kind="primary"]:hover { background:#6BDCA0; color:#0E1613; }
.stButton > button[kind="secondary"] { background: transparent; color: var(--ink); border:1px solid #3A4C45; border-radius:14px; }
[data-testid="stChatMessage"] { background: #15201C; border-radius: 14px; }
[data-testid="stDataFrame"] { border-radius: 16px; overflow: hidden; }
</style>
"""

CHECK_PATH = '<path d="M5 12l5 5L20 7"/>'


ICONS = {
    "research": '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>',
    "read": '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "book": '<path d="M8 7h11M8 12h11M8 17h11"/><path d="M4 7h.01M4 12h.01M4 17h.01" stroke-width="3"/>',
    "audit": '<path d="M12 3v18M5 7h14M5 7l-3 7h6zM19 7l-3 7h6z"/>',
    "collect": '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18M7 15h4"/>',
    "brief": '<path d="M6 3h9l3 3v15H6z"/><path d="M9 10h6M9 14h6"/>',
}

WORKERS = [
    # key, name, icon, badge html, matching progress steps
    ("research", "Researcher", "research", '<span class="chip light">SEC EDGAR</span>', ["research"]),
    ("reader", "Reader", "read", '<span class="chip">Nova · Claude</span>', ["read"]),
    ("bookkeeper", "Bookkeeper", "book", f'<span class="chip"><img src="{LOGO["crustdata"]}" alt="Crustdata"></span>', ["match", "post"]),
    ("auditor", "Auditor", "audit", '<span class="wnote">matches the bank</span>', ["verify", "gap_hunt"]),
    ("collector", "Collector", "collect", f'<span class="chip"><img src="{LOGO["dodo"]}" alt="Dodo Payments"></span>', ["actions"]),
    ("briefer", "Briefer", "brief", '<span class="wnote">writes your brief</span>', ["brief"]),
]


def svg_img(inner: str, size: int, color: str, stroke: float = 1.8, box: str = "0 0 24 24", cls: str = "") -> str:
    """Inline SVG is stripped by st.html, so icons are rendered as <img> data URIs."""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="{box}" fill="none" '
           f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>')
    uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    return f'<img src="{uri}" width="{size}" height="{size}" alt="" class="{cls}">'


def _svg(icon: str, color: str = "#8FE3B5") -> str:
    return svg_img(ICONS[icon], 38, color)


CHECK = svg_img(CHECK_PATH, 14, "#0E1613", 3)
CHECK_BIG = svg_img(CHECK_PATH, 30, "#0E1613", 2.6)
ARROW = svg_img('<path d="M2 10h22M18 4l6 6-6 6"/>', 28, "#4FD18B", 2, "0 0 28 20", "arrow")


def floor(states: dict[str, str] | None = None, final_text: str = "₹0 off", final_on: bool = True) -> str:
    """The 3D team floor. states: worker key -> '' | 'active' | 'done'."""
    states = states or {}
    parts = ['<div class="floor-wrap"><div class="floor">']
    parts.append('<div class="worker"><div class="block" style="background:#EEF3EF;border-bottom-color:#A9B8B0">'
                 + _svg("brief", "#0E1613") + '</div><span class="wname">Your month</span>'
                   '<span class="wnote">bank + bills</span></div>' + ARROW)
    for key, name, icon, badge, _ in WORKERS:
        cls = "block" + (" amber" if key == "auditor" else "") + (f" {states[key]}" if states.get(key) else "")
        color = "#F2B84B" if key == "auditor" else "#8FE3B5"
        parts.append(f'<div class="worker"><div class="{cls}">{_svg(icon, color)}</div>'
                     f'<span class="wname">{name}</span>{badge}</div>')
    final_style = "" if final_on else ' style="opacity:.35"'
    parts.append(ARROW + f'<div class="worker"{final_style}><div class="block final">{CHECK_BIG}'
                 f'<span class="mono" style="font-size:14px">{final_text}</span></div>'
                 f'<span class="wname">Closed books</span><span class="chip"><img src="{LOGO["entire"]}" alt="Entire"></span></div>')
    parts.append("</div></div>")
    return "".join(parts)


def pills(states: dict[str, str]) -> str:
    out = ['<div class="pills">']
    for key, name, *_ in WORKERS:
        s = states.get(key, "")
        dot = {"done": f'<span class="dot g">{CHECK}</span>', "active": '<span class="dot a">…</span>',
               "warn": '<span class="dot a">!</span>'}.get(s, '<span class="dot w">·</span>')
        out.append(f'<div class="pill">{dot}{name}</div>')
    out.append("</div>")
    return "".join(out)


def note(text: str, logo: str | None = "neatlogs") -> str:
    img = f'<img src="{LOGO[logo]}" alt="{logo}">' if logo else ""
    return f'<div class="footer-note">{img}<span>{text}</span></div>'


def tile(label: str, value: str, kind: str = "", tilt: bool = True) -> str:
    return f'<div class="tile {kind} {"tilt" if tilt else ""}"><div class="label">{label}</div><div class="big">{value}</div></div>'
