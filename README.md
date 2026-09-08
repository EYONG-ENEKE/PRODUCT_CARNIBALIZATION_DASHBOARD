# Product Cannibalization Analytics Dashboard

## Overview

The **Product Cannibalization Analytics Dashboard** is an interactive data analytics application built with **Python, Pandas, Plotly, Seaborn, Matplotlib, and Streamlit**.

The project analyzes promotional activity at product, category, brand, offer-type, channel, and monthly levels to identify:

- Promotion patterns
- Discount-depth behavior
- Promotion frequency
- Promotion risk
- Financial value transfer
- Potential chronic promotional dependency
- Products exhibiting characteristics associated with potential cannibalization

The application transforms raw promotional data into an interactive business intelligence dashboard that enables users to explore promotional strategies and identify products that may require management attention.

> **Important analytical note:** The available dataset primarily contains promotional and pricing information. It does not directly contain transaction-level units sold, customer conversion, gross margin, or incremental sales. Therefore, the dashboard identifies **potential cannibalization risk** rather than claiming causal or realized sales cannibalization.

---

# Business Problem

Frequent and deep promotional activity can create several business risks.

For example, a product that is repeatedly promoted at substantial discounts may:

1. Become dependent on promotional pricing.
2. Reduce the perceived value of its regular price.
3. Encourage customers to wait for promotions.
4. Increase revenue sacrifice from discounting.
5. Potentially divert demand from other products within the same portfolio.

The objective of this project is to provide an analytical framework for identifying these patterns and converting them into actionable promotional intelligence.

---

#  Project Objectives

The dashboard is designed to answer questions such as:

### Promotion Strategy

- Which offer types use the deepest discounts?
- Which categories receive the highest promotional intensity?
- Which promotional channels are most active?
- What percentage of promotions belong to each offer type?

### Promotion Risk

- Which categories have the highest promotion risk scores?
- Which products are promoted most frequently?
- Which products combine high promotional frequency with deep discounts?

### Financial Impact

- How much customer savings are represented by promotional discounts?
- What is the estimated listed-price-to-promotional-price sacrifice represented in the dataset?
- How does the promotional value transfer compare across selected products and categories?

### Cannibalization Risk

- Which products are repeatedly promoted?
- Which products combine high promotional frequency and deep discounting?
- Which products fall into the potential **Chronic Cannibalizer** segment?

---

#  Project Architecture

The application follows a modular analytics architecture:

```text
                    ┌─────────────────────────────┐
                    │       Streamlit UI          │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │       Dashboard Filters      │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │      Analytics Engine         │
                    │                              │
                    │ • KPI Analysis               │
                    │ • Risk Analysis              │
                    │ • Financial Analysis         │
                    │ • Cannibalization Analysis   │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │     Feature Engineering       │
                    │                              │
                    │ • Date Features              │
                    │ • Promotion Duration          │
                    │ • Revenue Sacrifice          │
                    │ • Monthly Features           │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │      Data Validation          │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │       Data Ingestion          │
                    │ CSV / TXT / XLSX / XLS       │
                    └─────────────────────────────┘
```

---

# 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Pandas | Data manipulation and analytical processing |
| NumPy | Numerical operations |
| Plotly | Interactive visualizations |
| Seaborn | Statistical visualization |
| Matplotlib | Analytical plotting |
| Streamlit | Interactive dashboard |
| pathlib | Cross-platform file management |
| Type Hints | Code maintainability and readability |

---

# 📁 Project Structure

Recommended production-style structure:

```text
PRODUCT_CANNIBALIZATION/
│
├── app.py
│
├── config/
│   └── settings.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── data_loader.py
│   ├── data_validation.py
│   ├── feature_engineering.py
│   ├── analytics.py
│   ├── cannibalization.py
│   └── visualization.py
│
├── notebooks/
│   └── exploratory_analysis.ipynb
│
├── tests/
│   ├── test_data_loader.py
│   ├── test_analytics.py
│   └── test_cannibalization.py
│
├── screenshots/
│   ├── dashboard.png
│   ├── promotion_analysis.png
│   ├── risk_analysis.png
│   └── cannibalization_matrix.png
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 📥 Data Input

The application supports the following file formats:

```text
.csv
.txt
.xlsx
.xls
```

The dataset contains promotional attributes such as:

- Category
- Item Brand
- ITEM
- English Description
- OFFER TYPE
- Channel
- START_DATE
- END_DATE
- corrected_Depth%
- Promo_Risk_Score
- Saving
- Price with VAT
- Promo Price with VAT
- LABELS

The application performs data-type conversion and feature engineering before analytical processing.

---

# ⚙️ Data Processing Pipeline

The data pipeline follows these stages:

```text
Raw Dataset
     │
     ▼
