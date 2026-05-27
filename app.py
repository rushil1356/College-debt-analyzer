import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from sqlalchemy import create_engine
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

# ── PAGE CONFIG ──────────────────────────────────────
st.set_page_config(
    page_title="College Debt Analyzer",
    page_icon="🎓",
    layout="wide"
)

# ── LOAD DATA ────────────────────────────────────────
@st.cache_resource
def get_engine():
    return create_engine("sqlite:///college_debt.db")

@st.cache_data
def load_data():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM colleges", engine)
    flagged = pd.read_sql("SELECT * FROM flagged_schools_clean", engine)
    return df, flagged

df, flagged = load_data()
engine = get_engine()
# ── HEADER ───────────────────────────────────────────
st.title("🎓 College Debt Outcome Mismatch Analyzer")

st.markdown("""
### Why does this exist?

Every year, over **2 million Americans** enroll in college programs 
without knowing a simple truth — some degrees cost more than they 
will ever pay back.

The federal government collects this data. It's public. It's free. 
But it's buried in 6,000-row spreadsheets that no student, parent, 
or counselor has time to dig through.

**This tool does that digging for you.**
""")

st.divider()

# ── PROBLEM + FINDINGS ───────────────────────────────
col_prob, col_find = st.columns([1, 1])

with col_prob:
    st.markdown("""
    #### 🔍 The Problem
    
    Colleges are not required to advertise what their graduates 
    actually earn — or how much debt they carry when they leave.
    
    A student choosing between two nursing programs in the same 
    city might not know that one leaves graduates earning **\$15,000 
    more per year** than the other, with **\$10,000 less debt**.
    
    That gap compounds over a lifetime.
    
    The **value score** in this tool is simple:
    
    > **Value Score = Median Earnings ÷ Median Debt**
    
    - Score **above 1.0** → graduates earn more than they borrowed ✅
    - Score **below 1.0** → graduates earn less than they borrowed ⚠️
    - Score **3.22** → the national average — most colleges are fine
    
    The goal isn't to say college is broken. 
    **It isn't.** The goal is to find the ones that are.
    """)

with col_find:
    st.markdown("""
    #### 📊 What the Data Actually Shows
    
    After analyzing **4,500 institutions** using the federal 
    College Scorecard API, here's what matters:
    """)
    
    st.info(
        "**46 schools** have graduates earning less than "
        "they borrowed — these are your red flags."
    )
    st.success(
        "**New Jersey ranks 6th nationally** for college value — "
        "if you're a Rutgers student, the data is on your side."
    )
    st.warning(
        "**School size means nothing.** Correlation between "
        "enrollment and outcomes: r = 0.09. A big name "
        "is not a guarantee."
    )
    st.error(
        "**69 institutions** flagged as outliers across debt, "
        "earnings, and completion rate simultaneously — "
        "not just expensive, but expensive *and* underperforming."
    )
    
    st.markdown("""
    > *Scroll down to explore the data, filter by state, 
    > or ask a plain English question about any school.*
    """)

st.divider()

# ── KPI METRICS ──────────────────────────────────────
st.markdown("#### 📈 Dataset at a Glance")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Institutions Analyzed", f"{len(df):,}")
col2.metric("Flagged Predatory", f"{len(flagged):,}",
            delta="isolation forest", delta_color="off")
col3.metric("Avg Value Score", f"{df['value_score'].mean():.2f}",
            help="Median earnings / median debt. Above 1.0 = good")
col4.metric("Below Break-even", f"{len(df[df['value_score']<1.0]):,}",
            delta="earning less than borrowed", delta_color="inverse")

st.divider()
# ── SIDEBAR ──────────────────────────────────────────
st.sidebar.header("🔍 Filter Schools")

states = ['All'] + sorted(df['state'].dropna().unique().tolist())
selected_state = st.sidebar.selectbox("State", states)

show_flagged = st.sidebar.checkbox(
    "Show only flagged predatory schools", False
)

value_min, value_max = st.sidebar.slider(
    "Value Score Range",
    min_value=0.0,
    max_value=float(df['value_score'].max()),
    value=(0.0, float(df['value_score'].max())),
    step=0.1
)

# ── FILTER LOGIC ─────────────────────────────────────
df_display = flagged if show_flagged else df

if selected_state != 'All':
    df_display = df_display[df_display['state'] == selected_state]

df_display = df_display[
    (df_display['value_score'] >= value_min) &
    (df_display['value_score'] <= value_max)
]

# ── SCHOOL TABLE ─────────────────────────────────────
st.subheader(f"📋 School Rankings ({len(df_display):,} schools)")

