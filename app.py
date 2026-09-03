import os
import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Pick'em Tracker", layout="wide")

# ==============================================================================
# CONFIGURATION
# ==============================================================================
DEFAULT_HIGHLIGHTS = [
    "User1",
    "User2",
    "User3",
    "User4",
    "User5",
    "User6"
]

DATA_DIR = "data"

# ==============================================================================
# DATA PARSER FOR COPY-PASTED TEXT / CSV
# ==============================================================================
def parse_pasted_data(content_str):
    """Parses tab-delimited or comma-delimited text into a DataFrame."""
    try:
        # Try tab-separated first (standard paste from Word tables or Excel)
        df = pd.read_csv(io.StringIO(content_str), sep="\t", dtype=str)
        if df.shape[1] <= 1:
            # Fallback to comma-separated or space-separated if tabs aren't detected
            df = pd.read_csv(io.StringIO(content_str), sep=r"\s{2,}|,", engine="python", dtype=str)
    except Exception:
        return None

    df = df.dropna(how="all")
    return df

def clean_and_normalize_data(df):
    """Cleans column headers and strips white space."""
    df.columns = [str(col).strip() for col in df.columns]
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df

# ==============================================================================
# APPLICATION INTERFACE
# ==============================================================================
st.title("Weekly Pick'em Standings")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Get all text files from data folder
text_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".txt") or f.endswith(".csv")]
text_files.sort()

st.sidebar.header("Settings & Controls")

selected_file = None
if text_files:
    selected_file = st.sidebar.selectbox("Select Week File", text_files, index=len(text_files) - 1)
else:
    st.sidebar.warning("No data files found in 'data/' folder. Add a file in GitHub or paste data below.")

# Option to paste data directly on the page for quick testing
st.sidebar.subheader("Quick Paste Test")
pasted_input = st.sidebar.text_area("Or paste raw weekly data here directly:", height=150)

# Highlight settings
st.sidebar.subheader("Highlighted Members")
highlight_input = st.sidebar.text_area(
    "Usernames to Highlight (one per line):", 
    value="\n".join(DEFAULT_HIGHLIGHTS)
)
highlight_list = [name.strip().lower() for name in highlight_input.split("\n") if name.strip()]

# Load data source
df = None
if pasted_input.strip():
    df = parse_pasted_data(pasted_input)
elif selected_file:
    file_path = os.path.join(DATA_DIR, selected_file)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    df = parse_pasted_data(content)

if df is not None and not df.empty:
    df = clean_and_normalize_data(df)
    
    # Identify Username column
    user_col = df.columns[0]
    for col in df.columns:
        if any(term in str(col).lower() for term in ["user", "member", "name", "player"]):
            user_col = col
            break

    # Flag highlighted rows
    df["_is_highlighted"] = df[user_col].astype(str).apply(
        lambda val: any(h in val.lower() for h in highlight_list)
    )

    # Section 1: Super smart guys summary
    st.subheader("⭐ Super smart guys summary")
    highlighted_df = df[df["_is_highlighted"]].drop(columns=["_is_highlighted"])
    
    if not highlighted_df.empty:
        st.dataframe(
            highlighted_df, 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("None of the specified highlighted usernames were found in this week's data.")

    st.markdown("---")

    # Section 2: Full Group Leaderboard
    st.subheader("📋 Full Group Leaderboard")

    def highlight_rows(row):
        if row["_is_highlighted"]:
            return ["background-color: #1e3d59; color: #ffffff; font-weight: bold;"] * len(row)
        return [""] * len(row)

    styled_df = df.style.apply(highlight_rows, axis=1)

    st.dataframe(
        df.drop(columns=["_is_highlighted"]),
        use_container_width=True,
        height=600
    )

else:
    st.info("No data loaded. Paste data into GitHub under `data/week1.txt` or use the sidebar paste box.")