Data Ingestion
     │
     ▼
Column Validation
     │
     ▼
Date Conversion
     │
     ▼
Missing/Fallback Handling
     │
     ▼
Numeric Conversion
     │
     ▼
Feature Engineering
     │
     ▼
Interactive Filtering
     │
     ▼
Analytical Aggregation
     │
     ▼
Visualization
     │
     ▼
Business Insights
```

---

# 🔧 Feature Engineering

The application creates analytical features including:

### Promotion Month

```python
df["Promo_Month"] = (
    df["START_DATE"]
    .dt.to_period("M")
    .astype(str)
)
```

### Promotion Duration

```python
df["Promotion_Duration_Days"] = (
    df["END_DATE"] - df["START_DATE"]
).dt.days + 1
```

### Revenue Sacrifice Proxy

```python
df["Revenue_Sacrifice"] = (
    df["Price with VAT"]
    - df["Promo Price with VAT"]
)
```

The revenue-sacrifice measure should be interpreted as a **price-discount proxy**, not actual realized revenue loss, unless transaction volume data is available.

---

# 📊 Dashboard Features

## 1. Executive KPI Dashboard

The application provides high-level promotional KPIs including:

- Total Promotions
- Average Discount Depth
- Average Promotion Risk
- Customer Savings

These metrics provide a quick overview of the selected analytical population.

---

## 2. Offer Type Analysis

The dashboard analyzes average discount depth across different promotion types.

Example analytical question:

> Which promotional mechanism is associated with the deepest discounting?

The results can help management evaluate whether certain promotion mechanisms are systematically more aggressive.

---

## 3. Category Analysis

The dashboard evaluates promotional discount depth across product categories.

This allows analysts to identify:

- Highly discounted categories
- Low-discount categories
- Categories receiving disproportionate promotional intensity

---

## 4. Promotion Type Distribution

The dashboard calculates the percentage distribution of promotional mechanisms.

Example:

```text
Offer Type A      35%
Offer Type B      27%
Offer Type C      21%
Other             17%
```

This provides visibility into the organization's promotional mix.

---

## 5. Channel Analysis

A boxplot is used to examine discount-depth distributions across promotional channels.

The visualization can reveal:

- Typical discount levels
- Variation in discount depth
- Potential outliers
- Differences between channels

---

#  Category-Level Risk Analysis

The dashboard calculates category-level:

- Average discount depth
- Average promotion risk score
- Promotion frequency

Categories are ranked according to their average risk score.

This provides a prioritization mechanism for further investigation.

---

#  Financial Value Transfer Analysis

The dashboard compares:

### Customer Savings

```text
Sum of promotional savings
```

against:

### Company Revenue Sacrifice Proxy

```text
Sum of:
Regular Price − Promotional Price
```

The comparison is visualized using an interactive donut chart.

### Interpretation

The metric should be interpreted carefully.

Without:

- Units sold
- Actual transactions
- Gross margin
- Cost of goods sold
- Incremental sales

the dashboard cannot establish actual company profit loss.

Therefore, this project deliberately treats the metric as a **promotional value-transfer / discount-sacrifice proxy**.

---

#  Monthly Promotional Trend Analysis

The dashboard evaluates promotional behavior over time.

Monthly metrics include:

- Average discount depth
- Average promotion risk score
- Promotion count

This enables identification of:

- Increasing promotional intensity
- Seasonal promotional patterns
- Changes in discount behavior
- Periods of elevated promotion risk

---

#  Product Cannibalization Risk Matrix

One of the key analytical components of the project is the **Product Cannibalization Risk Matrix**.

The model evaluates each product using two dimensions:

### X-Axis

**Promotional Frequency**

Measured as the number of unique months in which a product was promoted.

### Y-Axis

**Median Discount Depth**

The median promotional discount associated with the product.

---

#  Chronic Cannibalizer Identification

The project uses a rule-based screening methodology.

Products are classified as potential chronic cannibalizers when they satisfy both:

```text
Promotional Frequency ≥ 75th Percentile
AND
Discount Depth ≥ 75th Percentile
```

Conceptually:

```text
                 HIGH DISCOUNT
                       │
                       │
      Tactical         │       Potential
      Promotions       │       Chronic
                       │       Cannibalizers
                       │
