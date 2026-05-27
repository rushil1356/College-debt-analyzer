# 🎓 College Debt Outcome Mismatch Analyzer

> **Surfacing predatory academic programs using federal data — because students deserve to know what a degree actually costs.**

---
📄 **[View Full Analytical Report (PDF)](College_Debt_Outcome_Mismatch_Analyzer_Report.pdf)** — 11-page report with all findings, charts, and methodology for non-technical readers

## The Problem

Every year, over **2 million Americans** enroll in college programs without access to a fundamental piece of information — what graduates from that program actually earn, and how much debt they carry when they leave.

The U.S. Department of Education publishes this data annually through the College Scorecard API. It is free, comprehensive, and covers every accredited institution in America. But it is buried in machine-readable files that no student, parent, or counselor has time to interpret.

**This tool does that interpreting for you.**

---

## What It Does

- 📡 Pulls **6,322 institutions** from the U.S. College Scorecard API
- 💰 Computes a **Value Score** (median earnings ÷ median debt) for 4,500+ schools
- 🤖 Uses **Isolation Forest** anomaly detection to flag 69 predatory institutions across 4 dimensions simultaneously
- 💬 **NL→SQL interface** powered by Claude API — ask questions about any school in plain English
- 📊 Interactive **Streamlit dashboard** with tabbed charts, state drill-down, and sidebar filters
- 📄 One-click **PDF report export** with full findings, charts, and methodology for non-technical readers

---

## Key Findings

| # | Finding | Implication |
|---|---|---|
| 1 | Mean value score: **3.22** across 4,500 institutions | Most colleges return decent value |
| 2 | **46 schools** have graduates earning less than they borrowed | Break-even violations — concentrated, not systemic |
| 3 | **69 institutions** flagged as multi-dimensional outliers | Poor across debt, earnings, AND completion simultaneously |
| 4 | **New Jersey ranks 6th nationally** — top 2 value schools both in NJ | Strong local options for Rutgers students |
| 5 | School size: **r = 0.09** correlation with value score | Brand name is a poor proxy for financial outcomes |
| 6 | Flagged schools cluster at **$5K–$25K debt** | Moderate cost can still produce poor outcomes |
| 7 | Puerto Rico has highest flagged concentration | Geographic wage gaps create structural metric bias |

---

## Dashboard Features

**4 interactive tabs:**
- 🏫 **Worst Value Schools** — adjustable slider, red bars = below break-even
- 🗺️ **State Breakdown** — best/worst states, drill into any state's full school list
- ⚠️ **Flagged Institutions** — sort by value score, debt, or completion rate
- 📈 **Distributions** — value score, debt, and earnings histograms with summary stats

**Sidebar filters:** state selector, flagged-only toggle, value score range slider

**Plain English query interface:** type any question, Claude converts it to SQL, results display instantly

**PDF export:** one-click generation of a full 11-page analytical report with all findings and charts

---

## Tech Stack

```
Python · pandas · NumPy · scikit-learn · SQLite · SQLAlchemy
Streamlit · Anthropic Claude API · ReportLab · Matplotlib
U.S. College Scorecard API
```

---

## How to Run

```bash
git clone https://github.com/rushil1356/College-debt-analyzer
cd College-debt-analyzer
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_claude_api_key_here
COLLEGE_SCORECARD_API_KEY=your_scorecard_api_key_here
```

Get your free API keys:
- College Scorecard: https://collegescorecard.ed.gov/data/documentation/
- Anthropic Claude: https://console.anthropic.com

Run notebooks in order to build the database:
```
1. data_pipeline.ipynb         — pulls API data, computes value scores, loads SQLite
2. anomaly_detection.ipynb     — isolation forest, flags predatory institutions
```

Launch the dashboard:
```bash
streamlit run app.py
```

Generate the PDF report standalone:
```bash
python generate_report.py
```

---

## Project Structure

```
college-debt-analyzer/
├── data_pipeline.ipynb          # API ingestion, value scoring, SQLite load
├── anomaly_detection.ipynb      # Isolation forest, flagged schools, findings
├── app.py                       # Streamlit dashboard + NL→SQL interface
├── generate_report.py           # PDF report generator (ReportLab)
├── requirements.txt             # All dependencies
├── .env                         # API keys — never committed
└── .gitignore
```

---

## Sample Questions (NL→SQL Interface)

- *"Which schools in New Jersey have the highest value score?"*
- *"Show flagged schools with median debt over $30,000"*
- *"Which states have the most predatory institutions?"*
- *"List schools with completion rate above 80% and value score above 4"*

---

## Data Source

U.S. Department of Education — College Scorecard API
https://collegescorecard.ed.gov/data/documentation/

---

## Author

**Rushil Pandya** · CS Sophomore · Rutgers University '28

[![LinkedIn](https://img.shields.io/badge/LinkedIn-rushil--pandya-blue?logo=linkedin)](https://linkedin.com/in/rushil-pandya)
[![GitHub](https://img.shields.io/badge/GitHub-rushil1356-black?logo=github)](https://github.com/rushil1356)
