from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 2400, 1350
OUT = Path(__file__).with_name("arch-2-revenue-leakage-sprint.png")

WHITE = "#FFFFFF"
BLUE = "#4285F4"
RED = "#EA4335"
YELLOW = "#FBBC04"
GREEN = "#34A853"
CHARCOAL = "#202124"
GREY = "#F8F9FA"
MID_GREY = "#5F6368"
PALE_YELLOW = "#FFF8E1"


def load_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size, index=1 if bold and path.endswith(".ttc") else 0)
        except (OSError, ValueError):
            continue
    return ImageFont.load_default()


TITLE = load_font(44, True)
ZONE_FONT = load_font(22, True)
NODE_FONT = load_font(24, True)
SMALL_FONT = load_font(20, False)
SMALL_BOLD = load_font(20, True)
CHIP_FONT = load_font(20, False)

im = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
d = ImageDraw.Draw(im)


def dashed_line(points, fill, width=2, dash=12, gap=8):
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if x1 == x2:
            step = 1 if y2 >= y1 else -1
            pos, end = y1, y2
            while (pos - end) * step < 0:
                nxt = pos + step * min(dash, abs(end - pos))
                d.line((x1, pos, x2, nxt), fill=fill, width=width)
                pos = nxt + step * gap
        elif y1 == y2:
            step = 1 if x2 >= x1 else -1
            pos, end = x1, x2
            while (pos - end) * step < 0:
                nxt = pos + step * min(dash, abs(end - pos))
                d.line((pos, y1, nxt, y2), fill=fill, width=width)
                pos = nxt + step * gap
        else:
            raise ValueError("Only orthogonal dashed lines are supported")


