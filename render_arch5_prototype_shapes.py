#!/usr/bin/env python3
"""render_arch5_prototype_shapes.py -> arch-5-prototype-shapes.png (2400x1350)."""

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



OUT_IMAGE = OUT_SCRIPT.with_name("arch-5-prototype-shapes.png")

CARDS = [('A. Research / analyst multi-agent', 'ADK supervisor + sub-agents \u00b7 MCP data \u00b7 citations', 'adk-samples financial-advisor', 'Deutsche Bank (preview)'), ('B. Workflow agent with HITL', 'ADK sequential \u00b7 output_schema \u00b7 HITL pause \u00b7 LLM-judge gate \u00b7 Firestore checkpoint', 'small-business-loan-agent', 'Dojo chargeback agent'), ('C. Fin-crime / fraud triage', 'BigQuery + Dataplex \u00b7 agent over signals \u00b7 human decision \u00b7 audit', 'none public (B + safety-plugins)', 'HSBC (announced)'), ('D. Staff knowledge assistant', 'Gemini Enterprise \u00b7 Workflow Builder \u00b7 Vertex AI Search', 'rag-agent-search', 'Lloyds Athena, SIGNAL IDUNA'), ('E. Document-intensive analysis', 'ADK single agent \u00b7 multimodal Gemini \u00b7 batch', 'high-volume-document-analyzer', 'credit/KYC packs'), ('F. A2A mesh + governance', 'signed agent cards \u00b7 Agent Registry \u00b7 Agent Identity \u00b7 Gateway', 'a2a-samples sign_and_verify_agent_card', 'platform GA, no bank named')]
COLORS = [(BLUE_ACCENT, BLUE_BG), (GREEN_BORDER, GREEN_BG), (RED_BORDER, RED_BG), (BLUE_ACCENT, BLUE_BG), (AMBER_BORDER, AMBER_BG), (GREY_BORDER, GREY_BG)]


def render_image():
    im = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    d = ImageDraw.Draw(im)
    d.text((65, 38), "arch-5 \u2014 Six agent prototype shapes enterprises build on GCP", font=F_TITLE, fill=DARK_TEXT)
    cw, ch, gx, gy = 750, 560, 40, 40
    x0, y0 = 65, 125
    tf, lf, bf = load_font(30, True), load_font(18, True), load_font(22, False)
    for i, (name, stack, sample, ev) in enumerate(CARDS):
        c, r = i % 3, i // 3
        x1 = x0 + c * (cw + gx)
        y1 = y0 + r * (ch + gy)
        bd, bg = COLORS[i]
        d.rounded_rectangle((x1, y1, x1 + cw, y1 + ch), radius=16, fill=bg, outline=bd, width=3)
        y = y1 + 24
        for l in wrap_text(d, name, tf, cw - 50):
            d.text((x1 + 25, y), l, font=tf, fill=DARK_TEXT)
            y += 40
        y += 14
        for lab, txt in (("Stack", stack), ("Closest sample", sample), ("Evidence", ev)):
            d.text((x1 + 25, y), lab.upper(), font=lf, fill=MUTED_TEXT)
            y += 26
            for l in wrap_text(d, txt, bf, cw - 50):
                d.text((x1 + 25, y), l, font=bf, fill=DARK_TEXT)
                y += 31
            y += 18
    d.rectangle((0, 1290, WIDTH, HEIGHT), fill=FOOTER_BG)
    d.text((65, 1308), "arch-5 \u00b7 prototype shapes \u00b7 AICB \u00b7 Oct 2026", font=F_FOOTER, fill=WHITE)
    im.save(OUT_IMAGE, "PNG", optimize=True)
    print(f"Generated {OUT_IMAGE} ({OUT_IMAGE.stat().st_size:,} bytes)")


if __name__ == "__main__":
    render_image()
