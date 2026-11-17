---
name: who-data-query
description: >
  Query, discover, and extract epidemiological, demographic, health-system, and policy data
  from public World Health Organization (WHO) APIs: the GHO OData v4 API (`ghoapi.azureedge.net`),
  WHO xMart4 OData APIs (`xmart-api-public.who.int`: `DATA_` / `data.who.int`, `WIISE` / WUENIC
  immunization, `FLUMART` / FluNet, `REFMART`, `SCORE`, `MNCAH`, `NUTRITION` NLIS, `NTD`), the
  WHO Global TB Programme CSV API (`extranet.who.int/tme`), and WHDH COVID-19/vaccination feeds.
  ALWAYS trigger when the user asks for WHO statistics, GHO indicators, country health metrics,
  HIV/TB/malaria/NTD/NCD burden, mortality, life expectancy, HALE, DALYs, Global Health Estimates,
  vaccine coverage, health workforce, or GHED/UHC health financing.
---

# WHO Data Query Skill

A complete workflow and CLI toolkit for retrieving authoritative global health data from public, unauthenticated World Health Organization (WHO) APIs without guesswork or broken streams.

## Bundled CLI Tool (`scripts/who_query.py`)

Use the bundled zero-dependency Python CLI at `C:\Users\Antonio Flores\.claude\skills\who-data-query\scripts\who_query.py`.
- **Progressive Disclosure Rule:** Execute `who_query.py` directly via CLI commands; **do NOT read `scripts/who_query.py` into context** (its flags and behaviors are fully documented below), and only read `references/who_apis_catalog.md` if a required table or indicator code is not already listed in this file.
- **Batching Rule:** When extracting multiple tables or writing custom CSV schemas, run one quick CLI check or write a single self-contained Python script that fetches all required endpoints in one execution rather than making 10+ sequential shell calls.

```powershell
$cli = "C:\Users\Antonio Flores\.claude\skills\who-data-query\scripts\who_query.py"

# 1. Search the 3,092 GHO indicators by keyword
python $cli gho-search "life expectancy"

# 2. Inspect valid disaggregation dimensions (and dimension values) for a GHO indicator
python $cli gho-dims WHOSIS_000001 --show-values

# 3. Fetch GHO indicator observations (auto-handles Dim1=SEX_BTSX vs null, follows @odata.nextLink, optional CSV)
python $cli gho-data WHOSIS_000001 --countries BRA,ZAF,IND --start-year 2018 --top 30

# 4. List all tables (EntitySets) in a WHO xMart4 public database (DATA_, WIISE, FLUMART, REFMART, SCORE, MNCAH, NUTRITION, NTD)
python $cli xmart-tables WIISE

# 5. Query WIISE immunization coverage (note: DTP3 is coded as VACCINECODE='DTPCV3' in AD_COVERAGES; deduplicate by max REVISION_YEAR)
python $cli xmart-query WIISE AD_COVERAGES --filter "COUNTRY eq 'BRA' and YEAR eq 2023 and COVERAGE_CATEGORY eq 'WUENIC'" --select "COUNTRY,YEAR,REVISION_YEAR,VACCINECODE,PERCENTAGE" --top 30

# 6. Query World Health Statistics / SDG indicators in DATA_/RELAY_WHS (DIM_TIME is string '2021'; geography uses M49 '076' or GEO_NAME_SHORT 'Brazil'; unit-typed value cols e.g. RATE_PER_100000_N, PERCENT_POP_N)
python $cli xmart-query DATA_ RELAY_WHS --filter "GEO_NAME_SHORT eq 'Brazil' and DIM_TIME eq '2021' and IND_CODE eq 'SDGSUICIDE' and DIM_AGE eq 'TOTAL'" --select "IND_CODE,GEO_NAME_SHORT,DIM_GEO_CODE_M49,DIM_TIME,DIM_SEX,RATE_PER_100000_N,RATE_PER_100000_NL,RATE_PER_100000_NU" --top 10

# 7. Query WHO Global TB Programme live CSV datasets (dictionary, estimates, notifications, outcomes, budget, policies)
python $cli tb-data estimates --countries BRA,ZAF,MOZ --start-year 2020 --cols country,iso3,year,e_inc_100k,e_inc_100k_lo,e_inc_100k_hi,e_mort_100k,c_cdr

# 8. Query WHO World Health Data Hub (WHDH) COVID-19 & Vaccination feeds (table, daily, vaccination; auto-resolves ISO-3 to country names/ISO-2)
python $cli whdh-covid table --countries BRA,ZAF,IND
```