st.dataframe(
    df_display[[
        'school_name', 'state', 'city',
        'median_earnings', 'median_debt',
        'value_score', 'completion_rate'
    ]].sort_values('value_score').reset_index(drop=True),
    use_container_width=True,
    column_config={
        "school_name": "School",
        "state": "State",
        "city": "City",
        "median_earnings": st.column_config.NumberColumn(
            "Median Earnings", format="$%d"
        ),
        "median_debt": st.column_config.NumberColumn(
            "Median Debt", format="$%d"
        ),
        "value_score": st.column_config.NumberColumn(
            "Value Score", format="%.2f"
        ),
        "completion_rate": st.column_config.NumberColumn(
            "Completion Rate", format="%.0%%"
        ),
    }
)

st.divider()

# ── CHARTS — TABBED INTERFACE ────────────────────────
st.subheader("📊 Visual Analysis")

tab1, tab2, tab3, tab4 = st.tabs([
    "🏫 Worst Value Schools",
    "🗺️ State Breakdown", 
    "⚠️ Flagged Institutions",
    "📈 Distributions"
])

# ── TAB 1 — WORST VALUE SCHOOLS ──────────────────────
with tab1:
    st.markdown("### Bottom schools by earnings-to-debt ratio")
    st.markdown(
        "Schools where graduates earn the least relative "
        "to what they borrowed. Red bars = below break-even."
    )
    
    n_schools = st.slider(
        "Number of schools to show", 
        min_value=5, max_value=30, value=15, key="tab1_slider"
    )
    
    bottom_n = df.nsmallest(n_schools, 'value_score').copy()
    bottom_n['label'] = bottom_n['school_name'].str[:30] + \
                        ' (' + bottom_n['state'] + ')'
    
    fig1, ax1 = plt.subplots(figsize=(10, n_schools * 0.45 + 1))
    colors = ['#d32f2f' if v < 1.0 else '#f57c00' 
              for v in bottom_n['value_score']]
    ax1.barh(bottom_n['label'], bottom_n['value_score'], color=colors)
    ax1.axvline(x=1.0, color='white', linestyle='--',
                linewidth=1.5, label='Break-even (1.0)')
    ax1.set_xlabel('Value Score (Earnings / Debt)', color='white')
    ax1.set_title(f'Bottom {n_schools} Schools by Value Score',
                  color='white', fontweight='bold')
    ax1.tick_params(colors='white', labelsize=8)
    ax1.set_facecolor('#0e1117')
    fig1.patch.set_facecolor('#0e1117')
    ax1.legend(facecolor='#262730', labelcolor='white')
    ax1.invert_yaxis()
    plt.tight_layout()
    st.pyplot(fig1)
    
    # Table below chart
    st.dataframe(
        bottom_n[['school_name', 'state', 'city',
                  'median_earnings', 'median_debt', 'value_score']]
        .reset_index(drop=True),
        use_container_width=True,
        column_config={
            "median_earnings": st.column_config.NumberColumn(
                "Median Earnings", format="$%d"),
            "median_debt": st.column_config.NumberColumn(
                "Median Debt", format="$%d"),
            "value_score": st.column_config.NumberColumn(
                "Value Score", format="%.3f"),
        }
    )

