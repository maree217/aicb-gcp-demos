from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math


W, H = 2400, 1350
OUT = Path(__file__).with_name("arch-3-voice-whitelabel-platform.png")

WHITE = "#FFFFFF"
BLUE = "#4285F4"
RED = "#EA4335"
YELLOW = "#FBBC04"
GREEN = "#34A853"
CHARCOAL = "#202124"
GREY = "#F8F9FA"
PALE_YELLOW = "#FFF8E1"


def load_font(size, bold=False):
    candidates = (
        ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial Bold.ttf"]
        if bold
        else ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"]
    )
    for path in candidates:
        try:
            index = 1 if bold and path.endswith(".ttc") else 0
            return ImageFont.truetype(path, size=size, index=index)
        except (OSError, IndexError):
            pass
    return ImageFont.load_default()


TITLE = load_font(44, True)
NODE = load_font(25, True)
SMALL_NODE = load_font(23, True)
CAPTION = load_font(20, False)
ZONE_LABEL = load_font(21, True)
FOOT = load_font(21, True)


def dashed_round_rect(draw, box, radius, fill, outline, width=2, dash=12, gap=8):
    draw.rounded_rectangle(box, radius=radius, fill=fill)
    x1, y1, x2, y2 = box
    # Straight dashed edges; rounded corner arcs remain visually implied by the fill.
    for start, end, horizontal in [
        ((x1 + radius, y1), (x2 - radius, y1), True),
        ((x1 + radius, y2), (x2 - radius, y2), True),
        ((x1, y1 + radius), (x1, y2 - radius), False),
        ((x2, y1 + radius), (x2, y2 - radius), False),
    ]:
        length = (end[0] - start[0]) if horizontal else (end[1] - start[1])
        p = 0
        while p < length:
            q = min(p + dash, length)
            if horizontal:
                draw.line((start[0] + p, start[1], start[0] + q, start[1]), fill=outline, width=width)
            else:
                draw.line((start[0], start[1] + p, start[0], start[1] + q), fill=outline, width=width)
            p += dash + gap
    for corner, start, end in [
        ((x1 + radius, y1 + radius), 180, 270),
        ((x2 - radius, y1 + radius), 270, 360),
        ((x2 - radius, y2 - radius), 0, 90),
        ((x1 + radius, y2 - radius), 90, 180),
    ]:
        arc_box = (corner[0] - radius, corner[1] - radius, corner[0] + radius, corner[1] + radius)
        draw.arc(arc_box, start=start, end=end, fill=outline, width=width)


def wrap_text(draw, text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            trial = f"{line} {word}".strip()
            if line and draw.textbbox((0, 0), trial, font=font)[2] > max_width:
                lines.append(line)
                line = word
            else:
                line = trial
        if line:
            lines.append(line)
    return lines


def node(draw, box, text, border, fill=WHITE, font=NODE, radius=18, pad=22):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=border, width=2)
    x1, y1, x2, y2 = box
    lines = wrap_text(draw, text, font, x2 - x1 - 2 * pad)
    spacing = 7
    heights = [draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in lines]
    total = sum(heights) + spacing * (len(lines) - 1)
    y = y1 + (y2 - y1 - total) / 2
    for line, height in zip(lines, heights):
        bb = draw.textbbox((0, 0), line, font=font)
        x = x1 + (x2 - x1 - (bb[2] - bb[0])) / 2
        draw.text((x, y - bb[1]), line, font=font, fill=CHARCOAL)
        y += height + spacing


def arrowhead(draw, prev, tip, color=CHARCOAL, size=10):
    dx, dy = tip[0] - prev[0], tip[1] - prev[1]
    mag = math.hypot(dx, dy)
    ux, uy = dx / mag, dy / mag
    px, py = -uy, ux
    base = (tip[0] - ux * size, tip[1] - uy * size)
    draw.polygon([tip, (base[0] + px * size * 0.55, base[1] + py * size * 0.55),
                  (base[0] - px * size * 0.55, base[1] - py * size * 0.55)], fill=color)


def label(draw, xy, text):
    bb = draw.textbbox((0, 0), text, font=CAPTION)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    x, y = xy
    draw.rounded_rectangle((x - w / 2 - 7, y - h / 2 - 5, x + w / 2 + 7, y + h / 2 + 5),
                           radius=5, fill=WHITE)
    draw.text((x - w / 2, y - h / 2 - bb[1]), text, font=CAPTION, fill=CHARCOAL)


def connector(draw, points, caption, label_xy, dotted=False, color=CHARCOAL):
    if dotted:
        for a, b in zip(points, points[1:]):
            length = abs(b[0] - a[0]) + abs(b[1] - a[1])
            for p in range(0, int(length), 8):
                q = min(p + 3, length)
                if a[0] == b[0]:
                    direction = 1 if b[1] >= a[1] else -1
                    draw.line((a[0], a[1] + direction * p, a[0], a[1] + direction * q), fill=color, width=2)
                else:
                    direction = 1 if b[0] >= a[0] else -1
                    draw.line((a[0] + direction * p, a[1], a[0] + direction * q, a[1]), fill=color, width=2)
    else:
        draw.line(points, fill=color, width=2, joint="curve")
    arrowhead(draw, points[-2], points[-1], color=color)
    label(draw, label_xy, caption)