---

## Step 1: Route to the Right WHO API & Respect Boundaries

### Source Selection & Tie-Breaker Rules

| Backplane | Base URL | Protocol | Primary Domain & Tie-Breaker Rule |
| :--- | :--- | :--- | :--- |
| **1. GHO OData v4 API** | `https://ghoapi.azureedge.net/api/` | OData v4 JSON | **Default for cross-cutting indicator series.** 3,092 indicators (mortality, HIV, TB, malaria, NCDs, tobacco, alcohol, mental health, WASH, air pollution, workforce, UHC/financial protection, IHR SPAR) disaggregated by country, WHO region, year, sex, age, wealth quintile, or residence. |
| **2. WHO xMart4 Public OData APIs** | `https://xmart-api-public.who.int/{MART}/` | OData v4 JSON | **Use when programme-specific tables, WHS/SDG relays, or GHE tables are needed:**<br>– `DATA_` (backs `data.who.int`): Use `RELAY_WHS` for 113 World Health Statistics / SDG indicators (e.g. `SDGSUICIDE` using `RATE_PER_100000_N`, `RATE_PER_100000_NL`, `RATE_PER_100000_NU`; WASH using `PERCENT_POP_N`), `RELAY_3B_DATA` for Triple Billion targets (`COUNT_N`), `RELAY_GHE` for numeric GHE cause-specific counts/YLLs (`VALUE_NUMERIC`), and `RELAY_GHE_DATA` for top causes of death labels (`DEATH_TOP_CAUSE`, `VALUE_LABEL`).<br>– `WIISE`: Tie-breaker winner for detailed immunization data (`AD_COVERAGES` and deduplicated `MT_AD_COV_LONG`).<br>– `FLUMART`: Tie-breaker winner for weekly influenza surveillance (`VIW_FNT_DATADOT`, `VIW_FID_EPI`).<br>– `REFMART`: Master WHO country metadata (`REF_COUNTRY` bridging ISO-3 $\leftrightarrow$ ISO-2 $\leftrightarrow$ UN M49 codes).<br>– `MNCAH`, `NUTRITION` (`NLIS_FACTS_FOR_APP`), `NTD` (`V_FACT_WHO_REGISTRY`), `SCORE`. |
| **3. WHO Global TB Extranet API** | `https://extranet.who.int/tme/generateCSV.asp?ds={ds}` | Live CSV Stream | **Tie-breaker winner for granular TB report variables** (693 variables across `dictionary`, `estimates`, `notifications`, `outcomes`, `budget`, `policies`, including `c_cdr`, MDR/RR-TB cohorts `mdr_coh`, and fallback when GHO `/api/MDG_0000000020` omits a country like `IND`). |
| **4. WHDH COVID-19 Blob Feeds** | `https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/` | CSV Archive Stream | Official WHO COVID-19 daily cases/deaths (`daily`), cumulative summary (`table`), and vaccination uptake (`vaccination`). |

### Mandatory Scope, Staleness & Qualitative Boundaries
- **Negative Boundary (Non-WHO Sources):** Never relabel WHO GHO/xMart figures as World Bank, IMF, OECD, IHME GBD, or national ministry of health data. Also note that the WHO Mortality Database (raw ICD-9/10 death registration files) and ICTRP clinical trials are separate portals not served by these four APIs.
- **Staleness Boundary on WHDH COVID-19 Feeds:** The WHDH COVID-19 and vaccination CSV feeds are frozen historical archives (last updated late 2023 / early 2024). Always report the exact `Date_reported` or `DATE_UPDATED` value and never present them as current real-time surveillance.
- **Qualitative / Policy Indicators (`NumericValue = null`):** Many GHO indicators (e.g. tobacco bans, alcohol tax policies, dementia plans, IHR capacities) store categorical text (`"Yes"`, `"No"`, `"National"`) in `Value` while `NumericValue` is `null`. Never compute numeric averages on them; inspect `Value` directly.

For complete table lists, join keys, and high-frequency indicator codes across all four backplanes, read [references/who_apis_catalog.md](references/who_apis_catalog.md).