# ── TAB 2 — STATE BREAKDOWN ───────────────────────────
with tab2:
    st.markdown("### Average value score by state")
    
    view = st.radio(
        "Show",
        ["Best value states", "Worst value states", "All states"],
        horizontal=True,
        key="tab2_radio"
    )
    
    state_scores = df.groupby('state')['value_score'].agg(
        ['mean', 'count']
    ).reset_index()
    state_scores.columns = ['state', 'avg_value_score', 'num_schools']
    state_scores = state_scores[state_scores['num_schools'] >= 3]
    state_scores = state_scores.sort_values(
        'avg_value_score', ascending=False
    )
    
    if view == "Best value states":
        plot_data = state_scores.head(15)
        color = '#2e7d32'
        title = 'Top 15 Best Value States'
    elif view == "Worst value states":
        plot_data = state_scores.tail(15).sort_values('avg_value_score')
        color = '#d32f2f'
        title = 'Bottom 15 Worst Value States'
    else:
        plot_data = state_scores.sort_values('avg_value_score')
        color = 'steelblue'
        title = 'All States by Average Value Score'
    
    fig2, ax2 = plt.subplots(
        figsize=(10, len(plot_data) * 0.4 + 1)
    )
    ax2.barh(plot_data['state'], 
             plot_data['avg_value_score'], color=color)
    ax2.axvline(x=df['value_score'].mean(), color='orange',
                linestyle='--', linewidth=1.5,
                label=f"National avg: {df['value_score'].mean():.2f}")
    ax2.set_xlabel('Average Value Score', color='white')
    ax2.set_title(title, color='white', fontweight='bold')
    ax2.tick_params(colors='white')
    ax2.set_facecolor('#0e1117')
    fig2.patch.set_facecolor('#0e1117')
    ax2.legend(facecolor='#262730', labelcolor='white')
    ax2.invert_yaxis()
    plt.tight_layout()
    st.pyplot(fig2)
    
    # State detail table
    selected_state_tab = st.selectbox(
        "Drill into a specific state",
        [''] + sorted(df['state'].dropna().unique().tolist()),
        key="tab2_state"
    )
    
    if selected_state_tab:
        state_detail = df[df['state'] == selected_state_tab]\
            .sort_values('value_score')
        st.markdown(
            f"**{len(state_detail)} schools in {selected_state_tab}**"
        )
        st.dataframe(
            state_detail[['school_name', 'city', 'median_earnings',
                          'median_debt', 'value_score',
                          'completion_rate']]
            .reset_index(drop=True),
            use_container_width=True,
            column_config={
                "median_earnings": st.column_config.NumberColumn(
                    "Earnings", format="$%d"),
                "median_debt": st.column_config.NumberColumn(
                    "Debt", format="$%d"),
                "value_score": st.column_config.NumberColumn(
                    "Value Score", format="%.2f"),
                "completion_rate": st.column_config.NumberColumn(
                    "Completion", format="%.0%%"),
            }
        )

# ── TAB 3 — FLAGGED INSTITUTIONS ─────────────────────
with tab3:
    st.markdown("### Institutions flagged by isolation forest")
    st.markdown(
        "Flagged across 4 dimensions simultaneously: "
        "value score, median debt, completion rate, "
        "admission rate. Data quality filtered."
    )
    
    metric_choice = st.radio(
        "Sort flagged schools by",
        ["Value Score (worst first)", 
         "Median Debt (highest first)",
         "Completion Rate (lowest first)"],
        horizontal=True,
        key="tab3_metric"
    )
    
    sort_map = {
        "Value Score (worst first)": 
            ('value_score', True),
        "Median Debt (highest first)": 
            ('median_debt', False),
        "Completion Rate (lowest first)": 
            ('completion_rate', True)
    }
    
    sort_col, asc = sort_map[metric_choice]
    flagged_sorted = flagged.sort_values(sort_col, ascending=asc)\
        .head(20).copy()
    flagged_sorted['label'] = \
        flagged_sorted['school_name'].str[:28] + \
        ' (' + flagged_sorted['state'] + ')'
    
    fig3, ax3 = plt.subplots(figsize=(10, 8))
    ax3.barh(flagged_sorted['label'], 
             flagged_sorted[sort_col], color='#d32f2f')
    
    if sort_col == 'value_score':
        ax3.axvline(x=1.0, color='white', linestyle='--',
                    linewidth=1.5, label='Break-even')
        ax3.legend(facecolor='#262730', labelcolor='white')
    
    ax3.set_title(f'Top 20 Flagged Schools — {metric_choice}',
                  color='white', fontweight='bold')
    ax3.tick_params(colors='white', labelsize=8)
    ax3.set_facecolor('#0e1117')
    fig3.patch.set_facecolor('#0e1117')
    ax3.invert_yaxis()
    plt.tight_layout()
    st.pyplot(fig3)
    
    st.dataframe(
        flagged_sorted[['school_name', 'state', 'median_earnings',
                        'median_debt', 'value_score',
                        'completion_rate']]
        .reset_index(drop=True),
        use_container_width=True,
        column_config={
            "median_earnings": st.column_config.NumberColumn(
                "Earnings", format="$%d"),
            "median_debt": st.column_config.NumberColumn(
                "Debt", format="$%d"),
            "value_score": st.column_config.NumberColumn(
                "Value Score", format="%.2f"),
            "completion_rate": st.column_config.NumberColumn(
                "Completion", format="%.0%%"),
        }
    )

