import pandas as pd
import logging
from typing import Tuple

# -------------------------
# CONFIG
# -------------------------
INPUT_PATH = "data/train_Loan_Prediction.csv"
OUTPUT_PATH = "lending_bias_data.csv"

MIN_SAMPLE_SIZE = 50
REFERENCE_GROUP = ("Male", "Graduate")  # (Gender, Education)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# -------------------------
# LOAD DATA
# -------------------------
def load_data(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
        logging.info(f"Loaded dataset with shape {df.shape}")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

# -------------------------
# CLEAN DATA
# -------------------------
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = [col.strip() for col in df.columns]

    required_cols = [
        "Gender", "Education", "Loan_Status",
        "ApplicantIncome", "CoapplicantIncome", "LoanAmount"
    ]

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.dropna(subset=required_cols)

    df["Self_Employed"] = df.get("Self_Employed", "No").fillna("No")
    df["Credit_History"] = df.get("Credit_History", 0).fillna(0)

    return df

# -------------------------
# FEATURE ENGINEERING
# -------------------------
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["approved"] = (
        df["Loan_Status"]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("Y")
        .astype(int)
    )

    df["total_income"] = df["ApplicantIncome"] + df["CoapplicantIncome"]

    df["income_group"] = pd.cut(
        df["total_income"],
        bins=[0, 3000, 6000, 10000, float("inf")],
        labels=["low", "mid", "high", "very_high"]
    )

    return df

# -------------------------
# CONTROL FILTERS
# -------------------------
def apply_controls(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df[df["total_income"] > 1500]
    return df

# -------------------------
# GROUPING
# -------------------------
def compute_group_stats(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby(["Gender", "Education", "income_group"]).agg(
        approval_rate=("approved", "mean"),
        sample_size=("approved", "count")
    ).reset_index()

    logging.info(f"Computed group stats for {len(grouped)} groups")
    return grouped

# -------------------------
# REFERENCE GROUP
# -------------------------
def get_reference_rate(grouped: pd.DataFrame) -> float:
    ref = grouped[
        (grouped["Gender"] == REFERENCE_GROUP[0]) &
        (grouped["Education"] == REFERENCE_GROUP[1])
    ]

    if ref.empty:
        raise ValueError("Reference group not found in dataset")

    return float(ref["approval_rate"].iloc[0])

# -------------------------
# METRICS
# -------------------------
def compute_metrics(grouped: pd.DataFrame, reference_rate: float) -> pd.DataFrame:
    grouped = grouped.copy()

    grouped["disparity_ratio"] = grouped["approval_rate"].apply(
        lambda x: reference_rate / x if x > 0 else None
    )

    grouped["relative_rate"] = grouped["approval_rate"] / reference_rate

    grouped["fourfifths_breach"] = grouped["approval_rate"] < (0.8 * reference_rate)

    grouped["reference_approval_rate"] = reference_rate
    grouped["domain"] = "lending"

    return grouped

# -------------------------
# REMEDIATION
# -------------------------
def assign_remediation(grouped: pd.DataFrame) -> pd.DataFrame:
    def priority(ratio):
        if ratio is None:
            return "none"
        if ratio > 3:
            return "high"
        elif ratio > 1.5:
            return "medium"
        return "low"

    grouped["remediation_priority"] = grouped["disparity_ratio"].apply(priority)
    grouped["remediation_note"] = "Review loan approval criteria and credit scoring policies"

    return grouped

# -------------------------
# FILTER SMALL GROUPS
# -------------------------
def filter_small_groups(grouped: pd.DataFrame) -> pd.DataFrame:
    before = len(grouped)
    grouped = grouped[grouped["sample_size"] >= MIN_SAMPLE_SIZE]
    after = len(grouped)

    logging.info(f"Filtered small groups: {before} -> {after}")
    return grouped

# -------------------------
# SAVE OUTPUT
# -------------------------
def save_output(df: pd.DataFrame, path: str):
    try:
        df.to_csv(path, index=False)
        logging.info(f"Saved output to {path}")
    except Exception as e:
        raise RuntimeError(f"Failed to save output: {e}")

# -------------------------
# PIPELINE
# -------------------------
def run_pipeline(input_path: str, output_path: str) -> pd.DataFrame:
    logging.info("Starting lending bias pipeline")

    df = load_data(input_path)
    df = clean_data(df)
    df = engineer_features(df)
    df = apply_controls(df)

    grouped = compute_group_stats(df)
    reference_rate = get_reference_rate(grouped)

    grouped = compute_metrics(grouped, reference_rate)
    grouped = assign_remediation(grouped)
    grouped = filter_small_groups(grouped)

    save_output(grouped, output_path)

    logging.info("Pipeline completed successfully")

    return grouped

# -------------------------
# ENTRY POINT
# -------------------------
if __name__ == "__main__":
    run_pipeline(INPUT_PATH, OUTPUT_PATH)