───────────────────────┼────────────────────
                       │
      Baseline         │       Consistent
      Products         │       Promotional
                       │
                       │
                 LOW DISCOUNT
```

A product in the upper-right quadrant exhibits both:

- High promotional frequency
- High discount depth

Such products should be investigated further before being classified as actual cannibalizers.

---

#  Analytical Methodology

The project currently uses a **rule-based analytical framework** rather than a supervised machine-learning model.

The methodology is:

```text
Promotional Frequency
          +
Discount Depth
          +
Promotion Risk
          ↓
Risk Segmentation
          ↓
Potential Cannibalization
          ↓
Business Investigation
```

This approach provides an interpretable first-stage screening mechanism.

---

#  Important Model Limitation

The term **"cannibalization"** normally implies that increased sales of one product reduce sales of another product.

To prove this statistically, the dataset would ideally contain:

```text
Product
Date
Units Sold
Revenue
Price
Promotion Flag
Promotion Depth
Category
Brand
Customer
Margin
```

Preferably, the analysis would also incorporate:

- Product-level sales before promotion
- Sales during promotion
- Sales after promotion
- Sales of substitute products
- Customer-level purchasing behavior

With those variables, the project could progress from **risk screening** to quantitative cannibalization measurement.

---

#  Future Machine Learning Development

Future versions of this project can introduce machine learning.

## Phase 1 — Current

```text
Rule-Based Risk Screening
```

## Phase 2

```text
Customer/Product Segmentation
        ↓
Clustering
```

Potential algorithms:

- K-Means
- Hierarchical Clustering
- DBSCAN

## Phase 3

```text
Cannibalization Prediction
        ↓
Classification Model
```

Potential algorithms:

- Logistic Regression
- Random Forest
- XGBoost

## Phase 4

```text
Promotion Impact Modeling
        ↓
Causal Analysis
```

Potential methodologies:

- Difference-in-Differences
- Interrupted Time Series
- Propensity Score Methods
- Causal Impact Analysis

This would allow the project to move from:

> "Which products appear risky?"

toward:

> "What is the estimated incremental and cannibalized sales impact of a promotion?"

---

#  Business Value

The dashboard can support promotional decision-making by helping organizations:

- Identify products with excessive promotional dependency
- Monitor discount intensity
- Compare promotional strategies
- Identify high-risk product categories
- Monitor promotional trends
- Prioritize products for commercial review
- Improve promotional governance
- Develop data-driven promotion strategies

---

#  Installation

Clone the repository:

```bash
git clone <https://github.com/EYONG-ENEKE/PRODUCT_CARNIBALIZATION_DASHBOARD>
cd PRODUCT_CANNIBALIZATION
```

Create a virtual environment:

### Windows

```bash
python -m streamlit run "E:\PRODUCT_CARNIBALIZATION_DASHBOARD\PRODUCT_CARNIBALIZATION_DASHBOARD\DASHBOARD.py"
venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Requirements

Example `requirements.txt`:

```text
pandas
numpy
matplotlib
seaborn
plotly
streamlit
openpyxl
xlrd
```

---

# Running the Application

Launch the Streamlit application:

```bash
python -m streamlit run E:\PRODUCT_CARNIBALIZATION_DASHBORD\DASHBOARD.py
```

The application will open in your browser.

---

# 🖥️ Dashboard Workflow

```text
1. Launch Application
        ↓
2. Upload Dataset
        ↓
3. Select Date Range
        ↓
4. Select Category
        ↓
5. Select Brand
        ↓
6. Select Product
        ↓
7. Analyze KPIs
        ↓
8. Analyze Promotion Strategy
        ↓
9. Analyze Risk
        ↓
10. Analyze Financial Value Transfer
        ↓
11. Analyze Monthly Trends
        ↓
12. Identify Potential Chronic Cannibalizers
```

---

# 📸 Screenshots

Add dashboard screenshots to the repository:

```text
screenshots/
├── dashboard.png
├── promotion_strategy.png
├── category_risk.png
├── financial_analysis.png
└── cannibalization_matrix.png
```

Then reference them in this README:

```markdown
## Dashboard

![Product Cannibalization Dashboard](screenshots/dashboard.png)
```

---

