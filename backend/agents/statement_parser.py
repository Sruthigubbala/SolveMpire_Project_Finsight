"""
bank_statement_parser.py
========================
Parse Indian bank statements (PDF or CSV) into a clean, categorized DataFrame.

Supported banks
---------------
PDF : SBI, Union Bank of India, IPPB, Canara Bank, generic fallback
CSV : Canara Bank ePassbook, generic (SBI / HDFC / Axis / ICICI exports)

How detection works
-------------------
1. Score each bank parser using text headers + table headers + column patterns
2. Try parsers in confidence order (highest score first)
3. If the top parser fails → automatically try the next one (cascading fallback)
4. If ALL scored parsers fail → try every parser in sequence (try-all mode)
5. Generic PDF parser is always the last resort

Public API
----------
parse_statement(path) → pd.DataFrame
    Columns: date, description, amount, is_credit, category, weekday, month
"""

from __future__ import annotations

import os
import re
import traceback
from datetime import datetime

import pandas as pd
import pdfplumber


# ──────────────────────────────────────────────────────────────────────────────
# Category keyword map
# ──────────────────────────────────────────────────────────────────────────────

CATEGORIES: dict[str, list[str]] = {
    "electricity_bill": [
        "apepdcl", "apspdcl", "apeastern", "apnpdcl", "ap eastern",
        "tsspdcl", "tsnpdcl",
        "bescom", "hescom", "gescom", "mescom", "cesc",
        "msedcl", "mahavitaran",
        "tangedco", "tneb",
        "electricity", "bijli", "power bill", "eb bill", "discom",
        "torrent power", "adani electricity", "bses", "wbsedcl",
    ],
    "water_bill": [
        "water board", "water supply", "municipal water", "jal board",
        "hmws", "ghmc water", "bwssb", "cmdwss",
    ],
    "gas_bill": [
        "igl", "mgl", "agu", "piped gas", "gas bill", "png bill",
        "indane", "hp gas", "bharat gas", "lpg", "gas cylinder",
    ],
    "mobile_recharge": [
        "airtel", "vi ", "vodafone", "idea", "bsnl", "mtnl",
        "jio recharge", "reliance jio", "recharge",
    ],
    "broadband": [
        "airfiber", "air fiber", "orbgen", "jiofiber", "act fibernet",
        "broadband", "fiber", "hathway", "tataplay fiber",
    ],
    "insurance": [
        "pmsby", "pmjjby", "sbiya", "sbijb", "sbisb",
        "lic ", "star health", "bajaj allianz",
        "new india assurance", "hdfc ergo", "icici lombard",
        "insurance", "insure", "policy bazaar", "pairenewal",
    ],
    "food": [
        "zomato", "swiggy", "restaurant", "cafe", "dominos", "kfc",
        "hotel", "food", "kitchen", "dhaba", "biryani", "mess", "babai",
        "mcdonald", "burger king", "pizza hut", "subway", "haldiram",
        "barbeque", "bakery", "canteen", "hungry",
    ],
    "transport": [
        "apsrtc", "tsrtc", "ksrtc", "msrtc", "irctc", "uber", "ola",
        "petrol", "fuel", "metro", "rapido", "bus pass", "fastag",
        "roppen", "auto", "transpo", "bpcl", "hpcl", "iocl", "indian oil",
        "namma metro", "dmrc", "railsb", "indian r", "ekart",
    ],
    "subscriptions": [
        "netflix", "spotify", "amazon prime", "hotstar", "youtube premium",
        "zee5", "sonyliv", "voot", "mxplayer", "storytv", "story tv",
        "apple music", "google one", "adobe", "microsoft 365",
        "sharechat", "qubitech",
    ],
    "shopping": [
        "amazon", "flipkart", "myntra", "meesho", "ajio", "nykaa",
        "shop", "store", "mart", "reliance digital",
        "croma", "decathlon", "d-mart", "big bazaar", "jiomart",
        "zudio", "m s brands",
    ],
    "medical": [
        "pharmacy", "hospital", "clinic", "medplus", "apollo", "netmeds",
        "medical", "health", "care", "lab", "diagnostic",
        "sai heal", "sai phar", "1mg", "practo", "dr ", "thyrocare",
        "medisett",
    ],
    "savings": [
        "fd ", " fd", "sip ", "ppf", "investment", "mutual fund",
        "rd account", "nsc", "elss", "zerodha", "groww", "upstox",
        "coin by zerodha", "nps",
    ],
    "education": [
        "udemy", "coursera", "college", "fees", "books", "school",
        "tuition", "aditya e", "byju", "unacademy", "vedantu",
        "exam fee", "hall ticket", "iit madras",
    ],
    "rent": [
        "rent", "house", "flat", "pg ", "maintenance", "society fee",
        "housing society",
    ],
    "transfer": ["neft", "imps", "rtgs", "transfer to", "transfer"],
    "government": [
        "gst", "income tax", "property tax", "challan", "traffic fine",
        "aadhaar", "passport", "mvd", "rto", "ghmc", "cbdc",
    ],
    "groceries": [
        "blinkit", "bigbasket", "dunzo", "zepto", "grofers",
        "instamart", "supermarket", "grocery", "kirana",
    ],
    "credit_card_payment": [
        "sbi card", "sbicard", "hdfc credit", "icici credit", "axis credit",
        "credit card", "card payment", "card bill", "creditcard",
        "amex", "american express",
    ],
    "bank_fees": [
        "int.pd", "interest paid", "atm usage", "sms charge", "sms alert",
        "annual fee", "account maintenance", "service charge",
        "minimum balance", "cheque book", "dd charge", "neft charge",
        "imps charge", "processing fee", "late payment", "penalty",
        "bank charge", "ecs return", "nach return", "bounce charge",
        "debit atmcard amc", "annual maintenance charges", "sms charges",
    ],
    "atm_withdrawal": [
        "atw/", "atm/", "cash withdrawal", "cash at ", "atm cash",
        "atm-", "atm wdl", "atm wdl ",
    ],
    "cash_deposit": [
        "csh dep", "cash dep", "cdm",
    ],
    "interest_income": [
        "interest credit", "int cr", "interest cr", "int.pd",
    ],
    "salary": [
        "salary", "cemtex dep",
    ],
    "lpg_subsidy": [
        "lpg subsidy", "iocl lpg", "apbcr-dbl",
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
# Groq AI fallback categorizer
# ──────────────────────────────────────────────────────────────────────────────

_GROQ_CATEGORIES = list(CATEGORIES.keys()) + [
    "received", "personal_transfer", "other"
]
_groq_cache: dict[str, str] = {}


def _groq_categorize(description: str, is_credit: bool = False) -> str:
    key = description.lower()[:80]
    if key in _groq_cache:
        return _groq_cache[key]
    try:
        import requests
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "other"
        cat_list = ", ".join(_GROQ_CATEGORIES)
        prompt = (
            f"Classify this Indian bank transaction description into exactly ONE "
            f"category from this list: [{cat_list}].\n\n"
            f"Transaction: \"{description}\"\n"
            f"Direction: {'CREDIT (money received)' if is_credit else 'DEBIT (money spent)'}\n\n"
            f"Rules (apply in order):\n"
            f"- Int.Pd, Interest Paid, interest charged → bank_fees\n"
            f"- ATM Usage Charges, ATM Fee, SMS Charges, SMS Alert → bank_fees\n"
            f"- ATW/, ATM/, Cash Withdrawal → atm_withdrawal\n"
            f"- SBI CARD, SBICARD, HDFC Credit Card → credit_card_payment\n"
            f"- SBIYA / SBIJB / SBISB + PAI/RENEWAL → insurance\n"
            f"- PhonePe/UPI to a person with no recognizable merchant → personal_transfer\n"
            f"- INTEREST CREDIT → interest_income\n"
            f"- CEMTEX DEP, SALARY → salary\n"
            f"- CSH DEP, CDM deposit → cash_deposit\n"
            f"- APBCR-DBL, LPG SUBSIDY → lpg_subsidy\n"
            f"- If CREDIT and no match → received\n"
            f"- If DEBIT and truly unrecognizable → personal_transfer\n\n"
            f"Reply with ONLY the category name, nothing else."
        )
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 10,
                "temperature": 0,
            },
            timeout=5,
        )
        resp_json = resp.json()
        if "error" in resp_json:
            err_msg = resp_json["error"].get("message", str(resp_json["error"]))
            print(f"⚠️  Groq API error for '{description[:40]}': {err_msg}")
            return "other"
        if "choices" not in resp_json or not resp_json["choices"]:
            print(f"⚠️  Groq unexpected response for '{description[:40]}': {resp_json}")
            return "other"
        result = resp_json["choices"][0]["message"]["content"].strip().lower()
        matched = next(
            (c for c in _GROQ_CATEGORIES if c == result), "other"
        )
        _groq_cache[key] = matched
        return matched
    except Exception as exc:
        print(f"⚠️  Groq failed for '{description[:40]}': {exc}")
        return "other"


