from __future__ import annotations

import base64
import calendar
import io
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st


# =============================================================================
# 1. APPLICATION CONFIGURATION & COLOR PALETTE
# =============================================================================

APP_TITLE = "PRODUCT CANNIBALIZATION ANALYTICS"
APP_ICON = "📊"


DEFAULT_DATA_PATH = Path(
    r"E:\PRODUCT_CARNIBALIZATION_DASHBOARD\PRODUCT_CARNIBALIZATION_DASHBOARD\processesd_data\processed_data.csv"
)

ENCODING = "ISO-8859-1"

DATE_COLUMNS = [
    "START_DATE",
    "END_DATE",
]

REQUIRED_ANALYTICS_COLUMNS = [
    "Category",
    "Item Brand",
    "ITEM",
    "English Description",
    "OFFER TYPE",
    "Channel",
    "corrected_Depth%",
    "Promo_Risk_Score",
    "Saving",
    "Price with VAT",
    "Promo Price with VAT",
]

FALLBACK_COLUMNS = {
    "LABELS": "Standard Brand",
    "Channel": "Retail Pharmacy",
    "Promo_Risk_Score": 0.5,
    "Saving": 0.0,
    "Price with VAT": 0.0,
    "Promo Price with VAT": 0.0,
}

PALETTE = {
    "primary": "#1f77b4",
    "low_risk": "#2ca02c",      # Green
    "moderate_risk": "#ff7f0e", # Orange/Amber
    "cannibalizer": "#d62728",  # Vibrant Red
}

STATUS_COLOR_MAP = {
    "Low Risk": PALETTE["low_risk"],
    "Moderate Risk": PALETTE["moderate_risk"],
    "Chronic Cannibalization Risk": PALETTE["cannibalizer"],
}


# =============================================================================
# 2. STREAMLIT PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# 3. CUSTOM STYLING & SIDEBAR COLOR PALETTE
# =============================================================================

