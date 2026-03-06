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


def fetch_sp500_marketcaps(numrows: int = 500):
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

def search_edgar():
    pass

def search_wto():
    pass

def search_fred():
    pass
