import os
import io
import csv
from datetime import datetime, date, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
import requests
import yfinance as yf
import pandas as pd
import numpy as np
import time
import re
import xmltodict


def search_gdelt(
    keywords: list,
    project_id: str,
    credentials_file: str,
    match_all: bool = False,
    days_back: int = 7,
    limit: int = 100,
    output_file: str = None,
) -> list:
    """
    Search GDELT for articles matching keywords and optionally save to a text file.

    Args:
        keywords        : List of keyword strings to search for.
        project_id      : GCP project ID (used for BigQuery billing).
        credentials_file: Path to a service account JSON key file.
        match_all       : If True, articles must match ALL keywords (AND).
                          If False, articles match ANY keyword (OR). Default False.
        days_back       : How many days back to search. Default 7.
        limit           : Maximum number of results to return. Default 100.
        output_file     : Optional path to save results as a text file.
                          If None, results are returned but not saved.

    Returns:
        List of dicts with keys: "title", "url", "published_at"
    """
    if not keywords:
        raise ValueError("Provide at least one keyword.")

    # ── Build query ───────────────────────────────────────────────────────────
    operator = " AND " if match_all else " OR "
    conditions = operator.join(
        f"""(
            LOWER(g.DocumentIdentifier) LIKE '%{kw.lower()}%'
            OR LOWER(g.V2Themes)        LIKE '%{kw.lower()}%'
            OR LOWER(g.V2Persons)       LIKE '%{kw.lower()}%'
            OR LOWER(g.V2Organizations) LIKE '%{kw.lower()}%'
            OR LOWER(g.V2Locations)     LIKE '%{kw.lower()}%'
        )"""
        for kw in keywords
    )

    query = f"""
SELECT DISTINCT
    e.url         AS url,
    e.title       AS title,
    DATE(e.date)  AS published_at
FROM
    `gdelt-bq.gdeltv2.gsg_docembed` e
INNER JOIN
    `gdelt-bq.gdeltv2.gkg_partitioned` g
    ON e.url = g.DocumentIdentifier
WHERE
    DATE(e.date) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)
    AND DATE(g._PARTITIONTIME) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)
    AND ({conditions})
    AND e.title IS NOT NULL
    AND e.title != ''
ORDER BY
    published_at DESC
LIMIT {limit}
"""

    credentials = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    client = bigquery.Client(project=project_id, credentials=credentials)

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Searching for: {keywords}")
    rows = list(client.query(query).result())
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {len(rows)} articles found.")

    results = [
        {
            "title": (row["title"] or "").strip(),
            "url": (row["url"] or "").strip(),
            "published_at": str(row["published_at"]) if row["published_at"] else None,
        }
        for row in rows
    ]

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("GDELT Article Search Results\n")
            f.write(f"Generated : {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write(f"Keywords  : {', '.join(keywords)}\n")
            f.write(f"Logic     : {'ALL (AND)' if match_all else 'ANY (OR)'}\n")
            f.write(f"Days back : {days_back}\n")
            f.write(f"Results   : {len(results)}\n")
            f.write("=" * 80 + "\n\n")

            for i, article in enumerate(results, start=1):
                f.write(f"[{i}] {article['title'] or '(no title)'}\n")
                f.write(f"    Published :{article['published_at'] or 'unknown'}\n")
                f.write(f"    URL       :{article['url']}\n")
                f.write("\n")

            f.write("=" * 80 + "\n")
            f.write(f"Total: {len(results)} articles\n")


        print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Saved to: {os.path.abspath(output_file)}")

    return results

PORTWATCH_BASE_URL = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services"
    "/Daily_Chokepoints_Data/FeatureServer/0/query"
)

