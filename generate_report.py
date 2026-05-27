"""
College Debt Outcome Mismatch Analyzer — PDF Report Generator
Run from inside your college-debt-analyzer folder:
    python generate_report.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.colors import HexColor

# ── REPORTLAB COLORS ─────────────────────────────────
RL_ACCENT     = HexColor('#1A56DB')
RL_RED        = HexColor('#d32f2f')
RL_GREEN      = HexColor('#2e7d32')
RL_ORANGE     = HexColor('#f57c00')
RL_LIGHT_GRAY = HexColor('#f5f5f5')
RL_MID_GRAY   = HexColor('#888888')
RL_TEXT       = HexColor('#1a1a1a')
RL_WHITE      = HexColor('#ffffff')
RL_DD         = HexColor('#dddddd')
RL_EEF        = HexColor('#EEF2FF')
RL_FFF3F3     = HexColor('#FFF3F3')

# ── MATPLOTLIB COLORS ────────────────────────────────
MPL_BLUE   = '#1A56DB'
MPL_RED    = '#d32f2f'
MPL_GREEN  = '#2e7d32'
MPL_ORANGE = '#f57c00'
MPL_DARK   = '#333333'
MPL_LIGHT  = '#fafafa'

# ── STYLES ───────────────────────────────────────────
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'CT', fontName='Helvetica-Bold', fontSize=26,
    textColor=RL_TEXT, spaceAfter=4,
    alignment=TA_LEFT, leading=32)

subtitle_style = ParagraphStyle(
    'ST', fontName='Helvetica', fontSize=12,
    textColor=RL_MID_GRAY, spaceAfter=4,
    alignment=TA_LEFT)

h1_style = ParagraphStyle(
    'H1', fontName='Helvetica-Bold', fontSize=16,
    textColor=RL_ACCENT, spaceBefore=16,
    spaceAfter=6, leading=20)

h2_style = ParagraphStyle(
    'H2', fontName='Helvetica-Bold', fontSize=12,
    textColor=RL_TEXT, spaceBefore=10,
    spaceAfter=5, leading=15)

body_style = ParagraphStyle(
    'BD', fontName='Helvetica', fontSize=10,
    textColor=RL_TEXT, spaceAfter=5,
    leading=15, alignment=TA_JUSTIFY)

caption_style = ParagraphStyle(
    'CP', fontName='Helvetica-Oblique', fontSize=8.5,
    textColor=RL_MID_GRAY, spaceAfter=8,
    alignment=TA_CENTER)

finding_style = ParagraphStyle(
    'FD', fontName='Helvetica', fontSize=10,
    textColor=RL_TEXT, spaceAfter=4,
    leading=15, leftIndent=14)

# ── HELPERS ──────────────────────────────────────────
def fig_to_image(fig, width=6.0*inch):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130,
                bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    img = Image(buf, width=width)
    img.hAlign = 'CENTER'
    return img

def small_barh(labels, values, title, color,
               xlabel='', vline=None, vline_label=''):
    """Compact horizontal bar chart that always fits on a page."""
    n = len(labels)
    h = max(2.2, min(n * 0.28 + 0.5, 3.8))
    fig, ax = plt.subplots(figsize=(7.5, h))
    vals = [float(v) for v in values]
    labs = [str(l) for l in labels]
    bar_colors = (
        [MPL_RED if v < 1.0 else color for v in vals]
        if vline == 1.0 else [color] * len(vals)
    )
    ax.barh(labs, vals, color=bar_colors,
            edgecolor='white', linewidth=0.3)
    if vline is not None:
        ax.axvline(x=vline, color=MPL_DARK, linestyle='--',
                   linewidth=1.2, label=vline_label)
        ax.legend(fontsize=8, framealpha=0.8)
    ax.set_title(title, fontsize=10, fontweight='bold',
                 color='#1a1a1a', pad=8)
    ax.set_xlabel(xlabel, fontsize=8, color='#555555')
    ax.tick_params(axis='y', labelsize=7, colors=MPL_DARK)
    ax.tick_params(axis='x', labelsize=7, colors='#555555')
    ax.set_facecolor(MPL_LIGHT)
    fig.patch.set_facecolor('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.invert_yaxis()
    plt.tight_layout(pad=0.5)
    return fig

def tbl(data, col_widths, header_bg=None):
    """Quick table builder."""
    t = Table(data, colWidths=col_widths)
    bg = header_bg or RL_ACCENT
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  bg),
        ('TEXTCOLOR',     (0,0),(-1,0),  RL_WHITE),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,0),(-1,-1), 8.5),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [RL_LIGHT_GRAY, RL_WHITE]),
        ('ALIGN',         (0,0),(-1,-1), 'LEFT'),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('GRID',          (0,0),(-1,-1), 0.3, RL_DD),
    ]))
    return t

# ── LOAD DATA ─────────────────────────────────────────
print("Loading data...")
try:
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///college_debt.db")
    df      = pd.read_sql("SELECT * FROM colleges", engine)
    flagged = pd.read_sql("SELECT * FROM flagged_schools_clean", engine)
    print(f"  Loaded {len(df):,} schools, {len(flagged)} flagged")
except Exception as e:
    print(f"ERROR: {e}")
    print("Run from inside college-debt-analyzer/ folder")
    raise

# Pre-compute values used across sections
clean_scores  = df['value_score'].dropna()
national_mean = float(clean_scores.mean())
below_be      = int(len(df[df['value_score'] < 1.0]))

state_scores = (
    df.groupby('state')['value_score']
    .agg(['mean','count'])
    .reset_index()
)
state_scores.columns = ['state','avg_value_score','num_schools']
state_scores = (
    state_scores[state_scores['num_schools'] >= 3]
    .sort_values('avg_value_score', ascending=False)
    .reset_index(drop=True)
)
state_scores.index += 1

nj_rows      = state_scores[state_scores['state'] == 'NJ']
nj_position  = int(nj_rows.index[0]) if len(nj_rows) > 0 else 'N/A'
nj_score     = float(nj_rows['avg_value_score'].values[0]) \
               if len(nj_rows) > 0 else 0.0

# ── BUILD STORY ───────────────────────────────────────
print("Building PDF...")
story = []

# ════════════════════════════════════════════════════
# COVER
# ════════════════════════════════════════════════════
story.append(Spacer(1, 0.5*inch))
story.append(Paragraph("College Debt Outcome", title_style))
story.append(Paragraph("Mismatch Analyzer", title_style))
story.append(Spacer(1, 0.08*inch))
story.append(HRFlowable(width="100%", thickness=3,
                        color=RL_ACCENT, spaceAfter=10))
story.append(Paragraph(
    "Surfacing predatory academic programs using federal data — "
    "because students deserve to know what a degree actually costs.",
    subtitle_style))
story.append(Spacer(1, 0.25*inch))

meta = [
    ["Author",       "Rushil Pandya · CS Sophomore · Rutgers University '28"],
    ["Data Source",  "U.S. Department of Education — College Scorecard API"],
    ["Scope",        "6,322 institutions analyzed · 4,500 with complete outcome data"],
    ["Published",    datetime.now().strftime("%B %Y")],
    ["GitHub",       "github.com/rushil1356/College-debt-analyzer"],
]
mt = Table(meta, colWidths=[1.2*inch, 5.3*inch])
mt.setStyle(TableStyle([
    ('FONTNAME',      (0,0),(0,-1), 'Helvetica-Bold'),
    ('FONTNAME',      (1,0),(1,-1), 'Helvetica'),
    ('FONTSIZE',      (0,0),(-1,-1),9),
    ('TEXTCOLOR',     (0,0),(0,-1), RL_ACCENT),
    ('TEXTCOLOR',     (1,0),(1,-1), RL_TEXT),
    ('ROWBACKGROUNDS',(0,0),(-1,-1),[RL_LIGHT_GRAY, RL_WHITE]),
    ('TOPPADDING',    (0,0),(-1,-1),5),
    ('BOTTOMPADDING', (0,0),(-1,-1),5),
    ('LEFTPADDING',   (0,0),(-1,-1),8),
    ('GRID',          (0,0),(-1,-1),0.3, RL_DD),
]))
story.append(mt)
story.append(Spacer(1, 0.3*inch))

kpi = [[
    f"{len(df):,}\nInstitutions\nAnalyzed",
    f"{len(flagged)}\nFlagged\nPredatory",
    f"{national_mean:.2f}\nNational Avg\nValue Score",
    f"{below_be}\nBelow\nBreak-even",
]]
kt = Table(kpi, colWidths=[1.55*inch]*4)
kt.setStyle(TableStyle([
    ('BACKGROUND',  (0,0),(0,0), RL_ACCENT),
    ('BACKGROUND',  (1,0),(1,0), RL_RED),
    ('BACKGROUND',  (2,0),(2,0), RL_GREEN),
    ('BACKGROUND',  (3,0),(3,0), RL_ORANGE),
    ('TEXTCOLOR',   (0,0),(-1,-1), RL_WHITE),
    ('FONTNAME',    (0,0),(-1,-1), 'Helvetica-Bold'),
    ('FONTSIZE',    (0,0),(-1,-1), 11),
    ('ALIGN',       (0,0),(-1,-1), 'CENTER'),
    ('VALIGN',      (0,0),(-1,-1), 'MIDDLE'),
    ('ROWHEIGHT',   (0,0),(-1,-1), 65),
]))
story.append(kt)
story.append(PageBreak())

# ════════════════════════════════════════════════════
# SECTION 1 — THE PROBLEM
# ════════════════════════════════════════════════════
story.append(Paragraph("1. The Problem", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=RL_ACCENT, spaceAfter=8))
story.append(Paragraph(
    "Every year, over <b>2 million Americans</b> enroll in college programs "
    "without knowing a fundamental truth — some degrees cost more than they "
    "will ever pay back. The federal government collects this data. It is "
    "public, free, and comprehensive. But it is buried in machine-readable "
    "files that no student, parent, or counselor has time to interpret.",
    body_style))
story.append(Paragraph(
    "This analysis surfaces what that data actually shows — which institutions "
    "leave graduates financially worse off, and which deliver genuine value.",
    body_style))
story.append(Paragraph("The Value Score", h2_style))
story.append(Paragraph(
    "This project introduces a single metric — the <b>Value Score</b>:",
    body_style))

ft = Table(
    [["Value Score  =  Median Earnings (10 yrs out)  /  Median Debt at Graduation"]],
    colWidths=[6.5*inch])
ft.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),(-1,-1), RL_EEF),
    ('TEXTCOLOR',     (0,0),(-1,-1), RL_ACCENT),
    ('FONTNAME',      (0,0),(-1,-1), 'Helvetica-Bold'),
    ('FONTSIZE',      (0,0),(-1,-1), 10),
    ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
    ('TOPPADDING',    (0,0),(-1,-1), 12),
    ('BOTTOMPADDING', (0,0),(-1,-1), 12),
    ('BOX',           (0,0),(-1,-1), 1.5, RL_ACCENT),
]))
story.append(ft)
story.append(Spacer(1, 0.08*inch))

interp = tbl(
    [["Range","Meaning","Assessment"],
     ["Above 1.0","Earn more than borrowed","Healthy"],
     ["Equals 1.0","Earn exactly what borrowed","Break-even"],
     ["Below 1.0","Earn less than borrowed","Red flag"],
     ["National avg",f"{national_mean:.2f} — most colleges OK","Baseline"]],
    [1.2*inch, 3.2*inch, 1.8*inch])
story.append(interp)
story.append(PageBreak())

# ════════════════════════════════════════════════════
# SECTION 2 — NATIONAL PICTURE
# ════════════════════════════════════════════════════
story.append(Paragraph("2. The National Picture", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=RL_ACCENT, spaceAfter=8))
story.append(Paragraph(
    "The headline finding is reassuring: <b>the American college system is "
    "not broken</b>. The vast majority of institutions provide graduates with "
    "reasonable returns. The problem is concentrated, not systemic.",
    body_style))

fig_dist, ax_dist = plt.subplots(figsize=(7.5, 3.2))
ax_dist.hist(clean_scores.values, bins=50, color=MPL_BLUE,
             edgecolor='white', linewidth=0.3, alpha=0.85)
ax_dist.axvline(x=1.0, color=MPL_RED, linestyle='--',
                linewidth=1.8, label='Break-even (1.0)')
ax_dist.axvline(x=national_mean, color=MPL_ORANGE,
                linestyle='--', linewidth=1.8,
                label=f'Mean ({national_mean:.2f})')
ax_dist.set_xlabel('Value Score', fontsize=8)
ax_dist.set_ylabel('Institutions', fontsize=8)
ax_dist.set_title('Value Score Distribution — All US Colleges',
                  fontsize=10, fontweight='bold')
ax_dist.legend(fontsize=8)
ax_dist.set_facecolor(MPL_LIGHT)
fig_dist.patch.set_facecolor('white')
ax_dist.spines['top'].set_visible(False)
ax_dist.spines['right'].set_visible(False)
plt.tight_layout(pad=0.5)
story.append(fig_to_image(fig_dist, width=6.0*inch))
story.append(Paragraph(
    "Figure 1 — Right-skewed distribution with mean 3.22. "
    "Most schools deliver healthy returns.",
    caption_style))

for f in [
    f"<b>Mean of {national_mean:.2f}</b> — average graduate earns "
    f"${national_mean:.2f} for every $1.00 borrowed.",
    "<b>Right-skewed</b> — most schools cluster 2–4, with a long tail "
    "of high-performing vocational programs.",
    f"<b>Only {below_be} institutions (1.0%)</b> fall below break-even — "
    "a concentrated, identifiable problem.",
]:
    story.append(Paragraph(f"• {f}", finding_style))
story.append(PageBreak())

# ════════════════════════════════════════════════════
# SECTION 3 — WORST VALUE SCHOOLS
# ════════════════════════════════════════════════════
story.append(Paragraph("3. Worst Value Institutions", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=RL_ACCENT, spaceAfter=8))
story.append(Paragraph(
    "The 20 schools with the lowest value scores represent the clearest "
    "cases of financial mismatch — graduates carry debt that equals or "
    "exceeds their earnings a full decade after enrollment.",
    body_style))

b20 = df.nsmallest(20, 'value_score').copy()
b20['label'] = (b20['school_name'].str[:30] +
                ' (' + b20['state'] + ')')
story.append(fig_to_image(
    small_barh(b20['label'].values, b20['value_score'].values,
               '20 Worst Value Schools',
               MPL_ORANGE,
               xlabel='Value Score (red = below break-even)',
               vline=1.0, vline_label='Break-even'),
    width=6.0*inch))
story.append(Paragraph(
    "Figure 2 — Red bars indicate graduates earning less than borrowed.",
    caption_style))

story.append(Paragraph("Bottom 10 Schools", h2_style))
b10 = df.nsmallest(10, 'value_score')[
    ['school_name','state','median_earnings',
     'median_debt','value_score']].copy()
b10['median_earnings'] = b10['median_earnings'].apply(
    lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
b10['median_debt'] = b10['median_debt'].apply(
    lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
b10['value_score'] = b10['value_score'].apply(
    lambda x: f"{x:.3f}")
b10['school_name'] = b10['school_name'].str[:34]

td = [["School","St","Earnings","Debt","Score"]]
for _, r in b10.iterrows():
    td.append([r['school_name'], r['state'],
               r['median_earnings'], r['median_debt'],
               r['value_score']])
wt = Table(td,
    colWidths=[2.9*inch, 0.5*inch, 1.0*inch, 1.0*inch, 0.7*inch])
wt.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),(-1,0),  RL_ACCENT),
    ('TEXTCOLOR',     (0,0),(-1,0),  RL_WHITE),
    ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
    ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
    ('FONTSIZE',      (0,0),(-1,-1), 8),
    ('ROWBACKGROUNDS',(0,1),(-1,-1), [RL_FFF3F3, RL_WHITE]),
    ('ALIGN',         (1,0),(-1,-1), 'CENTER'),
    ('ALIGN',         (0,0),(0,-1),  'LEFT'),
    ('TOPPADDING',    (0,0),(-1,-1), 5),
    ('BOTTOMPADDING', (0,0),(-1,-1), 5),
    ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ('GRID',          (0,0),(-1,-1), 0.3, RL_DD),
    ('TEXTCOLOR',     (4,1),(4,-1),  RL_RED),
    ('FONTNAME',      (4,1),(4,-1),  'Helvetica-Bold'),
]))
story.append(wt)
story.append(PageBreak())

# ════════════════════════════════════════════════════
# SECTION 4 — ANOMALY DETECTION
# ════════════════════════════════════════════════════
story.append(Paragraph("4. Anomaly Detection", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=RL_ACCENT, spaceAfter=8))
story.append(Paragraph(
    "A single metric misses institutions that perform poorly across "
    "multiple dimensions simultaneously. An <b>Isolation Forest</b> model "
    "was trained on four features — value score, median debt, completion "
    "rate, and admission rate — to flag multi-dimensional outliers.",
    body_style))

story.append(tbl(
    [["Parameter","Value"],
     ["Algorithm","Isolation Forest (scikit-learn)"],
     ["Features","value_score, median_debt, completion_rate, admission_rate"],
     ["Contamination","5% expected outlier rate"],
     ["Scaling","StandardScaler applied before fitting"],
     ["Flagged","69 institutions after data quality filtering"],
     ["Filters","completion_rate > 0 and student_size >= 100"]],
    [1.7*inch, 4.8*inch]))
story.append(Spacer(1, 0.1*inch))

fc = flagged.nsmallest(15, 'value_score').copy()
fc['label'] = (fc['school_name'].str[:28] +
               ' (' + fc['state'] + ')')
story.append(fig_to_image(
    small_barh(fc['label'].values, fc['value_score'].values,
               'Top 15 Flagged Institutions — Value Score',
               MPL_RED, xlabel='Value Score',
               vline=1.0, vline_label='Break-even'),
    width=6.0*inch))
story.append(Paragraph(
    "Figure 3 — Flagged as outliers across all four dimensions simultaneously.",
    caption_style))

story.append(Paragraph("Data Quality Nuance", h2_style))
story.append(Paragraph(
    "Several flagged institutions have acceptable value scores but zero "
    "completion rates — reflecting newly launched programs with no graduates "
    "yet, not poor outcomes. Addressed via quality filtering.",
    body_style))
story.append(PageBreak())

# ════════════════════════════════════════════════════
# SECTION 5 — STATE ANALYSIS
# ════════════════════════════════════════════════════
story.append(Paragraph("5. State-Level Analysis", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=RL_ACCENT, spaceAfter=8))
story.append(Paragraph(
    "Value scores vary significantly by state, reflecting differences in "
    "tuition, local labor markets, cost of living, and institution mix.",
    body_style))

# Top 10 states — small chart
top10 = state_scores.head(10)
fig_top, ax_top = plt.subplots(figsize=(7, 2.4))
ax_top.barh(list(top10['state']),
            [float(v) for v in top10['avg_value_score']],
            color=MPL_GREEN, edgecolor='white', linewidth=0.3)
ax_top.set_title('Top 10 Best Value States',
                 fontsize=9, fontweight='bold')
ax_top.set_xlabel('Avg Value Score', fontsize=7)
ax_top.tick_params(labelsize=7)
ax_top.set_facecolor(MPL_LIGHT)
ax_top.spines['top'].set_visible(False)
ax_top.spines['right'].set_visible(False)
ax_top.invert_yaxis()
fig_top.patch.set_facecolor('white')
plt.tight_layout(pad=0.4)
story.append(fig_to_image(fig_top, width=5.5*inch))

story.append(Spacer(1, 0.08*inch))

# Bottom 10 states — small chart
bot10 = state_scores.tail(10).sort_values('avg_value_score')
fig_bot, ax_bot = plt.subplots(figsize=(7, 2.4))
ax_bot.barh(list(bot10['state']),
            [float(v) for v in bot10['avg_value_score']],
            color=MPL_RED, edgecolor='white', linewidth=0.3)
ax_bot.set_title('Bottom 10 Worst Value States',
                 fontsize=9, fontweight='bold')
ax_bot.set_xlabel('Avg Value Score', fontsize=7)
ax_bot.tick_params(labelsize=7)
ax_bot.set_facecolor(MPL_LIGHT)
ax_bot.spines['top'].set_visible(False)
ax_bot.spines['right'].set_visible(False)
ax_bot.invert_yaxis()
fig_bot.patch.set_facecolor('white')
plt.tight_layout(pad=0.4)
story.append(fig_to_image(fig_bot, width=5.5*inch))

story.append(Paragraph(
    "Figure 4 — Best and worst value states. "
    "States with fewer than 3 institutions excluded.",
    caption_style))

for f in [
    f"<b>New Jersey ranks {nj_position}th nationally</b> (avg {nj_score:.2f}). "
    "Top 2 individual value schools in the country are both NJ institutions.",
    "<b>Wyoming leads nationally</b> — low state tuition plus strong "
    "energy-sector wages.",
    "<b>Puerto Rico ranks lowest</b> — structural economic conditions, "
    "not institutional quality. A geographic bias in the metric.",
    "<b>School size is irrelevant</b> — r = 0.09 correlation between "
    "enrollment and value score.",
]:
    story.append(Paragraph(f"• {f}", finding_style))
story.append(PageBreak())

# ════════════════════════════════════════════════════
# SECTION 6 — HOW THIS HELPS STUDENTS
# ════════════════════════════════════════════════════
story.append(Paragraph("6. How This Helps Students", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=RL_ACCENT, spaceAfter=8))
story.append(Paragraph(
    "The interactive Streamlit dashboard translates 4,500 rows of federal "
    "data into four practical tools.",
    body_style))

story.append(tbl(
    [["Tool","What It Does","Who It Helps"],
     ["Value Rankings",
      "Sort 4,500 schools by earnings/debt, filter by state",
      "Students comparing schools locally"],
     ["Flagged List",
      "69 schools flagged as multi-dimensional outliers",
      "Anyone doing due diligence"],
     ["Plain English Queries",
      "Ask questions in plain English — Claude API converts to SQL",
      "Parents, counselors, non-technical users"],
     ["State Comparison",
      "Compare all 50 states with school-level drill-down",
      "Students considering out-of-state options"]],
    [1.4*inch, 2.8*inch, 2.3*inch]))

story.append(Spacer(1, 0.1*inch))
story.append(Paragraph("Limitations", h2_style))
for l in [
    "<b>10-year earnings median</b> — early career looks different in some fields.",
    "<b>Institution-level debt</b> — not program-level; medical and liberal "
    "arts programs share the same figure.",
    "<b>Correlation not causation</b> — low score reflects outcomes, "
    "not instruction quality.",
    "<b>Geographic wage bias</b> — lower-wage states produce lower scores "
    "regardless of school quality.",
]:
    story.append(Paragraph(f"• {l}", finding_style))
story.append(PageBreak())

# ════════════════════════════════════════════════════
# SECTION 7 — SUMMARY
# ════════════════════════════════════════════════════
story.append(Paragraph("7. Summary of Findings", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=RL_ACCENT, spaceAfter=8))

st = Table(
    [["#","Finding","Implication"],
     ["1", f"Mean value score {national_mean:.2f} across 4,500 institutions",
      "Most colleges are financially sound investments"],
     ["2", f"{below_be} schools below break-even (score < 1.0)",
      "Graduates earn less than borrowed — concentrated risk"],
     ["3", "69 institutions flagged as multi-dimensional outliers",
      "Poor across debt, earnings AND completion simultaneously"],
     ["4", f"NJ ranks {nj_position}th nationally; top 2 schools both in NJ",
      "Strong local value without leaving state"],
     ["5", "School size: r = 0.09 correlation with value",
      "Brand and enrollment are poor proxies for ROI"],
     ["6", "Flagged schools cluster at $5K-$25K debt",
      "Moderate cost can still mean poor outcomes"],
     ["7", "Puerto Rico has highest flagged concentration",
      "Geographic wage gaps create structural bias"]],
    colWidths=[0.3*inch, 3.1*inch, 3.1*inch])
st.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),(-1,0),  RL_ACCENT),
    ('TEXTCOLOR',     (0,0),(-1,0),  RL_WHITE),
    ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
    ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
    ('FONTSIZE',      (0,0),(-1,-1), 8.5),
    ('ROWBACKGROUNDS',(0,1),(-1,-1), [RL_LIGHT_GRAY, RL_WHITE]),
    ('ALIGN',         (0,0),(0,-1),  'CENTER'),
    ('FONTNAME',      (0,1),(0,-1),  'Helvetica-Bold'),
    ('TEXTCOLOR',     (0,1),(0,-1),  RL_ACCENT),
    ('VALIGN',        (0,0),(-1,-1), 'TOP'),
    ('TOPPADDING',    (0,0),(-1,-1), 6),
    ('BOTTOMPADDING', (0,0),(-1,-1), 6),
    ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ('GRID',          (0,0),(-1,-1), 0.3, RL_DD),
]))
story.append(st)
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph(
    "This analysis demonstrates that the college debt crisis, while real, "
    "is not uniformly distributed. The federal data exists to identify "
    "exactly which institutions are leaving students worse off — and this "
    "tool makes that identification accessible to anyone.",
    body_style))
story.append(Spacer(1, 0.1*inch))
story.append(HRFlowable(width="100%", thickness=1,
                        color=RL_DD, spaceAfter=6))
story.append(Paragraph(
    "Rushil Pandya · CS Sophomore · Rutgers University '28 · "
    "github.com/rushil1356/College-debt-analyzer · "
    "Data: U.S. Dept of Education College Scorecard API",
    caption_style))

# ── GENERATE ──────────────────────────────────────────
output_path = "College_Debt_Outcome_Mismatch_Analyzer_Report.pdf"
doc = SimpleDocTemplate(
    output_path, pagesize=letter,
    rightMargin=0.8*inch, leftMargin=0.8*inch,
    topMargin=0.8*inch,   bottomMargin=0.8*inch,
    title="College Debt Outcome Mismatch Analyzer",
    author="Rushil Pandya"
)
doc.build(story)
print(f"\nDone — {output_path}")
print(f"Size: {os.path.getsize(output_path)/1024:.0f} KB")