---

## Step 2: Follow the 4-Stage GHO Query Protocol (`ghoapi.azureedge.net`)

The GHO API exposes **5 catalog `EntitySet`s** (`Indicator`, `DIMENSION`, `IndicatorDimension`, `RegionCountry`, `Region`) and **3,092 indicator fact `EntitySet`s** (one table per `IndicatorCode`, all sharing an identical 25-column schema).

1. **Discover the `IndicatorCode`:**
   - Fetch `/api/Indicator` and filter client-side (or via `$filter=contains(IndicatorName,'<keyword>')`). Exclude `_ARCHIVED` codes unless historical archived series are explicitly requested.
2. **Check Applicable Stratification Dimensions:**
   - Query `/api/Indicator('<IndicatorCode>')/Dimensions`.
   - **Critical `Dim1` Trap:** Indicators like `WHOSIS_000001` stratify by `SEX` (`Dim1` = `SEX_BTSX`, `SEX_FMLE`, `SEX_MLE`), whereas indicators like `HIV_0000000001`, `MDG_0000000020`, `MALARIA_EST_INCIDENCE`, and `HWF_0001` do not (`Dim1` is `null`). Filtering `Dim1 eq 'SEX_BTSX'` on a non-sex-stratified indicator returns **zero rows**. Always check dimensions first (`who_query.py gho-data` does this automatically).
3. **Resolve Spatial & Dimension Codes:**
   - Country codes use ISO-3 (`SpatialDim eq 'BRA'`) mapped in `/api/RegionCountry`. WHO Regions are `AFR`, `AMR`, `SEAR`, `EUR`, `EMR`, `WPR`, plus `GLOBAL`.
   - Note that when querying without a country filter, `SpatialDim` contains countries, regions, and income groups (`SpatialDimType` = `COUNTRY`, `REGION`, `WORLDBANKINCOMEGROUP`, `GLOBAL`). Filter `SpatialDimType eq 'COUNTRY'` when you want country-level rows only.
4. **Extract Projected Fact Observations with 95% Uncertainty Bounds:**
   - Query `/api/<IndicatorCode>?$filter=...&$select=SpatialDim,SpatialDimType,ParentLocationCode,TimeDim,Dim1,Dim2,NumericValue,Low,High,Value,Comments,Date&$orderby=TimeDim desc`.
   - Always report `NumericValue` alongside its 95% uncertainty interval `[Low, High]` when non-null.
   - **Missing-Country GHO Fallback (e.g., `IND` on `MDG_0000000020`):** Live GHO `/api/MDG_0000000020` currently omits India (`IND` returns 0 rows). Whenever a country is missing from a GHO TB indicator, immediately fall back to the upstream WHO Global TB Programme live CSV (`who_query.py tb-data estimates --countries IND`, columns `e_inc_100k`, `e_inc_100k_lo`, `e_inc_100k_hi`) rather than searching across other GHO tables.

---

## Step 3: Enforce the Six Mandatory GHO Server-Quirk Workarounds

1. **Never call `GET /api/Region`:** The server streams 79 bytes (`{"@odata.context":...,"value":[`) and closes the connection (`JSONDecodeError`). Always use `/api/DIMENSION('REGION')/DimensionValues` or `/api/RegionCountry` (which already contains both `RegionCode` and `RegionName` for every ISO-3 `CountryCode`).
2. **Never use `$apply=groupby(...)` on GHO:** Server-side OData aggregation on `ghoapi.azureedge.net` truncates the HTTP stream right after `"value":[`. Fetch filtered/projected rows with `$filter` + `$select` and aggregate client-side.
3. **Never rely on `$expand` on Fact Tables:** Passing `?$expand=SpatialDimension` on GHO fact tables is a silent no-op. Fetch `/api/RegionCountry` or `/api/DIMENSION('<Code>')/DimensionValues` once and join client-side.
4. **Never use path segment `/$count`:** `GET /api/{Code}/$count` returns `HTTP 404`. Use `?$count=true&$top=1` to read `"@odata.count"` without transferring the full table.
5. **Follow `@odata.nextLink` for Large Queries:** GHO paginates large responses. Always loop on `@odata.nextLink` (or use `$skip`) until `len(rows) >= top` (`who_query.py` handles `@odata.nextLink` automatically).
6. **Escape PowerShell `$` Signs:** In PowerShell, double-quoted strings (`"..."`) interpolate `$filter`, `$select`, and `$top` as empty shell variables, silently corrupting OData URLs (`?=...` -> `HTTP 404`). Always pass OData URLs in single quotes (`'...'`) or via `who_query.py` CLI flags.