# ── TAB 4 — DISTRIBUTIONS ────────────────────────────
with tab4:
    st.markdown("### How value scores and debt distribute nationally")
    
    dist_choice = st.radio(
        "Select distribution",
        ["Value Score", "Median Debt", "Median Earnings"],
        horizontal=True,
        key="tab4_dist"
    )
    
    col_map = {
        "Value Score": ('value_score', 'steelblue', 
                        'Value Score (Earnings/Debt)'),
        "Median Debt": ('median_debt', '#f57c00', 'Median Debt ($)'),
        "Median Earnings": ('median_earnings', '#2e7d32', 
                           'Median Earnings ($)')
    }
    
    col, color, xlabel = col_map[dist_choice]
    clean = df[col].dropna()
    
    fig4, ax4 = plt.subplots(figsize=(10, 5))
    ax4.hist(clean, bins=50, color=color, edgecolor='#0e1117')
    ax4.axvline(x=clean.mean(), color='orange', linestyle='--',
                linewidth=2, 
                label=f"Mean: {clean.mean():,.0f}")
    ax4.axvline(x=clean.median(), color='white', linestyle='--',
                linewidth=2, 
                label=f"Median: {clean.median():,.0f}")
    
    if col == 'value_score':
        ax4.axvline(x=1.0, color='red', linestyle='--',
                    linewidth=2, label='Break-even (1.0)')
    
    ax4.set_xlabel(xlabel, color='white')
    ax4.set_ylabel('Number of Schools', color='white')
    ax4.set_title(f'Distribution of {dist_choice} — All Schools',
                  color='white', fontweight='bold')
    ax4.tick_params(colors='white')
    ax4.set_facecolor('#0e1117')
    fig4.patch.set_facecolor('#0e1117')
    ax4.legend(facecolor='#262730', labelcolor='white')
    plt.tight_layout()
    st.pyplot(fig4)
    
    # Summary stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mean", f"{clean.mean():,.0f}")
    c2.metric("Median", f"{clean.median():,.0f}")
    c3.metric("Min", f"{clean.min():,.0f}")
    c4.metric("Max", f"{clean.max():,.0f}")

st.divider()

# ── NL→SQL INTERFACE ─────────────────────────────────
st.subheader("💬 Ask the Data Anything")
st.markdown(
    "*Type a question in plain English — "
    "Claude converts it to SQL and queries the database*"
)

def get_schema():
    return """
    SQLite database with two tables:

    Table: colleges
    Columns: school_name (text), state (text), city (text),
             median_earnings (float), median_debt (float),
             value_score (float), completion_rate (float),
             admission_rate (float), student_size (float)

    Table: flagged_schools_clean
    Same columns as colleges.
    Contains only anomaly-flagged predatory institutions.
    """

def nl_to_sql(question):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Debug — remove after fixing
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found in environment. "
            "Check your .env file."
        )
    
    client = anthropic.Anthropic(api_key=api_key)
    
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""You are a SQL expert for SQLite.
Convert this question to a SQL query using this schema:
{get_schema()}

Question: {question}

Rules:
- Return ONLY the SQL query, nothing else
- No explanation, no markdown, no backticks
- Use LIMIT 20 unless the question asks for more
- Always include school_name and state in SELECT
- Use proper SQLite syntax"""
        }]
    )
    return message.content[0].text.strip()

# Example question buttons
st.markdown("**Try one of these:**")
ex1, ex2, ex3, ex4 = st.columns(4)

if ex1.button("🏆 Best value in NJ"):
    st.session_state.nl_question = \
        "Which schools in New Jersey have the highest value score?"

if ex2.button("⚠️ Most flagged states"):
    st.session_state.nl_question = \
        "Which states have the most flagged predatory schools?"

if ex3.button("💸 High debt low earnings"):
    st.session_state.nl_question = \
        "Show schools with median debt over 30000 but " \
        "median earnings under 25000"

if ex4.button("🎓 Best completion rates"):
    st.session_state.nl_question = \
        "Which schools have completion rate above 0.8 " \
        "and value score above 3?"

question = st.text_input(
    "Your question",
    value=st.session_state.get("nl_question", ""),
    placeholder="Which California schools have the worst value scores?",
    key="nl_input"
)

if question:
    with st.spinner("Generating SQL and querying..."):
        try:
            sql = nl_to_sql(question)

            with st.expander("🔍 Generated SQL — click to see"):
                st.code(sql, language='sql')

            result = pd.read_sql(sql, get_engine())

            if len(result) == 0:
                st.warning("Query returned no results — try rephrasing")
            else:
                st.success(f"✅ {len(result)} results found")
                st.dataframe(result, use_container_width=True)

        except Exception as e:
            st.error(f"Query failed: {str(e)}")
            st.info(
                "💡 Try rephrasing — e.g. "
                "'show schools in Texas with low value scores'"
            )

st.divider()

# ── FOOTER ───────────────────────────────────────────
st.markdown(
    "*Data source: U.S. Department of Education "
    "College Scorecard API · "
    "Built by Rushil Pandya · "
    "[github.com/rushil1356]"
    "(https://github.com/rushil1356/College-debt-analyzer)*"
)