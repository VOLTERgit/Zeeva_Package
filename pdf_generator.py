"""
Builds the branded 'Hair Transplant Package' PDF for Zeeva Clinic,
styled to match the clinic's reference design.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PAGE_W, PAGE_H = A4

# ---- palette (sampled from the Zeeva reference artwork) ----
DARK = HexColor("#0B2E36")      # deep navy-teal (headers, title)
TEAL = HexColor("#1CA39C")      # bright teal accent (logo / package line)
TEAL_DEEP = HexColor("#6AAEAA")  # table header bar / investment card - updated to main brand color (was #004749)
GOLD = HexColor("#D9A441")
LIGHT_BG = HexColor("#F4F6F6")
GRAY_TXT = HexColor("#5B6B6E")
BORDER = HexColor("#DDE3E3")
WHITE = white

# ---- footer brand colors (client-specified Pantone) ----
FOOTER_BG = HexColor("#6AAEAA")       # Pantone 2460 C
FOOTER_SUBTEXT = white                 # Cool Gray 5 C had unreadable contrast on 2460 C; kept white instead

# ---- footer contact details (PLACEHOLDERS - confirm and update these) ----
FOOTER_EMAIL = "info@zeevaclinic.com"
FOOTER_INSTAGRAM = "@zeevaclinic"

# ---- Bootstrap Icons (real glyph font, falls back to hand-drawn vector icons
# if the font file isn't found next to the assets folder) ----
BI_FONT = "BootstrapIcons"
BI_CHECK = "\uf633"   # check-lg
BI_STAR = "\uf586"    # star-fill
BI_GEM = "\uf3e6"      # gem (investment card badge)
BI_SHIELD_CHECK = "\uf52f"  # shield-check (terms & conditions badge)
BI_PEOPLE = "\uf4cf"    # people-fill (stats row)
BI_GLOBE = "\uf3ee"     # globe (stats row)
BI_WHATSAPP = "\uf618"  # whatsapp (footer)
BI_ENVELOPE = "\uf32c"  # envelope-fill (footer)
BI_INSTAGRAM = "\uf437"  # instagram (footer)
BI_WALLET = "\uf615"    # wallet2 (investment card - payment options)
BI_CARD = "\uf2d9"       # credit-card-2-front-fill (investment card - EMI)
_BI_AVAILABLE = False

# ---- Terms & Conditions (staff: edit this list to change the wording/order) ----
# NOTE: the client's original reference had a "Passport copy is mandatory..."
# clause that was removed per request. If a graft-count range or advance
# amount changes structurally, update the wording below to match.
TERMS_AND_CONDITIONS = [
    "Package cost includes all services mentioned above only.",
    "The package includes the grafts specified above. Following a detailed "
    "scalp and donor area assessment, additional charges will apply if a "
    "higher number of grafts is required to achieve the desired results.",
    "Extra medical treatment will be charged separately.",
    "Surgery suitability depends on medical evaluation and donor assessment.",
    "Long-term medication should be taken as advised by the doctor for "
    "optimal results.",
    "Advance booking confirmation is required for surgery, along with the "
    "advance payment mentioned above.",
    "Package amount is non-refundable once booking is confirmed.",
]


def _register_bi_font(assets_dir):
    """Registers the Bootstrap Icons TTF once. Looks for
    'bootstrap-icons.ttf' inside the assets folder. Safe to call every
    generate_pdf() - no-ops after the first successful registration."""
    global _BI_AVAILABLE
    if _BI_AVAILABLE:
        return
    font_path = os.path.join(assets_dir or "", "bootstrap-icons.ttf")
    try:
        pdfmetrics.registerFont(TTFont(BI_FONT, font_path))
        _BI_AVAILABLE = True
    except Exception:
        _BI_AVAILABLE = False


def _draw_bi_glyph(c, cx, cy, glyph, size, color=DARK):
    """Draws a Bootstrap Icons glyph centered at (cx, cy). Returns True if
    drawn, False if the icon font isn't available (caller should fall back
    to the vector-drawn version)."""
    if not _BI_AVAILABLE:
        return False
    c.saveState()
    c.setFillColor(color)
    c.setFont(BI_FONT, size)
    w = stringWidth(glyph, BI_FONT, size)
    c.drawString(cx - w / 2, cy - size * 0.34, glyph)
    c.restoreState()
    return True


def _round_rect(c, x, y, w, h, r=8, stroke=BORDER, fill=None, line_width=1):
    c.saveState()
    c.setStrokeColor(stroke)
    c.setLineWidth(line_width)
    if fill:
        c.setFillColor(fill)
        c.roundRect(x, y, w, h, r, stroke=1, fill=1)
    else:
        c.roundRect(x, y, w, h, r, stroke=1, fill=0)
    c.restoreState()


def _icon_circle(c, cx, cy, radius, fill=HexColor("#E7F3F2")):
    c.saveState()
    c.setFillColor(fill)
    c.circle(cx, cy, radius, stroke=0, fill=1)
    c.restoreState()


def _center_text(c, cx, y, text, font, size, color=DARK):
    c.setFont(font, size)
    c.setFillColor(color)
    w = stringWidth(text, font, size)
    c.drawString(cx - w / 2, y, text)


def _wrap_text(text, font, size, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if stringWidth(trial, font, size) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw_check_icon(c, cx, cy, size, color=DARK):
    if _draw_bi_glyph(c, cx, cy, BI_CHECK, size * 2.3, color):
        return
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(1.6)
    c.line(cx - size, cy, cx - size / 4, cy - size * 0.8)
    c.line(cx - size / 4, cy - size * 0.8, cx + size, cy + size * 0.6)
    c.restoreState()


def _draw_star(c, cx, cy, size, color=GOLD):
    if _draw_bi_glyph(c, cx, cy, BI_STAR, size * 2.3, color):
        return
    import math
    c.saveState()
    c.setFillColor(color)
    points = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        rad = size if i % 2 == 0 else size * 0.42
        points.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    p = c.beginPath()
    p.moveTo(*points[0])
    for pt in points[1:]:
        p.lineTo(*pt)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def _draw_person_silhouette(c, cx, cy, s, color):
    """One small person icon: round head + rounded-shoulder body."""
    c.saveState()
    c.setFillColor(color)
    c.circle(cx, cy + 1.15 * s, 0.62 * s, stroke=0, fill=1)
    body_w, body_h = 1.9 * s, 1.25 * s
    c.roundRect(cx - body_w / 2, cy - 0.55 * s - body_h, body_w, body_h, body_h / 2, stroke=0, fill=1)
    c.restoreState()


def _draw_people_icon(c, cx, cy, r, color=DARK):
    """Two overlapping people, representing patients / procedures."""
    s = r * 0.62
    _draw_person_silhouette(c, cx - s * 0.75, cy - s * 0.15, s * 0.82, HexColor("#7FBFBA"))
    _draw_person_silhouette(c, cx + s * 0.55, cy, s * 0.95, color)


def _draw_globe_icon(c, cx, cy, r, color=DARK):
    """A simple globe: outer circle + latitude line + meridian ellipse."""
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(1.15)
    g = r * 0.72
    c.circle(cx, cy, g, stroke=1, fill=0)
    c.line(cx - g, cy, cx + g, cy)
    c.ellipse(cx - g * 0.42, cy - g, cx + g * 0.42, cy + g, stroke=1, fill=0)
    c.line(cx, cy - g, cx, cy + g)
    c.restoreState()


def _draw_shield_icon(c, cx, cy, r, fill_color=None, check_color=WHITE):
    """A certification shield with a checkmark inside (used for ABHRS)."""
    s = r * 0.85
    c.saveState()
    if fill_color:
        c.setFillColor(fill_color)
    p = c.beginPath()
    p.moveTo(cx - s, cy + s * 0.55)
    p.lineTo(cx - s, cy - s * 0.15)
    p.lineTo(cx, cy - s * 1.15)
    p.lineTo(cx + s, cy - s * 0.15)
    p.lineTo(cx + s, cy + s * 0.55)
    p.curveTo(cx + s * 0.4, cy + s * 0.95, cx - s * 0.4, cy + s * 0.95, cx - s, cy + s * 0.55)
    p.close()
    c.drawPath(p, stroke=0, fill=1 if fill_color else 0)
    c.restoreState()
    _draw_check_icon(c, cx, cy - s * 0.1, s * 0.42, color=check_color)


def _draw_stat_icon(c, cx, cy, radius, kind, assets_dir):
    """
    Draws the icon for a stats-row badge. Uses the Bootstrap Icons font
    (same family as the checkmarks/star elsewhere) for visual consistency.
    Falls back to a custom PNG in the assets folder if present and the font
    isn't available, then to a hand-drawn vector icon as a last resort.

    kind: "procedures" | "trusted" | "abhrs"
    """
    if kind == "abhrs":
        _icon_circle(c, cx, cy, radius, fill=TEAL_DEEP)
        if _draw_bi_glyph(c, cx, cy, BI_SHIELD_CHECK, radius * 1.15, WHITE):
            return
    elif kind == "trusted":
        _icon_circle(c, cx, cy, radius, fill=HexColor("#E7F3F2"))
        if _draw_bi_glyph(c, cx, cy, BI_GLOBE, radius * 1.15, TEAL_DEEP):
            return
    else:  # procedures
        _icon_circle(c, cx, cy, radius, fill=HexColor("#E7F3F2"))
        if _draw_bi_glyph(c, cx, cy, BI_PEOPLE, radius * 1.15, TEAL_DEEP):
            return

    # Bootstrap font unavailable - fall back to a custom PNG if the clinic
    # dropped one in the assets folder, otherwise a hand-drawn vector icon.
    custom_names = {
        "procedures": "icon_procedures.png",
        "trusted": "icon_trusted.png",
        "abhrs": "icon_abhrs.png",
    }
    custom_path = os.path.join(assets_dir, custom_names.get(kind, ""))
    if assets_dir and os.path.exists(custom_path):
        d = radius * 1.7
        c.drawImage(custom_path, cx - d / 2, cy - d / 2, width=d, height=d,
                    preserveAspectRatio=True, mask="auto")
        return

    if kind == "abhrs":
        _draw_check_icon(c, cx, cy - 1, radius * 0.5, color=WHITE)
    elif kind == "trusted":
        _draw_globe_icon(c, cx, cy, radius, color=TEAL_DEEP)
    else:
        _draw_people_icon(c, cx, cy, radius, color=TEAL_DEEP)


def _terms_card(c, margin, content_w, y_top, draw=True):
    """Compact Terms & Conditions card for page 1 (two columns, numbered
    badges). Pass draw=False to only measure the height (used to reserve
    space before the Package Includes table is sized), then call again
    with draw=True at the final y position once the layout above it is
    settled.
    Returns the total card height in points."""
    header_h = 24
    body_pad = 11
    col_gap = 16
    col_w = (content_w - col_gap) / 2
    # Both columns get the SAME inset (14pt) from their own left boundary
    # to the number badge, and the same 14pt buffer from their own right
    # boundary to the far edge of wrapped text. Previously only the left
    # column had that 14pt inset applied - the right column's text ran
    # almost to the card's right edge (only ~4pt of padding) since it
    # inherited none of it. text_w now accounts for both the 14pt outer
    # pad and the 20pt badge-to-text offset on each side.
    COL_INSET = 14
    text_w = col_w - COL_INSET - 20 - COL_INSET
    body_font, body_size, line_h, row_gap = "Helvetica", 7.6, 9.4, 7

    n = len(TERMS_AND_CONDITIONS)
    left_n = (n + 1) // 2
    left_terms = TERMS_AND_CONDITIONS[:left_n]
    right_terms = TERMS_AND_CONDITIONS[left_n:]

    def col_height(terms):
        h = 0
        for t in terms:
            lines = _wrap_text(t, body_font, body_size, text_w)
            h += max(len(lines), 1) * line_h + row_gap
        return h - row_gap if terms else 0

    content_h = max(col_height(left_terms), col_height(right_terms))
    card_h = header_h + content_h + body_pad * 2

    if not draw:
        return card_h

    def ty(y_from_top):
        return PAGE_H - y_from_top

    card_top = y_top
    card_y_top = ty(card_top)
    _round_rect(c, margin, card_y_top - card_h, content_w, card_h, r=10, fill=WHITE)

    c.setFillColor(TEAL_DEEP)
    c.roundRect(margin, card_y_top - header_h, content_w, header_h, 10, stroke=0, fill=1)
    c.rect(margin, card_y_top - header_h, content_w, header_h / 2, stroke=0, fill=1)
    _icon_circle(c, margin + 20, card_y_top - header_h / 2, 8, fill=WHITE)
    if not _draw_bi_glyph(c, margin + 20, card_y_top - header_h / 2, BI_SHIELD_CHECK, 9, TEAL_DEEP):
        _draw_check_icon(c, margin + 20, card_y_top - header_h / 2 - 1, 3.4, color=TEAL_DEEP)
    c.setFont("Helvetica-Bold", 9.6)
    c.setFillColor(WHITE)
    c.drawString(margin + 36, card_y_top - header_h / 2 - 3.4, "TERMS & CONDITIONS")

    def draw_column(x, terms, start_num):
        y = card_top + header_h + body_pad
        for i, t in enumerate(terms):
            num = start_num + i
            lines = _wrap_text(t, body_font, body_size, text_w)
            badge_cy = ty(y + 6)
            c.setStrokeColor(DARK)
            c.setFillColor(WHITE)
            c.setLineWidth(0.9)
            c.circle(x + 7.5, badge_cy, 7, stroke=1, fill=1)
            c.setFont("Helvetica-Bold", 6.8)
            c.setFillColor(DARK)
            num_w = stringWidth(str(num), "Helvetica-Bold", 6.8)
            c.drawString(x + 7.5 - num_w / 2, badge_cy - 2.3, str(num))

            c.setFont(body_font, body_size)
            c.setFillColor(GRAY_TXT)
            for li, line in enumerate(lines):
                c.drawString(x + 20, ty(y + 6 - 2.3 + li * line_h), line)
            y += max(len(lines), 1) * line_h + row_gap

    draw_column(margin + COL_INSET, left_terms, 1)
    draw_column(margin + col_w + col_gap + COL_INSET, right_terms, left_n + 1)
    return card_h


def _draw_footer(c, margin, content_w, footer_y, patient, show_date_line=True):
    """Shared bottom contact-strip, used on every page.

    NOTE: Email and Instagram handle below are placeholders - swap
    FOOTER_EMAIL / FOOTER_INSTAGRAM for the clinic's real ones."""
    footer_h = 40
    c.setFillColor(FOOTER_BG)
    c.roundRect(margin, footer_y, content_w, footer_h, 8, stroke=0, fill=1)
    c.rect(margin, footer_y, content_w, footer_h / 2, stroke=0, fill=1)

    seg_w = content_w / 4
    footer_items = [
        (BI_CHECK, "BOOK ASSESSMENT", "Your journey starts here"),
        (BI_WHATSAPP, "+91 93133 14270", "Chat with us on WhatsApp"),
        (BI_ENVELOPE, FOOTER_EMAIL, "Email us"),
        (BI_GLOBE, "zeevaclinic.com", "Visit our website"),
    ]
    for i, (glyph, l1, l2) in enumerate(footer_items):
        fx = margin + seg_w * i
        _icon_circle(c, fx + 20, footer_y + footer_h / 2, 9, fill=WHITE)
        if not _draw_bi_glyph(c, fx + 20, footer_y + footer_h / 2, glyph, 9, TEAL_DEEP):
            _draw_check_icon(c, fx + 20, footer_y + footer_h / 2 - 1, 3.4, color=TEAL_DEEP)
        c.setFont("Helvetica-Bold", 7.6)
        c.setFillColor(WHITE)
        c.drawString(fx + 34, footer_y + footer_h / 2 + 3, l1)
        c.setFont("Helvetica", 6.3)
        c.setFillColor(FOOTER_SUBTEXT)
        c.drawString(fx + 34, footer_y + footer_h / 2 - 7, l2)

    if show_date_line:
        c.setFont("Helvetica", 7)
        c.setFillColor(GRAY_TXT)
        c.drawCentredString(PAGE_W / 2, footer_y - 8,
                             f"Prepared on {patient.get('date', '')}  |  Zeeva Skin & Hair Clinic, Ahmedabad  |  Instagram: {FOOTER_INSTAGRAM}")