---

## Step 4: Schema & Query Rules for xMart4 (`xmart-api-public.who.int`)

- **Server-Side OData Pushdown Works on `xmart-api-public.who.int`:** Always push down `$filter`, `$select`, `$orderby`, and `$top` to the server (and always pass a `timeout=30` on `urllib.request.urlopen`). Never scan all tables in a Mart or fetch an unfiltered `?$top=300` slice on million-row tables (`WIISE/AD_COVERAGES`, `DATA_/RELAY_WHS`, `FLUMART/VIW_FNT_DATADOT`).
- **`WIISE` Immunization Codes (`DTPCV3` = `DTP3`) & `REVISION_YEAR` Deduplication:**
  - In `WIISE/AD_COVERAGES` and `WIISE/MT_AD_COV_LONG`, 3rd-dose DTP coverage is stored under `VACCINECODE eq 'DTPCV3'` (and 1st-dose under `'DTPCV1'`), which maps to `ORIGINALCODE = 'DTP3'` in `WIISE/REF_COVERAGE_CODES` (`MCV1`, `BCG`, `POL3`, `HEPB3`, `HIB3`, `PCV3`, `ROTAC`, `IPV1`, `YFV` use their standard codes). If a user requests `DTP3`, query `VACCINECODE in ('DTPCV3','DTP3')` and map `'DTPCV3'` back to `'DTP3'` in output tables when requested.
  - `WIISE/AD_COVERAGES` stores historical WUENIC revision snapshots (`REVISION_YEAR` = `2023`, `2024`, `2025`) for the same `(COUNTRY, YEAR, COVERAGE_CATEGORY, VACCINECODE)`. Always deduplicate by keeping the row with the maximum `REVISION_YEAR` (or query `WIISE/MT_AD_COV_LONG` where `ISO_3_CODE`, `YEAR`, `COVERAGE_CATEGORY`, `ANTIGEN`, `COVERAGE` is already deduplicated to the latest revision).
- **Watch Column Types, Unit-Typed Value Columns & Join Keys on `DATA_` (`RELAY_WHS`, `RELAY_3B_DATA`, `RELAY_GHE`):**
  - `DIM_TIME` is `Edm.String` (`'2021'`), **not** `Edm.Int32`! Passing unquoted `DIM_TIME eq 2021` returns `HTTP 400 (Incompatible types Edm.String and Edm.Int32)`. Always quote it: `DIM_TIME eq '2021'`.
  - Geography on `DATA_` relay tables uses **UN M49 code** (`DIM_GEO_CODE_M49 eq '076'` for Brazil, `'710'` for South Africa) or short name (`GEO_NAME_SHORT eq 'Brazil'`), not ISO-3 (`BRA`).
  - In `DATA_/RELAY_WHS` (113 World Health Statistics / SDG indicators), values are stored in unit-specific columns alongside lower (`_NL`) and upper (`_NU`) 95% bounds:
    - Rates per 100,000 (e.g. `IND_CODE eq 'SDGSUICIDE'`, stratified by `DIM_SEX` in `'TOTAL'`, `'MALE'`, `'FEMALE'` and `DIM_AGE eq 'TOTAL'`): `RATE_PER_100000_N`, `RATE_PER_100000_NL`, `RATE_PER_100000_NU`.
    - Population percentages (e.g. `WSH_WATER_SAFELY_MANAGED`, `WSH_SANITATION_SAFELY_MANAGED`): `PERCENT_POP_N`, `PERCENT_POP_NL`, `PERCENT_POP_NU`.
    - Rates per 100 / 1,000, counts, and amounts: `RATE_PER_100_N`, `RATE_PER_1000_N`, `COUNT_N`, `AMOUNT_N`.
- **Root Mart Discovery:** Calling `https://xmart-api-public.who.int/` without a Mart code returns `HTTP 400`. Always include the Mart code and `?$format=json` (e.g. `https://xmart-api-public.who.int/WIISE?$format=json`).
