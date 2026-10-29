#!/usr/bin/env python3
"""
Summarise Feedzai Bank Account Fraud (BAF) data for a lightweight HTML portfolio.
Usage:
    python analyze_baf.py Base.csv
    python analyze_baf.py Base.csv --output baf-summary.json

Only aggregated metrics are exported to JSON. No individual application rows are written.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd

TARGET = "fraud_bool"
CAT_FIELDS = [
    "month", "payment_type", "employment_status", "housing_status", "source",
    "device_os", "device_brand", "email_is_free", "phone_home_valid",
    "phone_mobile_valid", "has_other_cards", "foreign_request", "keep_alive_session",
]
NUM_FIELDS = [
    "name_email_similarity", "credit_risk_score", "velocity_6h", "velocity_24h",
    "velocity_4w", "customer_age", "income", "device_distinct_emails_8w",
    "date_of_birth_distinct_emails_4w", "zip_count_4w", "bank_branch_count_8w",
    "prev_address_months_count", "current_address_months_count",
    "session_length_in_minutes", "proposed_credit_limit", "days_since_request",
    "intended_balcon_amount", "bank_months_count",
]
SENTINELS = [
    "prev_address_months_count", "current_address_months_count", "bank_months_count",
    "session_length_in_minutes", "device_distinct_emails_8w", "intended_balcon_amount",
]
MIN_GROUP = 30

def json_safe(x):
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating,)): return None if not np.isfinite(x) else float(x)
    if isinstance(x, float) and not math.isfinite(x): return None
    return x

def group_summary(df, field, categorical):
    cols = [field, TARGET]
    d = df[cols].copy()
    d[TARGET] = pd.to_numeric(d[TARGET], errors="coerce")
    d = d[d[TARGET].isin([0,1])]
    if categorical:
        d[field] = d[field].fillna("(blank)").astype(str)
        g = d.groupby(field, dropna=False)[TARGET].agg(applications="size", fraud="sum").reset_index()
        g["fraud_rate"] = g["fraud"] / g["applications"]
        g = g.sort_values("applications", ascending=False).head(30)
        label = g[field].astype(str).tolist()
    else:
        vals = pd.to_numeric(d[field], errors="coerce")
        # Preserve documented negative sentinel values as their own group so they remain visible.
        sentinel = vals < 0
        d["band"] = "Missing / unavailable"
        valid = vals[~sentinel & vals.notna()]
        if len(valid):
            try:
                bins = pd.qcut(valid, q=5, duplicates="drop")
                d.loc[valid.index, "band"] = bins.astype(str)
            except ValueError:
                d.loc[valid.index, "band"] = "Observed values"
        d.loc[vals.notna() & sentinel, "band"] = "Negative sentinel value"
        g = d.groupby("band", dropna=False)[TARGET].agg(applications="size", fraud="sum").reset_index()
        g["fraud_rate"] = g["fraud"] / g["applications"]
        order = ["Missing / unavailable", "Negative sentinel value"]
        g["_ord"] = g["band"].apply(lambda x: order.index(x) if x in order else 2)
        g = g.sort_values(["_ord", "band"]).drop(columns="_ord")
        label = g["band"].astype(str).tolist()
    out = []
    for _, row in g.iterrows():
        out.append({"label": str(row[field] if categorical else row["band"]),
                    "applications": int(row["applications"]), "fraud": int(row["fraud"]),
                    "fraud_rate": float(row["fraud_rate"])})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="Path to the BAF Base.csv file")
    ap.add_argument("--output", default="baf-summary.json", help="Output JSON path")
    args = ap.parse_args()
    source = Path(args.csv)
    if not source.exists(): raise SystemExit(f"File not found: {source}")
    print(f"Reading {source} …")
    df = pd.read_csv(source, low_memory=False)
    if TARGET not in df.columns:
        raise SystemExit(f"Required column '{TARGET}' not found. Check that this is a BAF dataset variant.")
    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
    df = df[df[TARGET].isin([0,1])].copy()
    total = len(df)
    fraud = int(df[TARGET].sum())
    if not total: raise SystemExit("No usable rows with fraud_bool equal to 0 or 1.")
    summary = {
        "meta": {
            "dataset": "Feedzai Bank Account Fraud (BAF)",
            "source_file": source.name,
            "rows_analysed": total,
            "fraud_label": TARGET,
            "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
            "note": "Aggregated summaries only; no application-level rows are included."
        },
        "overview": {
            "applications": total, "fraud": fraud, "legitimate": total-fraud,
            "fraud_rate": fraud/total, "legitimate_rate": (total-fraud)/total,
            "months": int(df["month"].nunique()) if "month" in df else None
        },
        "monthly": [],
        "features": {},
        "segment_rankings": {},
        "data_quality": [],
        "correlations": []
    }
    if "month" in df:
        m = df.groupby("month")[TARGET].agg(applications="size", fraud="sum").reset_index().sort_values("month")
        for _, r in m.iterrows():
            summary["monthly"].append({"month": json_safe(r["month"]), "applications": int(r["applications"]),
                "fraud": int(r["fraud"]), "fraud_rate": float(r["fraud"]/r["applications"])})
    for field in CAT_FIELDS:
        if field in df.columns and field != TARGET:
            vals = group_summary(df, field, True)
            summary["features"][field] = {"kind":"categorical", "groups": vals}
            eligible = [x for x in vals if x["applications"] >= MIN_GROUP]
            summary["segment_rankings"][field] = sorted(eligible, key=lambda x:x["fraud_rate"], reverse=True)[:10]
    for field in NUM_FIELDS:
        if field in df.columns and field != TARGET:
            vals = group_summary(df, field, False)
            summary["features"][field] = {"kind":"numeric", "groups": vals}
    for field in SENTINELS:
        if field in df.columns:
            s = pd.to_numeric(df[field], errors="coerce")
            summary["data_quality"].append({
                "field": field,
                "negative_sentinel_count": int((s < 0).sum()),
                "negative_sentinel_rate": float((s < 0).mean()),
                "blank_or_non_numeric_count": int(s.isna().sum()),
                "blank_or_non_numeric_rate": float(s.isna().mean())
            })
    # Numeric correlations are descriptive and explicitly exclude target-derived or outcome-like fields.
    corr_fields = [f for f in NUM_FIELDS if f in df.columns]
    for field in corr_fields:
        x = pd.to_numeric(df[field], errors="coerce")
        valid = x.notna() & df[TARGET].notna()
        if valid.sum() > 2 and x[valid].nunique() > 1:
            corr = x[valid].corr(df.loc[valid, TARGET], method="spearman")
            if pd.notna(corr):
                summary["correlations"].append({"feature":field,"spearman_correlation_with_fraud_label":float(corr),
                    "observations":int(valid.sum())})
    summary["correlations"].sort(key=lambda x: abs(x["spearman_correlation_with_fraud_label"]), reverse=True)
    # Keep the most relevant fields only in the correlation overview.
    summary["correlations"] = summary["correlations"][:12]
    output = Path(args.output)
    output.write_text(json.dumps(summary, indent=2, default=json_safe), encoding="utf-8")
    print(f"Saved aggregated summary to {output} ({output.stat().st_size:,} bytes)")
    print(f"Analysed {total:,} applications; fraud rate {fraud/total:.3%}.")
    print("No row-level application data was exported.")

if __name__ == "__main__":
    main()