def generate_pdf(save_path, patient, items, total, gst_applied, assets_dir, gst_amount=0):
    _register_bi_font(assets_dir)
    c = canvas.Canvas(save_path, pagesize=A4)
    margin = 36
    content_w = PAGE_W - 2 * margin

    def ty(y_from_top):
        """Convert a y-coordinate measured from the top of the page."""
        return PAGE_H - y_from_top

    # ================= HEADER =================
    # Rebalanced per feedback: the header/hero used to take ~190pt before
    # the patient row started; trimmed to free up room for a larger,
    # easier-to-read Terms & Conditions section further down the page.
    logo_path = os.path.join(assets_dir, "logo.png")
    if os.path.exists(logo_path):
        c.drawImage(logo_path, margin, ty(50), width=118, height=23.6,
                    preserveAspectRatio=True, mask="auto")

    hero_path = os.path.join(assets_dir, "hero_graphic.png")
    if os.path.exists(hero_path):
        hw, hh = 172, 147
        c.drawImage(hero_path, PAGE_W - margin - hw, ty(158), width=hw, height=hh,
                    preserveAspectRatio=True, mask="auto")

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(DARK)
    c.drawString(margin, ty(98), "HAIR TRANSPLANT")
    c.setFillColor(TEAL)
    c.drawString(margin, ty(124), "PACKAGE")

    c.setFont("Helvetica-BoldOblique", 10.8)
    c.setFillColor(DARK)
    c.drawString(margin, ty(144), "\u2014   Advanced Care. International Standards.")

    doctors = patient.get("doctors", "Dr. Anchal Shah & Dr. Diwaker Sharma")
    if doctors:
        c.setFont("Helvetica", 8.6)
        c.setFillColor(GRAY_TXT)
        c.drawString(margin, ty(159), f"Performed by {doctors}")

    # ================= PATIENT + STATS ROW =================
    row_top = 172
    row_h = 120
    left_w = content_w * 0.51
    gap = 14
    right_w = content_w - left_w - gap

    # ---- Prepared exclusively for card ----
    px, py = margin, ty(row_top + row_h)
    _round_rect(c, px, py, left_w, row_h, r=10, fill=WHITE)

    CARD_PAD = 14  # single consistent left/right inset used throughout this card

    badge_w = stringWidth("PREPARED EXCLUSIVELY FOR", "Helvetica-Bold", 8) + 20
    _round_rect(c, px + CARD_PAD, ty(row_top + 18), badge_w, 17, r=8, fill=TEAL_DEEP, stroke=TEAL_DEEP)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(WHITE)
    c.drawString(px + CARD_PAD + 10, ty(row_top + 13.5), "PREPARED EXCLUSIVELY FOR")

    if patient.get("country"):
        c.setFont("Helvetica", 8.8)
        c.setFillColor(GRAY_TXT)
        c.drawRightString(px + left_w - CARD_PAD, ty(row_top + 13.5), patient["country"])

    if patient.get("quotation_id"):
        c.setFont("Helvetica", 7.4)
        c.setFillColor(GRAY_TXT)
        c.drawRightString(px + left_w - CARD_PAD, ty(row_top + 30), f'Quotation ID: {patient["quotation_id"]}')

    # Field block rhythm tightened slightly (17pt -> 15pt row spacing, 16pt
    # -> 10pt gap under the divider) so the closing "Personalized Treatment
    # Plan" line lands with the same ~14-15pt bottom padding as the card's
    # top padding, instead of nearly touching the card's bottom edge.
    info_y = row_top + 46
    line_gap = 15
    fields = [
        ("Name", patient.get("name", "")),
        ("Age", f'{patient.get("age", "")} yrs' if patient.get("age") else ""),
        ("Phone", patient.get("phone", "")),
    ]
    for label, value in fields:
        c.setFont("Helvetica-Bold", 10.5)
        c.setFillColor(DARK)
        text = f"{label}: {value}" if value else f"{label}: -"
        c.drawString(px + CARD_PAD + 2, ty(info_y), text)
        info_y += line_gap

    dash_y = info_y + 4
    c.setStrokeColor(BORDER)
    c.setDash(2, 2)
    c.line(px + CARD_PAD, ty(dash_y), px + left_w - CARD_PAD, ty(dash_y))
    c.setDash()
    c.setFont("Helvetica", 8.8)
    c.setFillColor(GRAY_TXT)
    c.drawString(px + CARD_PAD + 2, ty(dash_y + 10), "\u2713  Personalized Treatment Plan")

    # ---- Stats row (3 boxes) ----
    sx, sy = px + left_w + gap, py
    _round_rect(c, sx, sy, right_w, row_h, r=10, fill=WHITE)
    seg_w = right_w / 3
    seg_pad = 10  # keep text clear of the divider lines / box edges
    text_max_w = seg_w - seg_pad * 2
    stats = [
        ("procedures", "15,000+", "Successful Hair Transplant Procedures"),
        ("trusted", "Trusted by", "Patients from 15+ Countries"),
        ("abhrs", "ABHRS", "Certified Clinic"),
    ]
    desc_font, desc_size = "Helvetica", 7.6

    # Wrap every description up front so the icon/label/description block
    # can be centered as one unit against the row's actual content height,
    # using the tallest (most-wrapped) column as the reference. All three
    # columns then share the exact same icon/label Y (so the row of icons
    # still reads as perfectly aligned left-to-right) while the block as a
    # whole sits centered in the box - matching the patient card's balanced
    # top/bottom padding instead of leaving uneven leftover whitespace
    # under whichever column happens to have the shortest description.
    wrapped_descs = [_wrap_text(desc, desc_font, desc_size, text_max_w) for _, _, desc in stats]
    max_lines = max((len(lines) for lines in wrapped_descs), default=1)
    STAT_ICON_R = 14
    STAT_DESC_LINE_H = 11.5
    block_h = STAT_ICON_R + 44 + (max_lines - 1) * STAT_DESC_LINE_H + 3
    icon_y = row_top + STAT_ICON_R + (row_h - block_h) / 2

    for i, (kind, l1, desc) in enumerate(stats):
        ccx = sx + seg_w * i + seg_w / 2
        _draw_stat_icon(c, ccx, ty(icon_y), STAT_ICON_R, kind, assets_dir)

        # shrink the top label font a touch if it doesn't fit either
        l1_size = 10.5
        while stringWidth(l1, "Helvetica-Bold", l1_size) > text_max_w and l1_size > 8:
            l1_size -= 0.5
        _center_text(c, ccx, ty(icon_y + 28), l1, "Helvetica-Bold", l1_size, DARK)

        dy = icon_y + 44
        for line in wrapped_descs[i]:
            _center_text(c, ccx, ty(dy), line, desc_font, desc_size, GRAY_TXT)
            dy += STAT_DESC_LINE_H

        if i < 2:
            c.setStrokeColor(BORDER)
            c.line(sx + seg_w * (i + 1), sy + 16, sx + seg_w * (i + 1), sy + row_h - 16)


    # ================= PACKAGE INCLUDES + INVESTMENT =================
    lower_top = row_top + row_h + 40
    table_w = content_w * 0.62
    card_x = margin
    header_h = 26

    # ---- Column layout ----
    # Three fixed regions: check-icon column, then a 35% / 65% split of the
    # remaining width for Service Name / Details. COL_PAD is applied
    # consistently as the left inset for every column, with a smaller
    # gutter before the next divider/border, so text never touches a line
    # and both columns start on a shared vertical guide.
    ICON_COL_W = 36
    COL_PAD = 10
    usable_w = table_w - ICON_COL_W
    name_region_w = usable_w * 0.35
    detail_region_w = usable_w * 0.65

    name_col_x = ICON_COL_W + COL_PAD
    detail_col_x = ICON_COL_W + name_region_w + COL_PAD
    name_col_w = name_region_w - COL_PAD * 1.5
    detail_col_w = detail_region_w - COL_PAD * 1.5

    card_top_y = ty(lower_top)

    # The package list can now run to 10-12+ rows depending on how many
    # items staff ticks (Advance Payment, technique note, etc. added extra
    # rows over time). Rather than a fixed font/row-height that could
    # overflow into the disclaimer/footer on a long list, try progressively
    # more compact row settings until the whole table fits in the space
    # available above the disclaimer + footer, reserving RESERVED_BOTTOM pt.
    # The Terms & Conditions card also lives in this reserved zone now
    # (everything must fit on one A4 page), so its height is measured
    # up front and folded into the reservation.
    terms_gap_above = 10
    terms_h = _terms_card(c, margin, content_w, 0, draw=False)
    RESERVED_BOTTOM = 96 + terms_gap_above + terms_h  # disclaimer (2 lines) + gaps + footer height + terms card
    budget_h = card_top_y - RESERVED_BOTTOM

    # (name_size, detail_size, min_row_h, row_pad, header_h)
    # Line height is derived from each font size at a fixed 1.35 ratio
    # (within the 1.3-1.4 range) instead of being hand-tuned per variant,
    # so name/detail text always keeps the same visual rhythm.
    # row_pad below is the TOTAL top+bottom padding budget for a row (not
    # per-side) so the auto-fit fallback chain still reliably lands
    # everything on one A4 page for long package lists, same as before -
    # only the normal/compact tiers (used for typical, shorter lists) get
    # the more generous premium spacing. line_h_ratio stays within the
    # 1.3-1.4 range requested, tightened toward 1.3 only for the two
    # fallback tiers that exist specifically to keep long lists on one page.
    LAYOUT_VARIANTS = [
        (9.3, 8.6, 32, 16, 27, 1.35),   # normal - matches the original design
        (8.7, 8.0, 27, 12, 24, 1.35),   # compact - kicks in for longer lists
        (8.0, 7.4, 20, 6, 19, 1.3),     # extra-compact - fallback for longer lists
        (7.4, 6.9, 15, 3, 16, 1.3),     # ultra-compact - everything on one A4 page
    ]

    chosen = LAYOUT_VARIANTS[-1]
    row_heights = []
    table_h = 0
    for variant in LAYOUT_VARIANTS:
        name_size, detail_size, min_row_h, row_pad, hdr_h, line_h_ratio = variant
        name_line_h = name_size * line_h_ratio
        detail_line_h = detail_size * line_h_ratio
        heights = []
        for item in items:
            name_lines = _wrap_text(item["name"], "Helvetica", name_size, name_col_w)
            detail_lines = _wrap_text(item["detail"], "Helvetica", detail_size, detail_col_w)
            name_block_h = len(name_lines) * name_line_h
            detail_block_h = len(detail_lines) * detail_line_h
            content_h = max(name_block_h, detail_block_h, name_line_h)
            heights.append(max(min_row_h, row_pad + content_h))
        candidate_h = hdr_h + 6 + sum(heights) + 10
        chosen, row_heights, table_h = variant, heights, candidate_h
        if candidate_h <= budget_h:
            break  # this variant fits - stop here

    NAME_SIZE, DETAIL_SIZE, MIN_ROW_H, ROW_PAD, header_h, CHOSEN_RATIO = chosen
    NAME_LINE_H = NAME_SIZE * CHOSEN_RATIO
    DETAIL_LINE_H = DETAIL_SIZE * CHOSEN_RATIO
    n_rows = max(len(items), 1)

    # The check-icon circle used to be a fixed 9pt radius (18pt across) no
    # matter how tight the rows got. On long package lists the auto-fit
    # logic above shrinks row height down to as little as 15pt to keep
    # everything on one page, so that fixed-size circle no longer fit
    # inside a row and started overlapping the circles directly above/below
    # it. The icon is now sized off the *shortest* row actually present in
    # this table, with a few pt of breathing room on top and bottom, and
    # never allowed below a small legible floor - so icons always sit
    # cleanly inside their own row with visible gaps to their neighbors.
    ICON_R = min(9.0, (min(row_heights) - 2) / 2) if row_heights else 9.0
    ICON_R = max(7.0, ICON_R)
    CHECK_SIZE = ICON_R * 0.4
    _round_rect(c, card_x, card_top_y - table_h, table_w, table_h, r=10, fill=WHITE)

    # section title above the card
    c.setFillColor(DARK)
    c.circle(card_x + 12, ty(lower_top - 26), 12, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(DARK)
    c.drawString(card_x + 30, ty(lower_top - 22), "PACKAGE INCLUDES")

    tbl_y = lower_top
    c.setFillColor(TEAL_DEEP)
    c.roundRect(card_x, ty(tbl_y + header_h), table_w, header_h, 6, stroke=0, fill=1)
    c.rect(card_x, ty(tbl_y + header_h) + header_h / 2, table_w, header_h / 2, stroke=0, fill=1)
    # Vertically center the header labels within header_h (which varies by
    # layout variant) instead of using a fixed baseline offset.
    header_font_size = 9.2 if header_h >= 25 else (8.6 if header_h >= 22 else 8.0)
    c.setFont("Helvetica-Bold", header_font_size)
    c.setFillColor(WHITE)
    header_label_y = tbl_y + header_h / 2 + header_font_size * 0.32
    c.drawString(card_x + name_col_x, ty(header_label_y), "SERVICES INCLUDED")
    c.drawString(card_x + detail_col_x, ty(header_label_y), "DETAILS")

    DIVIDER_INSET = 12  # keeps divider lines clear of the rounded table border
    ry = tbl_y + header_h + 6
    for idx, item in enumerate(items):
        row_h2 = row_heights[idx]
        row_y_top = ry
        if idx % 2 == 1:
            c.setFillColor(HexColor("#FAFBFB"))
            c.rect(card_x, ty(row_y_top + row_h2), table_w, row_h2, stroke=0, fill=1)
        cy_mid = row_y_top + row_h2 / 2
        center_pdf_y = ty(cy_mid)

        # Icon is anchored to THIS row's own vertical midpoint (row_y_top +
        # row_h2 / 2), never to a running/independent top-to-bottom offset,
        # so it always tracks its row even as row heights vary with wrapped
        # text. The tiny nudge (CHECK_SIZE * 0.1) corrects for the vector
        # checkmark glyph's own bounding box being drawn slightly bottom-
        # heavy, so the *visible* checkmark - not just its invisible anchor
        # point - lines up with the row's true center. ICON_R/CHECK_SIZE are
        # pre-scaled to the shortest row in this table so the circle always
        # fits inside its row instead of overlapping its neighbors.
        icon_cx = card_x + ICON_COL_W / 2
        _icon_circle(c, icon_cx, center_pdf_y, ICON_R, fill=HexColor("#E7F3F2"))
        _draw_check_icon(c, icon_cx, center_pdf_y - CHECK_SIZE * 0.1, CHECK_SIZE, color=TEAL_DEEP)

        name_lines = _wrap_text(item["name"], "Helvetica", NAME_SIZE, name_col_w)
        detail_lines = _wrap_text(item["detail"], "Helvetica", DETAIL_SIZE, detail_col_w)

        c.setFont("Helvetica", NAME_SIZE)
        c.setFillColor(DARK)
        n_block_h = (len(name_lines) - 1) * NAME_LINE_H
        n_start_y = center_pdf_y + n_block_h / 2 - 3.3
        for li, line in enumerate(name_lines):
            c.drawString(card_x + name_col_x, n_start_y - li * NAME_LINE_H, line)

        c.setFont("Helvetica", DETAIL_SIZE)
        c.setFillColor(GRAY_TXT)
        d_block_h = (len(detail_lines) - 1) * DETAIL_LINE_H
        d_start_y = center_pdf_y + d_block_h / 2 - 3.3
        for li, line in enumerate(detail_lines):
            c.drawString(card_x + detail_col_x, d_start_y - li * DETAIL_LINE_H, line)

        # Divider stops short of the rounded table border on both sides and
        # never runs directly under the last row (no divider beneath the
        # final item, so it doesn't collide with the card's bottom curve).
        if idx < len(items) - 1:
            c.setStrokeColor(BORDER)
            c.line(card_x + DIVIDER_INSET, ty(row_y_top + row_h2),
                   card_x + table_w - DIVIDER_INSET, ty(row_y_top + row_h2))
        ry += row_h2

    # ---- Investment card (right column) ----
    ix = card_x + table_w + gap
    iw = content_w - table_w - gap
    ih = table_h + 26
    iy_top = ty(lower_top - 26)
    _round_rect(c, ix, iy_top - ih, iw, ih, r=10, fill=WHITE)

    head_h = 46
    c.setFillColor(TEAL_DEEP)
    c.roundRect(ix, iy_top - head_h, iw, head_h, 10, stroke=0, fill=1)
    c.rect(ix, iy_top - head_h, iw, head_h / 2, stroke=0, fill=1)
    _icon_circle(c, ix + iw / 2, iy_top - 11, 9, fill=WHITE)
    _draw_bi_glyph(c, ix + iw / 2, iy_top - 11, BI_GEM, 9.5, TEAL_DEEP)
    _center_text(c, ix + iw / 2, iy_top - 29, "INVESTMENT FOR", "Helvetica-Bold", 8.6, WHITE)
    _center_text(c, ix + iw / 2, iy_top - 39, "HAIR RESTORATION", "Helvetica-Bold", 8.6, WHITE)

    price_y = iy_top - head_h - 22
    price_text = f"Rs {total:,.0f}"
    c.setFont("Helvetica-Bold", 19)
    c.setFillColor(TEAL_DEEP)
    pw = stringWidth(price_text, "Helvetica-Bold", 19)
    c.drawString(ix + (iw - pw) / 2, price_y, price_text)

    # Clearer GST breakdown per feedback - shows the pre-GST amount and the
    # actual GST rupees, then a bold "Final Payable Amount" so there's no
    # ambiguity about whether the headline price above already includes GST.
    ny = price_y - 16
    if gst_applied and gst_amount:
        pre_gst = total - gst_amount
        note_lines = _wrap_text(
            f"Rs {pre_gst:,.0f} + 5% GST (Rs {gst_amount:,.0f}) \u2014 applicable on surgery charges only",
            "Helvetica", 7.4, iw - 20)
        for line in note_lines:
            _center_text(c, ix + iw / 2, ny, line, "Helvetica", 7.4, GRAY_TXT)
            ny -= 9.5
        ny -= 3
        _center_text(c, ix + iw / 2, ny, f"Final Payable Amount: Rs {total:,.0f}",
                     "Helvetica-Bold", 8.2, DARK)
        ny -= 12
    else:
        note = "Inclusive of all charges (GST not applicable)"
        note_lines = _wrap_text(note, "Helvetica", 7.6, iw - 20)
        for line in note_lines:
            _center_text(c, ix + iw / 2, ny, line, "Helvetica", 7.6, GRAY_TXT)
            ny -= 10

    c.setStrokeColor(BORDER)
    c.line(ix + 12, ny - 4, ix + iw - 12, ny - 4)

    trust_items = [
        ("check", "ABHRS Certified"),
        ("star", "Google 4.9 Stars"),
        ("check", "Cutting Edge Medical Standards"),
    ]
    # Distribute the (now shorter) trust list evenly across the remaining
    # card height so it still reads as an intentional, balanced block
    # instead of leaving a big empty gap at the bottom of the card.
    trust_top = ny - 18
    trust_bottom_limit = (iy_top - ih) + 16
    available_h = max(trust_top - trust_bottom_limit, 0)
    item_gap = available_h / len(trust_items) if trust_items else 0
    item_gap = max(24, min(item_gap, 34))

    ty_cursor = trust_top
    for i, (icon_kind, t) in enumerate(trust_items):
        # Stop drawing gracefully if we somehow run out of card room rather
        # than overflowing past the card's rounded-rect bottom edge.
        if ty_cursor < trust_bottom_limit:
            break
        if icon_kind == "star":
            _draw_star(c, ix + 18, ty_cursor + 2, 4.5)
        else:
            _icon_circle(c, ix + 18, ty_cursor + 2, 6, fill=HexColor("#E7F3F2"))
            _draw_check_icon(c, ix + 18, ty_cursor + 1, 2.6, color=TEAL_DEEP)
        lines = _wrap_text(t, "Helvetica", 8, iw - 40)
        yy = ty_cursor
        c.setFont("Helvetica", 8)
        c.setFillColor(DARK)
        for line in lines:
            c.drawString(ix + 30, yy, line)
            yy -= 10
        ty_cursor -= item_gap

    # ================= TERMS & CONDITIONS (same page, below both cards) =================
    terms_top = lower_top + table_h + terms_gap_above
    _terms_card(c, margin, content_w, terms_top, draw=True)

    # ================= FIXED DISCLAIMER (not editable by staff) =================
    # Fixed just above the footer. The Package Includes table above uses
    # progressively more compact row spacing (see LAYOUT_VARIANTS / budget_h)
    # specifically so it never grows into this reserved zone.
    footer_h = 40
    footer_y = 16  # footer is always pinned to the bottom of the page
    disc_y1 = footer_y + footer_h + 20
    disc_y2 = disc_y1 - 10
    c.setFont("Helvetica-Oblique", 7.3)
    c.setFillColor(GRAY_TXT)
    c.drawString(margin, disc_y1, "* This budget and graft estimate may vary during in-person consultation.")
    c.drawString(margin, disc_y2, "** Subject to change as per hair follicle diameter, density and scalp width.")

    # ================= FOOTER =================
    _draw_footer(c, margin, content_w, footer_y, patient, show_date_line=True)

    c.showPage()
    c.save()