def apply_dashboard_style() -> None:
    """Applying lightweight CSS styling, animations, and sidebar coloring."""

    st.markdown(
        f"""
        <style>
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            .block-container {{
                padding-top: 2rem;
                padding-bottom: 2rem;
                animation: fadeIn 0.6s ease-out;
            }}

            h1 {{
                font-weight: 700;
                color: {PALETTE['primary']};
            }}

            /* Customizing Left Pane (Sidebar) Background and Borders */
            [data-testid="stSidebar"] {{
                background-color: #f1f3f5;
                border-right: 1px solid #dee2e6;
            }}

            .executive-box {{
                background-color: #f8f9fa;
                border-left: 5px solid {PALETTE['primary']};
                padding: 18px;
                border-radius: 4px;
                margin-bottom: 20px;
                font-size: 15px;
                line-height: 1.6;
                animation: fadeIn 0.8s ease-out;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# 4. DATA INGESTION
# =============================================================================

@st.cache_data(show_spinner=False)
def load_data(
    file_path: Optional[str] = None,
    uploaded_file=None,
) -> pd.DataFrame:

    if uploaded_file is not None:
        return read_uploaded_file(uploaded_file)

    if file_path is None:
        file_path = str(DEFAULT_DATA_PATH)

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Default dataset could not be found: {path}"
        )

    return pd.read_csv(
        path,
        encoding=ENCODING,
    )


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    extension = Path(uploaded_file.name).suffix.lower()

    if extension in {".csv", ".txt"}:
        return pd.read_csv(
            uploaded_file,
            encoding=ENCODING,
        )

    if extension in {".xlsx", ".xls"}:
        return pd.read_excel(uploaded_file)

    raise ValueError(
        f"Unsupported file type: {extension}"
    )


# =============================================================================
# 5. DATA VALIDATION & PREPROCESSING
# =============================================================================

def validate_columns(df: pd.DataFrame) -> list[str]:
    return [
        col for col in REQUIRED_ANALYTICS_COLUMNS if col not in df.columns
    ]


def add_fallback_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Promo_Month" not in df.columns and "START_DATE" in df.columns:
        df["Promo_Month"] = df["START_DATE"].dt.strftime("%Y-%m")
    for col, default_val in FALLBACK_COLUMNS.items():
        if col not in df.columns:
            df[col] = default_val
    return df


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in DATE_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Required date column '{col}' is missing.")
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df = df.dropna(subset=DATE_COLUMNS)
    df = add_fallback_columns(df)

    numeric_cols = [
        "corrected_Depth%",
        "Promo_Risk_Score",
        "Saving",
        "Price with VAT",
        "Promo Price with VAT",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Promo_Month"] = df["START_DATE"].dt.to_period("M").astype(str)
    df["Month"] = df["START_DATE"].dt.month
    df["Month_Name"] = df["Month"].map(lambda m: calendar.month_abbr[m])
    df["Revenue_Sacrifice"] = df["Price with VAT"] - df["Promo Price with VAT"]
    df["Promotion_Duration_Days"] = (df["END_DATE"] - df["START_DATE"]).dt.days + 1

    return df


# =============================================================================
# 6. FILTER ENGINE
# =============================================================================

def apply_filters(
    df: pd.DataFrame,
    categories: list[str],
    brands: list[str],
    items: list[str],
    descriptions: list[str],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    filtered = df.loc[
        (df["START_DATE"] >= start_date) & (df["END_DATE"] <= end_date)
    ].copy()

    filter_map = {
        "Category": categories,
        "Item Brand": brands,
        "ITEM": items,
        "English Description": descriptions,
    }

    for col, vals in filter_map.items():
        if vals:
            filtered = filtered[filtered[col].isin(vals)]

    return filtered


# =============================================================================
# 7. ANALYTICAL FUNCTIONS
# =============================================================================

def calculate_offer_type_analysis(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("OFFER TYPE", as_index=False)["corrected_Depth%"]
        .mean()
        .sort_values("corrected_Depth%", ascending=False)
    )


def calculate_category_analysis(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("Category", as_index=False)["corrected_Depth%"]
        .mean()
        .sort_values("corrected_Depth%", ascending=False)
    )


def calculate_promotion_distribution(df: pd.DataFrame) -> pd.DataFrame:
    dist = df["OFFER TYPE"].value_counts(normalize=True).mul(100).reset_index()
    dist.columns = ["Offer Type", "Percentage"]
    return dist


def calculate_category_risk(df: pd.DataFrame) -> pd.DataFrame:
    result = (
        df.groupby("Category")
        .agg(
            Average_Discount_Depth=("corrected_Depth%", "mean"),
            Average_Risk_Score=("Promo_Risk_Score", "mean"),
            Promotion_Frequency=("ITEM", "count"),
        )
        .reset_index()
    )
    return result.sort_values("Average_Risk_Score", ascending=False)


def calculate_financial_metrics(df: pd.DataFrame) -> dict[str, float]:
    customer_savings = df["Saving"].sum()
    price_reduction_value = df["Revenue_Sacrifice"].sum()
    return {
        "customer_savings": customer_savings,
        "price_reduction_value": price_reduction_value,
        "net_value_transfer": customer_savings - price_reduction_value,
    }


def calculate_monthly_trends(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.groupby("Promo_Month")
        .agg(
            Average_Discount_Depth=("corrected_Depth%", "mean"),
            Average_Risk_Score=("Promo_Risk_Score", "mean"),
            Promotion_Count=("ITEM", "count"),
        )
        .reset_index()
        .sort_values("Promo_Month")
    )
    monthly["Month_Name"] = pd.to_datetime(monthly["Promo_Month"]).dt.strftime("%b")
    return monthly


# =============================================================================
# 8. CANNIBALIZATION MATRIX, VICTIMS & ASSORTMENT ROLES
# =============================================================================

def calculate_cannibalization_matrix(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, float, float]:
    matrix_df = df.copy()
    matrix_df["Month_Period"] = matrix_df["START_DATE"].dt.to_period("M")

    item_metrics = (
        matrix_df.groupby("ITEM")
        .agg(
            Unique_Months=("Month_Period", "nunique"),
            Median_Discount=("corrected_Depth%", "median"),
        )
        .reset_index()
    )

    if item_metrics.empty:
        return item_metrics, 0, 0

    if item_metrics["Median_Discount"].max() > 1:
        item_metrics["Median_Discount"] /= 100

    freq_thresh = item_metrics["Unique_Months"].quantile(0.75)
    disc_thresh = item_metrics["Median_Discount"].quantile(0.75)

    def classify_status(row):
        is_high_freq = row["Unique_Months"] >= freq_thresh
        is_high_disc = row["Median_Discount"] >= disc_thresh
        if is_high_freq and is_high_disc:
            return "Chronic Cannibalization Risk"
        elif is_high_freq or is_high_disc:
            return "Moderate Risk"
        else:
            return "Low Risk"

    item_metrics["Product_Status"] = item_metrics.apply(classify_status, axis=1)

    return item_metrics, freq_thresh, disc_thresh


def calculate_victim_items(df: pd.DataFrame, matrix_df: pd.DataFrame) -> pd.DataFrame:
    if matrix_df.empty:
        return pd.DataFrame()

    chronic_items = matrix_df[matrix_df["Product_Status"] == "Chronic Cannibalization Risk"]["ITEM"].tolist()
    if not chronic_items:
        return pd.DataFrame()

    df_copy = df.copy()
    df_copy["Month_Period"] = df_copy["START_DATE"].dt.to_period("M")

    chronic_df = df_copy[df_copy["ITEM"].isin(chronic_items)][["Category", "ITEM", "Month_Period"]].drop_duplicates()
    sibling_df = df_copy[~df_copy["ITEM"].isin(chronic_items)]

    if sibling_df.empty or chronic_df.empty:
        return pd.DataFrame()

    item_monthly_activity = (
        sibling_df.groupby(["Category", "ITEM", "English Description", "Month_Period"])
        .size()
        .reset_index(name="Activity_Count")
    )

    active_chronic_months = set(zip(chronic_df["Category"], chronic_df["Month_Period"]))

    item_monthly_activity["Is_Cannibalizer_Active"] = item_monthly_activity.apply(
        lambda row: (row["Category"], row["Month_Period"]) in active_chronic_months, axis=1
    )

    comparison = (
        item_monthly_activity.groupby(["Category", "ITEM", "English Description", "Is_Cannibalizer_Active"])["Activity_Count"]
        .mean()
        .unstack(fill_value=0)
    )

    if True not in comparison.columns or False not in comparison.columns:
        return pd.DataFrame()

    comparison.columns = ["Activity_Baseline", "Activity_During_Cannibalizer"]
    comparison["Activity_Decline_Pct"] = (
        (comparison["Activity_Baseline"] - comparison["Activity_During_Cannibalizer"])
        / comparison["Activity_Baseline"].replace(0, 1)
    ) * 100

    victims = (
        comparison[comparison["Activity_Decline_Pct"] > 0]
        .reset_index()
        .sort_values("Activity_Decline_Pct", ascending=False)
    )
    return victims


def calculate_category_role_framework(df: pd.DataFrame, matrix_df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    
    item_agg = (
        df.groupby(["Category", "Item Brand", "ITEM", "English Description"])
        .agg(
            Promo_Count=("ITEM", "count"),
            Avg_Discount=("corrected_Depth%", "mean"),
            Total_Revenue_Sacrifice=("Revenue_Sacrifice", "sum")
        )
        .reset_index()
    )
    
    if item_agg.empty:
        return item_agg
        
    freq_median = item_agg["Promo_Count"].median()
    disc_median = item_agg["Avg_Discount"].median()
    
    def assign_role(row):
        if row["Promo_Count"] >= freq_median and row["Avg_Discount"] >= disc_median:
            return "Destination (Traffic Driver)"
        elif row["Promo_Count"] >= freq_median and row["Avg_Discount"] < disc_median:
            return "Routine (Core Staple)"
        elif row["Promo_Count"] < freq_median and row["Avg_Discount"] >= disc_median:
            return "Convenience / Promo-Driven"
        else:
            return "Seasonal / Niche"
            
    item_agg["Category_Role"] = item_agg.apply(assign_role, axis=1)
    
    if not matrix_df.empty and "Product_Status" in matrix_df.columns:
        item_agg = pd.merge(item_agg, matrix_df[["ITEM", "Product_Status"]], on="ITEM", how="left")
        item_agg["Product_Status"] = item_agg["Product_Status"].fillna("Low Risk")
        
    return item_agg.sort_values("Total_Revenue_Sacrifice", ascending=False)


# =============================================================================
# 9. EXPORTS & EXECUTIVE INSIGHTS
# =============================================================================

def render_dynamic_executive_insights(df: pd.DataFrame, matrix_df: pd.DataFrame, victim_df: pd.DataFrame):
    total_promos = len(df)
    fin = calculate_financial_metrics(df)
    
    chronic_count = 0
    if not matrix_df.empty and "Product_Status" in matrix_df.columns:
        chronic_count = matrix_df[matrix_df["Product_Status"] == "Chronic Cannibalization Risk"].shape[0]
    
    victim_count = len(victim_df) if not victim_df.empty else 0
    top_cat = df["Category"].mode()[0] if not df["Category"].empty else "N/A"

    summary_html = f"""
    <div class="executive-box">
        <b>💡 Dynamic Executive Portfolio Summary:</b><br>
        • Analyzed <b>{total_promos:,}</b> promotional events across active categories, led by high activity in <b>{top_cat}</b>.<br>
        • Identified <b>{chronic_count}</b> products with <i>Chronic Cannibalization Risk</i> and <b>{victim_count}</b> <i>Potentially Vulnerable Sibling Products</i> experiencing activity decline.<br>
        • Total potential price reduction value stands at <b>AED {fin['price_reduction_value']:,.2f}</b> against customer price benefits of <b>AED {fin['customer_savings']:,.2f}</b>.
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)


