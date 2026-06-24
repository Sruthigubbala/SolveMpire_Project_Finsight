"""
bank_statement_parser.py
========================
Parse Indian bank statements (PDF or CSV) into a clean, categorized DataFrame.

Supported banks
---------------
PDF : SBI, Union Bank of India, IPPB, Canara Bank, generic fallback
CSV : Canara Bank ePassbook, generic (SBI / HDFC / Axis / ICICI exports)

Public API
----------
parse_statement(path) → pd.DataFrame
    Columns: date, description, amount, is_credit, category, weekday, month
"""

from __future__ import annotations

import os
import re
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
        "pmsby", "pmjjby", "sbiya", "sbijb", "sbisb",          # SBI insurance codes
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
        "debit atmcard amc",                                    # SBI AMC
    ],
    "atm_withdrawal": [
        "atw/", "atm/", "cash withdrawal", "cash at ", "atm cash",
        "atm-", "atm wdl", "atm wdl ",
    ],
    "cash_deposit": [
        "csh dep", "cash dep", "cdm",
    ],
    "interest_income": [
        "interest credit", "int cr", "interest cr",
    ],
    "salary": [
        "salary", "cemtex dep",
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
        import requests  # noqa: PLC0415
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
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 10,
                "temperature": 0,
            },
            timeout=5,
        )
        result = (
            resp.json()["choices"][0]["message"]["content"].strip().lower()
        )
        matched = next(
            (c for c in _GROQ_CATEGORIES if c == result), "other"
        )
        _groq_cache[key] = matched
        return matched
    except Exception as exc:  # noqa: BLE001
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

    # ── Priority rules (always checked first) ──────────────────────────────

    # Interest income
    if any(k in d for k in CATEGORIES["interest_income"]):
        return "interest_income"

    # Salary / employer credit
    if any(k in d for k in CATEGORIES["salary"]):
        return "salary"

    # Cash deposits (CDM / CSH DEP)
    if any(k in d for k in CATEGORIES["cash_deposit"]):
        return "cash_deposit"

    # Bank fees (ATM AMC, SMS charges, etc.)
    if any(k in d for k in CATEGORIES["bank_fees"]):
        return "bank_fees"

    # ATM cash withdrawals
    if any(k in d for k in CATEGORIES["atm_withdrawal"]):
        return "atm_withdrawal"
    # Long digit string = ATM ref pattern
    if re.match(r"^\d{10,}/\d+", desc.strip()):
        return "atm_withdrawal"

    # SBI insurance premium codes (SBIYA / SBIJB / SBISB)
    if re.search(r"\bsbi[yjs]b?\d+", d):
        return "insurance"

    # Credit card payments
    if any(k in d for k in CATEGORIES["credit_card_payment"]):
        return "credit_card_payment"

    # Government / CBDC
    if any(k in d for k in CATEGORIES["government"]):
        return "government"

    # ── UPI direction routing ───────────────────────────────────────────────

    # SBI UPI: UPI/DR = debit, UPI/CR = credit
    # Also handles "DEP TFR" / "WDL TFR" prefix which SBI uses
    if "upi/cr" in d or "dep tfr" in d:
        hit = _keyword_scan(d)
        return hit if hit else "received"

    if "upi/dr" in d or "wdl tfr" in d:
        hit = _keyword_scan(d)
        if hit:
            return hit
        groq = _groq_categorize(desc, is_credit=False)
        return groq if groq != "other" else "personal_transfer"

    # Union Bank UPI
    if "upiab/" in d:
        hit = _keyword_scan(d)
        return hit if hit else "received"

    if "upiar/" in d:
        hit = _keyword_scan(d)
        if hit:
            return hit
        groq = _groq_categorize(desc, is_credit=False)
        return groq if groq != "other" else "personal_transfer"

    # IPPB UPI
    if "~cr~" in d or "~ft~" in d:
        hit = _keyword_scan(d)
        return hit if hit else "received"

    if "~dr~" in d:
        hit = _keyword_scan(d)
        if hit:
            return hit
        groq = _groq_categorize(desc, is_credit=False)
        return groq if groq != "other" else "personal_transfer"

    # IMPS credit
    if "impsab/" in d or "imps" in d:
        return "transfer"

    # ── Full keyword scan for non-UPI transactions ──────────────────────────
    hit = _keyword_scan(d, skip=())
    if hit:
        return hit

    # ── Groq AI fallback ────────────────────────────────────────────────────
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
# SBI PDF parser  (NEW)
# ──────────────────────────────────────────────────────────────────────────────

