# backend/agents/pattern_analysis.py
import pandas as pd

def analyze_patterns(df: pd.DataFrame) -> dict:
    # Exclude income rows from spend analysis. Previously this only checked
    # the description text — now that parse_statement() can assign
    # category="income" directly from the bank's own Category column,
    # we exclude on BOTH signals so an income row can never leak into
    # the spending breakdown (e.g. showing "Income: ₹45,000" as a category
    # in the Spending by Category chart).
    is_income = (
        df["description"].str.lower().str.contains("credit|salary|stipend", na=False)
        | (df["category"] == "income")
    )
    debits = df[~is_income]

    if debits.empty:
        return {
            "total_spent": 0, "by_category": {}, "weekend_spend": 0,
            "subscription_total": 0, "subscription_detail": {},
            "monthly_trend": {}, "top_category": "other",
            "transaction_count": 0,
        }

    total   = debits["amount"].sum()
    by_cat  = debits.groupby("category")["amount"].sum().sort_values(ascending=False)
    weekend = debits[debits["weekday"].isin(["Saturday", "Sunday"])]["amount"].sum()
    subs    = debits[debits["category"] == "subscriptions"]
    monthly = debits.groupby("month")["amount"].sum()
    sub_detail = (subs.groupby("description")["amount"]
                  .sum().sort_values(ascending=False).head(10).to_dict())

    return {
        "total_spent":         round(total, 2),
        "by_category":         {k: round(v, 2) for k, v in by_cat.items()},
        "weekend_spend":       round(weekend, 2),
        "subscription_total":  round(subs["amount"].sum(), 2),
        "subscription_detail": sub_detail,
        "monthly_trend":       {k: round(v, 2) for k, v in monthly.items()},
        "top_category":        by_cat.index[0] if not by_cat.empty else "other",
        "transaction_count":   len(debits),
    }