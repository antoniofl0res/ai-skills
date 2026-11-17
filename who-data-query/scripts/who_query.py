#!/usr/bin/env python3
"""
who_query.py - Unified CLI for querying all public World Health Organization (WHO) APIs:
  1. WHO Global Health Observatory (GHO) OData v4 API (https://ghoapi.azureedge.net/api/)
  2. WHO xMart4 Enterprise Data Warehouse OData v4 APIs (https://xmart-api-public.who.int/)
  3. WHO Global Tuberculosis Programme CSV API (https://extranet.who.int/tme/generateCSV.asp)
  4. WHO World Health Data Hub (WHDH) COVID-19 & Vaccination Feeds (https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/)
"""

import argparse
import csv
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GHO_BASE = "https://ghoapi.azureedge.net/api/"
XMART_BASE = "https://xmart-api-public.who.int/"
TB_BASE = "https://extranet.who.int/tme/generateCSV.asp?ds="
WHDH_COVID_FEEDS = {
    "table": "https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-table-data.csv",
    "daily": "https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-data.csv",
    "vaccination": "https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/vaccination-data.csv",
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/csv, */*",
}


def fetch_bytes(url: str, timeout: int = 25, retries: int = 3) -> bytes:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read(400).decode("utf-8-sig", errors="replace")
            except Exception:
                pass
            last_err = RuntimeError(f"HTTP {e.code} on {url}: {body or e.reason}")
            # Retry on transient 5xx or xmart-relay cold-miss 404 ("An error occurred while sending the request.")
            if e.code in (500, 502, 503, 504) or (e.code == 404 and "sending the request" in body):
                if attempt < retries:
                    time.sleep(0.9 * attempt)
                    continue
            raise last_err
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(0.9 * attempt)
    raise last_err


def fetch_json(url: str, timeout: int = 25, retries: int = 3) -> dict:
    raw = fetch_bytes(url, timeout=timeout, retries=retries).decode("utf-8-sig", errors="replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid/truncated JSON response from {url} ({len(raw)} bytes): {raw[:200]}") from e


def fetch_odata_rows(url: str, max_rows: int = 50, timeout: int = 25) -> tuple:
    """Fetches OData rows and automatically follows @odata.nextLink until max_rows is reached."""
    rows = []
    total_count = None
    next_url = url
    pages = 0
    while next_url and len(rows) < max_rows and pages < 20:
        payload = fetch_json(next_url, timeout=timeout)
        if total_count is None and "@odata.count" in payload:
            total_count = payload["@odata.count"]
        batch = payload.get("value", [])
        rows.extend(batch)
        next_url = payload.get("@odata.nextLink")
        pages += 1
        if not batch:
            break
    return rows[:max_rows], total_count


def build_odata_url(base_url: str, path: str, params: dict = None) -> str:
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    if not params:
        return url
    parts = []
    for k, v in params.items():
        if v is None or v == "":
            continue
        # Percent-encode spaces, &, +, #, etc., while keeping OData syntax delimiters readable
        encoded_v = urllib.parse.quote(str(v), safe="(),'_=<>!$")
        parts.append(f"{k}={encoded_v}")
    return f"{url}?{'&'.join(parts)}" if parts else url


def resolve_country_identifiers(countries_csv: str) -> set:
    """
    Expands a comma-separated list of country identifiers (ISO-3, ISO-2, M49, or Name)
    into a set containing all matching ISO-3, ISO-2, M49, and short/formal country names
    using REFMART/REF_COUNTRY (with fallback to GHO /api/RegionCountry).
    """
    tokens = {c.strip().upper() for c in countries_csv.split(",") if c.strip()}
    if not tokens:
        return set()
    expanded = set(tokens)
    try:
        url = f"{XMART_BASE}REFMART/REF_COUNTRY?$select=CODE_ISO_3,CODE_ISO_2,GEO_M49_CODE,NAME_SHORT_EN,NAME_FORMAL_EN&$top=300"
        rows = fetch_json(url, timeout=12, retries=2).get("value", [])
        for r in rows:
            vals = {
                str(r.get("CODE_ISO_3") or "").upper(),
                str(r.get("CODE_ISO_2") or "").upper(),
                str(r.get("GEO_M49_CODE") or "").upper(),
                str(r.get("NAME_SHORT_EN") or "").upper(),
                str(r.get("NAME_FORMAL_EN") or "").upper(),
            } - {""}
            if tokens & vals:
                expanded |= vals
        return expanded
    except Exception:
        pass

    try:
        url = build_odata_url(GHO_BASE, "RegionCountry")
        rows = fetch_json(url, timeout=12, retries=2).get("value", [])
        for r in rows:
            vals = {
                str(r.get("CountryCode") or "").upper(),
                str(r.get("CountryName") or "").upper(),
            } - {""}
            if tokens & vals:
                expanded |= vals
    except Exception:
        pass
    return expanded


def print_markdown_table(rows: list, columns: list = None, max_rows: int = 100):
    if not rows:
        print("No matching records found.")
        return
    if not columns:
        columns = list(rows[0].keys())
    display_rows = rows[:max_rows]
    header = "| " + " | ".join(str(c) for c in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    print(header)
    print(sep)
    for r in display_rows:
        vals = []
        for c in columns:
            v = r.get(c, "")
            if v is None:
                v = ""
            vals.append(str(v).replace("\r", " ").replace("\n", " ").replace("|", "\\|"))
        print("| " + " | ".join(vals) + " |")
    if len(rows) > max_rows:
        print(f"\n*(Showing {max_rows} of {len(rows)} returned rows)*")


def save_csv(rows: list, csv_path: str, columns: list = None):
    if not rows:
        return
    if not columns:
        columns = list(rows[0].keys())
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {len(rows)} rows to CSV: {csv_path}")


# ---------------------------------------------------------------------------
# 1. GHO COMMANDS
# ---------------------------------------------------------------------------
def cmd_gho_search(args):
    q = args.keyword.strip()
    url = build_odata_url(GHO_BASE, "Indicator")
    data = fetch_json(url).get("value", [])
    q_low = q.lower()
    matched = []
    for item in data:
        code = item.get("IndicatorCode") or ""
        name = item.get("IndicatorName") or ""
        is_archived = "ARCHIVED" in code.upper() or "archived" in name.lower()
        if not args.include_archived and is_archived:
            continue
        if q_low in code.lower() or q_low in name.lower():
            matched.append({
                "IndicatorCode": code,
                "IndicatorName": name,
                "Status": "ARCHIVED" if is_archived else "ACTIVE",
            })
    print(f"Found {len(matched)} matching GHO indicators for '{q}':\n")
    print_markdown_table(matched, ["IndicatorCode", "IndicatorName", "Status"], max_rows=args.top)
    if args.csv:
        save_csv(matched, args.csv, ["IndicatorCode", "IndicatorName", "Status"])


def cmd_gho_dims(args):
    code = args.indicator_code.strip()
    url = build_odata_url(GHO_BASE, f"Indicator('{code}')/Dimensions")
    dims = fetch_json(url).get("value", [])
    print(f"Applicable dimensions for Indicator '{code}' ({len(dims)}):\n")
    print_markdown_table(dims, ["IndicatorCode", "Dimension", "DimensionName"])
    if args.show_values and dims:
        for d in dims:
            dim_code = d.get("Dimension")
            if not dim_code or dim_code in ("YEAR", "COUNTRY"):
                continue
            try:
                v_url = build_odata_url(GHO_BASE, f"DIMENSION('{dim_code}')/DimensionValues", {"$top": 25})
                vals = fetch_json(v_url).get("value", [])
                print(f"\nSample values for DIMENSION('{dim_code}'):")
                print_markdown_table(vals, ["Code", "Title", "ParentCode"], max_rows=20)
            except Exception as e:
                print(f"Could not fetch values for {dim_code}: {e}")


def cmd_gho_data(args):
    code = args.indicator_code.strip()
    sex_filter = args.sex
    if sex_filter == "AUTO":
        try:
            dims_url = build_odata_url(GHO_BASE, f"Indicator('{code}')/Dimensions")
            dims = [d.get("Dimension") for d in fetch_json(dims_url).get("value", [])]
            sex_filter = "SEX_BTSX" if "SEX" in dims else "ALL"
        except Exception:
            sex_filter = "ALL"

    filter_parts = []
    if args.countries:
        cty_list = [c.strip().upper() for c in args.countries.split(",") if c.strip()]
        if len(cty_list) == 1:
            filter_parts.append(f"SpatialDim eq '{cty_list[0]}'")
        elif len(cty_list) > 1:
            quoted = ",".join(f"'{c}'" for c in cty_list)
            filter_parts.append(f"SpatialDim in ({quoted})")

    if sex_filter and sex_filter.upper() != "ALL":
        filter_parts.append(f"Dim1 eq '{sex_filter}'")

    if args.start_year is not None:
        filter_parts.append(f"TimeDim ge {args.start_year}")
    if args.end_year is not None:
        filter_parts.append(f"TimeDim le {args.end_year}")
    if args.filter:
        filter_parts.append(f"({args.filter})")

    select_cols = args.select or "SpatialDim,SpatialDimType,ParentLocationCode,TimeDim,Dim1,Dim2,NumericValue,Low,High,Value,Date"
    params = {
        "$filter": " and ".join(filter_parts) if filter_parts else None,
        "$select": select_cols,
        "$orderby": args.orderby or "TimeDim desc",
        "$top": args.top,
        "$count": "true",
    }
    url = build_odata_url(GHO_BASE, code, params)
    rows, total_count = fetch_odata_rows(url, max_rows=args.top)

    if not rows and sex_filter == "SEX_BTSX" and args.sex == "AUTO":
        filter_parts = [p for p in filter_parts if not p.startswith("Dim1 eq")]
        params["$filter"] = " and ".join(filter_parts) if filter_parts else None
        url = build_odata_url(GHO_BASE, code, params)
        rows, total_count = fetch_odata_rows(url, max_rows=args.top)

    print(f"GHO Query URL: {url}")
    print(f"Total Matched Records (@odata.count): {total_count if total_count is not None else len(rows)}\n")
    if args.countries:
        found_ctys = {r.get("SpatialDim") for r in rows if r.get("SpatialDim")}
        missing_ctys = [c for c in cty_list if c not in found_ctys]
        if missing_ctys:
            print(f"WARNING: Requested country code(s) {missing_ctys} returned 0 rows in GHO /api/{code} (or were outside --top={args.top}).")
            if code == "MDG_0000000020" or code.startswith("TB_"):
                print(
                    f"  -> Upstream fallback: Run `python who_query.py tb-data estimates --countries {','.join(missing_ctys)}` "
                    "for `e_inc_100k`, `e_inc_100k_lo`, `e_inc_100k_hi`.\n"
                )
    cols = [c.strip() for c in select_cols.split(",") if c.strip()]
    print_markdown_table(rows, cols, max_rows=args.top)
    if args.csv:
        save_csv(rows, args.csv, cols)


# ---------------------------------------------------------------------------
# 2. XMART4 COMMANDS (FULL SERVER-SIDE ODATA PUSHDOWN + @odata.nextLink)
# ---------------------------------------------------------------------------
def cmd_xmart_tables(args):
    mart = args.mart.strip().upper()
    url = f"{XMART_BASE}{mart}?$format=json"
    data = fetch_json(url)
    tables = data.get("value", [])
    if args.keyword:
        kw = args.keyword.lower()
        tables = [t for t in tables if kw in (t.get("name") or "").lower()]
    print(f"WHO xMart4 Mart '{mart}' ({len(tables)} EntitySets):\n")
    print_markdown_table(tables, ["name", "kind", "url"], max_rows=200)


def cmd_xmart_query(args):
    mart = args.mart.strip().upper()
    table = args.table.strip()

    params = {
        "$filter": args.filter,
        "$select": args.select,
        "$orderby": args.orderby,
        "$top": args.top,
        "$count": "true" if args.count else None,
    }
    url = build_odata_url(f"{XMART_BASE}{mart}", table, params)
    print(f"xMart4 Query URL: {url}")
    rows, total_count = fetch_odata_rows(url, max_rows=args.top, timeout=30)
    if total_count is not None:
        print(f"Total Matched Records (@odata.count): {total_count}")
    print(f"Returned rows: {len(rows)}\n")

    cols = [c.strip() for c in args.select.split(",") if c.strip()] if args.select else (list(rows[0].keys())[:10] if rows else None)
    print_markdown_table(rows, cols, max_rows=args.top)
    if args.csv:
        save_csv(rows, args.csv, cols)


# ---------------------------------------------------------------------------
# 3. WHO GLOBAL TB PROGRAMME CSV API COMMAND
# ---------------------------------------------------------------------------
def cmd_tb_data(args):
    ds = args.dataset.strip()
    url = f"{TB_BASE}{urllib.parse.quote(ds)}"
    print(f"Fetching WHO Global TB Programme dataset '{ds}' from: {url}")
    text = fetch_bytes(url, timeout=35, retries=3).decode("utf-8-sig", errors="replace")
    if not text.strip() or text.lstrip().startswith("<!DOCTYPE") or text.lstrip().startswith("<html"):
        raise RuntimeError(f"Invalid or empty CSV returned for TB dataset '{ds}'. Valid datasets include: dictionary, estimates, notifications, outcomes, budget, policies.")

    reader = csv.DictReader(io.StringIO(text))
    countries = resolve_country_identifiers(args.countries) if args.countries else None
    kw = args.keyword.lower() if args.keyword else None

    matched = []
    for row in reader:
        if countries:
            row_codes = {
                (row.get("iso3") or "").upper(),
                (row.get("iso2") or "").upper(),
                (row.get("country") or "").upper(),
            } - {""}
            if not (countries & row_codes):
                continue
        if args.start_year is not None and row.get("year"):
            try:
                if int(row["year"]) < args.start_year:
                    continue
            except ValueError:
                pass
        if args.end_year is not None and row.get("year"):
            try:
                if int(row["year"]) > args.end_year:
                    continue
            except ValueError:
                pass
        if kw and kw not in json.dumps(row).lower():
            continue
        matched.append(row)

    print(f"Matched {len(matched)} rows in TB dataset '{ds}'.\n")
    cols = [c.strip() for c in args.cols.split(",")] if args.cols else (list(matched[0].keys())[:10] if matched else None)
    print_markdown_table(matched, cols, max_rows=args.top)
    if args.csv:
        save_csv(matched, args.csv, cols if args.cols else (list(matched[0].keys()) if matched else None))


# ---------------------------------------------------------------------------
# 4. WHDH COVID-19 & VACCINATION FEEDS COMMAND
# ---------------------------------------------------------------------------
def cmd_whdh_covid(args):
    feed = args.feed.strip().lower()
    url = WHDH_COVID_FEEDS.get(feed)
    if not url:
        raise SystemExit(f"Unknown feed '{feed}'. Choose from: {', '.join(WHDH_COVID_FEEDS.keys())}")
    print(f"Fetching WHDH feed '{feed}' from: {url}")
    print("Note: WHDH COVID-19 & vaccination CSVs are historical WHO archives; check Date_reported / DATE_UPDATED.")
    text = fetch_bytes(url, timeout=30, retries=3).decode("utf-8-sig", errors="replace")

    reader = csv.DictReader(io.StringIO(text))
    countries = resolve_country_identifiers(args.countries) if args.countries else None
    matched = []
    for row in reader:
        if countries:
            code_candidates = {
                (row.get("ISO3") or "").upper(),
                (row.get("Country_code") or "").upper(),
                (row.get("Name") or "").upper(),
                (row.get("COUNTRY") or "").upper(),
                (row.get("Country") or "").upper(),
            } - {""}
            if not (countries & code_candidates):
                continue
        matched.append(row)

    print(f"Matched {len(matched)} rows in WHDH '{feed}' feed.\n")
    cols = [c.strip() for c in args.cols.split(",")] if args.cols else (list(matched[0].keys())[:10] if matched else None)
    print_markdown_table(matched, cols, max_rows=args.top)
    if args.csv:
        save_csv(matched, args.csv, cols if args.cols else (list(matched[0].keys()) if matched else None))


def main():
    parser = argparse.ArgumentParser(description="Unified WHO Data Query CLI (GHO, xMart4, TB Extranet, WHDH)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # gho-search
    p_search = sub.add_parser("gho-search", help="Search the 3,092 GHO indicators by keyword")
    p_search.add_argument("keyword", help="Search keyword (e.g. 'life expectancy', 'malaria', 'HIV')")
    p_search.add_argument("--include-archived", action="store_true", help="Include archived indicators")
    p_search.add_argument("--top", type=int, default=50, help="Max rows to display (default: 50)")
    p_search.add_argument("--csv", help="Optional path to save results as CSV")
    p_search.set_defaults(func=cmd_gho_search)

    # gho-dims
    p_dims = sub.add_parser("gho-dims", help="List valid dimensions for a GHO IndicatorCode")
    p_dims.add_argument("indicator_code", help="GHO IndicatorCode (e.g. WHOSIS_000001)")
    p_dims.add_argument("--show-values", action="store_true", help="Also fetch sample DimensionValues for each dimension")
    p_dims.set_defaults(func=cmd_gho_dims)

    # gho-data
    p_data = sub.add_parser("gho-data", help="Fetch observations from a GHO Indicator table")
    p_data.add_argument("indicator_code", help="GHO IndicatorCode (e.g. WHOSIS_000001, HIV_0000000001)")
    p_data.add_argument("--countries", help="Comma-separated ISO-3 or WHO Region codes (e.g. BRA,ZAF,IND,AFR,GLOBAL)")
    p_data.add_argument("--sex", default="AUTO", help="Dim1 sex filter: AUTO (default), SEX_BTSX, SEX_FMLE, SEX_MLE, or ALL")
    p_data.add_argument("--start-year", type=int, help="Minimum TimeDim year (e.g. 2015)")
    p_data.add_argument("--end-year", type=int, help="Maximum TimeDim year (e.g. 2024)")
    p_data.add_argument("--filter", help="Additional raw OData $filter clause")
    p_data.add_argument("--select", help="Comma-separated columns to project")
    p_data.add_argument("--orderby", default="TimeDim desc", help="OData $orderby clause (default: 'TimeDim desc')")
    p_data.add_argument("--top", type=int, default=50, help="Max rows to fetch (default: 50)")
    p_data.add_argument("--csv", help="Optional path to save results as CSV")
    p_data.set_defaults(func=cmd_gho_data)

    # xmart-tables
    p_xt = sub.add_parser("xmart-tables", help="List all EntitySets in a WHO xMart4 public database")
    p_xt.add_argument("mart", help="Mart code: DATA_, WIISE, FLUMART, REFMART, SCORE, MNCAH, NUTRITION, NTD")
    p_xt.add_argument("--keyword", help="Optional keyword filter on table names")
    p_xt.set_defaults(func=cmd_xmart_tables)

    # xmart-query
    p_xq = sub.add_parser("xmart-query", help="Query a WHO xMart4 OData table")
    p_xq.add_argument("mart", help="Mart code (e.g. REFMART, WIISE, DATA_, FLUMART, NUTRITION, NTD)")
    p_xq.add_argument("table", help="EntitySet table name (e.g. REF_COUNTRY, AD_COVERAGES, RELAY_GHE_DATA)")
    p_xq.add_argument("--filter", help="OData $filter expression")
    p_xq.add_argument("--select", help="Comma-separated $select column names")
    p_xq.add_argument("--orderby", help="OData $orderby expression")
    p_xq.add_argument("--top", type=int, default=25, help="Max rows to fetch (default: 25)")
    p_xq.add_argument("--count", action="store_true", help="Request @odata.count")
    p_xq.add_argument("--csv", help="Optional path to save results as CSV")
    p_xq.set_defaults(func=cmd_xmart_query)

    # tb-data
    p_tb = sub.add_parser("tb-data", help="Query WHO Global TB Programme live CSV datasets")
    p_tb.add_argument("dataset", help="Dataset code: dictionary, estimates, notifications, outcomes, budget, policies")
    p_tb.add_argument("--countries", help="Comma-separated ISO-3, ISO-2, or country names (e.g. BRA,ZAF,IND)")
    p_tb.add_argument("--start-year", type=int, help="Minimum year")
    p_tb.add_argument("--end-year", type=int, help="Maximum year")
    p_tb.add_argument("--keyword", help="Substring filter (useful when searching 'dictionary')")
    p_tb.add_argument("--cols", help="Comma-separated column names to display")
    p_tb.add_argument("--top", type=int, default=30, help="Max rows to display (default: 30)")
    p_tb.add_argument("--csv", help="Optional path to save results as CSV")
    p_tb.set_defaults(func=cmd_tb_data)

    # whdh-covid
    p_cov = sub.add_parser("whdh-covid", help="Query WHO WHDH COVID-19 & Vaccination CSV feeds")
    p_cov.add_argument("feed", choices=["table", "daily", "vaccination"], help="Feed name: table, daily, or vaccination")
    p_cov.add_argument("--countries", help="Comma-separated ISO-3, ISO-2, or country names (e.g. BRA,ZAF,Brazil)")
    p_cov.add_argument("--cols", help="Comma-separated column names to display")
    p_cov.add_argument("--top", type=int, default=30, help="Max rows to display (default: 30)")
    p_cov.add_argument("--csv", help="Optional path to save results as CSV")
    p_cov.set_defaults(func=cmd_whdh_covid)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