def _extract_sbi_metadata(pdf_path: str) -> dict[str, str]:
    """
    Extract account-level metadata from SBI statement page 1.

    Returns a dict with keys: account_number, ifsc, branch, holder_name,
    account_type, opening_balance, closing_balance, statement_from,
    statement_to.  Any field that cannot be found is left as an empty string.
    """
    meta: dict[str, str] = {
        "account_number": "",
        "ifsc": "",
        "branch": "",
        "holder_name": "",
        "account_type": "",
        "opening_balance": "",
        "closing_balance": "",
        "statement_from": "",
        "statement_to": "",
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
            nm = re.search(
                r"(?:Welcome:|Mr\.|Mrs\.|Ms\.)\s*([A-Za-z\s]+)", lc
            )
            if nm and not meta["holder_name"]:
                meta["holder_name"] = nm.group(1).strip()

    # Statement date range: "Statement From  : 01-04-2025 to 31-03-2026"
    m = re.search(
        r"Statement From\s*:\s*(\d{2}-\d{2}-\d{4})\s+to\s+(\d{2}-\d{2}-\d{4})",
        text,
    )
    if m:
        meta["statement_from"] = m.group(1)
        meta["statement_to"] = m.group(2)

    # Opening / closing from statement summary table on last page
    m = re.search(
        r"Brought Forward.*?([\d,]+\.?\d*)\s*CR", text, re.DOTALL
    )
    if m:
        meta["opening_balance"] = m.group(1).replace(",", "")

    return meta


def parse_sbi_pdf(path: str) -> pd.DataFrame:
    """
    Parse an SBI (State Bank of India) PDF statement.

    SBI statement columns:
        Value Date | Post Date | Details | Ref No/Cheque No | ₹ Debit | ₹ Credit | Balance

    DEP TFR  = deposit / credit entry
    WDL TFR  = withdrawal / debit entry
    ATM WDL  = ATM cash withdrawal
    """
    rows: list[dict] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 7:
                        continue
                    # Column layout: [value_date, post_date, details, ref, debit, credit, balance]
                    date_str = str(row[0] or "").strip()
                    details  = str(row[2] or "").replace("\n", " ").strip()
                    debit    = str(row[4] or "").strip()
                    credit   = str(row[5] or "").strip()

                    # Only process rows that look like real transaction dates
                    if not re.match(r"\d{2}/\d{2}/\d{4}", date_str):
                        continue
                    # Skip header-like rows
                    if details.lower() in ("details", "particulars", "narration"):
                        continue

                    debit_val  = _clean_amount(debit)
                    credit_val = _clean_amount(credit)

                    # Determine direction
                    d = details.upper()
                    # SBI explicitly labels: DEP TFR = credit, WDL TFR = debit
                    # ATM WDL = debit; INTEREST CREDIT = credit; CSH DEP = credit
                    if credit_val and float(credit_val) > 0:
                        rows.append({
                            "date": date_str,
                            "description": details,
                            "amount": credit_val,
                            "is_credit": True,
                        })
                    elif debit_val and float(debit_val) > 0:
                        rows.append({
                            "date": date_str,
                            "description": details,
                            "amount": debit_val,
                            "is_credit": False,
                        })

    if not rows:
        raise ValueError("No transactions found in SBI PDF.")

    df = pd.DataFrame(rows)
    # Reformat date from DD/MM/YYYY → standard string for _parse_dates
    df["date"] = df["date"].str.replace("/", "-")   # → DD-MM-YYYY
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Union Bank PDF parser
# ──────────────────────────────────────────────────────────────────────────────

def parse_union_bank_pdf(path: str) -> pd.DataFrame:
    """
    Parse Union Bank of India PDF statement.
    Columns: SI | Date | Particulars | Chq Num | Withdrawal | Deposit | Balance
    """
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
# IPPB PDF parser
# ──────────────────────────────────────────────────────────────────────────────

def parse_ippb_pdf(path: str) -> pd.DataFrame:
    """
    Parse India Post Payments Bank (IPPB) PDF statement.
    Columns: DATE | TRAN ID | TRANSACTION PARTICULARS | WITHDRWAL | DEPOSIT | BALANCE | Cr/Dr
    """
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
        raise ValueError("No transactions found in IPPB PDF.")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Canara Bank ePassbook PDF parser
# ──────────────────────────────────────────────────────────────────────────────

def parse_canara_bank_pdf(path: str) -> pd.DataFrame:
    """
    Parse Canara Bank ePassbook PDF statement (text-extraction approach).
    """
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
                        "date": date_str,
                        "description": full_desc,
                        "amount": amount,
                        "is_credit": is_credit,
                    })
                elif line.lower().startswith("chq:"):
                    desc_lines = []
                else:
                    desc_lines.append(line)

    if not rows:
        raise ValueError("No transactions found in Canara Bank PDF.")
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Generic / fallback PDF parser
# ──────────────────────────────────────────────────────────────────────────────

