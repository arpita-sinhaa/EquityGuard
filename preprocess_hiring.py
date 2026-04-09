import pandas as pd
from typing import Optional

# -------------------------
# CONFIG
# -------------------------
DATA_PATH = "data/adult.data"
OUTPUT_PATH = "hiring_bias_data.csv"

MIN_EDUCATION = 10
MIN_HOURS = 25
MIN_SAMPLE_SIZE = 100

REFERENCE_GROUP = {
    "sex": "Male",
    "race": "White",
    "age_group": "25-34"
}

# -------------------------
# COLUMN NAMES
# -------------------------
COLUMNS = [
    "age", "workclass", "fnlwgt", "education", "education-num",
    "marital-status", "occupation", "relationship", "race",
    "sex", "capital-gain", "capital-loss", "hours-per-week",
    "native-country", "income"
]

# -------------------------
# UTILS
# -------------------------
def safe_divide(numerator: float, denominator: float) -> Optional[float]:
    if denominator == 0 or pd.isna(denominator):
        return None
    return numerator / denominator

def assign_priority(ratio: Optional[float]) -> str:
    if ratio is None:
        return "low"
    elif ratio > 3:
        return "high"
    elif ratio > 1.5:
        return "medium"
    else:
        return "low"

def get_age_group(age: int) -> str:
    if 25 <= age <= 34:
        return "25-34"
    elif 35 <= age <= 44:
        return "35-44"
    elif 45 <= age <= 54:
        return "45-54"
    else:
        return "55+"

# -------------------------
# LOAD DATA
# -------------------------
def load_data(path: str) -> pd.DataFrame:
    print("Loading dataset...")
    df = pd.read_csv(path, names=COLUMNS, skipinitialspace=True)
    print(f"Initial rows: {len(df)}")
    return df

# -------------------------
# CLEAN DATA
# -------------------------
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    print("Cleaning data...")
    df = df.replace("?", pd.NA).dropna()

    # Normalize income column
    df["income"] = df["income"].str.strip()

    print(f"Rows after cleaning: {len(df)}")
    return df

# -------------------------
# APPLY FILTERS
# -------------------------
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    print("Applying control filters...")

    df = df[df["education-num"] >= MIN_EDUCATION]
    df = df[df["hours-per-week"] >= MIN_HOURS]

    print(f"Rows after filtering: {len(df)}")
    return df

# -------------------------
# FEATURE ENGINEERING
# -------------------------
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    print("Engineering features...")

    df["age_group"] = df["age"].apply(get_age_group)
    df["approved"] = df["income"].apply(lambda x: 1 if ">50K" in x else 0)

    return df

# -------------------------
# AGGREGATION
# -------------------------
def compute_group_stats(df: pd.DataFrame) -> pd.DataFrame:
    print("Computing group statistics...")

    grouped = df.groupby(["sex", "race", "age_group"]).agg(
        approval_rate=("approved", "mean"),
        sample_size=("approved", "count")
    ).reset_index()

    return grouped

# -------------------------
# REFERENCE RATE
# -------------------------
def get_reference_rate(grouped: pd.DataFrame) -> float:
    ref = grouped[
        (grouped["sex"] == REFERENCE_GROUP["sex"]) &
        (grouped["race"] == REFERENCE_GROUP["race"]) &
        (grouped["age_group"] == REFERENCE_GROUP["age_group"])
    ]

    if ref.empty:
        raise ValueError("Reference group not found. Try adjusting filters.")

    return ref["approval_rate"].values[0]

# -------------------------
# METRICS
# -------------------------
def compute_metrics(grouped: pd.DataFrame, reference_rate: float) -> pd.DataFrame:
    print("Computing fairness metrics...")

    grouped["disparity_ratio"] = grouped["approval_rate"].apply(
        lambda x: safe_divide(reference_rate, x)
    )

    # Better interpretability
    grouped["relative_rate"] = grouped["approval_rate"].apply(
        lambda x: safe_divide(x, reference_rate)
    )

    grouped["fourfifths_breach"] = grouped["approval_rate"] < (0.8 * reference_rate)
    grouped["reference_approval_rate"] = reference_rate
    grouped["domain"] = "hiring"

    grouped["remediation_priority"] = grouped["disparity_ratio"].apply(assign_priority)
    grouped["remediation_note"] = "Review hiring criteria for potential bias"

    return grouped

# -------------------------
# FINAL FILTER
# -------------------------
def filter_small_samples(grouped: pd.DataFrame) -> pd.DataFrame:
    print("Filtering small sample sizes...")
    grouped = grouped[grouped["sample_size"] >= MIN_SAMPLE_SIZE]
    print(f"Final groups: {len(grouped)}")
    return grouped

# -------------------------
# MAIN PIPELINE
# -------------------------
def main():
    df = load_data(DATA_PATH)
    df = clean_data(df)
    df = apply_filters(df)
    df = engineer_features(df)

    grouped = compute_group_stats(df)
    reference_rate = get_reference_rate(grouped)
    grouped = compute_metrics(grouped, reference_rate)
    grouped = filter_small_samples(grouped)

    grouped.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Data saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()