def _keyword_scan(
    d: str, skip: tuple[str, ...] = ("transfer",)
) -> str | None:
    """Return the first matching category or None."""
    for cat, kws in CATEGORIES.items():
        if cat in skip:
            continue
        if any(k in d for k in kws):
            return cat
    return None


def categorize(desc: str, is_credit: bool) -> str:
    """Classify a transaction description into a spending category."""
    d = desc.lower()

    # ── Priority rules ──────────────────────────────────────────────────────

    if any(k in d for k in CATEGORIES["lpg_subsidy"]):
        return "lpg_subsidy"

    if any(k in d for k in ["interest credit", "int cr", "interest cr"]):
        return "interest_income"

    if "int.pd" in d or any(k in d for k in CATEGORIES["bank_fees"]):
        return "bank_fees"

    if any(k in d for k in CATEGORIES["salary"]):
        return "salary"

    if any(k in d for k in CATEGORIES["cash_deposit"]):
        return "cash_deposit"

    if any(k in d for k in CATEGORIES["atm_withdrawal"]):
        return "atm_withdrawal"
    if re.match(r"^\d{10,}/\d+", desc.strip()):
        return "atm_withdrawal"

    if re.search(r"\bsbi[yjs]b?\d+", d):
        return "insurance"

    if any(k in d for k in CATEGORIES["credit_card_payment"]):
        return "credit_card_payment"

    if any(k in d for k in CATEGORIES["government"]):
        return "government"

    # ── UPI direction routing ───────────────────────────────────────────────

    if "upi/cr" in d or "dep tfr" in d:
        hit = _keyword_scan(d)
        return hit if hit else "received"

    if "upi/dr" in d or "wdl tfr" in d:
        hit = _keyword_scan(d)
        if hit:
            return hit
        groq = _groq_categorize(desc, is_credit=False)
        return groq if groq != "other" else "personal_transfer"

    if "upiab/" in d:
        hit = _keyword_scan(d)
        return hit if hit else "received"

    if "upiar/" in d:
        hit = _keyword_scan(d)
        if hit:
            return hit
        groq = _groq_categorize(desc, is_credit=False)
        return groq if groq != "other" else "personal_transfer"

    if "~cr~" in d or "~ft~" in d:
        hit = _keyword_scan(d)
        return hit if hit else "received"

    if "~rvl~" in d:
        return "received"

    if "~dr~" in d:
        hit = _keyword_scan(d)
        if hit:
            return hit
        groq = _groq_categorize(desc, is_credit=False)
        return groq if groq != "other" else "personal_transfer"

    if "impsab/" in d or "imps" in d:
        return "transfer"

    hit = _keyword_scan(d, skip=())
    if hit:
        return hit

    groq = _groq_categorize(desc, is_credit=is_credit)
    if groq == "other" and not is_credit:
        return "personal_transfer"
    return groq