# All 28 PortWatch chokepoint IDs mapped to human-readable names
PORTWATCH_CHOKEPOINT_NAMES = {
    "chokepoint1":  "Suez Canal",
    "chokepoint2":  "Panama Canal",
    "chokepoint3":  "Bosporus Strait",
    "chokepoint4":  "Bab el-Mandeb Strait",
    "chokepoint5":  "Malacca Strait",
    "chokepoint6":  "Strait of Hormuz",
    "chokepoint7":  "Cape of Good Hope",
    "chokepoint8":  "Gibraltar Strait",
    "chokepoint9":  "Dover Strait",
    "chokepoint10": "Oresund Strait",
    "chokepoint11": "Taiwan Strait",
    "chokepoint12": "Korea Strait",
    "chokepoint13": "Tsugaru Strait",
    "chokepoint14": "Luzon Strait",
    "chokepoint15": "Lombok Strait",
    "chokepoint16": "Ombai Strait",
    "chokepoint17": "Bohai Strait",
    "chokepoint18": "Torres Strait",
    "chokepoint19": "Sunda Strait",
    "chokepoint20": "Makassar Strait",
    "chokepoint21": "Magellan Strait",
    "chokepoint22": "Yucatan Channel",
    "chokepoint23": "Windward Passage",
    "chokepoint24": "Mona Passage",
    "chokepoint25": "Florida Strait",
    "chokepoint26": "Mozambique Channel",
    "chokepoint27": "Bass Strait",
    "chokepoint28": "English Channel",
}

# Fields returned by the API
PORTWATCH_OUT_FIELDS = ",".join([
    "year", "month", "day", "portid", "portname",
    "n_total", "n_cargo", "n_tanker",
    "n_container", "n_dry_bulk", "n_general_cargo", "n_roro",
    "capacity", "capacity_cargo", "capacity_tanker",
    "capacity_container", "capacity_dry_bulk", "capacity_general_cargo", "capacity_roro",
])

PORTWATCH_CSV_COLUMNS = [
    "date", "portid", "portname",
    "n_total", "n_cargo", "n_tanker",
    "n_container", "n_dry_bulk", "n_general_cargo", "n_roro",
    "capacity_total_mt", "capacity_cargo_mt", "capacity_tanker_mt",
    "capacity_container_mt", "capacity_dry_bulk_mt", "capacity_general_cargo_mt", "capacity_roro_mt",
]


