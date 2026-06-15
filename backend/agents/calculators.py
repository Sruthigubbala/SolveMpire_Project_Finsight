# backend/agents/calculators.py
import pandas as pd

def calculate_savings_opportunities(df: pd.DataFrame, patterns: dict) -> list:
    opps = []

    food    = df[df["category"] == "food"]
    impulse = food[food["amount"] > 300]
    if not impulse.empty:
        potential = impulse["amount"].sum() - (len(impulse) * 300)
        opps.append({
            "title":  "Reduce large food orders",
            "detail": f"{len(impulse)} orders above ₹300 detected",
            "saving": round(potential, 2),
            "tip":    "Set a ₹300 cap per food order"
        })

    if patterns["subscription_total"] > 500:
        lowest = min(patterns["subscription_detail"].values()) \
                 if patterns["subscription_detail"] else 0
        opps.append({
            "title":  "Cancel one unused subscription",
            "detail": f"You pay ₹{patterns['subscription_total']:,.0f}/month on subscriptions",
            "saving": round(lowest, 2),
            "tip":    "Audit which services you used this month"
        })

    weekday_avg    = (patterns["total_spent"] - patterns["weekend_spend"]) / 20
    weekend_per_day = patterns["weekend_spend"] / 8
    if weekend_per_day > weekday_avg * 1.5:
        excess = patterns["weekend_spend"] - (weekday_avg * 8)
        opps.append({
            "title":  "Control weekend spending",
            "detail": f"Weekend spend ₹{patterns['weekend_spend']:,.0f} — higher than weekday average",
            "saving": round(excess * 0.5, 2),
            "tip":    "Plan weekend activities with a fixed budget"
        })

    return opps


def calculate_health_score(df: pd.DataFrame, patterns: dict) -> dict:
    opps         = calculate_savings_opportunities(df, patterns)
    income_rows  = df[df["description"].str.lower().str.contains(
                      "credit|salary|stipend", na=False)]
    total_income = income_rows["amount"].sum()

    if total_income > 0:
        rate = (total_income - patterns["total_spent"]) / total_income
        s1   = min(30, int(rate * 100))
        b1   = {"label": f"Savings rate: {rate*100:.1f}%", "score": s1, "max": 30, "good": rate >= 0.2}
    else:
        s1 = 15
        b1 = {"label": "Savings rate: income not detected", "score": 15, "max": 30, "good": None}

    sub_ratio = (patterns["subscription_total"] / total_income) if total_income > 0 else 0.05
    s2 = max(0, 20 - int(sub_ratio * 200))
    b2 = {"label": f"Subscriptions: ₹{patterns['subscription_total']:,.0f}/month",
          "score": s2, "max": 20, "good": s2 >= 15}

    w_ratio = patterns["weekend_spend"] / patterns["total_spent"] if patterns["total_spent"] else 0
    s3 = max(0, 20 - int(w_ratio * 100))
    b3 = {"label": f"Weekend spending: {w_ratio*100:.0f}% of total",
          "score": s3, "max": 20, "good": w_ratio < 0.35}

    top_pct = (list(patterns["by_category"].values())[0] / patterns["total_spent"]
               if patterns["total_spent"] else 0)
    s4 = max(0, 15 - int(top_pct * 30))
    b4 = {"label": f"Top category: {top_pct*100:.0f}% of spend",
          "score": s4, "max": 15, "good": top_pct < 0.5}

    s5 = max(0, 15 - len(opps) * 4)
    b5 = {"label": f"Savings opportunities missed: {len(opps)}",
          "score": s5, "max": 15, "good": len(opps) == 0}

    final = s1 + s2 + s3 + s4 + s5
    label = ("Excellent" if final >= 80 else "Good" if final >= 65
             else "Moderate" if final >= 45 else "Needs Work")

    return {"score": final, "label": label, "breakdown": [b1, b2, b3, b4, b5]}