def generate_excel_report(filtered_df: pd.DataFrame, matrix_df: pd.DataFrame, victim_df: pd.DataFrame, role_df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        filtered_df.to_excel(writer, sheet_name="Filtered Promotions", index=False)
        matrix_df.to_excel(writer, sheet_name="Cannibalization Matrix", index=False)
        if not victim_df.empty:
            victim_df.to_excel(writer, sheet_name="Vulnerable Sibling Items", index=False)
        if not role_df.empty:
            role_df.to_excel(writer, sheet_name="Assortment Roles", index=False)
    return output.getvalue()


def generate_html_report(df: pd.DataFrame, matrix_df: pd.DataFrame, victim_df: pd.DataFrame) -> str:
    fin = calculate_financial_metrics(df)
    chronic_count = matrix_df[matrix_df["Product_Status"] == "Chronic Cannibalization Risk"].shape[0] if not matrix_df.empty else 0
    
    html = f"""
    <html>
    <head>
        <title>Promotional Cannibalization Executive Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 30px; color: #333; }}
            h1 {{ color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 10px; }}
            h2 {{ color: #333; margin-top: 30px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Executive Promotional Cannibalization Report</h1>
        <p><b>Generated on:</b> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</p>
        
        <h2>Executive Key Performance Indicators</h2>
        <ul>
            <li><b>Total Promotions Evaluated:</b> {len(df):,}</li>
            <li><b>Products with Chronic Cannibalization Risk:</b> {chronic_count}</li>
            <li><b>Customer Price Benefit:</b> AED {fin['customer_savings']:,.2f}</li>
            <li><b>Potential Price Reduction Value:</b> AED {fin['price_reduction_value']:,.2f}</li>
        </ul>

        <h2>Potentially Vulnerable Sibling Products</h2>
        {victim_df.head(10).to_html(index=False, classes='table') if not victim_df.empty else "<p>No vulnerable sibling data available.</p>"}

        <h2>Chronic Cannibalization Risk Products</h2>
        {matrix_df[matrix_df['Product_Status'] == 'Chronic Cannibalization Risk'].to_html(index=False, classes='table') if not matrix_df.empty else "<p>No chronic items available.</p>"}
    </body>
    </html>
    """
    return html


# =============================================================================
# 10. CHART FUNCTIONS
# =============================================================================

def plot_offer_type_analysis(data: pd.DataFrame):
    fig = px.bar(
        data,
        x="OFFER TYPE",
        y="corrected_Depth%",
        text="corrected_Depth%",
        title="Average Discount Depth by Offer Type",
        template="plotly_white",
        color="OFFER TYPE",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(xaxis_title="Offer Type", yaxis_title="Average Discount Depth", showlegend=False)
    return fig


def plot_category_analysis(data: pd.DataFrame):
    fig = px.bar(
        data,
        x="Category",
        y="corrected_Depth%",
        title="Average Discount Depth by Category",
        template="plotly_white",
        color="Category",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_layout(xaxis_title="Category", yaxis_title="Average Discount Depth", showlegend=False)
    return fig


def plot_promotion_distribution(data: pd.DataFrame):
    fig = px.bar(
        data,
        x="Percentage",
        y="Offer Type",
        orientation="h",
        text="Percentage",
        title="Promotion Type Distribution",
        template="plotly_white",
        color="Offer Type",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(showlegend=False)
    return fig


def plot_channel_distribution(data: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=data, x="Channel", y="corrected_Depth%", ax=ax, palette="Blues")
    ax.set_title("Discount Depth Distribution by Channel", fontweight="bold")
    ax.set_xlabel("Channel")
    ax.set_ylabel("Discount Depth")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig


def plot_value_transfer(metrics: dict[str, float]):
    value_transfer = pd.DataFrame(
        {
            "Metric": ["Customer Price Benefit", "Potential Price Reduction Value"],
            "Value": [metrics["customer_savings"], metrics["price_reduction_value"]],
        }
    )
    fig = px.pie(
        value_transfer,
        names="Metric",
        values="Value",
        hole=0.45,
        title="Customer Price Benefit vs Potential Price Reduction Value",
        color="Metric",
        color_discrete_map={
            "Customer Price Benefit": PALETTE["low_risk"],
            "Potential Price Reduction Value": PALETTE["cannibalizer"],
        },
    )
    return fig


def plot_monthly_trends(data: pd.DataFrame):
    fig = px.line(
        data,
        x="Month_Name",
        y="Average_Discount_Depth",
        markers=True,
        title="Monthly Promotional Performance Trend",
        template="plotly_white",
        color_discrete_sequence=[PALETTE["primary"]],
    )
    fig.update_layout(xaxis_title="Month", yaxis_title="Average Discount Depth")
    return fig


def plot_cannibalization_matrix(
    data: pd.DataFrame, freq_thresh: float, disc_thresh: float
):
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.scatterplot(
        data=data,
        x="Unique_Months",
        y="Median_Discount",
        hue="Product_Status",
        palette=STATUS_COLOR_MAP,
        alpha=0.85,
        s=90,
        ax=ax,
    )
    ax.axvline(freq_thresh, color=PALETTE["cannibalizer"], linestyle="--", linewidth=2)
    ax.axhline(disc_thresh, color=PALETTE["cannibalizer"], linestyle="--", linewidth=2)
    ax.set_title("Product Cannibalization Risk Matrix", fontsize=16, fontweight="bold")
    ax.set_xlabel("Promotional Frequency (Unique Active Months)")
    ax.set_ylabel("Median Discount Depth")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.legend(title="Risk Status", loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=True)
    plt.tight_layout()
    return fig


def plot_category_role_distribution(role_df: pd.DataFrame):
    fig = px.scatter(
        role_df,
        x="Promo_Count",
        y="Avg_Discount",
        color="Category_Role",
        hover_data=["ITEM", "English Description", "Total_Revenue_Sacrifice"],
        title="Assortment Optimization: Strategic Category Roles",
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_layout(
        xaxis_title="Promotional Frequency (Count)",
        yaxis_title="Average Discount Depth",
        legend_title="Assortment Role",
    )
    return fig


# =============================================================================
# 11. SIDEBAR & UTILITIES
# =============================================================================

def render_sidebar_filters(df: pd.DataFrame):
    st.sidebar.markdown(f"<h2 style='color: {PALETTE['primary']}; font-size: 1.3rem;'>🔍 Dashboard Controls</h2>", unsafe_allow_html=True)
    
    min_date = df["START_DATE"].min().date()
    max_date = df["END_DATE"].max().date()

    start_date = st.sidebar.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

    if start_date > end_date:
        st.sidebar.error("Start Date cannot be after End Date.")
        return None

    # Safe cascaded filtering with explicit .empty checks
    categories = st.sidebar.multiselect("Category", options=sorted(df["Category"].dropna().unique()))
    cat_subset = df[df["Category"].isin(categories)] if categories else df

    brand_options = sorted(cat_subset["Item Brand"].dropna().unique()) if not cat_subset.empty else sorted(df["Item Brand"].dropna().unique())
    brands = st.sidebar.multiselect("Item Brand", options=brand_options)
    brand_subset = cat_subset[cat_subset["Item Brand"].isin(brands)] if brands and not cat_subset.empty else cat_subset

    item_options = sorted(brand_subset["ITEM"].dropna().unique()) if not brand_subset.empty else sorted(df["ITEM"].dropna().unique())
    items = st.sidebar.multiselect("ITEM", options=item_options)
    item_subset = brand_subset[brand_subset["ITEM"].isin(items)] if items and not brand_subset.empty else brand_subset

    desc_options = sorted(item_subset["English Description"].dropna().unique()) if not item_subset.empty else sorted(df["English Description"].dropna().unique())
    descriptions = st.sidebar.multiselect("English Description", options=desc_options)

    # What-If Simulation Sidebar Section
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"<h3 style='color: {PALETTE['primary']}; font-size: 1.1rem;'>🔮 Promo Simulation Engine</h3>", unsafe_allow_html=True)
    sim_depth_adjustment = st.sidebar.slider("Adjust Discount Depth (%)", -20, 20, 0, step=1, help="Simulate margin and revenue shift by modifying overall promotion depth.")

    return {
        "categories": categories,
        "brands": brands,
        "items": items,
        "descriptions": descriptions,
        "start_date": pd.Timestamp(start_date),
        "end_date": pd.Timestamp(end_date),
        "sim_depth_adjustment": sim_depth_adjustment,
    }


def render_kpis(df: pd.DataFrame):
    metrics = calculate_financial_metrics(df)
    total_promos = len(df)
    avg_disc = df["corrected_Depth%"].mean()
    avg_risk = df["Promo_Risk_Score"].mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Promotions", f"{total_promos:,}")
    with c2:
        st.metric("Average Discount Depth", f"{avg_disc:.2f}")
    with c3:
        st.metric("Average Promotion Risk", f"{avg_risk:.2f}")
    with c4:
        st.metric("Customer Price Benefit (AED)", f"{metrics['customer_savings']:,.2f}")


def highlight_risk_status(row):
    status = row.get("Product_Status")
    if status == "Chronic Cannibalization Risk":
        return ["background-color: #f8d7da; color: #721c24"] * len(row)
    elif status == "Moderate Risk":
        return ["background-color: #fff3cd; color: #856404"] * len(row)
    elif status == "Low Risk":
        return ["background-color: #d4edda; color: #155724"] * len(row)
    return [""] * len(row)


# =============================================================================
# 12. MAIN APP (TABBED ARCHITECTURE)
# =============================================================================

def main() -> None:
    apply_dashboard_style()
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.caption("Promotional strategy, financial impact, assortment roles, and professional cannibalization intelligence")
    st.caption("Author : EYONG-ENEKE")

    uploaded_file = st.file_uploader("Upload Promotional Dataset", type=["csv", "txt", "xlsx", "xls"])

    try:
        df = load_data(file_path=str(DEFAULT_DATA_PATH), uploaded_file=uploaded_file)
    except Exception as exc:
        st.error(f"Unable to load dataset: {exc}")
        st.stop()

    if validate_columns(df):
        st.warning("Missing some analytics columns, fallback defaults applied.")

    try:
        df = preprocess_data(df)
    except Exception as exc:
        st.error(f"Data preprocessing failed: {exc}")
        st.stop()

    filters = render_sidebar_filters(df)
    if filters is None:
        st.stop()

    filtered_df = apply_filters(
        df=df,
        categories=filters["categories"],
        brands=filters["brands"],
        items=filters["items"],
        descriptions=filters["descriptions"],
        start_date=filters["start_date"],
        end_date=filters["end_date"],
    )

    if filtered_df.empty:
        st.warning("No records match the selected filters.")
        st.stop()

    # Apply What-If Simulation Adjustment if selected
    sim_adj = filters["sim_depth_adjustment"]
    if sim_adj != 0:
        filtered_df = filtered_df.copy()
        filtered_df["corrected_Depth%"] = filtered_df["corrected_Depth%"] * (1 + sim_adj / 100)
        filtered_df["Revenue_Sacrifice"] = filtered_df["Revenue_Sacrifice"] * (1 + sim_adj / 100)

    # Pre-calculate Matrix and Victims
    matrix_df, freq_thresh, disc_thresh = calculate_cannibalization_matrix(filtered_df)
    victim_df = calculate_victim_items(filtered_df, matrix_df)
    role_df = calculate_category_role_framework(filtered_df, matrix_df)

    # DYNAMIC EXECUTIVE INSIGHTS BOX
    render_dynamic_executive_insights(filtered_df, matrix_df, victim_df)

    # ENTERPRISE DOWNLOAD BUTTONS (HTML Report & Multi-Sheet Excel Workbook)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        html_report = generate_html_report(filtered_df, matrix_df, victim_df)
        st.download_button(
            label="📄 Download Executive HTML Report",
            data=html_report,
            file_name="executive_cannibalization_report.html",
            mime="text/html",
            use_container_width=True,
        )
    with col_dl2:
        excel_bytes = generate_excel_report(filtered_df, matrix_df, victim_df, role_df)
        st.download_button(
            label="📊 Download Multi-Sheet Enterprise Excel Workbook",
            data=excel_bytes,
            file_name="cannibalization_enterprise_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.divider()

    # =========================================================================
    # TABBED NAVIGATION WORKSPACE
    # =========================================================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Executive Overview & Financials", 
        "🏷️ Promotion & Channel Strategy", 
        "⚠️ Cannibalization Matrix", 
        "🛒 Assortment & Vulnerability"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: EXECUTIVE OVERVIEW & FINANCIALS
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("Executive Promotional Performance")
        render_kpis(filtered_df)
        st.divider()

        st.subheader("Financial Value Transfer")
        fin_metrics = calculate_financial_metrics(filtered_df)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Customer Price Benefit (AED)", f"{fin_metrics['customer_savings']:,.2f}")
        with c2:
            st.metric("Potential Price Reduction Value (AED)", f"{fin_metrics['price_reduction_value']:,.2f}")
        with c3:
            verdict = "Customer Benefit Exceeds Price Reduction" if fin_metrics["customer_savings"] > fin_metrics["price_reduction_value"] else "Price Reduction Exceeds Customer Benefit"
            st.metric("Value Transfer Verdict", verdict)

        st.plotly_chart(plot_value_transfer(fin_metrics), use_container_width=True)

        st.subheader("Monthly Promotional Trend Analysis")
        monthly_trends = calculate_monthly_trends(filtered_df)
        st.plotly_chart(plot_monthly_trends(monthly_trends), use_container_width=True)
        with st.expander("View Monthly Trend Data"):
            st.dataframe(monthly_trends, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 2: PROMOTION & CHANNEL STRATEGY
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("Promotion Strategy Analysis")
        offer_type_df = calculate_offer_type_analysis(filtered_df)
        category_df = calculate_category_analysis(filtered_df)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_offer_type_analysis(offer_type_df), use_container_width=True)
            with st.expander("View Offer Type Data"):
                st.dataframe(offer_type_df, use_container_width=True)
        with col2:
            st.plotly_chart(plot_category_analysis(category_df), use_container_width=True)
            with st.expander("View Category Data"):
                st.dataframe(category_df, use_container_width=True)

        st.subheader("Promotion Type & Channel Analysis")
        promo_dist = calculate_promotion_distribution(filtered_df)
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_promotion_distribution(promo_dist), use_container_width=True)
        with c2:
            chan_fig = plot_channel_distribution(filtered_df)
            st.pyplot(chan_fig, use_container_width=True)
            plt.close(chan_fig)

        st.subheader("Category-Level Promotion Risk")
        cat_risk = calculate_category_risk(filtered_df)
        st.dataframe(cat_risk, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 3: CANNIBALIZATION MATRIX
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("Product Cannibalization Risk Matrix")
        if matrix_df.empty:
            st.info("Insufficient data to calculate the cannibalization matrix.")
        else:
            chronic_count = matrix_df[matrix_df["Product_Status"] == "Chronic Cannibalization Risk"].shape[0]
            mod_count = matrix_df[matrix_df["Product_Status"] == "Moderate Risk"].shape[0]

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Products Analyzed", f"{len(matrix_df):,}")
            with c2:
                st.metric("Chronic Risk Items", f"{chronic_count:,}")
            with c3:
                st.metric("Moderate Risk Items", f"{mod_count:,}")
            with c4:
                st.metric("Severe Rate", f"{chronic_count / len(matrix_df) * 100:.1f}%")

            matrix_fig = plot_cannibalization_matrix(matrix_df, freq_thresh, disc_thresh)
            st.pyplot(matrix_fig, use_container_width=True)
            plt.close(matrix_fig)

            with st.expander("View Cannibalization Matrix Data with Risk Coloring"):
                styled_matrix = matrix_df.style.apply(highlight_risk_status, axis=1)
                st.dataframe(styled_matrix, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 4: ASSORTMENT & VULNERABILITY
    # -------------------------------------------------------------------------
    with tab4:
        st.subheader("Potentially Vulnerable Sibling Products")
        st.markdown("Highlighting non-chronic items within categories where items with chronic cannibalization risk are active that experience an activity decline.")
        
        if victim_df.empty:
            st.info("No significant vulnerable sibling products detected under current filter conditions.")
        else:
            st.metric("Potentially Vulnerable Sibling Products Identified", f"{len(victim_df):,}")
            st.dataframe(victim_df, use_container_width=True)

        st.divider()

        st.subheader("Category Role & Assortment Optimization")
        st.markdown("Classifying retail items by strategic merchandising role to balance traffic generation against margin sacrifice.")
        
        if role_df.empty:
            st.info("Insufficient data to compute category roles under current filters.")
        else:
            role_counts = role_df["Category_Role"].value_counts().reset_index()
            role_counts.columns = ["Role", "Item Count"]
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.dataframe(role_counts, use_container_width=True)
            with c2:
                st.plotly_chart(plot_category_role_distribution(role_df), use_container_width=True)
                
            with st.expander("View Full Assortment Role Mapping"):
                st.dataframe(role_df, use_container_width=True)

    st.divider()
    st.caption("Product Cannibalization Analytics |Promotional Intelligence Dashboard")

if __name__ == "__main__":
    main()



