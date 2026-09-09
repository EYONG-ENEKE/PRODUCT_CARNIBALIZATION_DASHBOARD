from __future__ import annotations

import calendar
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st


# =============================================================================
# 1. APPLICATION CONFIGURATION
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
# 3. CUSTOM STYLING
# =============================================================================

def apply_dashboard_style() -> None:
    """Applying  lightweight CSS styling to the Streamlit application."""

    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }

            h1 {
                font-weight: 700;
            }

            .metric-card {
                padding: 10px;
            }
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
    """
    Read CSV, TXT, XLSX, or XLS uploaded through Streamlit.
    """

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
# 5. DATA VALIDATION
# =============================================================================

def validate_columns(df: pd.DataFrame) -> list[str]:
    """
    Identify missing columns required for analytics.
    """

    missing_columns = [
        column
        for column in REQUIRED_ANALYTICS_COLUMNS
        if column not in df.columns
    ]

    return missing_columns


def add_fallback_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add controlled fallback values for optional analytics columns.
    """

    df = df.copy()

    if "Promo_Month" not in df.columns and "START_DATE" in df.columns:
        df["Promo_Month"] = df["START_DATE"].dt.strftime("%Y-%m")

    for column, default_value in FALLBACK_COLUMNS.items():

        if column not in df.columns:
            df[column] = default_value

    return df


# =============================================================================
# 6. DATA PREPROCESSING
# =============================================================================

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform data type conversion, validation, and feature engineering.
    """

    df = df.copy()

    # -------------------------------------------------------------------------
    # Date processing
    # -------------------------------------------------------------------------

    for column in DATE_COLUMNS:

        if column not in df.columns:
            raise ValueError(
                f"Required date column '{column}' is missing."
            )

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
        )

    # -------------------------------------------------------------------------
    # Remove invalid dates
    # -------------------------------------------------------------------------

    df = df.dropna(
        subset=DATE_COLUMNS
    )

    # -------------------------------------------------------------------------
    # Optional fallback variables
    # -------------------------------------------------------------------------

    df = add_fallback_columns(df)

    # -------------------------------------------------------------------------
    # Numeric conversion
    # -------------------------------------------------------------------------

    numeric_columns = [
        "corrected_Depth%",
        "Promo_Risk_Score",
        "Saving",
        "Price with VAT",
        "Promo Price with VAT",
    ]

    for column in numeric_columns:

        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    # -------------------------------------------------------------------------
    # Feature engineering
    # -------------------------------------------------------------------------

    df["Promo_Month"] = (
        df["START_DATE"]
        .dt.to_period("M")
        .astype(str)
    )

    df["Month"] = df["START_DATE"].dt.month

    df["Month_Name"] = df["Month"].map(
        lambda month: calendar.month_abbr[month]
    )

    df["Revenue_Sacrifice"] = (
        df["Price with VAT"]
        - df["Promo Price with VAT"]
    )

    df["Promotion_Duration_Days"] = (
        df["END_DATE"] - df["START_DATE"]
    ).dt.days + 1

    return df


# =============================================================================
# 7. FILTER ENGINE
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
    """
    Apply dashboard filters in a controlled transformation pipeline.
    """

    filtered = df.loc[
        (df["START_DATE"] >= start_date)
        & (df["END_DATE"] <= end_date)
    ].copy()

    filter_map = {
        "Category": categories,
        "Item Brand": brands,
        "ITEM": items,
        "English Description": descriptions,
    }

    for column, selected_values in filter_map.items():

        if selected_values:
            filtered = filtered[
                filtered[column].isin(selected_values)
            ]

    return filtered


# =============================================================================
# 8. ANALYTICAL FUNCTIONS
# =============================================================================