# ──────────────────────────────────────────────────────────────────────────────
# Date helpers
# ──────────────────────────────────────────────────────────────────────────────

_DATE_RE = re.compile(
    r"^\d{1,2}[/-]\d{2}[/-]\d{2,4}$"
    r"|^\d{1,2}-[A-Za-z]{3}-\d{2,4}$"
    r"|^\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4}$"
)
_DATE_FORMATS = [
    "%d-%m-%Y", "%d/%m/%Y", "%d-%b-%Y", "%d-%b-%y",
    "%d %b %Y", "%d %b %y", "%d-%m-%y", "%d/%m/%y", "%Y-%m-%d",
]


def _is_date(val: str) -> bool:
    return bool(_DATE_RE.match(val.strip()))


def _parse_dates(series: pd.Series) -> pd.Series:
    parsed = pd.Series([pd.NaT] * len(series), index=series.index)
    remaining = series.copy()
    for fmt in _DATE_FORMATS:
        mask = parsed.isna() & remaining.notna()
        if not mask.any():
            break
        attempt = pd.to_datetime(
            remaining[mask], format=fmt, errors="coerce"
        )
        parsed[mask] = attempt
    return parsed


def _clean_amount(val: str) -> str:
    return re.sub(r"[^\d.]", "", val or "").strip()


# ──────────────────────────────────────────────────────────────────────────────
# PDF text + table extractor (with pdfplumber; fallback-safe)
# ──────────────────────────────────────────────────────────────────────────────

def _extract_pdf_signals(path: str) -> tuple[str, list | None]:
    """
    Extract the first page's text (uppercase) and first table.
    Returns ("", None) if extraction fails entirely.
    """
    try:
        with pdfplumber.open(path) as pdf:
            text        = pdf.pages[0].extract_text() or ""
            first_table = pdf.pages[0].extract_table()
        return text.upper(), first_table
    except Exception as exc:
        print(f"⚠️  Could not read PDF signals: {exc}")
        return "", None


def _table_header_str(table: list | None) -> str:
    """Return the first row of a table joined as an uppercase string."""
    if not table:
        return ""
    return " ".join(str(c or "") for c in (table[0] or [])).upper()


# ──────────────────────────────────────────────────────────────────────────────
# Bank confidence scorer
# ──────────────────────────────────────────────────────────────────────────────

def _score_banks(header: str, tbl_header: str) -> dict[str, int]:
    scores: dict[str, int] = {
        "sbi": 0,
        "ippb": 0,
        "union": 0,
        "canara": 0,
        "generic": 1,
    }

    if "STATE BANK OF INDIA" in header:
        scores["sbi"] += 10
    if "SBIN0" in header or re.search(r"\bSBIN\d", header):
        scores["sbi"] += 8
    if "SBIYA" in header or "SBIJB" in header or "SBISB" in header:
        scores["sbi"] += 6
    if "VALUE DATE" in tbl_header and "DEBIT" in tbl_header:
        scores["sbi"] += 5
    if "BRANCH NAME" in header or "ACCOUNT NUMBER" in header:
        scores["sbi"] += 2

    if "INDIA POST PAYMENTS BANK" in header:
        scores["ippb"] += 10
    if "INDIA POST" in header:
        scores["ippb"] += 8
    if re.search(r"\bIPPB\b", header) or re.search(r"\bIPOS\b", header):
        scores["ippb"] += 8
    if "WITHDRWAL" in tbl_header:
        scores["ippb"] += 10
    if "TRAN ID" in tbl_header and "TRANSACTION PARTICULARS" in tbl_header:
        scores["ippb"] += 8
    if "~CR~" in header or "~DR~" in header or "~FT~" in header:
        scores["ippb"] += 6
    if "IPOS" in header:
        scores["ippb"] += 6

    if "UNION BANK OF INDIA" in header:
        scores["union"] += 10
    if re.search(r"\bUBIN\d{7}\b", header):
        scores["union"] += 8
    if "PARTICULARS" in tbl_header and "WITHDRAWAL" in tbl_header:
        scores["union"] += 6
    if "UBIN" in header and scores["union"] < 5:
        scores["union"] += 2

    if "CANARA" in header:
        scores["canara"] += 10
    if re.search(r"\bCNRB\d", header):
        scores["canara"] += 8
    if "CANARABANK" in header or "CANARA BANK" in header:
        scores["canara"] += 5
    if "UPI/CR" in header or "UPI/DR" in header:
        scores["canara"] += 3

    return scores