def dashed_round_rect(box, radius, outline, fill=None, width=2, dash=14, gap=9):
    x1, y1, x2, y2 = box
    if fill:
        d.rounded_rectangle(box, radius=radius, fill=fill)
    # Clean dashed perimeter with short orthogonal segments; corner gaps are intentional.
    dashed_line([(x1 + radius, y1), (x2 - radius, y1)], outline, width, dash, gap)
    dashed_line([(x2, y1 + radius), (x2, y2 - radius)], outline, width, dash, gap)
    dashed_line([(x2 - radius, y2), (x1 + radius, y2)], outline, width, dash, gap)
    dashed_line([(x1, y2 - radius), (x1, y1 + radius)], outline, width, dash, gap)
    d.arc((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=outline, width=width)
    d.arc((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 360, fill=outline, width=width)
    d.arc((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=outline, width=width)
    d.arc((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=outline, width=width)


def wrap(text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if d.textbbox((0, 0), trial, font=font)[2] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def centered_text(box, text, font=NODE_FONT, fill=CHARCOAL, padding=18, spacing=8):
    x1, y1, x2, y2 = box
    lines = wrap(text, font, x2 - x1 - 2 * padding)
    heights = [d.textbbox((0, 0), line, font=font)[3] - d.textbbox((0, 0), line, font=font)[1] for line in lines]
    total = sum(heights) + spacing * (len(lines) - 1)
    y = y1 + (y2 - y1 - total) / 2
    for line, h in zip(lines, heights):
        bb = d.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        d.text((x1 + (x2 - x1 - tw) / 2, y - bb[1]), line, font=font, fill=fill)
        y += h + spacing


def node(box, text, border, fill=WHITE, radius=18, width=3, font=NODE_FONT):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=border, width=width)
    centered_text(box, text, font=font)


def arrowhead(point, direction, color, size=9):
    x, y = point
    if direction == "right":
        pts = [(x, y), (x - size, y - size // 2), (x - size, y + size // 2)]
    elif direction == "left":
        pts = [(x, y), (x + size, y - size // 2), (x + size, y + size // 2)]
    elif direction == "down":
        pts = [(x, y), (x - size // 2, y - size), (x + size // 2, y - size)]
    else:
        pts = [(x, y), (x - size // 2, y + size), (x + size // 2, y + size)]
    d.polygon(pts, fill=color)


def caption(cx, cy, text, font=SMALL_FONT, color=CHARCOAL):
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad_x, pad_y = 9, 5
    box = (cx - tw / 2 - pad_x, cy - th / 2 - pad_y, cx + tw / 2 + pad_x, cy + th / 2 + pad_y)
    d.rounded_rectangle(box, radius=6, fill=WHITE)
    d.text((cx - tw / 2, cy - th / 2 - bb[1]), text, font=font, fill=color)


def horizontal_arrow(x1, x2, y, label, color=CHARCOAL, label_y=None):
    d.line((x1, y, x2, y), fill=color, width=2)
    arrowhead((x2, y), "right", color)
    caption((x1 + x2) / 2, label_y if label_y is not None else y - 28, label, color=color)


# Title
d.text((70, 48), "Rung B — Revenue Leakage Decision Sprint (post-gate entry product, £1,500 fixed / 5 days)", font=TITLE, fill=CHARCOAL)

# GCP and VPC-SC zones
GCP = (470, 180, 2340, 1205)
dashed_round_rect(GCP, 24, BLUE, GREY, width=3)
d.rounded_rectangle((510, 158, 842, 206), radius=8, fill=WHITE)
d.text((527, 169), "GCP · europe-west2 (London)", font=ZONE_FONT, fill=BLUE)

VPC = (1315, 355, 1635, 790)
dashed_round_rect(VPC, 20, RED, "#FFFDFD", width=2, dash=10, gap=7)
d.rounded_rectangle((1342, 337, 1608, 380), radius=7, fill=WHITE)
d.text((1360, 347), "VPC perimeter (VPC-SC)", font=SMALL_BOLD, fill=RED)

# Outside-GCP source with internal feed chips
CLIENT = (55, 420, 405, 735)
d.rounded_rectangle(CLIENT, radius=20, fill=WHITE, outline=CHARCOAL, width=3)
centered_text((75, 438, 385, 505), "Client's existing data", font=NODE_FONT)
chips = [
    (90, 525, 370, 575, "inbox export"),
    (90, 592, 370, 642, "call logs"),
    (90, 659, 370, 709, "accounting / PMS export"),
]
for x1, y1, x2, y2, label in chips:
    d.rounded_rectangle((x1, y1, x2, y2), radius=10, fill=GREY, outline="#9AA0A6", width=2)
    centered_text((x1, y1, x2, y2), label, font=CHIP_FONT, padding=10, spacing=3)

# Main pipeline nodes
GCS = (510, 485, 720, 685)
JOB = (780, 485, 1015, 685)
BQ = (1075, 455, 1285, 715)
GEMINI = (1350, 455, 1600, 715)
GATE = (1660, 430, 1940, 740)
OUTPUT = (2000, 485, 2290, 685)

node(GCS, "GCS landing bucket (per-client, versioned)", GREEN)
node(JOB, "Cloud Run Job — ingest + reconcile", BLUE)
node(BQ, "BigQuery — outcome joins:\nenquiry → booking → revenue\nML.GENERATE_\nEMBEDDING · VECTOR_SEARCH", BLUE, font=load_font(20, True))
node(GEMINI, "Gemini analysis — cached AICB doctrine prefix (90% cheaper input)", BLUE, font=load_font(22, True))
node(GATE, "Human approval — named accountable adviser (write-ahead outbox + /q)", RED, font=load_font(22, True))
node(OUTPUT, "Evidence pack generator → PDF / client portal", GREEN)

# Main arrows and captions
horizontal_arrow(405, 510, 585, "secure upload, client-scoped", label_y=390)
horizontal_arrow(720, 780, 585, "ingest", label_y=420)
horizontal_arrow(1015, 1075, 585, "load", label_y=420)
horizontal_arrow(1285, 1350, 585, "read corpus", label_y=420)
horizontal_arrow(1600, 1660, 585, "submit for approval", label_y=800)
horizontal_arrow(1940, 2000, 585, "approved pack", label_y=800)

# Rejection loop: gate → above pipeline → Gemini, entirely orthogonal and dashed.
loop = [(1800, 430), (1800, 295), (1475, 295), (1475, 455)]
dashed_line(loop, RED, width=3, dash=12, gap=8)
arrowhead((1475, 455), "down", RED, size=11)
caption(1638, 270, "rejected claims return with notes", font=SMALL_BOLD, color=RED)

# Bottom governance annotations
KILL = (570, 915, 1510, 1045)
d.rounded_rectangle(KILL, radius=16, fill=PALE_YELLOW, outline=YELLOW, width=3)
centered_text(KILL, "Kill criteria: ≥2/10 pay · ≥70% of enquiries join to outcomes · renewal after month 2", font=load_font(23, True), padding=28)

AUDIT = (1660, 900, 2250, 1060)
node(AUDIT, "Cloud Audit Logs — every claim carries confidence + source", CHARCOAL, font=load_font(22, True))

# Subtle dotted association from approval/output area to audit log.
dashed_line([(1955, 740), (1955, 900)], MID_GREY, width=2, dash=6, gap=7)
arrowhead((1955, 900), "down", MID_GREY, size=8)
caption(2070, 820, "record claim trail", color=MID_GREY)

# Bottom caption strip
d.rectangle((0, 1260, WIDTH, HEIGHT), fill=CHARCOAL)
d.text((70, 1288), "Rung B · revenue leakage sprint · AICB · Aug 2026", font=load_font(24, True), fill=WHITE)

assert im.size == (2400, 1350)
assert im.mode == "RGB"
im.save(OUT, format="PNG", optimize=True)
print(f"{OUT} ({OUT.stat().st_size:,} bytes)")
