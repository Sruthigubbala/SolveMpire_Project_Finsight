# backend/agents/pattern_analysis.py
import pandas as pd

def analyze_patterns(df: pd.DataFrame) -> dict:
    debits  = df[~df["description"].str.lower().str.contains(
                  "credit|salary|stipend", na=False)]
    total   = debits["amount"].sum()
    by_cat  = debits.groupby("category")["amount"].sum().sort_values(ascending=False)
    weekend = debits[debits["weekday"].isin(["Saturday","Sunday"])]["amount"].sum()
    subs    = debits[debits["category"] == "subscriptions"]
    monthly = debits.groupby("month")["amount"].sum()
    sub_detail = (subs.groupby("description")["amount"]
                  .sum().sort_values(ascending=False).head(10).to_dict())
    return {
        "total_spent":         round(total, 2),
        "by_category":         {k: round(v,2) for k,v in by_cat.items()},
        "weekend_spend":       round(weekend, 2),
        "subscription_total":  round(subs["amount"].sum(), 2),
        "subscription_detail": sub_detail,
        "monthly_trend":       {k: round(v,2) for k,v in monthly.items()},
        "top_category":        by_cat.index[0] if not by_cat.empty else "other",
        "transaction_count":   len(debits),
    }