# 📤 Exporting Results

The dashboard provides CSV downloads for major analytical outputs.

Available outputs include:

```text
offer_type_analysis.csv
category_analysis.csv
category_risk_analysis.csv
monthly_promotion_trends.csv
cannibalization_matrix.csv
```

This allows analysts to continue analysis outside the Streamlit environment.

---

# 🧪 Testing Strategy

A production version of the project should include automated tests.

Example:

```text
tests/
│
├── test_data_loader.py
├── test_data_validation.py
├── test_feature_engineering.py
├── test_analytics.py
└── test_cannibalization.py
```

Example test:

```python
def test_cannibalization_thresholds():

    matrix, frequency_threshold, discount_threshold = (
        calculate_cannibalization_matrix(df)
    )

    assert frequency_threshold >= 0
    assert discount_threshold >= 0
```

---

# 🔐 Data Privacy

Do not commit confidential company or customer information to GitHub.

Use:

```text
.gitignore
```

to exclude:

```text
data/raw/
*.csv
*.xlsx
*.xls
.env
venv/
__pycache__/
```

For portfolio demonstrations, use:

- Synthetic data
- Anonymized data
- Public datasets
- Aggregated datasets

---

# Development Roadmap

### Version 1.0

- [x] Promotional data ingestion
- [x] Interactive filtering
- [x] Discount-depth analysis
- [x] Category analysis
- [x] Promotion distribution
- [x] Channel analysis
- [x] Risk analysis
- [x] Financial value-transfer analysis
- [x] Monthly trends
- [x] Cannibalization risk matrix

### Version 2.0

- [ ] Modular multi-file architecture
- [ ] Automated data-quality tests
- [ ] Unit testing
- [ ] Configuration management
- [ ] Advanced logging
- [ ] Improved dashboard UX

### Version 3.0

- [ ] Product clustering
- [ ] ML-based promotion risk prediction
- [ ] SHAP model explainability
- [ ] Promotion effectiveness prediction
- [ ] Automated anomaly detection

### Version 4.0

- [ ] Transaction-level sales integration
- [ ] Causal inference
- [ ] Incremental sales measurement
- [ ] True cannibalization measurement
- [ ] Promotion optimization engine

---

#  Skills Demonstrated

This project demonstrates practical experience in:

### Python

- Functions
- Type hints
- Exception handling
- Modular programming
- Object-oriented/project architecture concepts
- Path management

### Data Analytics

- Data cleaning
- Data transformation
- Aggregation
- KPI development
- Trend analysis
- Risk segmentation
- Financial analysis

### Data Visualization

- Plotly
- Matplotlib
- Seaborn
- Interactive dashboards
- Statistical visualizations

### Data Science

- Feature engineering
- Quantile-based segmentation
- Analytical modeling
- Risk scoring
- Exploratory data analysis
- Preparation for machine-learning modeling

### Business Intelligence

- Promotional strategy analysis
- Product portfolio analysis
- Commercial risk identification
- Decision-support analytics

---

# Key Analytical Insight

The central idea behind this project is that **promotion frequency and discount depth should be analyzed together**.

A product that receives a single deep promotion is fundamentally different from a product that receives deep discounts repeatedly throughout the year.

Therefore:

```text
Promotion Frequency
          ×
Discount Depth
          ↓
Promotional Dependency Signal
          ↓
Potential Cannibalization Risk
```

This provides a more meaningful commercial screening mechanism than analyzing discount depth alone.

---

#  Disclaimer

This project is an analytical decision-support tool.

The identification of a **"Chronic Cannibalizer"** represents a **risk-screening classification**, not proof that a product is causing sales cannibalization.

Actual cannibalization should be validated using transaction-level sales, customer behavior, product substitution, pricing, margin, and time-series information.

---

#  License

This project is intended for educational, portfolio, and analytical demonstration purposes.

Add an appropriate license before distributing the repository publicly.

---

#  Author

**Data Analytics & Data Science Portfolio Project**

Built with:

```text
Python
Pandas
Plotly
Seaborn
Matplotlib
Streamlit
```

---

## Project Summary

The **Product Cannibalization Analytics Dashboard** combines promotional analytics, financial value-transfer analysis, risk segmentation, and product-level promotional behavior into a single interactive decision-support platform.

The project demonstrates how raw promotional data can be transformed into **actionable commercial intelligence**, while maintaining an important distinction between **observed promotional behavior and proven business causality**.