def calculate_offer_type_analysis(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate average discount depth by offer type."""

    return (
        df.groupby("OFFER TYPE", as_index=False)
        ["corrected_Depth%"]
        .mean()
        .sort_values(
            "corrected_Depth%",
            ascending=False,
        )
    )


def calculate_category_analysis(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate average discount depth by product category."""

    return (
        df.groupby("Category", as_index=False)
        ["corrected_Depth%"]
        .mean()
        .sort_values(
            "corrected_Depth%",
            ascending=False,
        )
    )


def calculate_promotion_distribution(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate percentage distribution of promotion types."""

    distribution = (
        df["OFFER TYPE"]
        .value_counts(normalize=True)
        .mul(100)
        .reset_index()
    )

    distribution.columns = [
        "Offer Type",
        "Percentage",
    ]

    return distribution


def calculate_category_risk(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate category-level promotion frequency,
    discount depth and risk.
    """

    result = (
        df.groupby("Category")
        .agg(
            Average_Discount_Depth=(
                "corrected_Depth%",
                "mean",
            ),
            Average_Risk_Score=(
                "Promo_Risk_Score",
                "mean",
            ),
            Promotion_Frequency=(
                "ITEM",
                "count",
            ),
        )
        .reset_index()
    )

    return result.sort_values(
        "Average_Risk_Score",
        ascending=False,
    )


def calculate_financial_metrics(
    df: pd.DataFrame,
) -> dict[str, float]:
    """
    Calculate financial value transfer metrics.
    """

    customer_savings = df["Saving"].sum()

    revenue_sacrifice = df["Revenue_Sacrifice"].sum()

    net_value_transfer = (
        customer_savings
        - revenue_sacrifice
    )

    return {
        "customer_savings": customer_savings,
        "revenue_sacrifice": revenue_sacrifice,
        "net_value_transfer": net_value_transfer,
    }


def calculate_monthly_trends(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate monthly promotional performance trends."""

    monthly = (
        df.groupby("Promo_Month")
        .agg(
            Average_Discount_Depth=(
                "corrected_Depth%",
                "mean",
            ),
            Average_Risk_Score=(
                "Promo_Risk_Score",
                "mean",
            ),
            Promotion_Count=(
                "ITEM",
                "count",
            ),
        )
        .reset_index()
        .sort_values("Promo_Month")
    )

    monthly["Month_Name"] = pd.to_datetime(
        monthly["Promo_Month"]
    ).dt.strftime("%b")

    return monthly


# =============================================================================
# 9. CANNIBALIZATION ANALYSIS
# =============================================================================

def calculate_cannibalization_matrix(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, float, float]:
    """
    Identify potential chronic cannibalizers based on:

    X-axis:
        Number of unique promotional months

    Y-axis:
        Median discount depth

    Classification:
        Items above the 75th percentile of both metrics.
    """

    matrix_df = df.copy()

    matrix_df["Month_Period"] = (
        matrix_df["START_DATE"]
        .dt.to_period("M")
    )

    item_metrics = (
        matrix_df.groupby("ITEM")
        .agg(
            Unique_Months=(
                "Month_Period",
                "nunique",
            ),
            Median_Discount=(
                "corrected_Depth%",
                "median",
            ),
        )
        .reset_index()
    )

    if item_metrics.empty:
        return item_metrics, 0, 0

    # Normalize discount depth if supplied as percentage.
    if item_metrics["Median_Discount"].max() > 1:
        item_metrics["Median_Discount"] /= 100

    frequency_threshold = (
        item_metrics["Unique_Months"]
        .quantile(0.75)
    )

    discount_threshold = (
        item_metrics["Median_Discount"]
        .quantile(0.75)
    )

    chronic_mask = (
        (item_metrics["Unique_Months"] >= frequency_threshold)
        &
        (
            item_metrics["Median_Discount"]
            >= discount_threshold
        )
    )

    item_metrics["Product_Status"] = "Other Items"

    item_metrics.loc[
        chronic_mask,
        "Product_Status",
    ] = "Chronic Cannibalizer"

    return (
        item_metrics,
        frequency_threshold,
        discount_threshold,
    )


# =============================================================================
# 10. CHART FUNCTIONS
# =============================================================================

def plot_offer_type_analysis(
    data: pd.DataFrame,
):
    """Create offer type vs discount depth chart."""

    fig = px.bar(
        data,
        x="OFFER TYPE",
        y="corrected_Depth%",
        text="corrected_Depth%",
        title="Average Discount Depth by Offer Type",
        template="plotly_white",
    )

    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
    )

    fig.update_layout(
        xaxis_title="Offer Type",
        yaxis_title="Average Discount Depth",
    )

    return fig


def plot_category_analysis(
    data: pd.DataFrame,
):
    """Create category discount-depth chart."""

    fig = px.bar(
        data,
        x="Category",
        y="corrected_Depth%",
        title="Average Discount Depth by Category",
        template="plotly_white",
    )

    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Average Discount Depth",
    )

    return fig


def plot_promotion_distribution(
    data: pd.DataFrame,
):
    """Create promotion type distribution chart."""

    fig = px.bar(
        data,
        x="Percentage",
        y="Offer Type",
        orientation="h",
        text="Percentage",
        title="Promotion Type Distribution",
        template="plotly_white",
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
    )

    return fig


def plot_channel_distribution(
    data: pd.DataFrame,
):
    """Create channel discount-depth boxplot."""

    fig, ax = plt.subplots(
        figsize=(9, 5)
    )

    sns.boxplot(
        data=data,
        x="Channel",
        y="corrected_Depth%",
        ax=ax,
    )

    ax.set_title(
        "Discount Depth Distribution by Channel"
    )

    ax.set_xlabel("Channel")
    ax.set_ylabel("Discount Depth")

    plt.xticks(
        rotation=45,
        ha="right",
    )

    plt.tight_layout()

    return fig


def plot_value_transfer(
    metrics: dict[str, float],
):
    """Create customer-vs-company value transfer chart."""

    value_transfer = pd.DataFrame(
        {
            "Metric": [
                "Customer Gain",
                "Company Revenue Sacrifice",
            ],
            "Value": [
                metrics["customer_savings"],
                metrics["revenue_sacrifice"],
            ],
        }
    )

    fig = px.pie(
        value_transfer,
        names="Metric",
        values="Value",
        hole=0.45,
        title="Customer Gain vs Company Revenue Sacrifice",
    )

    return fig


def plot_monthly_trends(
    data: pd.DataFrame,
):
    """Create monthly promotional trend chart."""

    fig = px.line(
        data,
        x="Month_Name",
        y=[
            "Average_Discount_Depth",
            "Average_Risk_Score",
        ],
        markers=True,
        title="Monthly Promotional Performance",
        template="plotly_white",
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Average Value",
        legend_title="Metric",
    )

    return fig


def plot_cannibalization_matrix(
    data: pd.DataFrame,
    frequency_threshold: float,
    discount_threshold: float,
):
    """Create promotional cannibalization matrix."""

    fig, ax = plt.subplots(
        figsize=(12, 8)
    )

    sns.scatterplot(
        data=data,
        x="Unique_Months",
        y="Median_Discount",
        hue="Product_Status",
        alpha=0.65,
        s=80,
        ax=ax,
    )

    ax.axvline(
        frequency_threshold,
        linestyle="--",
        linewidth=2,
    )

    ax.axhline(
        discount_threshold,
        linestyle="--",
        linewidth=2,
    )

    ax.set_title(
        "Product Cannibalization Risk Matrix",
        fontsize=16,
        fontweight="bold",
    )

    ax.set_xlabel(
        "Promotional Frequency "
        "(Unique Active Months)"
    )

    ax.set_ylabel(
        "Median Discount Depth"
    )

    ax.yaxis.set_major_formatter(
        mtick.PercentFormatter(1.0)
    )

    ax.legend(
        title="Product Status",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=2,
    )

    plt.tight_layout()

    return fig


# =============================================================================
# 11. SIDEBAR FILTERS
# =============================================================================

def render_sidebar_filters(
    df: pd.DataFrame,
):
    """Render interactive dashboard filters."""

    st.sidebar.header("Dashboard Filters")

    # -------------------------------------------------------------------------
    # Date filters
    # -------------------------------------------------------------------------

    min_date = df["START_DATE"].min().date()
    max_date = df["END_DATE"].max().date()

    start_date = st.sidebar.date_input(
        "Start Date",
        value=min_date,
        min_value=min_date,
        max_value=max_date,
    )

    end_date = st.sidebar.date_input(
        "End Date",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
    )

    if start_date > end_date:

        st.sidebar.error(
            "Start Date cannot be after End Date."
        )

        return None

    # -------------------------------------------------------------------------
    # Category filter
    # -------------------------------------------------------------------------

    categories = st.sidebar.multiselect(
        "Category",
        options=sorted(
            df["Category"]
            .dropna()
            .unique()
        ),
    )

    category_subset = (
        df[df["Category"].isin(categories)]
        if categories
        else df
    )

    # -------------------------------------------------------------------------
    # Brand filter
    # -------------------------------------------------------------------------

    brands = st.sidebar.multiselect(
        "Item Brand",
        options=sorted(
            category_subset["Item Brand"]
            .dropna()
            .unique()
        ),
    )

    brand_subset = (
        category_subset[
            category_subset["Item Brand"].isin(brands)
        ]
        if brands
        else category_subset
    )

    # -------------------------------------------------------------------------
    # Item filter
    # -------------------------------------------------------------------------

    items = st.sidebar.multiselect(
        "ITEM",
        options=sorted(
            brand_subset["ITEM"]
            .dropna()
            .unique()
        ),
    )

    item_subset = (
        brand_subset[
            brand_subset["ITEM"].isin(items)
        ]
        if items
        else brand_subset
    )

    # -------------------------------------------------------------------------
    # Description filter
    # -------------------------------------------------------------------------

    descriptions = st.sidebar.multiselect(
        "English Description",
        options=sorted(
            item_subset["English Description"]
            .dropna()
            .unique()
        ),
    )

    return {
        "categories": categories,
        "brands": brands,
        "items": items,
        "descriptions": descriptions,
        "start_date": pd.Timestamp(start_date),
        "end_date": pd.Timestamp(end_date),
    }


# =============================================================================
# 12. DOWNLOAD UTILITY
# =============================================================================

def render_download_button(
    df: pd.DataFrame,
    filename: str,
    label: str = "Download CSV",
) -> None:
    """Render a standardized CSV download button."""

    csv_data = df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label=label,
        data=csv_data,
        file_name=filename,
        mime="text/csv",
    )


# =============================================================================
# 13. KPI SECTION
# =============================================================================

def render_kpis(
    df: pd.DataFrame,
) -> None:
    """Render executive-level promotional KPIs."""

    metrics = calculate_financial_metrics(df)

    total_promotions = len(df)

    avg_discount = df[
        "corrected_Depth%"
    ].mean()

    avg_risk = df[
        "Promo_Risk_Score"
    ].mean()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Promotions",
            f"{total_promotions:,}",
        )

    with col2:
        st.metric(
            "Average Discount Depth",
            f"{avg_discount:.2f}",
        )

    with col3:
        st.metric(
            "Average Promotion Risk",
            f"{avg_risk:.2f}",
        )

    with col4:
        st.metric(
            "Customer Savings(AED)",
            f"{metrics['customer_savings']:,.2f}",
        )


# =============================================================================
# 14. MAIN DASHBOARD
# =============================================================================

def main() -> None:
    """Application entry point."""

    apply_dashboard_style()

    st.title(
        f"{APP_ICON} {APP_TITLE}"
    )

    st.caption(
        "Promotional strategy, financial impact and "
        "product cannibalization intelligence"
    )

    # =========================================================================
    # DATA UPLOAD
    # =========================================================================

    uploaded_file = st.file_uploader(
        "Upload Promotional Dataset",
        type=[
            "csv",
            "txt",
            "xlsx",
            "xls",
        ],
    )

    # =========================================================================
    # DATA LOAD
    # =========================================================================

    try:

        df = load_data(
            file_path=str(DEFAULT_DATA_PATH),
            uploaded_file=uploaded_file,
        )

    except Exception as exc:

        st.error(
            f"Unable to load dataset: {exc}"
        )

        st.stop()

    # =========================================================================
    # DATA VALIDATION
    # =========================================================================

    missing_columns = validate_columns(df)

    if missing_columns:

        st.warning(
            "The following analytics columns are missing: "
            + ", ".join(missing_columns)
        )

    # =========================================================================
    # PREPROCESSING
    # =========================================================================

    try:

        df = preprocess_data(df)

    except Exception as exc:

        st.error(
            f"Data preprocessing failed: {exc}"
        )

        st.stop()

    # =========================================================================
    # SIDEBAR FILTERS
    # =========================================================================

    filters = render_sidebar_filters(df)

    if filters is None:
        st.stop()

    # =========================================================================
    # APPLY FILTERS
    # =========================================================================

    filtered_df = apply_filters(
        df=df,
        categories=filters["categories"],
        brands=filters["brands"],
        items=filters["items"],
        descriptions=filters["descriptions"],
        start_date=filters["start_date"],
        end_date=filters["end_date"],
    )

    # =========================================================================
    # EMPTY DATA CHECK
    # =========================================================================

    if filtered_df.empty:

        st.warning(
            "No records match the selected filters."
        )

        st.stop()

    # =========================================================================
    # EXECUTIVE KPI SECTION
    # =========================================================================

    st.subheader(
        "Executive Promotional Performance"
    )

    render_kpis(filtered_df)

    st.divider()

    # =========================================================================
    # OFFER & CATEGORY ANALYSIS
    # =========================================================================

    st.subheader(
        "Promotion Strategy Analysis"
    )

    offer_type_df = (
        calculate_offer_type_analysis(
            filtered_df
        )
    )

    category_df = (
        calculate_category_analysis(
            filtered_df
        )
    )

    col1, col2 = st.columns(2)

    with col1:

        st.plotly_chart(
            plot_offer_type_analysis(
                offer_type_df
            ),
            use_container_width=True,
        )

        with st.expander(
            "View Offer Type Data"
        ):

            st.dataframe(
                offer_type_df,
                use_container_width=True,
            )

            render_download_button(
                offer_type_df,
                "offer_type_analysis.csv",
            )

    with col2:

        st.plotly_chart(
            plot_category_analysis(
                category_df
            ),
            use_container_width=True,
        )

        with st.expander(
            "View Category Data"
        ):

            st.dataframe(
                category_df,
                use_container_width=True,
            )

            render_download_button(
                category_df,
                "category_analysis.csv",
            )

    # =========================================================================
    # PROMOTION DISTRIBUTION
    # =========================================================================

    st.subheader(
        "Promotion Type & Channel Analysis"
    )

    promotion_distribution = (
        calculate_promotion_distribution(
            filtered_df
        )
    )

    col1, col2 = st.columns(2)

    with col1:

        st.plotly_chart(
            plot_promotion_distribution(
                promotion_distribution
            ),
            use_container_width=True,
        )

    with col2:

        channel_fig = plot_channel_distribution(
            filtered_df
        )

        st.pyplot(
            channel_fig,
            use_container_width=True,
        )

        plt.close(channel_fig)

    # =========================================================================
    # CATEGORY RISK
    # =========================================================================

    st.subheader(
        "Category-Level Promotion Risk"
    )

    category_risk = calculate_category_risk(
        filtered_df
    )

    st.dataframe(
        category_risk,
        use_container_width=True,
    )

    render_download_button(
        category_risk,
        "category_risk_analysis.csv",
    )

    # =========================================================================
    # FINANCIAL VALUE TRANSFER
    # =========================================================================

    st.subheader(
        "Financial Value Transfer"
    )

    financial_metrics = calculate_financial_metrics(
        filtered_df
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Customer Savings(AED)",
            f"{financial_metrics['customer_savings']:,.2f}",
        )

    with col2:

        st.metric(
            "Company Revenue Sacrifice(AED)",
            f"{financial_metrics['revenue_sacrifice']:,.2f}",
        )

    with col3:

        if (
            financial_metrics["customer_savings"]
            >
            financial_metrics["revenue_sacrifice"]
        ):

            verdict = "Customers Gain More"

        else:

            verdict ='Company Retains More Value'
        

        st.metric(
            "Value Transfer Verdict",
            verdict,
        )

    st.plotly_chart(
        plot_value_transfer(
            financial_metrics
        ),
        use_container_width=True,
    )

    # =========================================================================
    # MONTHLY TRENDS
    # =========================================================================

    st.subheader(
        "Monthly Promotional Trend Analysis"
    )

    monthly_trends = calculate_monthly_trends(
        filtered_df
    )

    st.plotly_chart(
        plot_monthly_trends(
            monthly_trends
        ),
        use_container_width=True,
    )

    with st.expander(
        "View Monthly Trend Data"
    ):

        st.dataframe(
            monthly_trends,
            use_container_width=True,
        )

        render_download_button(
            monthly_trends,
            "monthly_promotion_trends.csv",
        )

    # =========================================================================
    # CANNIBALIZATION MATRIX
    # =========================================================================

    st.subheader(
        "Product Cannibalization Risk Matrix"
    )

    (
        matrix_df,
        frequency_threshold,
        discount_threshold,
    ) = calculate_cannibalization_matrix(
        filtered_df
    )

    if matrix_df.empty:

        st.info(
            "Insufficient data to calculate the "
            "cannibalization matrix."
        )

    else:

        chronic_count = (
            matrix_df[
                matrix_df["Product_Status"]
                == "Chronic Cannibalizer"
            ]
            .shape[0]
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Products Analyzed",
                f"{len(matrix_df):,}",
            )

        with col2:
            st.metric(
                "Potential Chronic Cannibalizers",
                f"{chronic_count:,}",
            )

        with col3:
            st.metric(
                "Cannibalization Rate",
                f"{chronic_count / len(matrix_df) * 100:.1f}%",
            )

        matrix_fig = plot_cannibalization_matrix(
            matrix_df,
            frequency_threshold,
            discount_threshold,
        )

        st.pyplot(
            matrix_fig,
            use_container_width=True,
        )

        plt.close(matrix_fig)

        with st.expander(
            "View Cannibalization Matrix Data"
        ):

            st.dataframe(
                matrix_df,
                use_container_width=True,
            )

            render_download_button(
                matrix_df,
                "cannibalization_matrix.csv",
            )

    # =========================================================================
    # FOOTER
    # =========================================================================

    st.divider()
    st.caption(
        "Product Cannibalization Analytics | "
        "Promotional Intelligence Dashboard"
    )

    st.caption(
            "Author : "
            "EYONG EYONG-ENEKE ALAIN"
        )

# =============================================================================
# 15. APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()
