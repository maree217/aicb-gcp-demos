#!/usr/bin/env python3
"""render_arch4_enterprise_multiagent.py -> arch-4-enterprise-multiagent.png (2400x1350)."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Canvas dimensions & paths
WIDTH, HEIGHT = 2400, 1350
OUT_SCRIPT = Path(__file__).resolve()

# Palette
WHITE = "#FFFFFF"
PANEL_BG = "#F8FAFC"
DARK_TEXT = "#0F172A"
MID_TEXT = "#475569"
MUTED_TEXT = "#64748B"
FOOTER_BG = "#1E293B"

# Border & status colors
BLUE_ACCENT = "#3B82F6"
BLUE_BG = "#EFF6FF"
BLUE_TEXT = "#1D4ED8"

GREEN_BORDER = "#10B981"
GREEN_BG = "#ECFDF5"
GREEN_BADGE_BG = "#DCFCE7"
GREEN_TEXT = "#065F46"

AMBER_BORDER = "#F59E0B"
AMBER_BG = "#FFFBEB"
AMBER_BADGE_BG = "#FEF3C7"
AMBER_TEXT = "#92400E"

GREY_BORDER = "#9CA3AF"
GREY_BG = "#F9FAFB"
GREY_BADGE_BG = "#E5E7EB"
GREY_TEXT = "#374151"

RED_BORDER = "#EF4444"
RED_BG = "#FEF2F2"
RED_BADGE_BG = "#FEE2E2"
RED_TEXT = "#991B1B"
RED_DARK = "#7F1D1D"


def load_font(size, bold=False):
    """Load robust system fonts on macOS with standard fallbacks."""
    candidates = (
        [
            ("/System/Library/Fonts/Helvetica.ttc", 1),
            ("/System/Library/Fonts/HelveticaNeue.ttc", 1),
            ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
            ("/Library/Fonts/Arial Bold.ttf", 0),
        ]
        if bold
        else [
            ("/System/Library/Fonts/Helvetica.ttc", 0),
            ("/System/Library/Fonts/HelveticaNeue.ttc", 0),
            ("/System/Library/Fonts/Supplemental/Arial.ttf", 0),
            ("/Library/Fonts/Arial.ttf", 0),
        ]
    )
    for path, idx in candidates:
        try:
            return ImageFont.truetype(path, size=size, index=idx)
        except (OSError, IndexError, ValueError):
            continue
    return ImageFont.load_default()


# Fonts
F_TITLE = load_font(40, True)
F_SUBTITLE = load_font(18, False)
F_COL_TITLE = load_font(23, True)
F_COL_SUB = load_font(14, False)
F_CARD_TITLE = load_font(19, True)
F_CARD_SUB = load_font(13, False)
F_BADGE = load_font(13, True)
F_BODY = load_font(14, False)
F_BODY_BOLD = load_font(14, True)
F_SMALL = load_font(12, False)
F_ITEM = load_font(19, False)
F_FOOTER = load_font(19, True)
F_FOOTER_SUB = load_font(15, False)


def wrap_text(draw, text, font, max_width):
    """Wrap text to fit within max_width in pixels."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = ""
        for word in words:
            trial = word if not current else f"{current} {word}"
            bbox = draw.textbbox((0, 0), trial, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def draw_dashed_rect(draw, box, radius, fill, outline, width=3, dash=12, gap=8):
    """Draw a rounded rectangle with dashed orthogonal perimeter and corner arcs."""
    x1, y1, x2, y2 = box
    if fill:
        draw.rounded_rectangle(box, radius=radius, fill=fill)
    for x in range(x1 + radius, x2 - radius, dash + gap):
        draw.line((x, y1, min(x + dash, x2 - radius), y1), fill=outline, width=width)
    for x in range(x1 + radius, x2 - radius, dash + gap):
        draw.line((x, y2, min(x + dash, x2 - radius), y2), fill=outline, width=width)
    for y in range(y1 + radius, y2 - radius, dash + gap):
        draw.line((x1, y, x1, min(y + dash, y2 - radius)), fill=outline, width=width)
    for y in range(y1 + radius, y2 - radius, dash + gap):
        draw.line((x2, y, x2, min(y + dash, y2 - radius)), fill=outline, width=width)
    draw.arc((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=outline, width=width)
    draw.arc((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 360, fill=outline, width=width)
    draw.arc((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=outline, width=width)
    draw.arc((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=outline, width=width)


def draw_badge(draw, x_right, y_top, text, bg, fg, border=None, font=F_BADGE, pad_x=9, pad_y=4):
    """Draw a status pill badge aligned to x_right."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    bw = tw + 2 * pad_x
    bh = th + 2 * pad_y
    bx1 = x_right - bw
    by1 = y_top
    bx2 = x_right
    by2 = y_top + bh
    draw.rounded_rectangle((bx1, by1, bx2, by2), radius=5, fill=bg, outline=border or fg, width=1)
    tx = bx1 + pad_x - bbox[0]
    ty = by1 + pad_y - bbox[1]
    draw.text((tx, ty), text, font=font, fill=fg)
    return (bx1, by1, bx2, by2)



OUT_IMAGE = OUT_SCRIPT.with_name("arch-4-enterprise-multiagent.png")


def center(draw, box, text, font, fill):
    x1, y1, x2, y2 = box
    lines = wrap_text(draw, text, font, x2 - x1 - 24)
    lh = font.size + 6
    y = y1 + ((y2 - y1) - lh * len(lines)) // 2
    for l in lines:
        w = draw.textbbox((0, 0), l, font=font)[2]
        draw.text(((x1 + x2 - w) // 2, y), l, font=font, fill=fill)
        y += lh


def row(draw, x1, x2, y1, y2, texts, bg, bd, fg=DARK_TEXT, font=None, gap=20, w=2):
    font = font or load_font(20, True)
    n = len(texts)
    bw = (x2 - x1 - gap * (n - 1)) / n
    boxes = []
    for i, t in enumerate(texts):
        b = (int(x1 + i * (bw + gap)), y1, int(x1 + i * (bw + gap) + bw), y2)
        draw.rounded_rectangle(b, radius=10, fill=bg, outline=bd, width=w)
        center(draw, b, t, font, fg)
        boxes.append(b)
    return boxes


def layer(draw, y1, y2, label, border, bg=PANEL_BG, w=2):
    draw.rounded_rectangle((65, y1, 1990, y2), radius=14, fill=bg, outline=border, width=w)
    draw.text((88, y1 + 16), label, font=load_font(23, True), fill=DARK_TEXT)


def render_image():
    im = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    d = ImageDraw.Draw(im)
    d.text((65, 38), "arch-4 \u2014 Governed enterprise multi-agent platform on GCP (target)", font=F_TITLE, fill=DARK_TEXT)
    X1, X2 = 88, 1967
    B = load_font(20, True)

    y = 112
    layer(d, y, y + 120, "Surfaces", BLUE_ACCENT)
    row(d, X1, X2, y + 54, y + 104, ["Gemini Enterprise app", "internal portal", "customer channels"], BLUE_BG, BLUE_ACCENT)

    y = 246
    layer(d, y, y + 176, "Agent marketplace & registry", BLUE_ACCENT)
    fb = row(d, X1, X2, y + 50, y + 100, ["templates", "build", "eval gate", "publish"], WHITE, BLUE_ACCENT, gap=70)
    for a, b in zip(fb, fb[1:]):
        cy = (a[1] + a[3]) // 2
        w = d.textbbox((0, 0), "->", font=B)[2]
        d.text(((a[2] + b[0] - w) // 2, cy - 14), "->", font=B, fill=BLUE_TEXT)
    row(d, X1, X2, y + 116, y + 162, ["Agent Registry (GA)", "Agent Gallery", "Workflow Builder no-code (GA)"], BLUE_BG, BLUE_ACCENT)

    y = 436
    layer(d, y, y + 150, "Control plane", RED_BORDER, RED_BG, 4)
    row(d, X1, X2, y + 54, y + 130, ["Agent Gateway (egress allow/deny)", "Agent Identity (SPIFFE)", "Model Armor guardrails", "human approval gate"], WHITE, RED_BORDER, RED_DARK)

    y = 600
    layer(d, y, y + 270, "Agents", GREEN_BORDER, GREEN_BG)
    ab = row(d, X1, X2, y + 54, y + 190, ["Research/KYC agent (ADK supervisor + sub-agents)", "Workflow agent with HITL (lending/disputes)", "Fin-crime triage agent", "Leakage agent (AICB demo)"], WHITE, GREEN_BORDER, GREEN_TEXT)
    ly = y + 226
    d.line((ab[0][0] + (ab[0][2]-ab[0][0])//2, ly, ab[-1][0] + (ab[-1][2]-ab[-1][0])//2, ly), fill=GREEN_BORDER, width=4)
    for b in ab:
        cx = (b[0] + b[2]) // 2
        d.line((cx, b[3], cx, ly), fill=GREEN_BORDER, width=4)
    cap = "A2A between agents"
    cf = load_font(19, True)
    tb = d.textbbox((0, 0), cap, font=cf)
    cx = (X1 + X2) // 2
    d.rectangle((cx - (tb[2]-tb[0])//2 - 14, ly - 16, cx + (tb[2]-tb[0])//2 + 14, ly + 16), fill=GREEN_BG)
    d.text((cx - (tb[2]-tb[0])//2, ly - 13), cap, font=cf, fill=GREEN_TEXT)

    y = 884
    layer(d, y, y + 186, "Models", GREY_BORDER)
    row(d, X1, X2, y + 50, y + 112, ["Gemini (Vertex)", "Claude on Vertex (London / EU multi-region)", "Third-party/open models"], WHITE, GREY_BORDER)
    cap = "portability = CTP exit plan"
    cf = load_font(19, True)
    d.text((cx - d.textbbox((0, 0), cap, font=cf)[2] // 2, y + 138), cap, font=cf, fill=GREY_TEXT)

    y = 1084
    layer(d, y, y + 176, "Tools & data", BLUE_ACCENT)
    row(d, X1, X2, y + 54, y + 150, ["MCP servers", "BigQuery / Dataplex", "Vertex AI Search (RAG)", "licensed data connectors"], BLUE_BG, BLUE_ACCENT)

    # Assurance bar
    bar = (2020, 112, 2335, 1260)
    d.rounded_rectangle(bar, radius=14, fill=AMBER_BG, outline=AMBER_BORDER, width=4)
    d.text((2042, 130), "Assurance", font=load_font(26, True), fill=AMBER_TEXT)
    items = ["Model inventory & risk tier (PRA SS1/23)", "Independent validation", "Eval: accuracy \u00b7 coherence \u00b7 hallucination, daily", "Audit logs + citations", "Observability (Cloud Trace)"]
    iy = 200
    for it in items:
        b = (2038, iy, 2317, iy + 170)
        d.rounded_rectangle(b, radius=10, fill=WHITE, outline=AMBER_BORDER, width=2)
        center(d, b, it, load_font(20, False), AMBER_TEXT)
        iy += 192

    d.rectangle((0, 1290, WIDTH, HEIGHT), fill=FOOTER_BG)
    d.text((65, 1308), "arch-4 \u00b7 target state \u00b7 AICB \u00b7 Oct 2026", font=F_FOOTER, fill=WHITE)
    im.save(OUT_IMAGE, "PNG", optimize=True)
    print(f"Generated {OUT_IMAGE} ({OUT_IMAGE.stat().st_size:,} bytes)")


if __name__ == "__main__":
    render_image()