def _ranked_parsers(scores: dict[str, int]) -> list[str]:
    """Return bank names sorted by score descending; generic always last."""
    ranked = sorted(
        [(k, v) for k, v in scores.items() if k != "generic"],
        key=lambda x: x[1],
        reverse=True,
    )
    names = [k for k, v in ranked if v > 0]
    names.append("generic")
    return names


# ──────────────────────────────────────────────────────────────────────────────
# SBI PDF parser
# ──────────────────────────────────────────────────────────────────────────────

def _extract_sbi_metadata(pdf_path: str) -> dict[str, str]:
    meta: dict[str, str] = {
        "account_number": "", "ifsc": "", "branch": "", "holder_name": "",
        "account_type": "", "opening_balance": "", "closing_balance": "",
        "statement_from": "", "statement_to": "",
    }
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text() or ""

    for line in text.splitlines():
        lc = line.strip()
        if "Account Number" in lc:
            m = re.search(r":\s*(\d{10,})", lc)
            if m:
                meta["account_number"] = m.group(1)
        if "IFSC" in lc and "Code" in lc:
            m = re.search(r":\s*(SBIN\w+)", lc)
            if m:
                meta["ifsc"] = m.group(1)
        if "Branch Name" in lc:
            m = re.search(r":\s*(.+)", lc)
            if m:
                meta["branch"] = m.group(1).strip()
        if "Product" in lc and "Savings" in lc:
            meta["account_type"] = "Savings Account"
        if "Welcome:" in lc or "Mr." in lc or "Mrs." in lc or "Ms." in lc:
            nm = re.search(r"(?:Welcome:|Mr\.|Mrs\.|Ms\.)\s*([A-Za-z\s]+)", lc)
            if nm and not meta["holder_name"]:
                meta["holder_name"] = nm.group(1).strip()

    m = re.search(
        r"Statement From\s*:\s*(\d{2}-\d{2}-\d{4})\s+to\s+(\d{2}-\d{2}-\d{4})", text,
    )
    if m:
        meta["statement_from"] = m.group(1)
        meta["statement_to"] = m.group(2)

    m = re.search(r"Brought Forward.*?([\d,]+\.?\d*)\s*CR", text, re.DOTALL)
    if m:
        meta["opening_balance"] = m.group(1).replace(",", "")

    return meta


def parse_sbi_pdf(path: str) -> pd.DataFrame:
    rows: list[dict] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 7:
                        continue
                    date_str = str(row[0] or "").strip()
                    details  = str(row[2] or "").replace("\n", " ").strip()
                    debit    = str(row[4] or "").strip()
                    credit   = str(row[5] or "").strip()

                    if not re.match(r"\d{2}/\d{2}/\d{4}", date_str):
                        continue
                    if details.lower() in ("details", "particulars", "narration"):
                        continue

                    debit_val  = _clean_amount(debit)
                    credit_val = _clean_amount(credit)

                    if credit_val and float(credit_val) > 0:
                        rows.append({
                            "date": date_str, "description": details,
                            "amount": credit_val, "is_credit": True,
                        })
                    elif debit_val and float(debit_val) > 0:
                        rows.append({
                            "date": date_str, "description": details,
                            "amount": debit_val, "is_credit": False,
                        })

    if not rows:
        raise ValueError("No transactions found in SBI PDF.")

    df = pd.DataFrame(rows)
    df["date"] = df["date"].str.replace("/", "-")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Union Bank PDF parser
# ──────────────────────────────────────────────────────────────────────────────

def parse_union_bank_pdf(path: str) -> pd.DataFrame:
    rows: list[dict] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            header_idx = None
            for i, row in enumerate(table):
                if row is None:
                    continue
                joined = " ".join(str(c or "").upper() for c in row)
                if (
                    "DATE" in joined
                    and "PARTICULARS" in joined
                    and "WITHDRAWAL" in joined
                ):
                    header_idx = i
                    break

            if header_idx is None:
                continue

            for row in table[header_idx + 1:]:
                if row is None or len(row) < 6:
                    continue
                date_str   = str(row[1] or "").strip()
                desc       = str(row[2] or "").replace("\n", " ").strip()
                withdrawal = str(row[4] or "").strip()
                deposit    = str(row[5] or "").strip()

                if not _is_date(date_str):
                    continue
                if "opening balance" in desc.lower():
                    continue

                w_val = _clean_amount(withdrawal)
                d_val = _clean_amount(deposit)

                if w_val and float(w_val) > 0:
                    rows.append({
                        "date": date_str, "description": desc,
                        "amount": w_val, "is_credit": False,
                    })
                elif d_val and float(d_val) > 0:
                    rows.append({
                        "date": date_str, "description": desc,
                        "amount": d_val, "is_credit": True,
                    })

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("No transactions found in Union Bank PDF.")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# IPPB PDF parser — enhanced with multi-layout support
# ──────────────────────────────────────────────────────────────────────────────

