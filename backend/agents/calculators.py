# backend/agents/calculators.py
import pandas as pd


def calculate_savings_opportunities(df: pd.DataFrame, patterns: dict) -> list:
    opps = []
    if patterns["total_spent"] == 0:
        return opps

    food    = df[(df["category"] == "food") & (df["is_credit"] == False)]
    impulse = food[food["amount"] > 300]
    if not impulse.empty:
        potential = impulse["amount"].sum() - (len(impulse) * 300)
        if potential > 0:
            opps.append({
                "title":  "Reduce large food orders",
                "detail": f"{len(impulse)} orders above ₹300 detected",
                "saving": round(potential, 2),
                "tip":    "Set a ₹300 cap per food order"
            })

    if patterns["subscription_total"] > 500 and patterns["subscription_detail"]:
        lowest = min(patterns["subscription_detail"].values())
        opps.append({
            "title":  "Cancel one unused subscription",
            "detail": f"You pay ₹{patterns['subscription_total']:,.0f}/month on subscriptions",
            "saving": round(lowest, 2),
            "tip":    "Audit which services you used this month"
        })

    dates = df["date"].dropna()
    if not dates.empty:
        full_range     = pd.date_range(dates.min(), dates.max(), freq="D")
        n_weekend_days = (full_range.weekday >= 5).sum()
        n_weekday_days = (full_range.weekday < 5).sum()
    else:
        n_weekend_days = n_weekday_days = 0

    if n_weekday_days > 0 and n_weekend_days > 0:
        weekday_total   = patterns["total_spent"] - patterns["weekend_spend"]
        weekday_avg_day = weekday_total / n_weekday_days
        weekend_avg_day = patterns["weekend_spend"] / n_weekend_days
        if weekend_avg_day > weekday_avg_day * 1.5 and weekday_avg_day > 0:
            excess = patterns["weekend_spend"] - (weekday_avg_day * n_weekend_days)
            if excess > 0:
                opps.append({
                    "title":  "Control weekend spending",
                    "detail": f"Weekend spend ₹{patterns['weekend_spend']:,.0f} — higher than weekday average",
                    "saving": round(excess * 0.5, 2),
                    "tip":    "Plan weekend activities with a fixed budget"
                })

    return opps


def calculate_health_score(df: pd.DataFrame, patterns: dict) -> dict:
    if patterns["total_spent"] == 0 or patterns["transaction_count"] == 0:
        return {
            "score": 0, "label": "Insufficient Data",
            "breakdown": [{"label": "Not enough transaction data to score",
                           "score": 0, "max": 100, "good": None}]
        }

    opps = calculate_savings_opportunities(df, patterns)

    # ✅ Use is_credit column — catches all UPI deposits, not just
    #    rows whose description contains "credit/salary/stipend"
    income_rows  = df[df["is_credit"] == True]
    total_income = income_rows["amount"].sum()

    # ── Component 1: Savings rate (0–30 pts) ──────────────────────────
    if total_income > 0:
        rate = (total_income - patterns["total_spent"]) / total_income
        s1   = max(0, min(30, int(rate * 100)))
        b1   = {
            "label": f"Savings rate: {rate*100:.1f}%"
                     + (" (overspent this period)" if rate < 0 else ""),
            "score": s1, "max": 30, "good": rate >= 0.2
        }
    else:
        s1 = 15
        b1 = {"label": "Savings rate: income not detected", "score": 15, "max": 30, "good": None}

    # ── Component 2: Subscription load (0–20 pts) ─────────────────────
    sub_ratio = (patterns["subscription_total"] / total_income) if total_income > 0 else 0.05
    s2 = max(0, min(20, 20 - int(sub_ratio * 200)))
    b2 = {"label": f"Subscriptions: ₹{patterns['subscription_total']:,.0f}/month",
          "score": s2, "max": 20, "good": s2 >= 15}

    # ── Component 3: Weekend spending ratio (0–20 pts) ─────────────────
    w_ratio = patterns["weekend_spend"] / patterns["total_spent"] if patterns["total_spent"] else 0
    s3 = max(0, min(20, 20 - int(w_ratio * 100)))
    b3 = {"label": f"Weekend spending: {w_ratio*100:.0f}% of total",
          "score": s3, "max": 20, "good": w_ratio < 0.35}

    # ── Component 4: Category concentration (0–15 pts) ─────────────────
    top_pct = (list(patterns["by_category"].values())[0] / patterns["total_spent"]
               if patterns["by_category"] and patterns["total_spent"] else 0)
    s4 = max(0, min(15, 15 - int(top_pct * 30)))
    b4 = {"label": f"Top category: {top_pct*100:.0f}% of spend",
          "score": s4, "max": 15, "good": top_pct < 0.5}

    # ── Component 5: Missed savings opportunities (0–15 pts) ───────────
    s5 = max(0, min(15, 15 - len(opps) * 4))
    b5 = {"label": f"Savings opportunities missed: {len(opps)}",
          "score": s5, "max": 15, "good": len(opps) == 0}

    final = s1 + s2 + s3 + s4 + s5
    label = ("Excellent" if final >= 80 else "Good" if final >= 65
             else "Moderate" if final >= 45 else "Needs Work")

    return {"score": final, "label": label, "breakdown": [b1, b2, b3, b4, b5]}