# WHO Public APIs: Complete Reference Catalog

This reference documents the schemas, endpoints, join keys, and high-frequency indicator codes across all four public World Health Organization (WHO) API backplanes.

## Table of Contents
1. [Backplane 1: WHO Global Health Observatory (GHO) OData v4 API](#1-backplane-1-who-global-health-observatory-gho-odata-v4-api)
2. [Backplane 2: WHO xMart4 Enterprise Data Warehouse Public OData APIs](#2-backplane-2-who-xmart4-enterprise-data-warehouse-public-odata-apis)
3. [Backplane 3: WHO Global Tuberculosis Programme CSV API](#3-backplane-3-who-global-tuberculosis-programme-csv-api)
4. [Backplane 4: WHO World Health Data Hub (WHDH) COVID-19 & Vaccination Feeds](#4-backplane-4-who-world-health-data-hub-whdh-covid-19--vaccination-feeds)
5. [High-Frequency GHO Indicator Codes by Domain](#5-high-frequency-gho-indicator-codes-by-domain)

---

## 1. Backplane 1: WHO Global Health Observatory (GHO) OData v4 API

- **Base URL:** `https://ghoapi.azureedge.net/api/`
- **Schema URL:** `https://ghoapi.azureedge.net/api/$metadata` (12.17 MB EDMX XML)
- **Total EntitySets:** 3,097 (5 Catalog EntitySets + 3,092 Indicator Fact EntitySets)

### Catalog EntitySets
- `/api/Indicator`: `IndicatorCode` (key), `IndicatorName`, `Language` (`"EN"`). Navigation: `/api/Indicator('{Code}')/Dimensions`.
- `/api/DIMENSION`: `Code` (key), `Title` (202 dimensions). Navigation: `/api/DIMENSION('{Code}')/DimensionValues`.
- `/api/IndicatorDimension`: `IndicatorCode`, `Dimension`, `DimensionName`, `Language`.
- `/api/RegionCountry`: `CountryCode` (ISO-3 key, 266 countries/areas), `CountryName`, `RegionCode` (`AFR`, `AMR`, `SEAR`, `EUR`, `EMR`, `WPR`), `RegionName`, `Language`.
- `/api/Region`: **BROKEN ON SERVER** (stream truncates at byte 79). Always use `/api/DIMENSION('REGION')/DimensionValues`.

### 25-Column Fact Schema (`/api/{IndicatorCode}`)
- **Identity (2):** `Id` (`Edm.Int64`), `IndicatorCode` (`Edm.String`)
- **Spatial (4):** `SpatialDimType` (`COUNTRY`, `REGION`, `GLOBAL`, `WORLDBANKINCOMEGROUP`, `UNREGION`, `DHSMICSGEOREGION`), `SpatialDim` (ISO-3 or region code), `ParentLocationCode`, `ParentLocation`
- **Temporal (5):** `TimeDimType` (`YEAR`), `TimeDim` (`Edm.Int32`), `TimeDimensionValue`, `TimeDimensionBegin`, `TimeDimensionEnd`
- **Disaggregation (8):** `Dim1Type`, `Dim1`, `Dim2Type`, `Dim2`, `Dim3Type`, `Dim3`, `DataSourceDimType`, `DataSourceDim`
- **Values & 95% Uncertainty Bounds (4):** `Value` (display string), `NumericValue` (`Edm.Decimal`), `Low` (`Edm.Decimal`), `High` (`Edm.Decimal`)
- **Audit (2):** `Comments`, `Date` (`Edm.DateTimeOffset`)

---

## 2. Backplane 2: WHO xMart4 Enterprise Data Warehouse Public OData APIs

- **Base Pattern:** `https://xmart-api-public.who.int/{MART}/{ENTITY_SET}`
- **Service Document:** `https://xmart-api-public.who.int/{MART}?$format=json`
- **Schema Document:** `https://xmart-api-public.who.int/{MART}/$metadata`
- **Supported OData v4 Query Parameters:** `$filter`, `$select`, `$orderby`, `$top`, `$skip`, `$count=true`, `$apply=groupby(...)`.

### Verified Public xMart4 Marts & Join Keys

| Mart Code | Domain | EntitySets | Key Tables, Country/Time Join Keys & Type Caveats |
| :--- | :--- | :---: | :--- |
| **`DATA_`** | World Health Data Hub (`data.who.int`) | 93 | – `RELAY_WHS`: 113 World Health Statistics / SDG indicators (e.g. `SDGSUICIDE`, `MDG_0000000020`, `WSH_WATER_SAFELY_MANAGED`, `WSH_SANITATION_SAFELY_MANAGED`, `NUTRITION_WH_2`, `SDGNTDTREATMENT`).<br>  *Join/Filter Keys:* `DIM_GEO_CODE_M49` (`Edm.String`, e.g. `'076'` for Brazil, `'710'` for South Africa), `GEO_NAME_SHORT` (`'Brazil'`), `DIM_TIME` (**`Edm.String`** — must be quoted: `DIM_TIME eq '2021'`), `DIM_SEX` (`'TOTAL'`, `'MALE'`, `'FEMALE'`), `DIM_AGE` (`'TOTAL'`), `DIM_DEG_URB`, `DIM_POP_WEALTH_QUINTILE`.<br>  *Unit-Typed Value Columns:* `RATE_PER_100000_N` (`_NL`, `_NU`), `PERCENT_POP_N` (`_NL`, `_NU`), `RATE_PER_100_N` (`_NL`, `_NU`), `RATE_PER_1000_N`, `COUNT_N`, `AMOUNT_N`.<br>– `RELAY_GHE`: Numeric Global Health Estimates (`IND_CODE` in `'AVERAGE_DEATH'`, `'DEATH_RANK_CAUSE'`, `'DEATHS_CONTRIBUTION'`, `'TOTAL_YLL_COUNT'`, `'WHOSIS_000007'`, `'WHOSIS_000015'`; values in `VALUE_NUMERIC`, `DIM_1_CODE eq 'DIM_GHECAUSE'`, `DIM_GEO_CODE_M49`).<br>– `RELAY_GHE_DATA`: Top causes of death text labels (`IND_CODE eq 'DEATH_TOP_CAUSE'`, `VALUE_LABEL`, `TEXT_N`; note `COUNT_N` and `RATE_PER_100_N` are `null` here).<br>– `RELAY_3B_DATA`: Triple Billion targets (`DIM_GEO_CODE_M49`, `GEO_NAME_SHORT`, `DIM_TIME` string-typed, `TRIPLE_BILLION`, `COUNT_N`, `COUNT_NL`, `COUNT_NU`).<br>– `RELAY_TB_DATA`, `RELAY_GLASS_AMR`, `WHO_COUNTRY_OFFICE_FULL`. |
| **`WIISE`** | WHO Immunization Data Portal (WUENIC / JRF) | 138 | – `AD_COVERAGES`: Official vaccine coverage.<br>  *Join/Filter Keys:* `COUNTRY` (ISO-3 string, e.g. `'BRA'`), `WHO_REGION` (`'AMRO'`, `'AFRO'`, `'EURO'`, `'SEARO'`, `'EMRO'`, `'WPRO'`), `YEAR` (`Edm.Int32`, e.g. `2023`), `REVISION_YEAR` (`Edm.Int32` — **deduplicate by keeping max `REVISION_YEAR`**), `COVERAGE_CATEGORY` (`'WUENIC'`, `'ADMIN'`, `'OFFICIAL'`), `VACCINECODE` (**note: 3rd-dose DTP is `'DTPCV3'` and 1st-dose is `'DTPCV1'`, mapped from `ORIGINALCODE='DTP3'`/`'DTP1'` in `REF_COVERAGE_CODES`**; `'MCV1'`, `'MCV2'`, `'BCG'`, `'POL3'`, `'HEPB3'`, `'HIB3'`, `'PCV3'`, `'ROTAC'`, `'IPV1'`, `'YFV'`), `PERCENTAGE`, `DOSES`, `TARGETNUMBER`.<br>– `MT_AD_COV_LONG`: Pre-deduplicated latest revision coverage table (`ISO_3_CODE`, `YEAR`, `COVERAGE_CATEGORY`, `ANTIGEN` where DTP3 is `'DTPCV3'`, `COVERAGE`).<br>– `AD_INCIDENCES`, `AD_OUTBREAKS`, `AD_SCHEDULES`, `AD_VACCINE_INTRODUCTIONS`, `REF_VACCINES`, `REF_COVERAGE_CODES`. |
| **`FLUMART`** | Global Influenza Surveillance (GISRS / FluNet / FluID) | 21 | – `VIW_FNT_DATADOT` & `VIW_FNT`: Weekly virological influenza surveillance.<br>  *Join/Filter Keys:* `COUNTRY_CODE` (ISO-3 string, e.g. `'BRA'`, `'ETH'`), `WHOREGION` (`'AMR'`, `'AFR'`), `ISO_YEAR` (`Edm.Int32`), `ISO_WEEK` (`Edm.Int32`), `ISO_WK_SDATE`.<br>– `VIW_FID_EPI`: FluID epidemiological ILI/SARI surveillance (`COUNTRY_CODE`, `ISO_YEAR`, `ISO_WEEK`). |
| **`REFMART`** | WHO Master Reference Data Mart | 18 | – `REF_COUNTRY`: Canonical country registry and ID bridge (249 countries/territories).<br>  *Join/Filter Keys:* `CODE_ISO_3` (`'BRA'`), `CODE_ISO_2` (`'BR'`), `GEO_M49_CODE` (`'076'`), `CODE_ISO_NUMERIC` (`76`), `NAME_SHORT_EN`, `NAME_FORMAL_EN`, `CAPITAL_CITY`, `GRP_WB_INCOME` (`'HIC'`, `'UMC'`, `'LMC'`, `'LIC'`), `GRP_WHO_REGION` (`'AFR'`, `'AMR'`, `'SEAR'`, `'EUR'`, `'EMR'`, `'WPR'`).<br>– `REF_POPULATION`: Official reference populations.<br>– `COUNTRY_TO_M49_ISO3_LOOKUP`: Direct M49 $\leftrightarrow$ ISO-3 crosswalk. |
| **`MNCAH`** | Maternal, Newborn, Child & Adolescent Health | 109 | – `MCA_FACT_DATA_AGGREGATED`, `FACT_DATA_MCA`, `SRHR_SelfCare_Main_Data`, `BD_FACT`. |
| **`NUTRITION`** | Nutrition Landscape Information System (NLIS) | 53 | – `NLIS_FACTS_FOR_APP`: Country nutrition indicators.<br>  *Join/Filter Keys:* `SpatialDimensionValueCode` (ISO-3, e.g. `'BRA'`), `YearNumber` (`Edm.Int32`), `IndicatorCode` (`'NLIS_NU_CA_011'`), `FactValueNumeric`, `FactValueString`.<br>– `GTT_FACT`: Global Nutrition Targets tracking (stunting, anaemia, low birthweight, exclusive breastfeeding, overweight). |
| **`NTD`** | Neglected Tropical Diseases Registry | 4 | – `V_FACT_WHO_REGISTRY`: Certification and elimination status.<br>  *Join/Filter Keys:* `CODE_ISO_3` (`'BRA'`, `'SUR'`), `GRP_WHO_REGION`, `DISEASE_CODE` (`'DRA'`, `'TRA'`, `'ONC'`, `'LF'`), `DISEASE`, `STATUS` (`'CERTIFIED'`, `'ENDEMIC'`), `YEAR` (`Edm.Int32`), `HAS_ELIMINATED`. |
| **`SCORE`** | Health Data Technical Package & Pulse Surveys | 35 | – `PULSE_COUNTRY`, `PULSE_EHS`, `PULSE_NCD`: Essential health services continuity survey rounds. |

---

## 3. Backplane 3: WHO Global Tuberculosis Programme CSV API

- **Base URL:** `https://extranet.who.int/tme/generateCSV.asp?ds={dataset}` (Note: `ds=` is case-sensitive; invalid dataset names return an empty 200 HTML response).
- **Verified `ds=` Dataset Codes:**
  - `dictionary`: Variable dictionary (`variable_name`, `dataset`, `code_list`, `definition`) covering 693 TB variables across 19 categories. Note: has no `iso3` or `year` column; filter with `--keyword`.
  - `estimates`: Annual TB burden estimates. Join keys: `iso3` (`BRA`), `iso2` (`BR`), `country` (`Brazil`), `g_whoregion` (`AMR`), `year` (`2024`). Key metrics: `e_pop_num`, `e_inc_100k`, `e_inc_100k_lo`, `e_inc_100k_hi`, `e_inc_num`, `e_inc_tbhiv_100k`, `e_mort_exc_tbhiv_100k`, `e_mort_tbhiv_100k`, `e_mort_100k`, `c_cdr`.
  - `notifications`: Case notifications stratified by bacteriologically confirmed vs clinically diagnosed, pulmonary vs extrapulmonary, age, sex, and HIV status (`iso3`, `year`, `new_sp`, `new_sn`, `new_ep`, `c_newinc`, `newrel_hivpos`).
  - `outcomes`: Treatment outcomes cohorts (`iso3`, `year`, `new_sp_coh`, `new_sp_cur`, `new_sp_cmplt`, `new_sp_died`, `new_sp_fail`, `c_new_tsr`, `mdr_coh`, `xdr_coh`).
  - `budget`: National TB programme budgets (`iso3`, `year`, `tx_dstb`, `budget_cpp_dstb`, `tx_mdr`, `budget_cpp_mdr`, `tot_budget`).
  - `policies`: National TB policies, prison/HCW screening, and preventive therapy guidelines (`iso3`, `year`).

---

## 4. Backplane 4: WHO World Health Data Hub (WHDH) COVID-19 & Vaccination Feeds

*(Historical archive feeds; always report `Date_reported` / `DATE_UPDATED`)*

- **1. Global Cumulative Summary Table (`table`):**
  - URL: `https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-table-data.csv`
  - **Key Trap:** Has **no `ISO3` or `ISO2` column**! Uses full country name in `Name` (`Brazil`, `South Africa`, `Global`) and full region name in `WHO Region` (`Americas`, `Africa`, `Europe`, etc.). `who_query.py whdh-covid table --countries BRA,ZAF` automatically resolves ISO-3/ISO-2 codes to country names via `REFMART/REF_COUNTRY`.
  - Columns: `Name,WHO Region,Cases - cumulative total,Cases - cumulative total per 100000 population,Cases - newly reported in last 7 days,Cases - newly reported in last 7 days per 100000 population,Cases - newly reported in last 24 hours,Deaths - cumulative total,Deaths - cumulative total per 100000 population,Deaths - newly reported in last 7 days,Deaths - newly reported in last 7 days per 100000 population,Deaths - newly reported in last 24 hours`
- **2. Daily Cases & Deaths by Country (`daily`):**
  - URL: `https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-data.csv`
  - Key Columns: `Country_code` (**ISO-2**, e.g. `BR`, `ZA`), `Country` (`Brazil`, `South Africa`), `WHO_region` (`AMRO`, `AFRO`), `Date_reported` (`YYYY-MM-DD`), `New_cases`, `Cumulative_cases`, `New_deaths`, `Cumulative_deaths`.
- **3. Global COVID-19 Vaccination Uptake (`vaccination`):**
  - URL: `https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/vaccination-data.csv`
  - Key Columns: `ISO3` (**ISO-3**, e.g. `BRA`, `ZAF`), `COUNTRY` (`Brazil`, `South Africa`), `WHO_REGION` (`AMRO`, `AFRO`), `DATE_UPDATED`, `TOTAL_VACCINATIONS`, `PERSONS_VACCINATED_1PLUS_DOSE`, `TOTAL_VACCINATIONS_PER100`, `PERSONS_VACCINATED_1PLUS_DOSE_PER100`, `PERSONS_LAST_DOSE`, `PERSONS_LAST_DOSE_PER100`, `PERSONS_BOOSTER_ADD_DOSE_PER100`.

---

## 5. High-Frequency GHO Indicator Codes by Domain

| Domain | `IndicatorCode` | Indicator Name | Uses `SEX` (`Dim1`)? |
| :--- | :--- | :--- | :---: |
| **Demographics & Mortality** | `WHOSIS_000001` | Life expectancy at birth (years) | Yes (`SEX_BTSX`, `SEX_FMLE`, `SEX_MLE`) |
| | `WHOSIS_000002` | Healthy life expectancy (HALE) at birth (years) | Yes |
| | `WHOSIS_000015` | Life expectancy at age 60 (years) | Yes |
| | `MDG_0000000001` | Infant mortality rate (per 1,000 live births) | Yes |
| | `MDG_0000000007` | Under-five mortality rate (per 1,000 live births) | Yes |
| | `MDG_0000000026` | Maternal mortality ratio (per 100,000 live births) | No (`Dim1` is `null`) |
| **HIV / AIDS** | `HIV_0000000001` | Estimated number of people (all ages) living with HIV | No (`Dim1` is `null`) |
| | `HIV_0000000026` | Number of new HIV infections | No (`Dim1` is `null`) |
| | `HIV_0000000006` | Number of people dying from HIV-related causes | No (`Dim1` is `null`) |
| **Tuberculosis** | `MDG_0000000020` | Incidence of tuberculosis (per 100,000 population per year) | No (`Dim1` is `null`) |
| | `TB_e_inc_num` | Number of incident tuberculosis cases | No (`Dim1` is `null`) |
| | `TB_e_inc_tbhiv_100k` | Incidence of tuberculosis (per 100,000) (HIV-positive cases) | No (`Dim1` is `null`) |
| **Malaria** | `MALARIA_EST_INCIDENCE` | Estimated malaria incidence (per 1,000 population at risk) | No (`Dim1` is `null`) |
| | `MALARIA_EST_DEATHS` | Estimated number of malaria deaths | No (`Dim1` is `null`) |
| **UHC & Health Financing** | `FINPROTECTION_CATA_TOT_10_POP` | Population with household health expenditures >10% of income (%) | Optional (`RESIDENCEAREATYPE`) |
| | `GHED_CHEGDP_SHA2011` | Current health expenditure (CHE) as % of GDP | No |
| **Health Workforce** | `HWF_0001` | Medical doctors (per 10,000 population) | No |
| | `HWF_0006` | Nursing and midwifery personnel (per 10,000 population) | No |
| **NCDs & Mental Health** | `MH_12` | Age-standardized suicide rates (per 100,000 population) | Yes |
| | `NCD_BMI_30A` | Prevalence of obesity among adults, BMI >= 30 (age-standardized) (%) | Yes |