def search_portwatch(
    chokepoints: list = PORTWATCH_CHOKEPOINT_NAMES.keys(),
    start_date: str = None,
    end_date: str = None,
    days_back: int = 30,
    output_file: str = None,
) -> list:
    """
    Fetch daily chokepoint transit calls and trade volume from IMF PortWatch.

    Args:
        chokepoints : List of chokepoint IDs to filter (e.g. ["chokepoint1", "chokepoint4"]).
                      Use None to fetch all 28 chokepoints.
                      See CHOKEPOINT_NAMES dict for all valid IDs and their names.
        start_date  : Start date as "YYYY-MM-DD". Overrides days_back if provided.
        end_date    : End date as "YYYY-MM-DD". Defaults to today if start_date is given.
        days_back   : Number of days back from today to fetch (used if start_date is None).
                      Default: 30.
        output_file : Optional path to save results as a CSV file.

    Returns:
        List of dicts, one per chokepoint-day, with keys:
            date, portid, portname,
            n_total, n_cargo, n_tanker, n_container, n_dry_bulk, n_general_cargo, n_roro,
            capacity_total_mt, capacity_cargo_mt, capacity_tanker_mt,
            capacity_container_mt, capacity_dry_bulk_mt, capacity_general_cargo_mt, capacity_roro_mt
    """


    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end   = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.today()
    else:
        end   = datetime.today()
        start = end - timedelta(days=days_back)

    where_clauses = [
        f"year >= {start.year} AND year <= {end.year}",
        f"month >= {start.month} AND month <= {end.month}",
        f"day >= {start.day} AND day <= {end.day}",
    ]

    if chokepoints:
        ids = ", ".join(f"'{cp}'" for cp in chokepoints)
        where_clauses.append(f"portid IN ({ids})")

    where = " AND ".join(where_clauses)

    params = {
        "where":          where,
        "outFields":      PORTWATCH_OUT_FIELDS,
        "orderByFields":  "year ASC, month ASC, day ASC, portid ASC",
        "resultOffset":   0,
        "resultRecordCount": 2000,
        "f":              "json",
    }

    all_features = []
    print(f"[{datetime.now():%H:%M:%S}] Fetching chokepoint data "
          f"({start:%Y-%m-%d} → {end:%Y-%m-%d})...")

    # Page through results (API returns max 2000 records per call)
    while True:
        response = requests.get(PORTWATCH_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(f"ArcGIS API error: {data['error']}")

        features = data.get("features", [])
        all_features.extend(features)

        if not data.get("exceededTransferLimit"):
            break

        params["resultOffset"] += 2000
        print(f"[{datetime.now():%H:%M:%S}]   Paging... {len(all_features)} records so far")

    print(f"[{datetime.now():%H:%M:%S}] {len(all_features)} records received.")

    if not all_features:
        print("No data returned for the given filters.")
        return []

    records = []
    for f in all_features:
        a = f["attributes"]
        yr, mo, dy = a.get("year"), a.get("month"), a.get("day")
        try:
            date_str = f"{yr}-{int(mo):02d}-{int(dy):02d}"
        except (TypeError, ValueError):
            date_str = None

        records.append({
            "date":                   date_str,
            "portid":                 a.get("portid", ""),
            "portname":               a.get("portname", PORTWATCH_CHOKEPOINT_NAMES.get(a.get("portid"), "")),
            "n_total":                a.get("n_total"),
            "n_cargo":                a.get("n_cargo"),
            "n_tanker":               a.get("n_tanker"),
            "n_container":            a.get("n_container"),
            "n_dry_bulk":             a.get("n_dry_bulk"),
            "n_general_cargo":        a.get("n_general_cargo"),
            "n_roro":                 a.get("n_roro"),
            "capacity_total_mt":      a.get("capacity"),
            "capacity_cargo_mt":      a.get("capacity_cargo"),
            "capacity_tanker_mt":     a.get("capacity_tanker"),
            "capacity_container_mt":  a.get("capacity_container"),
            "capacity_dry_bulk_mt":   a.get("capacity_dry_bulk"),
            "capacity_general_cargo_mt": a.get("capacity_general_cargo"),
            "capacity_roro_mt":       a.get("capacity_roro"),
        })

    # Optionally save CSV
    if output_file:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=PORTWATCH_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(records)
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            f.write(output.getvalue())
        print(f"[{datetime.now():%H:%M:%S}] Saved {len(records)} rows to: {output_file}")

    return records

VESSELFINDER_BASE_URL = "https://api.vesselfinder.com"

VESSELFINDER_ENDPOINTS = {
    "vessels":   "/vessels",     # specific vessels by IMO/MMSI (credit-based)
    "fleet":     "/vesselslist", # pre-configured fleet (subscription-based)
    "area":      "/livedata",    # all vessels in a bounding box (credit-based)
    "portcalls": "/portcalls",   # arrival/departure history (credit-based)
}

VESSELFINDER_AIS_CSV_COLUMNS = [
    "mmsi", "imo", "name", "callsign", "timestamp",
    "latitude", "longitude", "course", "speed", "heading",
    "navstat", "type", "draught", "destination", "eta",
    "zone", "eca", "src", "length_m", "width_m",
]

VESSELFINDER_PORTCALL_CSV_COLUMNS = [
    "mmsi", "imo", "locode", "port", "country", "event", "timestamp",
]

def search_credit_risk(symbol: str, output_file: str= ""):
    all_data = []

    t = yf.Ticker(symbol)

    info = t.info

    # Basic company info + ratios
    data = {
        "symbol": symbol,
        "longName": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "marketCap": info.get("marketCap"),
        "debtToEquity": info.get("debtToEquity"),
        "currentRatio": info.get("currentRatio"),
        "quickRatio": info.get("quickRatio"),
        "totalDebt": info.get("totalDebt"),
        "freeCashflow": info.get("freeCashflow"),
        "operatingCashflow": info.get("operatingCashflow"),
        "recommendation": info.get("recommendationKey"),
        "dividendYield": info.get("dividendYield")
    }

    try:
        bs = t.balance_sheet
        data["totalAssets"] = bs.loc["Total Assets"].iloc[0] if "Total Assets" in bs.index else None
        data["totalLiab"] = bs.loc["Total Liab"].iloc[0] if "Total Liab" in bs.index else None
        data["retainedEarnings"] = bs.loc["Retained Earnings"].iloc[0] if "Retained Earnings" in bs.index else None
    except Exception as e:
        print(f"Error reading balance sheet for {symbol}: {e}")
        data["totalAssets"] = None
        data["totalLiab"] = None
        data["retainedEarnings"] = None

    all_data.append(data)

    if output_file:
        df = pd.DataFrame(all_data)
        print(f"Writing to {output_file}")
        df.to_csv(output_file, index=False)

    return all_data


def search_sp500_marketcaps():
    """
    Fetches all S&P 500 companies and their market caps.

    Returns:
        DataFrame with columns:
            ticker, name, sector, industry, market_cap, market_cap_billions
        Sorted by market_cap descending.
    """

    # ── Step 1: Pull S&P 500 constituent list from Wikipedia ─────────────────
    print(f"[{datetime.now():%H:%M:%S}] Fetching S&P 500 list from Wikipedia...")
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    tables = pd.read_html(io.StringIO(response.text), flavor="lxml")
    sp500 = tables[0][[
        "Symbol", "Security", "GICS Sector", "GICS Sub-Industry"
    ]].rename(columns={
        "Symbol":            "ticker",
        "Security":          "name",
        "GICS Sector":       "sector",
        "GICS Sub-Industry": "industry",
    })

    # Yahoo Finance uses "-" not "." in tickers (e.g. BRK.B → BRK-B)
    sp500["ticker"] = sp500["ticker"].str.replace(".", "-", regex=False)
    print(f"[{datetime.now():%H:%M:%S}] {len(sp500)} companies found.")

    # ── Step 2: Fetch market caps from Yahoo Finance ──────────────────────────
    print(f"[{datetime.now():%H:%M:%S}] Fetching market caps from Yahoo Finance...")

    market_caps = []
    total = len(sp500)


    for i, row in sp500.iterrows():
        ticker = row["ticker"]
        try:
            info = yf.Ticker(ticker).info
            cap  = info.get("marketCap")
        except Exception:
            cap = None

        market_caps.append(cap)

        # Progress update every 50 tickers
        n = list(sp500.index).index(i) + 1
        if n % 50 == 0 or n == total:
            print(f"[{datetime.now():%H:%M:%S}]   {n}/{total} fetched...")

        # Be polite to Yahoo's servers
        time.sleep(0.1)

    # ── Step 3: Assemble and sort ─────────────────────────────────────────────
    sp500["market_cap"]         = market_caps
    sp500["market_cap_billions"] = sp500["market_cap"].apply(
        lambda x: round(x / 1e9, 2) if x else None
    )

    df = sp500.sort_values("market_cap", ascending=False).reset_index(drop=True)
    df.index += 1  # rank starts at 1

    missing = df["market_cap"].isna().sum()
    if missing:
        print(f"[{datetime.now():%H:%M:%S}] Note: {missing} tickers returned no market cap data.")

    print(f"[{datetime.now():%H:%M:%S}] Done. Largest: {df.iloc[0]['name']} "
          f"(${df.iloc[0]['market_cap_billions']}B)")

    return df.to_dict()

#=============================

EDGAR_HEADERS = {"User-Agent": "research@example.com"}  # SEC requires a valid User-Agent

# ── XBRL tags to extract ──────────────────────────────────────────────────────
# Each entry: (human label, [list of candidate XBRL tags in priority order])
# Multiple candidates handle cases where companies use different tag names.
EDGAR_XBRL_METRICS = {
    # Cash Flow
    "operating_cash_flow":    ["NetCashProvidedByUsedInOperatingActivities"],
    "capex":                  ["PaymentsToAcquirePropertyPlantAndEquipment",
                               "PaymentsForCapitalImprovements"],
    "free_cash_flow":         ["FreeCashFlow"],  # not always reported; derived if missing

    # Liquidity
    "cash":                   ["CashAndCashEquivalentsAtCarryingValue",
                               "CashCashEquivalentsAndShortTermInvestments"],
    "current_assets":         ["AssetsCurrent"],
    "current_liabilities":    ["LiabilitiesCurrent"],
    "accounts_payable":       ["AccountsPayableCurrent"],

    # Profitability / Coverage
    "revenue":                ["RevenueFromContractWithCustomerExcludingAssessedTax",
                               "Revenues", "SalesRevenueNet"],
    "cogs":                   ["CostOfGoodsAndServicesSold",
                               "CostOfRevenue", "CostOfGoodsSold"],
    "operating_income":       ["OperatingIncomeLoss"],
    "interest_expense":       ["InterestExpense",
                               "InterestAndDebtExpense"],
    "net_income":             ["NetIncomeLoss"],

    # Debt
    "long_term_debt":         ["LongTermDebt",
                               "LongTermDebtNoncurrent"],
    "current_long_term_debt": ["LongTermDebtCurrent",
                               "CurrentPortionOfLongTermDebt"],
}


def search_edgar_financials(
    cik: str,
    company_name: str,
    output_file: str = None,
) -> dict:
    """
    Fetch key financial metrics from EDGAR XBRL and extract credit ratings
    from the most recent 10-K filing.

    Args:
        cik          : SEC CIK number, with or without leading zeros (e.g. "0000320193" or "320193").
        company_name : Company name, used for display and 10-K credit rating search.
        output_file  : Optional path to save results as CSV.

    Returns:
        Dict with keys:
            company, cik, retrieved_at,
            metrics  -> dict of latest annual values for each financial metric,
            derived  -> dict of calculated ratios (current_ratio, interest_coverage,
                        dpo, free_cash_flow if not directly reported),
            credit_ratings -> list of raw strings mentioning ratings found in 10-K,
            periods  -> dict mapping each metric to the period it was reported for
    """

    cik_padded = cik.lstrip("0").zfill(10)  # EDGAR requires 10-digit zero-padded CIK

    # ── 1. Fetch XBRL company facts ───────────────────────────────────────────
    print(f"[{datetime.now():%H:%M:%S}] Fetching XBRL facts for CIK {cik_padded}...")
    facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
    r = requests.get(facts_url, headers=EDGAR_HEADERS, timeout=30)
    r.raise_for_status()
    facts = r.json()

    us_gaap = facts.get("facts", {}).get("us-gaap", {})

    # ── 2. Extract latest annual value for each metric ────────────────────────
    metrics = {}
    periods = {}

    for label, tags in EDGAR_XBRL_METRICS.items():
        value, period = _get_latest_annual(us_gaap, tags)
        metrics[label] = value
        periods[label] = period

    # ── 3. Derive ratios ──────────────────────────────────────────────────────
    derived = {}

    # Current Ratio = Current Assets / Current Liabilities
    if metrics["current_assets"] and metrics["current_liabilities"]:
        derived["current_ratio"] = round(
            metrics["current_assets"] / metrics["current_liabilities"], 2
        )

    # Interest Coverage = Operating Income / Interest Expense
    if metrics["operating_income"] and metrics["interest_expense"] and metrics["interest_expense"] != 0:
        derived["interest_coverage_ratio"] = round(
            metrics["operating_income"] / metrics["interest_expense"], 2
        )

    # DPO = Accounts Payable / COGS * 365
    if metrics["accounts_payable"] and metrics["cogs"] and metrics["cogs"] != 0:
        derived["days_payable_outstanding"] = round(
            (metrics["accounts_payable"] / metrics["cogs"]) * 365, 1
        )

    # Free Cash Flow = Operating Cash Flow - CapEx (if not directly reported)
    if not metrics["free_cash_flow"]:
        if metrics["operating_cash_flow"] and metrics["capex"]:
            derived["free_cash_flow"] = metrics["operating_cash_flow"] - metrics["capex"]
    else:
        derived["free_cash_flow"] = metrics["free_cash_flow"]

    # ── 4. Fetch credit ratings from most recent 10-K ─────────────────────────
    print(f"[{datetime.now():%H:%M:%S}] Fetching 10-K filings index...")
    credit_ratings = _extract_credit_ratings(cik_padded)

    # ── 5. Assemble result ────────────────────────────────────────────────────
    result = {
        "company":        company_name,
        "cik":            cik_padded,
        "retrieved_at":   datetime.now().isoformat(),
        "metrics":        metrics,
        "derived":        derived,
        "credit_ratings": credit_ratings,
        "periods":        periods,
    }

    _print_summary(result)

    # ── 6. Optionally save CSV ────────────────────────────────────────────────
    if output_file:
        _save_csv(result, output_file)

    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_latest_annual(us_gaap: dict, tags: list) -> tuple:
    """
    Try each tag in order, return the most recent annual (10-K) value and its period.
    Returns (None, None) if no data found.
    """
    for tag in tags:
        data = us_gaap.get(tag, {})
        units = data.get("units", {})
        entries = units.get("USD", units.get("shares", []))

        # Filter to annual 10-K filings only
        annual = [
            e for e in entries
            if e.get("form") in ("10-K", "10-K/A")
            and e.get("fp") == "FY"
        ]
        if not annual:
            continue

        # Sort by end date descending, take most recent
        annual.sort(key=lambda x: x.get("end", ""), reverse=True)
        latest = annual[0]
        return latest.get("val"), latest.get("end")

    return None, None


def _extract_credit_ratings(cik_padded: str) -> list:
    """
    Fetches the most recent 10-K filing and searches for credit rating mentions.
    Returns a list of unique matched strings.
    """
    # Get filing index
    sub_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    r = requests.get(sub_url, headers=EDGAR_HEADERS, timeout=30)
    r.raise_for_status()
    submissions = r.json()

    filings = submissions.get("filings", {}).get("recent", {})
    forms   = filings.get("form", [])
    docs    = filings.get("primaryDocument", [])
    accnums = filings.get("accessionNumber", [])

    # Find most recent 10-K
    ten_k_idx = next((i for i, f in enumerate(forms) if f == "10-K"), None)
    if ten_k_idx is None:
        print(f"[{datetime.now():%H:%M:%S}] No 10-K found.")
        return []

    accession = accnums[ten_k_idx].replace("-", "")
    doc       = docs[ten_k_idx]
    filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik_padded)}/{accession}/{doc}"

    print(f"[{datetime.now():%H:%M:%S}] Fetching 10-K: {filing_url}")
    try:
        r = requests.get(filing_url, headers=EDGAR_HEADERS, timeout=60)
        r.raise_for_status()
        text = r.text
    except Exception as e:
        print(f"[{datetime.now():%H:%M:%S}] Could not fetch 10-K: {e}")
        return []

    # Search for credit rating patterns
    # Matches things like: "A+", "Baa1", "BBB-", "investment grade", "Moody's ... Aa3"
    patterns = [
        r"(?:Moody['\u2019]?s|S&P|Standard\s*&\s*Poor['\u2019]?s|Fitch)[^.]{0,80}?(?:rated?|rating|assigned)[^.]{0,80}\.",
        r"(?:rated?|rating(?:s)?)[^.]{0,60}?(?:Aaa|Aa[123]|A[123]|Baa[123]|Ba[123]|B[123]|Caa|Ca|C|AAA|AA[+-]?|A[+-]?|BBB[+-]?|BB[+-]?|B[+-]?|CCC[+-]?|CC|D)[^.]{0,40}\.",
        r"(?:Aaa|Aa[123]|A[123]|Baa[123]|Ba[123]|B[123]|AAA|AA[+-]?|A[+-]?|BBB[+-]?|BB[+-]?|B[+-]?|CCC[+-]?)[^.]{0,60}?(?:Moody|S&P|Fitch|rated?|rating|outlook)[^.]{0,60}\.",
        r"investment[\s-]grade",
        r"speculative[\s-]grade",
        r"credit\s+(?:rating|outlook)[^.]{0,120}\.",
    ]

    matches = set()
    clean_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))  # strip HTML tags

    for pattern in patterns:
        for m in re.finditer(pattern, clean_text, re.IGNORECASE):
            snippet = m.group(0).strip()
            if len(snippet) > 20:  # filter out very short noise matches
                matches.add(snippet)

    ratings = sorted(matches)
    print(f"[{datetime.now():%H:%M:%S}] Found {len(ratings)} credit rating mention(s) in 10-K.")
    return ratings