def _parse_generic_pdf(path: str) -> pd.DataFrame:
    """Generic fallback PDF parser for HDFC, Axis, and other formats."""
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
                str(c or "").strip()
                for c in table[header_idx]
                if c is not None
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
                elif any(
                    x in cu for x in ("PARTICULAR", "DESCRIPTION", "NARRATION")
                ):
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

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("Could not extract transactions from this PDF.")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# PDF auto-detect router
# ──────────────────────────────────────────────────────────────────────────────

def parse_pdf_statement(path: str) -> pd.DataFrame:
    """
    Auto-detect PDF bank format and dispatch to the correct parser.
    Detection order: SBI → Union Bank → IPPB → Canara → generic fallback.
    """
    with pdfplumber.open(path) as pdf:
        text        = pdf.pages[0].extract_text() or ""
        first_table = pdf.pages[0].extract_table()

    header = text.upper()

    # SBI detection: header contains "STATE BANK OF INDIA" or IFSC starts with SBIN
    if "STATE BANK OF INDIA" in header or "SBIN0" in header or "SBIYA" in header:
        return parse_sbi_pdf(path)

    # Union Bank
    if "UNION BANK" in header or "UBIN" in header:
        return parse_union_bank_pdf(path)

    # IPPB
    if "INDIA POST" in header or "IPPB" in header or "IPOS" in header:
        return parse_ippb_pdf(path)

    # Canara Bank
    if "CANARA" in header or "CNRB" in header:
        return parse_canara_bank_pdf(path)

    # Check first table header for known patterns
    if first_table:
        hj = " ".join(str(c or "") for c in (first_table[0] or [])).upper()
        if "WITHDRWAL" in hj:
            return parse_ippb_pdf(path)
        if "PARTICULARS" in hj and "WITHDRAWAL" in hj:
            return parse_union_bank_pdf(path)
        # SBI-style column signature
        if "VALUE DATE" in hj and "DEBIT" in hj and "CREDIT" in hj:
            return parse_sbi_pdf(path)

    return _parse_generic_pdf(path)


# ──────────────────────────────────────────────────────────────────────────────
# Canara Bank ePassbook CSV parser
# ──────────────────────────────────────────────────────────────────────────────

