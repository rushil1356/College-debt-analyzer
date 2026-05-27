"""
College Debt Outcome Mismatch Analyzer — PDF Report Generator
Run this script from inside your college-debt-analyzer folder:
    python generate_report.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.colors import HexColor

# ── COLORS ───────────────────────────────────────────
DARK       = HexColor('#0f1117')
ACCENT     = HexColor('#1A56DB')
RED        = HexColor('#d32f2f')
GREEN      = HexColor('#2e7d32')
ORANGE     = HexColor('#f57c00')
LIGHT_GRAY = HexColor('#f5f5f5')
MID_GRAY   = HexColor('#888888')
TEXT       = HexColor('#1a1a1a')
WHITE      = HexColor('#ffffff')

# ── STYLES ───────────────────────────────────────────
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'CustomTitle',
    fontName='Helvetica-Bold',
    fontSize=28,
    textColor=TEXT,
    spaceAfter=6,
    alignment=TA_LEFT,
    leading=34
)

subtitle_style = ParagraphStyle(
    'Subtitle',
    fontName='Helvetica',
    fontSize=13,
    textColor=MID_GRAY,
    spaceAfter=4,
    alignment=TA_LEFT
)

h1_style = ParagraphStyle(
    'H1',
    fontName='Helvetica-Bold',
    fontSize=18,
    textColor=ACCENT,
    spaceBefore=20,
    spaceAfter=8,
    leading=22
)

h2_style = ParagraphStyle(
    'H2',
    fontName='Helvetica-Bold',
    fontSize=13,
    textColor=TEXT,
    spaceBefore=14,
    spaceAfter=6,
    leading=16
)

body_style = ParagraphStyle(
    'Body',
    fontName='Helvetica',
    fontSize=10.5,
    textColor=TEXT,
    spaceAfter=6,
    leading=16,
    alignment=TA_JUSTIFY
)

caption_style = ParagraphStyle(
    'Caption',
    fontName='Helvetica-Oblique',
    fontSize=9,
    textColor=MID_GRAY,
    spaceAfter=12,
    alignment=TA_CENTER
)

finding_style = ParagraphStyle(
    'Finding',
    fontName='Helvetica',
    fontSize=10.5,
    textColor=TEXT,
    spaceAfter=5,
    leading=16,
    leftIndent=16,
    bulletIndent=0
)

label_style = ParagraphStyle(
    'Label',
    fontName='Helvetica-Bold',
    fontSize=9,
    textColor=WHITE,
    alignment=TA_CENTER
)

# ── CHART HELPERS ─────────────────────────────────────
def fig_to_image(fig, width=6.5*inch):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150,
                bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    img = Image(buf, width=width)
    img.hAlign = 'CENTER'
    return img

def make_bar_chart(labels, values, title, color,
                   xlabel='', vline=None, vline_label='',
                   figsize=(8, 5)):
    fig, ax = plt.subplots(figsize=figsize)
    bar_colors = [RED if v < 1.0 else color for v in values] \
        if vline == 1.0 else [color] * len(values)
    bars = ax.barh(labels, values, color=bar_colors,
                   edgecolor='white', linewidth=0.4)
    if vline is not None:
        ax.axvline(x=vline, color='#333333', linestyle='--',
                   linewidth=1.5, label=vline_label)
        ax.legend(fontsize=9, framealpha=0.8)
    ax.set_title(title, fontsize=12, fontweight='bold',
                 color='#1a1a1a', pad=10)
    ax.set_xlabel(xlabel, fontsize=9, color='#555555')
    ax.tick_params(axis='y', labelsize=8, colors='#333333')
    ax.tick_params(axis='x', labelsize=8, colors='#555555')
    ax.set_facecolor('#fafafa')
    fig.patch.set_facecolor('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.invert_yaxis()
    plt.tight_layout()
    return fig

# ── LOAD DATA ─────────────────────────────────────────
print("Loading data...")
try:
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///college_debt.db")
    df      = pd.read_sql("SELECT * FROM colleges", engine)
    flagged = pd.read_sql("SELECT * FROM flagged_schools_clean", engine)
    print(f"  Loaded {len(df):,} schools, {len(flagged)} flagged")
except Exception as e:
    print(f"ERROR loading database: {e}")
    print("Make sure you run this from inside college-debt-analyzer/")
    raise

# ── BUILD PDF ─────────────────────────────────────────
print("Building PDF...")

story = []

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COVER PAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
story.append(Spacer(1, 0.6*inch))

# Title block
story.append(Paragraph(
    "College Debt Outcome", title_style))
story.append(Paragraph(
    "Mismatch Analyzer", title_style))
story.append(Spacer(1, 0.1*inch))
story.append(HRFlowable(
    width="100%", thickness=3,
    color=ACCENT, spaceAfter=12))
story.append(Paragraph(
    "Surfacing predatory academic programs using federal data — "
    "because students deserve to know what a degree actually costs.",
    subtitle_style))

story.append(Spacer(1, 0.3*inch))

# Meta info table
meta_data = [
    ["Author",      "Rushil Pandya · CS Sophomore · Rutgers University '28"],
    ["Data Source", "U.S. Department of Education — College Scorecard API"],
    ["Institutions","6,322 analyzed · 4,500 with complete outcome data"],
    ["Published",   datetime.now().strftime("%B %Y")],
    ["GitHub",      "github.com/rushil1356/College-debt-analyzer"],
]
meta_table = Table(meta_data, colWidths=[1.3*inch, 5.2*inch])
meta_table.setStyle(TableStyle([
    ('FONTNAME',    (0,0), (0,-1), 'Helvetica-Bold'),
    ('FONTNAME',    (1,0), (1,-1), 'Helvetica'),
    ('FONTSIZE',    (0,0), (-1,-1), 9.5),
    ('TEXTCOLOR',   (0,0), (0,-1), ACCENT),
    ('TEXTCOLOR',   (1,0), (1,-1), TEXT),
    ('ROWBACKGROUNDS', (0,0), (-1,-1), [LIGHT_GRAY, WHITE]),
    ('TOPPADDING',  (0,0), (-1,-1), 6),
    ('BOTTOMPADDING',(0,0),(-1,-1), 6),
    ('LEFTPADDING', (0,0), (-1,-1), 10),
    ('GRID',        (0,0), (-1,-1), 0.3, HexColor('#dddddd')),
]))
story.append(meta_table)
story.append(Spacer(1, 0.4*inch))

# KPI summary boxes
kpi_data = [[
    f"{len(df):,}\nInstitutions\nAnalyzed",
    f"{len(flagged)}\nFlagged\nPredatory",
    f"{df['value_score'].mean():.2f}\nNational Avg\nValue Score",
    f"{len(df[df['value_score']<1.0])}\nBelow\nBreak-even",
]]
kpi_table = Table(kpi_data, colWidths=[1.6*inch]*4)
kpi_table.setStyle(TableStyle([
    ('BACKGROUND',   (0,0), (0,0), ACCENT),
    ('BACKGROUND',   (1,0), (1,0), RED),
    ('BACKGROUND',   (2,0), (2,0), GREEN),
    ('BACKGROUND',   (3,0), (3,0), ORANGE),
    ('TEXTCOLOR',    (0,0), (-1,-1), WHITE),
    ('FONTNAME',     (0,0), (-1,-1), 'Helvetica-Bold'),
    ('FONTSIZE',     (0,0), (-1,-1), 11),
    ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
    ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
    ('ROWHEIGHT',    (0,0), (-1,-1), 72),
    ('LEFTPADDING',  (0,0), (-1,-1), 8),
    ('RIGHTPADDING', (0,0), (-1,-1), 8),
]))
story.append(kpi_table)

story.append(PageBreak())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 1 — THE PROBLEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
story.append(Paragraph("1. The Problem", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=ACCENT, spaceAfter=10))

story.append(Paragraph(
    "Every year, over <b>2 million Americans</b> enroll in college programs "
    "without access to a fundamental piece of information — what graduates "
    "from that program actually earn, and how much debt they carry when they leave.",
    body_style))

story.append(Paragraph(
    "The U.S. Department of Education collects this data. It publishes it annually "
    "through the College Scorecard API. It is free, comprehensive, and covers every "
    "accredited institution in America. But it is buried in machine-readable files "
    "that require significant data engineering to interpret — far beyond what any "
    "prospective student, parent, or high school counselor can reasonably do.",
    body_style))

story.append(Paragraph(
    "The result: students make one of the largest financial decisions of their lives "
    "with incomplete information. Some graduate into careers that comfortably service "
    "their debt. Others spend decades paying back loans from programs that never "
    "delivered on their implied promise.",
    body_style))

story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("The Value Score", h2_style))
story.append(Paragraph(
    "This analysis introduces a simple metric — the <b>Value Score</b> — defined as:",
    body_style))

# Formula box
formula_data = [[
    "Value Score  =  Median Earnings (10 yrs after entry)  ÷  Median Debt at Graduation"
]]
formula_table = Table(formula_data, colWidths=[6.5*inch])
formula_table.setStyle(TableStyle([
    ('BACKGROUND',   (0,0), (-1,-1), HexColor('#EEF2FF')),
    ('TEXTCOLOR',    (0,0), (-1,-1), ACCENT),
    ('FONTNAME',     (0,0), (-1,-1), 'Helvetica-Bold'),
    ('FONTSIZE',     (0,0), (-1,-1), 11),
    ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
    ('TOPPADDING',   (0,0), (-1,-1), 14),
    ('BOTTOMPADDING',(0,0), (-1,-1), 14),
    ('BOX',          (0,0), (-1,-1), 1.5, ACCENT),
]))
story.append(formula_table)
story.append(Spacer(1, 0.1*inch))

interp_data = [
    ["Score > 1.0", "Graduates earn more than they borrowed", "Healthy outcome"],
    ["Score = 1.0", "Graduates earn exactly what they borrowed", "Break-even"],
    ["Score < 1.0", "Graduates earn less than they borrowed", "Red flag"],
    ["National avg", "3.22 across all scored institutions",    "Most schools are fine"],
]
interp_table = Table(
    [["Score Range", "Meaning", "Assessment"]] + interp_data,
    colWidths=[1.3*inch, 3.2*inch, 2.0*inch])
interp_table.setStyle(TableStyle([
    ('BACKGROUND',   (0,0), (-1,0), ACCENT),
    ('TEXTCOLOR',    (0,0), (-1,0), WHITE),
    ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTNAME',     (0,1), (-1,-1),'Helvetica'),
    ('FONTSIZE',     (0,0), (-1,-1), 9.5),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[LIGHT_GRAY, WHITE]),
    ('ALIGN',        (0,0), (-1,-1), 'LEFT'),
    ('TOPPADDING',   (0,0), (-1,-1), 7),
    ('BOTTOMPADDING',(0,0), (-1,-1), 7),
    ('LEFTPADDING',  (0,0), (-1,-1), 10),
    ('GRID',         (0,0), (-1,-1), 0.3, HexColor('#dddddd')),
    ('TEXTCOLOR',    (2,1), (2,1),   GREEN),
    ('TEXTCOLOR',    (2,3), (2,3),   RED),
    ('FONTNAME',     (2,1), (2,3),   'Helvetica-Bold'),
]))
story.append(interp_table)

story.append(PageBreak())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 2 — NATIONAL PICTURE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
story.append(Paragraph("2. The National Picture", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=ACCENT, spaceAfter=10))

story.append(Paragraph(
    "Before identifying the worst performers, it is important to establish what "
    "the data shows at the national level. The headline finding is reassuring: "
    "<b>the American college system is not broken</b>. The vast majority of "
    "institutions provide graduates with reasonable returns on their educational investment.",
    body_style))

# Distribution chart
fig_dist, ax_dist = plt.subplots(figsize=(8, 3.8))
clean_scores = df['value_score'].dropna()
ax_dist.hist(clean_scores, bins=50, color='#1A56DB',
             edgecolor='white', linewidth=0.4, alpha=0.85)
ax_dist.axvline(x=1.0, color='#d32f2f', linestyle='--',
                linewidth=2, label='Break-even (1.0)')
ax_dist.axvline(x=clean_scores.mean(), color='#f57c00',
                linestyle='--', linewidth=2,
                label=f'National mean ({clean_scores.mean():.2f})')
ax_dist.set_xlabel('Value Score (Earnings / Debt)', fontsize=9)
ax_dist.set_ylabel('Number of Institutions', fontsize=9)
ax_dist.set_title(
    'Distribution of Value Scores Across All US Colleges',
    fontsize=11, fontweight='bold')
ax_dist.legend(fontsize=9, framealpha=0.9)
ax_dist.set_facecolor('#fafafa')
fig_dist.patch.set_facecolor('white')
ax_dist.spines['top'].set_visible(False)
ax_dist.spines['right'].set_visible(False)
plt.tight_layout()
story.append(fig_to_image(fig_dist, width=6.5*inch))
story.append(Paragraph(
    "Figure 1 — Value score distribution across 4,500 scored institutions. "
    "The distribution is right-skewed with a mean of 3.22, indicating that "
    "most graduates earn significantly more than they borrowed.",
    caption_style))

story.append(Paragraph(
    "The distribution reveals three important macro-level findings:",
    body_style))

findings_nat = [
    ("<b>The mean value score of 3.22</b> means the average American college "
     "graduate earns $3.22 for every $1.00 borrowed — a healthy return on investment."),
    ("<b>The distribution is right-skewed</b>, meaning most schools cluster in the "
     "2–4 range with a long tail of high-performing institutions, particularly "
     "vocational and technical programs with low debt and strong employment outcomes."),
    ("<b>Only 46 institutions (1.0%)</b> fall below the break-even line — a "
     "concentrated problem, not a systemic one. The issue is identifiable and addressable."),
]
for f in findings_nat:
    story.append(Paragraph(f"• {f}", finding_style))

story.append(PageBreak())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 3 — WORST VALUE SCHOOLS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
story.append(Paragraph("3. Worst Value Institutions", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=ACCENT, spaceAfter=10))

story.append(Paragraph(
    "The 20 schools with the lowest value scores represent the clearest cases "
    "of financial mismatch between cost and outcome. Graduates from these "
    "institutions carry debt loads that exceed — or nearly equal — their "
    "annual earnings a full decade after enrollment.",
    body_style))

# Worst 20 chart
bottom_20 = df.nsmallest(20, 'value_score').copy()
bottom_20['label'] = (bottom_20['school_name'].str[:32] +
                      ' (' + bottom_20['state'] + ')')
fig_worst = make_bar_chart(
    bottom_20['label'].values,
    bottom_20['value_score'].values,
    '20 Worst Value Schools — Earnings vs Debt Ratio',
    '#f57c00',
    xlabel='Value Score (red = below break-even)',
    vline=1.0,
    vline_label='Break-even (1.0)',
    figsize=(8, 7)
)
story.append(fig_to_image(fig_worst, width=6.5*inch))
story.append(Paragraph(
    "Figure 2 — Bottom 20 schools by value score. Red bars indicate institutions "
    "where graduates earn less than they borrowed. Dashed line marks the break-even threshold.",
    caption_style))

# Bottom 10 table
story.append(Paragraph("Table: Bottom 10 Schools by Value Score", h2_style))
b10 = df.nsmallest(10, 'value_score')[
    ['school_name','state','median_earnings','median_debt','value_score']
].copy()
b10['median_earnings'] = b10['median_earnings'].apply(
    lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
b10['median_debt'] = b10['median_debt'].apply(
    lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
b10['value_score'] = b10['value_score'].apply(lambda x: f"{x:.3f}")
b10['school_name'] = b10['school_name'].str[:35]

table_data = [["School", "State", "Earnings", "Debt", "Score"]]
for _, row in b10.iterrows():
    table_data.append([
        row['school_name'], row['state'],
        row['median_earnings'], row['median_debt'], row['value_score']
    ])

worst_table = Table(
    table_data,
    colWidths=[2.8*inch, 0.6*inch, 1.0*inch, 1.0*inch, 0.7*inch])
worst_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0),  ACCENT),
    ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
    ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
    ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
    ('FONTSIZE',      (0,0), (-1,-1), 8.5),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [HexColor('#FFF3F3'), WHITE]),
    ('ALIGN',         (1,0), (-1,-1), 'CENTER'),
    ('ALIGN',         (0,0), (0,-1),  'LEFT'),
    ('TOPPADDING',    (0,0), (-1,-1), 6),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ('LEFTPADDING',   (0,0), (-1,-1), 8),
    ('GRID',          (0,0), (-1,-1), 0.3, HexColor('#dddddd')),
    ('TEXTCOLOR',     (4,1), (4,-1),  RED),
    ('FONTNAME',      (4,1), (4,-1),  'Helvetica-Bold'),
]))
story.append(worst_table)

story.append(PageBreak())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 4 — ANOMALY DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
story.append(Paragraph("4. Anomaly Detection — Flagged Institutions", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=ACCENT, spaceAfter=10))

story.append(Paragraph(
    "A single metric like value score can miss institutions that perform poorly "
    "across multiple dimensions simultaneously. To address this, an "
    "<b>Isolation Forest</b> model was trained on four features: value score, "
    "median debt, completion rate, and admission rate.",
    body_style))

story.append(Paragraph(
    "Isolation Forest identifies anomalies by measuring how easily an observation "
    "can be isolated from the rest of the dataset. Institutions that are outliers "
    "across all four dimensions simultaneously — not just one — are flagged as "
    "structurally concerning.",
    body_style))

# Model results table
model_data = [
    ["Parameter",         "Value"],
    ["Algorithm",         "Isolation Forest (scikit-learn)"],
    ["Features used",     "value_score, median_debt, completion_rate, admission_rate"],
    ["Contamination",     "5% (expected outlier rate)"],
    ["Scaling",           "StandardScaler (required — debt in $40Ks vs score in 0-15)"],
    ["Institutions flagged","69 (after data quality filtering)"],
    ["Quality filters",   "completion_rate > 0, student_size >= 100"],
]
model_table = Table(model_data, colWidths=[2.2*inch, 4.3*inch])
model_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0),  ACCENT),
    ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
    ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
    ('FONTNAME',      (0,1), (0,-1),  'Helvetica-Bold'),
    ('FONTNAME',      (1,1), (1,-1),  'Helvetica'),
    ('FONTSIZE',      (0,0), (-1,-1), 9),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [LIGHT_GRAY, WHITE]),
    ('TEXTCOLOR',     (0,1), (0,-1),  ACCENT),
    ('TEXTCOLOR',     (1,1), (-1,-1), TEXT),
    ('TOPPADDING',    (0,0), (-1,-1), 7),
    ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ('LEFTPADDING',   (0,0), (-1,-1), 10),
    ('GRID',          (0,0), (-1,-1), 0.3, HexColor('#dddddd')),
]))
story.append(model_table)
story.append(Spacer(1, 0.15*inch))

# Flagged schools chart
flagged_chart = flagged.nsmallest(15, 'value_score').copy()
flagged_chart['label'] = (flagged_chart['school_name'].str[:30] +
                          ' (' + flagged_chart['state'] + ')')
fig_flag = make_bar_chart(
    flagged_chart['label'].values,
    flagged_chart['value_score'].values,
    'Top 15 Flagged Institutions — Value Score',
    RED,
    xlabel='Value Score',
    vline=1.0,
    vline_label='Break-even (1.0)',
    figsize=(8, 6)
)
story.append(fig_to_image(fig_flag, width=6.5*inch))
story.append(Paragraph(
    "Figure 3 — Top 15 flagged institutions by value score. "
    "These schools were flagged as multi-dimensional outliers "
    "by the Isolation Forest model.",
    caption_style))

story.append(Paragraph("Key Nuance — Data Quality", h2_style))
story.append(Paragraph(
    "Several flagged institutions have acceptable value scores but were flagged "
    "due to zero or near-zero completion rates. In most cases this reflects "
    "<b>data incompleteness</b> (newly launched programs with no graduates yet) "
    "rather than genuinely poor outcomes. This is documented in the analysis and "
    "addressed through the quality filtering step.",
    body_style))

story.append(PageBreak())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 5 — STATE ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
story.append(Paragraph("5. State-Level Analysis", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=ACCENT, spaceAfter=10))

story.append(Paragraph(
    "Value scores vary significantly by state, reflecting differences in "
    "tuition levels, local labor markets, cost of living, and the mix of "
    "institution types present in each state.",
    body_style))

state_scores = df.groupby('state')['value_score'].agg(
    ['mean','count']).reset_index()
state_scores.columns = ['state','avg_value_score','num_schools']
state_scores = state_scores[state_scores['num_schools'] >= 3]\
    .sort_values('avg_value_score', ascending=False)

fig_states, axes = plt.subplots(1, 2, figsize=(9, 5.5))

top10 = state_scores.head(10)
axes[0].barh(top10['state'], top10['avg_value_score'],
             color='#2e7d32', edgecolor='white', linewidth=0.4)
axes[0].set_title('Top 10 States', fontsize=10,
                  fontweight='bold')
axes[0].set_xlabel('Avg Value Score', fontsize=8)
axes[0].tick_params(labelsize=8)
axes[0].set_facecolor('#fafafa')
axes[0].spines['top'].set_visible(False)
axes[0].spines['right'].set_visible(False)
axes[0].invert_yaxis()

bot10 = state_scores.tail(10).sort_values('avg_value_score')
axes[1].barh(bot10['state'], bot10['avg_value_score'],
             color='#d32f2f', edgecolor='white', linewidth=0.4)
axes[1].set_title('Bottom 10 States', fontsize=10,
                  fontweight='bold')
axes[1].set_xlabel('Avg Value Score', fontsize=8)
axes[1].tick_params(labelsize=8)
axes[1].set_facecolor('#fafafa')
axes[1].spines['top'].set_visible(False)
axes[1].spines['right'].set_visible(False)
axes[1].invert_yaxis()

fig_states.patch.set_facecolor('white')
plt.suptitle('Average Value Score by State',
             fontsize=12, fontweight='bold', y=1.01)
plt.tight_layout()
story.append(fig_to_image(fig_states, width=6.5*inch))
story.append(Paragraph(
    "Figure 4 — Best and worst value states by average institution value score. "
    "States with fewer than 3 institutions are excluded.",
    caption_style))

nj_rank = state_scores.reset_index(drop=True)
nj_rank.index += 1
nj_position = nj_rank[nj_rank['state']=='NJ'].index[0]

story.append(Paragraph("Notable State Findings", h2_style))
state_findings = [
    (f"<b>New Jersey ranks {nj_position}th nationally</b> with an average value "
     f"score of {nj_rank[nj_rank['state']=='NJ']['avg_value_score'].values[0]:.2f}. "
     "The top two highest-value individual schools in the entire dataset are both "
     "NJ institutions — New Community Career & Technical Institute and Adult and "
     "Continuing Education-BCTS."),
    ("<b>Wyoming leads nationally</b> in average value score, driven by low "
     "tuition at state institutions combined with above-average wages in the "
     "energy sector."),
    ("<b>Puerto Rico shows the lowest scores</b>, reflecting structural economic "
     "conditions rather than institutional quality — lower average earnings in PR "
     "mechanically reduce value scores regardless of debt levels. This represents "
     "a geographic bias in the metric that must be acknowledged."),
    ("<b>School size is not predictive</b> — correlation between enrollment and "
     "value score is r = 0.09, essentially zero. Large flagship universities and "
     "small community colleges perform equally variably."),
]
for f in state_findings:
    story.append(Paragraph(f"• {f}", finding_style))

story.append(PageBreak())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 6 — HOW THIS HELPS STUDENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
story.append(Paragraph("6. How This Helps Students", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=ACCENT, spaceAfter=10))

story.append(Paragraph(
    "Data without accessibility is just noise. The Streamlit dashboard built "
    "alongside this analysis translates 4,500 rows of federal data into three "
    "practical tools for students, parents, and counselors:",
    body_style))

use_cases = [
    ["Tool", "What It Does", "Who It Helps"],
    ["Value Score Rankings",
     "Sort all 4,500 schools by earnings-to-debt ratio, "
     "filter by state",
     "Students comparing schools in their region"],
    ["Flagged Institution List",
     "See the 69 schools flagged as multi-dimensional "
     "outliers by the ML model",
     "Anyone doing due diligence on a specific school"],
    ["Plain English Query Interface",
     "Ask questions like 'which NJ schools have the "
     "best value score?' — Claude API converts to SQL",
     "Non-technical users: parents, counselors"],
    ["State Comparison",
     "Compare average outcomes across all 50 states "
     "with drill-down to individual institutions",
     "Students considering out-of-state enrollment"],
]
use_table = Table(
    use_cases,
    colWidths=[1.5*inch, 2.8*inch, 2.2*inch])
use_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0),  ACCENT),
    ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
    ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
    ('FONTNAME',      (0,1), (0,-1),  'Helvetica-Bold'),
    ('FONTNAME',      (1,1), (-1,-1), 'Helvetica'),
    ('FONTSIZE',      (0,0), (-1,-1), 9),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [LIGHT_GRAY, WHITE]),
    ('TEXTCOLOR',     (0,1), (0,-1),  ACCENT),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING',    (0,0), (-1,-1), 8),
    ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ('LEFTPADDING',   (0,0), (-1,-1), 10),
    ('GRID',          (0,0), (-1,-1), 0.3, HexColor('#dddddd')),
]))
story.append(use_table)
story.append(Spacer(1, 0.2*inch))

story.append(Paragraph("Limitations", h2_style))
story.append(Paragraph(
    "This analysis should be interpreted with appropriate caution:",
    body_style))
limitations = [
    "<b>Earnings data reflects 10-year median outcomes</b> — early-career "
    "earnings may look different from long-term outcomes for some fields.",
    "<b>Debt data is institution-level, not program-level</b> — a medical "
    "school and a liberal arts college within the same university share the "
    "same debt figure, which may obscure program-level variation.",
    "<b>This analysis identifies correlation, not causation</b> — a low "
    "value score reflects outcomes, not necessarily the quality of instruction "
    "or the school's intent.",
    "<b>Geographic bias exists</b> — states with lower average wages "
    "will systematically produce lower value scores regardless of "
    "institutional quality.",
]
for l in limitations:
    story.append(Paragraph(f"• {l}", finding_style))

story.append(PageBreak())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 7 — SUMMARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
story.append(Paragraph("7. Summary of Findings", h1_style))
story.append(HRFlowable(width="100%", thickness=1,
                        color=ACCENT, spaceAfter=10))

summary_data = [
    ["#", "Finding", "Implication"],
    ["1",
     "Mean value score: 3.22 across 4,500 institutions",
     "Most colleges are financially sound investments"],
    ["2",
     "46 schools below break-even (score < 1.0)",
     "Graduates earn less than they borrowed — concentrated risk"],
    ["3",
     "69 institutions flagged as multi-dimensional outliers",
     "These schools underperform across debt, earnings, AND completion"],
    ["4",
     "New Jersey ranks 6th nationally; top 2 schools both in NJ",
     "Local students have strong value options without leaving state"],
    ["5",
     "School size has r = 0.09 correlation with value score",
     "Brand name and enrollment are poor proxies for ROI"],
    ["6",
     "Flagged schools cluster at $5K-$25K debt — not the most expensive",
     "Moderate-cost schools can still produce poor outcomes"],
    ["7",
     "Puerto Rico has highest concentration of flagged schools",
     "Geographic wage gaps create structural bias in the metric"],
]
sum_table = Table(
    summary_data,
    colWidths=[0.3*inch, 3.0*inch, 3.2*inch])
sum_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0),  ACCENT),
    ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
    ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
    ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
    ('FONTSIZE',      (0,0), (-1,-1), 9),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [LIGHT_GRAY, WHITE]),
    ('ALIGN',         (0,0), (0,-1),  'CENTER'),
    ('FONTNAME',      (0,1), (0,-1),  'Helvetica-Bold'),
    ('TEXTCOLOR',     (0,1), (0,-1),  ACCENT),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING',    (0,0), (-1,-1), 7),
    ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ('LEFTPADDING',   (0,0), (-1,-1), 8),
    ('GRID',          (0,0), (-1,-1), 0.3, HexColor('#dddddd')),
]))
story.append(sum_table)
story.append(Spacer(1, 0.3*inch))

# Closing statement
story.append(Paragraph(
    "This analysis demonstrates that the college debt crisis, while real, "
    "is not uniformly distributed. The federal data exists to identify exactly "
    "which institutions are leaving students worse off — and this tool makes "
    "that identification accessible to anyone, regardless of their technical background.",
    body_style))

story.append(Spacer(1, 0.15*inch))
story.append(HRFlowable(width="100%", thickness=1,
                        color=HexColor('#dddddd'), spaceAfter=10))
story.append(Paragraph(
    "Built by Rushil Pandya · CS Sophomore · Rutgers University '28 · "
    "github.com/rushil1356/College-debt-analyzer · "
    "Data: U.S. Department of Education College Scorecard API",
    caption_style))

# ── GENERATE PDF ──────────────────────────────────────
output_path = "College_Debt_Outcome_Mismatch_Analyzer_Report.pdf"

doc = SimpleDocTemplate(
    output_path,
    pagesize=letter,
    rightMargin=0.85*inch,
    leftMargin=0.85*inch,
    topMargin=0.85*inch,
    bottomMargin=0.85*inch,
    title="College Debt Outcome Mismatch Analyzer",
    author="Rushil Pandya"
)

doc.build(story)
print(f"\nPDF generated: {output_path}")
print(f"Size: {os.path.getsize(output_path)/1024:.0f} KB")