def parse_ippb_pdf(path: str) -> pd.DataFrame:
    rows: list[dict] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            header_idx = None
            for i, row in enumerate(table):
                if row is None:
                    continue
                joined = " ".join(str(c or "").upper() for c in row)
                if "DATE" in joined and (
                    "WITHDRWAL" in joined or "WITHDRAWAL" in joined
                ) and "DEPOSIT" in joined:
                    header_idx = i
                    break

            if header_idx is None:
                continue

            for row in table[header_idx + 1:]:
                if row is None or len(row) < 5:
                    continue

                date_str   = str(row[0] or "").strip()
                desc       = str(row[2] or "").replace("\n", " ").strip()
                withdrawal = str(row[3] or "").strip()
                deposit    = str(row[4] or "").strip()

                if not _is_date(date_str):
                    continue
                if "opening balance" in desc.lower():
                    continue

                w_val = _clean_amount(withdrawal)
                d_val = _clean_amount(deposit)
                is_reversal = "~rvl~" in desc.lower()

                if is_reversal:
                    amount = w_val or d_val
                    if amount and float(amount) > 0:
                        rows.append({
                            "date": date_str, "description": desc,
                            "amount": amount, "is_credit": True,
                        })
                elif w_val and float(w_val) > 0:
                    rows.append({
                        "date": date_str, "description": desc,
                        "amount": w_val, "is_credit": False,
                    })
                elif d_val and float(d_val) > 0:
                    rows.append({
                        "date": date_str, "description": desc,
                        "amount": d_val, "is_credit": True,
                    })

    if not rows:
        DATE_AMOUNT_RE = re.compile(
            r"(\d{2}-\d{2}-\d{4})"
            r"(.+?)"
            r"([\d,]+\.\d{2})"
            r"(?:\s+([\d,]+\.\d{2}))?"
        )
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for line in text.splitlines():
                    m = DATE_AMOUNT_RE.match(line.strip())
                    if not m:
                        continue
                    date_str = m.group(1)
                    desc     = m.group(2).strip()
                    amt      = float(m.group(3).replace(",", ""))
                    dl = desc.lower()
                    is_credit = (
                        "~cr~" in dl
                        or "~ft~" in dl
                        or "~rvl~" in dl
                        or "deposit" in dl
                    )
                    rows.append({
                        "date": date_str, "description": desc,
                        "amount": str(amt), "is_credit": is_credit,
                    })

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("No transactions found in IPPB PDF.")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Canara Bank ePassbook PDF parser
# ──────────────────────────────────────────────────────────────────────────────

def parse_canara_bank_pdf(path: str) -> pd.DataFrame:
    DATE_LINE_RE = re.compile(
        r"(\d{2}-\d{2}-\d{4})"
        r"(.*?)"
        r"([\d,]+\.\d{2})"
        r"\s+([\d,]+\.\d{2})\s*$"
    )
    SKIP_RE = re.compile(
        r"^page\s+\d+$|^date\s+particulars|^statement for a/c"
        r"|^customer id|^name\s+|^phone\s+|^address|^branch|^ifsc"
        r"|opening balance|closing balance|^disclaimer"
        r"|^unless the constituent|^beware of phishing|^imb users"
        r"|^are you a merchant|^computer output|end of statement"
        r"|^details of ombudsman|^the banking ombudsman|^10/3/8"
        r"|^e-mail:|^change in the address|^do not share"
        r"|www\.canarabank|code or could be|phishing"
        r"|^3/2 korimilli|^jagannaikpur|kakinada andhra"
        r"|jagannaickpur|andhra pradesh",
        re.IGNORECASE,
    )

    rows: list[dict] = []
    desc_lines: list[str] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in [ln.strip() for ln in text.split("\n")]:
                if not line or SKIP_RE.search(line):
                    continue
                m = DATE_LINE_RE.search(line)
                if m:
                    date_str = m.group(1)
                    inline   = m.group(2).strip()
                    amount   = float(m.group(3).replace(",", ""))

                    parts = desc_lines[:]
                    if inline:
                        parts.append(inline)
                    full_desc = " ".join(p for p in parts if p).strip()
                    desc_lines = []

                    du = full_desc.upper()
                    if "UPI/CR" in du or "NEFT/CR" in du:
                        is_credit = True
                    elif "UPI/DR" in du or "NEFT/DR" in du:
                        is_credit = False
                    else:
                        is_credit = False

                    rows.append({
                        "date": date_str, "description": full_desc,
                        "amount": amount, "is_credit": is_credit,
                    })
                elif line.lower().startswith("chq:"):
                    desc_lines = []
                else:
                    desc_lines.append(line)

    if not rows:
        raise ValueError("No transactions found in Canara Bank PDF.")
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Generic / fallback PDF parser  (tries both table and text modes)
# ──────────────────────────────────────────────────────────────────────────────