img = Image.new("RGB", (W, H), WHITE)
d = ImageDraw.Draw(img)

d.text((70, 48), "Rung C + D — Voice Recapture Pilots & Advisory White-Label Platform (scale path)",
       font=TITLE, fill=CHARCOAL)

# Zones
gcp = (585, 135, 2330, 1260)
dashed_round_rect(d, gcp, 24, GREY, BLUE, width=3, dash=15, gap=10)
d.rounded_rectangle((618, 117, 939, 156), radius=8, fill=WHITE)
d.text((632, 124), "GCP · europe-west2 (London)", font=ZONE_LABEL, fill=BLUE)

vpc = (1125, 450, 1575, 735)
dashed_round_rect(d, vpc, 20, WHITE, RED, width=3, dash=12, gap=9)
d.rounded_rectangle((1155, 432, 1405, 470), radius=8, fill=WHITE)
d.text((1167, 439), "VPC perimeter (VPC-SC)", font=ZONE_LABEL, fill=RED)

# Nodes: external and top band
phone = (55, 520, 315, 630)
twilio = (355, 500, 555, 650)
workspace = (720, 205, 1235, 325)
security = (1690, 190, 2225, 340)
node(d, phone, "Customer phone call (PSTN)", CHARCOAL, font=SMALL_NODE)
node(d, twilio, "Twilio SIP / Media Streams (8kHz μ-law)", YELLOW, font=SMALL_NODE)
node(d, workspace, "Advisory partner workspace (white-label, multi-tenant)", YELLOW)
node(d, security, "Per-client data isolation + Model Armor + VPC-SC exfiltration denial", RED)

# Voice path
bridge = (650, 485, 1070, 700)
live = (1175, 520, 1525, 665)
store = (1650, 485, 2245, 700)
node(d, bridge, "Transcode bridge — Cloud Run\n(μ-law <-> 16kHz PCM, 20–40ms chunks, session resumption)", BLUE, font=SMALL_NODE)
node(d, live, "Gemini Live API — native audio, barge-in", BLUE, font=SMALL_NODE)
node(d, store, "Conversation store — Firestore (hot) to BigQuery (reconciled to bookings & revenue)", GREEN, font=SMALL_NODE)

# Agent / dispatch band
agent = (680, 805, 1190, 950)
gate = (1260, 805, 1645, 950)
dispatch = (1715, 805, 2245, 950)
node(d, agent, "Agent layer — Cloud Workflows: re-engagement · quote follow-up · review requests", BLUE, font=SMALL_NODE)
node(d, gate, "Client approval gate (their thumb on the queue)", RED, font=SMALL_NODE)
node(d, dispatch, "Dispatch — SMS / email / callback (write-ahead outbox)", GREEN, font=SMALL_NODE)

# Bottom nodes
annotation = (660, 1050, 1565, 1175)
audit = (1715, 1050, 2245, 1175)
node(d, annotation, "Entry only via paid design-partner pilot · non-clinical verticals · 100-call PSTN production bar",
     YELLOW, fill=PALE_YELLOW, font=SMALL_NODE)
node(d, audit, "Cloud Trace + per-client audit ledger", CHARCOAL, font=SMALL_NODE)

# External arrows
connector(d, [(315, 575), (355, 575)], "inbound call", (335, 545))
connector(d, [(555, 575), (610, 575), (610, 592), (650, 592)], "media stream", (607, 545))

# Voice arrows
connector(d, [(1070, 592), (1175, 592)], "pcm chunks", (1122, 562))
connector(d, [(1525, 592), (1650, 592)], "persist turns", (1587, 562))

# Agent arrows
connector(d, [(1190, 877), (1260, 877)], "queue action", (1225, 847))
connector(d, [(1645, 877), (1715, 877)], "approved", (1680, 847))
connector(d, [(1948, 700), (1948, 755), (935, 755), (935, 805)], "trigger agents", (1450, 730))

# Workspace and security controls
connector(d, [(975, 325), (975, 390), (1452, 390), (1452, 805)], "own the queue", (1210, 365))
connector(d, [(1235, 265), (1690, 265)], "policy", (1462, 235))
connector(d, [(1958, 340), (1958, 410), (1500, 410), (1500, 450)], "deny exfil", (1730, 380), color=RED)

# Observability arrows
connector(d, [(1350, 665), (1350, 995), (1840, 995), (1840, 1050)], "traces", (1510, 970), dotted=True)
connector(d, [(2040, 950), (2040, 1050)], "audit", (2090, 1000), dotted=True)

# Caption strip
d.rectangle((0, 1285, W, H), fill=CHARCOAL)
footer = "Rung C+D · voice + white-label · AICB · Aug 2026"
bb = d.textbbox((0, 0), footer, font=FOOT)
d.text(((W - (bb[2] - bb[0])) / 2, 1306), footer, font=FOOT, fill=WHITE)

assert img.size == (2400, 1350)
assert img.mode == "RGB"
img.save(OUT, "PNG", optimize=True)
print(f"{OUT} ({OUT.stat().st_size:,} bytes)")