def parse_canara_csv(path: str) -> pd.DataFrame:
    """Parse Canara Bank ePassbook CSV export (dual-column layout)."""
    df_raw = pd.read_csv(path, header=None, dtype=str)
    DATE_RE_CANARA = re.compile(r"^\d{2}-\d{2}-\d{4}$")

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

    transactions: list[dict] = []
    layout = 1
    cur_date: str | None   = None
    cur_parts: list[str]   = []
    cur_dep: float | None  = None
    cur_with: float | None = None
    cur_bal: float | None  = None

    def flush() -> None:
        nonlocal cur_date, cur_parts, cur_dep, cur_with, cur_bal
        if cur_date:
            transactions.append({
                "date": cur_date,
                "description": " ".join(p for p in cur_parts if p),
                "deposit": cur_dep,
                "withdrawal": cur_with,
                "balance": cur_bal,
            })
        cur_date = None
        cur_parts = []
        cur_dep = cur_with = cur_bal = None

    for _, row_s in df_raw.iterrows():
        row = list(row_s)
        c0 = _get(row, 0)
        c1 = _get(row, 1)

        if c0 == "Date" and c1 == "Particulars":
            layout = 2
            continue
        if c0 == "" and c1 == "Date":
            layout = 1
            continue
        if re.match(r"^page\s+\d+$", c0, re.I):
            continue
        if re.match(r"^page\s+\d+$", _get(row, 4), re.I):
            continue

        if DATE_RE_CANARA.match(c0):
            flush()
            cur_date = c0
            if layout == 1:
                cur_parts = [_get(row, 3)]
                cur_dep   = _num(row, 7)
                cur_with  = _num(row, 8) or _num(row, 9)
                cur_bal   = _num(row, 10)
            else:
                cur_parts = [c1]
                cur_dep   = _num(row, 2)
                cur_with  = _num(row, 3)
                cur_bal   = _num(row, 4)
        elif cur_date is not None:
            if layout == 1:
                p = _get(row, 3)
                if cur_dep  is None: cur_dep  = _num(row, 7)
                if cur_with is None: cur_with = _num(row, 8) or _num(row, 9)
                if cur_bal  is None: cur_bal  = _num(row, 10)
            else:
                p = c1
                if cur_dep  is None: cur_dep  = _num(row, 2)
                if cur_with is None: cur_with = _num(row, 3)
                if cur_bal  is None: cur_bal  = _num(row, 4)
            if p:
                cur_parts.append(p)

    flush()

    df = pd.DataFrame(transactions)
    if df.empty:
        raise ValueError("No transactions found in Canara Bank CSV.")

    def _is_credit(row: pd.Series) -> bool:
        d = row["description"].upper()
        if "UPI/CR" in d or "NEFT/CR" in d:
            return True
        if "UPI/DR" in d or "NEFT/DR" in d:
            return False
        return bool(row["deposit"] and not row["withdrawal"])

    df["is_credit"] = df.apply(_is_credit, axis=1)
    df["amount"] = df.apply(
        lambda r: r["deposit"] if r["deposit"] else r["withdrawal"], axis=1
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
# Generic CSV parser  (SBI / HDFC / Axis / ICICI exports)
# ──────────────────────────────────────────────────────────────────────────────

def _parse_generic_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
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

    df.setdefault("is_credit", False)
    return df


# ──────────────────────────────────────────────────────────────────────────────
# NLP query agent
# ──────────────────────────────────────────────────────────────────────────────

def answer_question(question: str, df: pd.DataFrame) -> str:
    """
    Answer a natural-language question about a parsed transactions DataFrame.
    Uses the Gemini API (claude-sonnet-4-6 via Anthropic proxy if preferred,
    or google-generativeai).  Falls back to Groq llama3 if GEMINI_API_KEY
    is absent.
    """
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

    # Try Gemini first
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI  # noqa: PLC0415
            from langchain_core.messages import HumanMessage            # noqa: PLC0415
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-lite",
                google_api_key=gemini_key,
            )
            return llm.invoke([HumanMessage(content=prompt)]).content
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️  Gemini failed: {exc} — falling back to Groq")

    # Fallback: Groq
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            import requests  # noqa: PLC0415
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
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
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

    # ── Parse raw rows ───────────────────────────────────────────────────────
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

    # ── Common post-processing ───────────────────────────────────────────────
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
# Quick sanity test (run directly: python bank_statement_parser.py <path>)
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