def _parse_generic_pdf(path: str) -> pd.DataFrame:
    rows: list[dict] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            header_idx = None
            for i, row in enumerate(table):
                if row is None:
                    continue
                joined = " ".join(str(c or "").upper() for c in row)
                if "DATE" in joined and (
                    "DEPOSIT" in joined or "CREDIT" in joined
                ):
                    header_idx = i
                    break

            if header_idx is None:
                continue

            header_row = [
                str(c or "").strip() for c in table[header_idx] if c is not None
            ]
            col_map: dict[str, int] = {}
            for idx, cell in enumerate(header_row):
                cu = cell.upper()
                if "DATE" in cu:
                    col_map.setdefault("date", idx)
                elif any(x in cu for x in ("WITHDRAW", "DEBIT", "DR")):
                    col_map.setdefault("debit", idx)
                elif any(x in cu for x in ("DEPOSIT", "CREDIT", "CR")):
                    col_map.setdefault("credit", idx)
                elif any(x in cu for x in ("PARTICULAR", "DESCRIPTION", "NARRATION")):
                    col_map.setdefault("desc", idx)

            col_map.setdefault("date", 0)
            col_map.setdefault("desc", 2)
            col_map.setdefault("debit", 3)
            col_map.setdefault("credit", 4)

            for row in table[header_idx + 1:]:
                if row is None:
                    continue
                crow = [str(c or "").strip() for c in row]
                while len(crow) < 6:
                    crow.append("")

                date_str = crow[col_map["date"]] if col_map["date"] < len(crow) else ""
                desc     = crow[col_map["desc"]] if col_map["desc"] < len(crow) else ""
                debit    = crow[col_map["debit"]] if col_map["debit"] < len(crow) else ""
                credit   = crow[col_map["credit"]] if col_map["credit"] < len(crow) else ""

                desc = desc.replace("\n", " ").strip()
                if not _is_date(date_str) or "opening balance" in desc.lower():
                    continue

                w_val = _clean_amount(debit)
                d_val = _clean_amount(credit)

                if w_val and float(w_val) > 0:
                    rows.append({
                        "date": date_str, "description": desc,
                        "amount": w_val, "is_credit": False,
                    })
                elif d_val and float(d_val) > 0:
                    rows.append({
                        "date": date_str, "description": desc,
                        "amount": d_val, "is_credit": True,
                    })

    if not rows:
        DATE_AMOUNT_RE = re.compile(
            r"(\d{2}[/-]\d{2}[/-]\d{4})"
            r"(.{5,80}?)"
            r"([\d,]+\.\d{2})"
            r"\s+([\d,]+\.\d{2})\s*$"
        )
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for line in text.splitlines():
                    m = DATE_AMOUNT_RE.match(line.strip())
                    if not m:
                        continue
                    amount_col = float(m.group(3).replace(",", ""))
                    desc       = m.group(2).strip()
                    du         = desc.upper()
                    is_credit  = (
                        "CR" in du.split()
                        or "/CR" in du
                        or "CREDIT" in du
                        or "DEPOSIT" in du
                    )
                    rows.append({
                        "date": m.group(1), "description": desc,
                        "amount": str(amount_col), "is_credit": is_credit,
                    })

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("Could not extract transactions from this PDF.")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Parser registry
# ──────────────────────────────────────────────────────────────────────────────

_PARSER_MAP: dict[str, callable] = {
    "sbi":     parse_sbi_pdf,
    "ippb":    parse_ippb_pdf,
    "union":   parse_union_bank_pdf,
    "canara":  parse_canara_bank_pdf,
    "generic": _parse_generic_pdf,
}


# ──────────────────────────────────────────────────────────────────────────────
# PDF auto-detect router with cascading fallback
# ──────────────────────────────────────────────────────────────────────────────

def parse_pdf_statement(path: str) -> pd.DataFrame:
    header, first_table = _extract_pdf_signals(path)
    tbl_header = _table_header_str(first_table)

    scores  = _score_banks(header, tbl_header)
    ordered = _ranked_parsers(scores)

    print(f"🏦 Bank detection scores: {scores}")
    print(f"   Trying parsers in order: {ordered}")

    errors: list[str] = []
    for bank in ordered:
        parser = _PARSER_MAP[bank]
        try:
            df = parser(path)
            if df is not None and not df.empty:
                print(f"✅ Successfully parsed with '{bank}' parser ({len(df)} rows)")
                return df
            else:
                errors.append(f"[{bank}] returned empty DataFrame")
        except Exception as exc:
            errors.append(f"[{bank}] {type(exc).__name__}: {exc}")
            print(f"⚠️  '{bank}' parser failed: {exc} — trying next…")

    raise ValueError(
        "All parsers failed. Details:\n" + "\n".join(errors)
    )


# ──────────────────────────────────────────────────────────────────────────────
# Canara Bank ePassbook CSV parser  ← FIXED
# ──────────────────────────────────────────────────────────────────────────────