def _print_summary(result: dict) -> None:
    m = result["metrics"]
    d = result["derived"]

    def fmt(val, divisor=1e9, suffix="B"):
        if val is None:
            return "N/A"
        return f"${val / divisor:.2f}{suffix}"

    print(f"\n{'='*55}")
    print(f"  {result['company']} (CIK: {result['cik']})")
    print(f"{'='*55}")
    print(f"  Revenue              : {fmt(m['revenue'])}")
    print(f"  Operating Income     : {fmt(m['operating_income'])}")
    print(f"  Net Income           : {fmt(m['net_income'])}")
    print(f"  Operating Cash Flow  : {fmt(m['operating_cash_flow'])}")
    print(f"  Free Cash Flow       : {fmt(d.get('free_cash_flow'))}")
    print(f"  Cash                 : {fmt(m['cash'])}")
    print(f"  Current Ratio        : {d.get('current_ratio', 'N/A')}")
    print(f"  Interest Coverage    : {d.get('interest_coverage_ratio', 'N/A')}x")
    print(f"  Days Payable (DPO)   : {d.get('days_payable_outstanding', 'N/A')} days")
    print(f"  Long-term Debt       : {fmt(m['long_term_debt'])}")
    if result["credit_ratings"]:
        print(f"\n  Credit Rating Mentions ({len(result['credit_ratings'])}):")
        for r in result["credit_ratings"][:5]:  # show first 5
            print(f"    - {r[:120]}")
    print(f"{'='*55}\n")


def _save_csv(result: dict, output_file: str) -> None:
    rows = []

    # Metrics
    for key, val in result["metrics"].items():
        rows.append({
            "category": "metric",
            "key":      key,
            "value":    val,
            "period":   result["periods"].get(key, ""),
        })

    # Derived
    for key, val in result["derived"].items():
        rows.append({
            "category": "derived",
            "key":      key,
            "value":    val,
            "period":   "",
        })

    # Credit ratings
    for rating in result["credit_ratings"]:
        rows.append({
            "category": "credit_rating",
            "key":      "mention",
            "value":    rating,
            "period":   "",
        })

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["category", "key", "value", "period"])
    writer.writeheader()
    writer.writerows(rows)

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())

    print(f"[{datetime.now():%H:%M:%S}] Saved to: {output_file}")

