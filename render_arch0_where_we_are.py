#!/usr/bin/env python3
"""
render_arch0_where_we_are.py
Architecture State Diagram: "Where we are — AICB on GCP (10 Oct 2026)"
Renders high-resolution 2400x1350 PNG matching arch-1/2/3 visual doctrine.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Canvas dimensions & paths
WIDTH, HEIGHT = 2400, 1350
OUT_SCRIPT = Path(__file__).resolve()
OUT_IMAGE = OUT_SCRIPT.with_name("arch-0-where-we-are.png")

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


def render_image():
    im = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(im)

    # ==========================================
    # 1. HEADER & TITLE
    # ==========================================
    draw.text((65, 38), "Where we are — AICB on GCP (10 Oct 2026)", font=F_TITLE, fill=DARK_TEXT)

    # ==========================================
    # 2. LEGEND ROW (Top Right)
    # ==========================================
    legend_items = [
        ("DONE / DONE LOCAL", GREEN_BG, GREEN_BORDER, GREEN_TEXT, False),
        ("PARTIAL / TODO", AMBER_BG, AMBER_BORDER, AMBER_TEXT, False),
        ("NOT STARTED", GREY_BG, GREY_BORDER, GREY_TEXT, False),
        ("GAP (ENTERPRISE)", RED_BG, RED_BORDER, RED_TEXT, True),
    ]

    leg_x_end = 2335
    leg_y = 52
    chip_h = 32
    for label, bg, border, fg, is_dashed in reversed(legend_items):
        tbox = draw.textbbox((0, 0), label, font=F_BADGE)
        tw = tbox[2] - tbox[0]
        cw = tw + 44
        cx1 = leg_x_end - cw
        cx2 = leg_x_end
        cy1 = leg_y
        cy2 = leg_y + chip_h

        if is_dashed:
            draw_dashed_rect(draw, (cx1, cy1, cx2, cy2), radius=7, fill=bg, outline=border, width=2, dash=6, gap=4)
        else:
            draw.rounded_rectangle((cx1, cy1, cx2, cy2), radius=7, fill=bg, outline=border, width=2)

        # Dot indicator
        dot_r = 5
        dot_cx = cx1 + 16
        dot_cy = cy1 + chip_h // 2
        draw.ellipse((dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r), fill=border)

        tx = cx1 + 28 - tbox[0]
        ty = cy1 + (chip_h - (tbox[3] - tbox[1])) // 2 - tbox[1]
        draw.text((tx, ty), label, font=F_BADGE, fill=fg)

        leg_x_end = cx1 - 14

    # ==========================================
    # 3. FOUR COLUMN GEOMETRY
    # ==========================================
    col_w = 548
    col_gap = 26
    start_x = 65
    cols_x = [(start_x + i * (col_w + col_gap), start_x + i * (col_w + col_gap) + col_w) for i in range(4)]

    y_header_top = 138
    y_header_h = 86
    y_header_bottom = y_header_top + y_header_h
    y_content_top = 238
    y_content_bottom = 836

    # Header specs for 4 columns
    headers_meta = [
        ("arch-1 Operator estate", "", BLUE_ACCENT, BLUE_BG),
        ("arch-2 Revenue Leakage Sprint", "", BLUE_ACCENT, BLUE_BG),
        ("arch-3 Voice + white-label", "", BLUE_ACCENT, BLUE_BG),
        ("Missing: enterprise multi-agent layer", "", RED_BORDER, RED_BG),
    ]

    for i, (col_x1, col_x2) in enumerate(cols_x):
        title, sub, border_col, bg_col = headers_meta[i]
        hb = (col_x1, y_header_top, col_x2, y_header_bottom)
        if i == 3:
            draw_dashed_rect(draw, hb, radius=12, fill=bg_col, outline=border_col, width=3, dash=10, gap=6)
            draw.text((col_x1 + 18, y_header_top + 29), title, font=F_COL_TITLE, fill=RED_TEXT)
        else:
            draw.rounded_rectangle(hb, radius=12, fill=PANEL_BG, outline=border_col, width=2)
            draw.text((col_x1 + 18, y_header_top + 29), title, font=F_COL_TITLE, fill=DARK_TEXT)

    # Col 4 Outer Framing: Dashed red border around entire Col 4 content area
    c4_x1, c4_x2 = cols_x[3]
    draw_dashed_rect(
        draw,
        (c4_x1, y_content_top - 6, c4_x2, y_content_bottom + 4),
        radius=14,
        fill="#FFF9F9",
        outline=RED_BORDER,
        width=3,
        dash=14,
        gap=8,
    )

    def card(x1, x2, y1, y2, title, items, kind, badge):
        pal = {"g": (GREEN_BG, GREEN_BORDER, GREEN_BADGE_BG, GREEN_TEXT, 3),
               "a": (AMBER_BG, AMBER_BORDER, AMBER_BADGE_BG, AMBER_TEXT, 3),
               "n": (GREY_BG, GREY_BORDER, GREY_BADGE_BG, GREY_TEXT, 2)}[kind]
        bg, bd, bbg, btx, w = pal
        draw.rounded_rectangle((x1, y1, x2, y2), radius=12, fill=bg, outline=bd, width=w)
        draw_badge(draw, x2 - 16, y1 + 16, badge, bbg, btx, bd)
        draw.text((x1 + 18, y1 + 16), title, font=F_CARD_TITLE, fill=DARK_TEXT)
        cy = y1 + 62
        for it in items:
            for l in wrap_text(draw, it, F_ITEM, x2 - x1 - 40):
                draw.text((x1 + 18, cy), l, font=F_ITEM, fill=DARK_TEXT)
                cy += 27
            cy += 8

    c1_x1, c1_x2 = cols_x[0]
    card(c1_x1, c1_x2, 238, 400, "Stage 0 landing zone",
         ["IAM, WIF, budget killswitch, Artifact Registry"], "g", "DONE")
    card(c1_x1, c1_x2, 420, 582, "Stage 1 foundations",
         ["State, monitoring, CI IAM"], "a", "DRAFTED, NOT APPLIED")
    card(c1_x1, c1_x2, 602, 820, "Not started",
         ["Cloud SQL", "Cloud Run services", "Vertex", "Workflows approval gates"], "n", "NOT STARTED")

    c2_x1, c2_x2 = cols_x[1]
    card(c2_x1, c2_x2, 238, 520, "Synthetic-clinic demo",
         ["Built & tested locally: match identities (99.4% precision) -> detect 5 leak types -> \u00a331.6k at risk (synthetic) -> drafted actions awaiting approval.",
          "Status: DONE (local, public repo)"], "g", "DONE")
    card(c2_x1, c2_x2, 540, 680, "Gemini matching hook", ["Stub"], "a", "STUB")
    card(c2_x1, c2_x2, 700, 840, "Deploy", ["GCS / BigQuery / Cloud Run deploy"], "n", "NOT STARTED")
    card(c2_x1, c2_x2, 860, 1000, "Campaign G13", ["Registered; 3 target clinics: TODO Ram"], "a", "TODO")

    c3_x1, c3_x2 = cols_x[2]
    card(c3_x1, c3_x2, 238, 460, "Not started",
         ["Gemini Live bridge", "Agent layer", "Client approval gate"], "n", "NOT STARTED")

    c4_x1, c4_x2 = cols_x[3]
    labels = ["Agent registry", "A2A between agents", "Central eval & red-teaming",
              "Model risk inventory (PRA SS1/23)", "Agent gateway + identity", "Shared observability"]
    cy = y_content_top + 10
    for lab in labels:
        b4 = (c4_x1 + 14, cy, c4_x2 - 14, cy + 70)
        draw_dashed_rect(draw, b4, radius=9, fill=WHITE, outline=RED_BORDER, width=2, dash=8, gap=5)
        draw.text((c4_x1 + 28, cy + 22), lab, font=F_CARD_TITLE, fill=RED_DARK)
        cy += 82
    banner = (c4_x1 + 14, cy + 6, c4_x2 - 14, cy + 76)
    draw.rounded_rectangle(banner, radius=12, fill=RED_DARK, outline=RED_BORDER, width=2)
    draw.text((c4_x1 + 28, cy + 28), "target state -> arch-4", font=load_font(21, True), fill=WHITE)

    # ==========================================
    # 8. DARK FOOTER BAR
    # ==========================================
    y_footer_top = 1290
    draw.rectangle((0, y_footer_top, WIDTH, HEIGHT), fill=FOOTER_BG)
    draw.text((65, y_footer_top + 18), "Where we are · AICB · Oct 2026", font=F_FOOTER, fill=WHITE)

    # Save and verify
    im.save(OUT_IMAGE, "PNG", optimize=True)
    print(f"Generated {OUT_IMAGE} ({OUT_IMAGE.stat().st_size:,} bytes)")


if __name__ == "__main__":
    render_image()