def parse_canara_csv(path: str) -> pd.DataFrame:
    """
    Parse Canara Bank ePassbook CSV export.

    Layout detection
    ----------------
    The export uses two section layouts across pages:

    Layout 1  (cols):  c0=date, c3=narration, c7=deposit, c9=withdrawal, c10=balance
    Layout 2  (cols):  c0=date, c1=narration, c2=deposit, c3=withdrawal, c4=balance
      detected by header row: c0="Date", c1="Particulars"

    In BOTH layouts the narration is spread across multiple rows BEFORE the
    date row.  After the date row come post-date noise lines (hash/date stamp,
    time stamp, Chq: reference) that must be skipped.
    """
    df_raw = pd.read_csv(path, header=None, dtype=str)
    DATE_RE_CANARA = re.compile(r"^\d{2}-\d{2}-\d{4}$")

    # File-level meta rows (bank/customer header block at top of file)
    META_C0 = re.compile(
        r"^(customer|name|phone|address|statement|branch|ifsc|jagann|pradesh|3/2)",
        re.IGNORECASE,
    )

    def _get(row: list, i: int) -> str:
        v = str(row[i]).strip() if i < len(row) else ""
        return "" if v in ("nan", "NaN") else v

    def _num(row: list, i: int) -> float | None:
        v = _get(row, i)
        c = re.sub(r"[^\d.]", "", v)
        try:
            return float(c) if c else None
        except ValueError:
            return None

    def _is_noise(s: str) -> bool:
        """Return True if a narration token is post-date noise, not real narration."""
        if not s:
            return True
        # Chq: reference lines
        if re.match(r"^chq:", s, re.IGNORECASE):
            return True
        # Page markers
        if re.match(r"^page\s+\d+", s, re.IGNORECASE):
            return True
        # Column header words
        if re.match(
            r"^(date|particulars|deposits|withdrawals|balance|opening balance|closing balance)$",
            s, re.IGNORECASE,
        ):
            return True
        # Pure time stamp HH:MM:SS
        if re.match(r"^\d{2}:\d{2}:\d{2}$", s):
            return True
        # Hash/date continuation line: hex chars followed by /dd/mm/yyyy
        if re.match(r"^[0-9A-Fa-f]{6,}/\d{2}/\d{2}/\d{4}", s):
            return True
        # Lines starting with // (hash reference continuations)
        if s.startswith("//"):
            return True
        return False

    transactions: list[dict] = []
    pending_parts: list[str] = []
    layout = 1  # default: Layout 1

    for _, row_s in df_raw.iterrows():
        row = list(row_s)
        c0 = _get(row, 0)
        c1 = _get(row, 1)

        # ── Layout-switch header detection ──────────────────────────────────
        # Layout 2 header: c0="Date", c1="Particulars"
        if c0 == "Date" and c1 == "Particulars":
            layout = 2
            pending_parts = []
            continue
        # Layout 1 header: c1="Date", c4="Particulars"
        if c1 == "Date" and _get(row, 4) == "Particulars":
            layout = 1
            pending_parts = []
            continue

        # ── Skip file-level meta rows ───────────────────────────────────────
        if META_C0.match(c0):
            continue

        # ── Skip page markers in various columns ────────────────────────────
        if re.match(r"^page\s+\d+$", _get(row, 4), re.IGNORECASE) or \
           re.match(r"^page\s+\d+$", _get(row, 10), re.IGNORECASE):
            continue

        # ── Date row: commit accumulated narration as one transaction ───────
        if DATE_RE_CANARA.match(c0):
            if layout == 1:
                dep   = _num(row, 7)
                with_ = _num(row, 9)
                bal   = _num(row, 10)
            else:  # layout 2
                dep   = _num(row, 2)
                with_ = _num(row, 3)
                bal   = _num(row, 4)

            desc = " ".join(p for p in pending_parts if p).strip()
            pending_parts = []

            # Only record rows that actually carry an amount
            if dep is not None or with_ is not None:
                transactions.append({
                    "date":        c0,
                    "description": desc,
                    "deposit":     dep,
                    "withdrawal":  with_,
                    "balance":     bal,
                })
            continue

        # ── Non-date row: accumulate narration token ────────────────────────
        narr = _get(row, 3) if layout == 1 else c1
        if narr and not _is_noise(narr):
            pending_parts.append(narr)

    if not transactions:
        raise ValueError("No transactions found in Canara Bank CSV.")

    df = pd.DataFrame(transactions)

    def _is_credit(row: pd.Series) -> bool:
        d = row["description"].upper()
        if "UPI/CR" in d or "NEFT/CR" in d:
            return True
        if "UPI/DR" in d or "NEFT/DR" in d:
            return False
        has_dep = pd.notna(row["deposit"]) and row["deposit"] > 0
        has_wdl = pd.notna(row["withdrawal"]) and row["withdrawal"] > 0
        return has_dep and not has_wdl

    df["is_credit"] = df.apply(_is_credit, axis=1)
    df["amount"] = df.apply(
        lambda r: r["deposit"] if pd.notna(r["deposit"]) and r["deposit"] > 0 else r["withdrawal"],
        axis=1,
    )
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(r"[^\d.]", "", regex=True)
        .pipe(pd.to_numeric, errors="coerce")
        .abs()
    )
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Generic CSV parser
# ──────────────────────────────────────────────────────────────────────────────

def _parse_generic_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        engine="python",
        on_bad_lines="warn"
    )

    df.columns = [c.strip().lower() for c in df.columns]


    rename: dict[str, str] = {}
    for col in df.columns:
        cl = col.lower()
        if cl == "date":
            rename[col] = "date"
        elif cl in ("description", "particulars", "narration", "details", "remarks"):
            rename[col] = "description"
        elif cl in ("amount", "debit", "withdrawal", "dr amount"):
            rename[col] = "amount"
        elif cl in ("credit", "deposit", "cr amount"):
            rename[col] = "credit_amount"
        elif cl in ("type", "txn type", "cr/dr", "transaction type"):
            rename[col] = "type"
    df = df.rename(columns=rename)

    if "credit_amount" in df.columns and "is_credit" not in df.columns:
        credit_vals = (
            df["credit_amount"].astype(str)
            .str.replace(",", "").str.replace(r"[^\d.]", "", regex=True)
            .pipe(pd.to_numeric, errors="coerce")
        )
        debit_vals = (
            df.get("amount", pd.Series(dtype=float)).astype(str)
            .str.replace(",", "").str.replace(r"[^\d.]", "", regex=True)
            .pipe(pd.to_numeric, errors="coerce")
        )
        df["is_credit"] = credit_vals.fillna(0) > debit_vals.fillna(0)
        df["amount"]    = credit_vals.fillna(0) + debit_vals.fillna(0)

    if "type" in df.columns and "is_credit" not in df.columns:
        df["is_credit"] = df["type"].str.upper().str.contains(
            "CR|CREDIT|DEPOSIT", na=False
        )

    if "is_credit" not in df.columns:
        df["is_credit"] = False
    return df


# ──────────────────────────────────────────────────────────────────────────────
# NLP query agent
# ──────────────────────────────────────────────────────────────────────────────

def answer_question(question: str, df: pd.DataFrame) -> str:
    by_cat   = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    by_merch = (
        df.groupby("description")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
    )
    by_day   = df.groupby("weekday")["amount"].sum()
    by_month = df.groupby("month")["amount"].sum()

    debits  = df[df["is_credit"] == False]
    credits = df[df["is_credit"] == True]

    context = f"""
Total transactions : {len(df)}
Total debits       : ₹{debits['amount'].sum():,.2f}  ({len(debits)} txns)
Total credits      : ₹{credits['amount'].sum():,.2f}  ({len(credits)} txns)
Date range         : {df['date'].min().date()} to {df['date'].max().date()}

Spend by Category:
{by_cat.to_string()}

Top 15 Payees/Merchants:
{by_merch.to_string()}

By Day of Week:
{by_day.to_string()}

By Month:
{by_month.to_string()}
"""
    prompt = (
        "You are a personal finance assistant. Answer the user's question "
        "using only the data below. Be specific, use ₹ amounts. "
        "If the data is insufficient, say so clearly.\n\n"
        f"Data:\n{context}\n\nQuestion: {question}"
    )

    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-lite",
                google_api_key=gemini_key,
            )
            return llm.invoke([HumanMessage(content=prompt)]).content
        except Exception as exc:
            print(f"⚠️  Gemini failed: {exc} — falling back to Groq")

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            import requests
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama3-8b-8192",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                    "temperature": 0.2,
                },
                timeout=15,
            )
            resp_json = resp.json()
            if "error" in resp_json:
                err_msg = resp_json["error"].get("message", str(resp_json["error"]))
                print(f"⚠️  Groq API error: {err_msg}")
            elif "choices" in resp_json and resp_json["choices"]:
                return resp_json["choices"][0]["message"]["content"]
            else:
                print(f"⚠️  Groq unexpected response: {resp_json}")
        except Exception as exc:
            print(f"⚠️  Groq also failed: {exc}")

    return "⚠️  No LLM API key found. Set GEMINI_API_KEY or GROQ_API_KEY."


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

def parse_statement(path: str) -> pd.DataFrame:
    """
    Parse any Indian bank statement (PDF or CSV) and return a clean DataFrame.

    Supported sources
    -----------------
    PDF : SBI, Union Bank, IPPB, Canara Bank, generic fallback
    CSV : Canara Bank ePassbook, generic (SBI/HDFC/Axis/ICICI)

    Output columns
    --------------
    date        – datetime
    description – raw narration string
    amount      – absolute float (always positive)
    is_credit   – True = money IN, False = money OUT
    category    – classified spending category
    weekday     – day name  (e.g. "Monday")
    month       – period string  (e.g. "2025-04")
    """
    p = path.lower()

    if p.endswith(".pdf"):
        df = parse_pdf_statement(path)

    elif p.endswith(".csv"):
        try:
            peek        = pd.read_csv(path, header=None, nrows=8, dtype=str)
            header_text = peek.to_string().upper()
        except Exception:
            header_text = ""

        if "CANARA" in header_text or "CNRB" in header_text:
            df = parse_canara_csv(path)
        else:
            df = _parse_generic_csv(path)

    else:
        raise ValueError(f"Unsupported file format: {path}")

    df["category"] = df.apply(
        lambda r: categorize(r["description"], r.get("is_credit", False)),
        axis=1,
    )

    df["amount"] = (
        df["amount"].astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(r"[^\d.]", "", regex=True)
        .pipe(pd.to_numeric, errors="coerce")
        .abs()
    )

    df["date"] = _parse_dates(df["date"].astype(str))

    n_bad = df["date"].isna().sum()
    if n_bad > 0:
        print(f"⚠️  {n_bad} row(s) had unparseable dates — dropped.")

    n_before = len(df)
    df = df.dropna(subset=["amount", "date"])
    if (dropped := n_before - len(df)) > 0:
        print(f"⚠️  Dropped {dropped} row(s) during cleaning.")

    df["weekday"] = df["date"].dt.day_name()
    df["month"]   = df["date"].dt.to_period("M").astype(str)
    df = df.reset_index(drop=True)
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Quick sanity test
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python bank_statement_parser.py <statement.pdf|csv>")
        sys.exit(1)

    file_path = sys.argv[1]
    print(f"Parsing: {file_path}")
    result = parse_statement(file_path)
    print(f"\n✅ Parsed {len(result)} transactions")
    print(f"   Date range : {result['date'].min().date()} → {result['date'].max().date()}")
    print(f"   Total debit: ₹{result[~result['is_credit']]['amount'].sum():,.2f}")
    print(f"   Total credit: ₹{result[result['is_credit']]['amount'].sum():,.2f}")
    print("\nCategory breakdown:")
    print(result.groupby("category")["amount"].sum().sort_values(ascending=False).to_string())
    print("\nFirst 5 rows:")
    print(result.head().to_string())