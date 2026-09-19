# Olist E-Commerce Data Pipeline

Module 2 Assignment — a complete data pipeline for the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce): ingestion, a star-schema warehouse, data quality testing, and business analysis.

This README covers setup and repo structure only.

## Architecture

```
Kaggle CSVs -> Meltano -> BigQuery (raw) -> dbt (star schema) -> dbt tests + Great Expectations -> DuckDB/Polars + SQLAlchemy analysis
```
GitHub Actions orchestrates the entire data pipeline from data ingestion to data quality testing.

## Repository structure

```
.
├── README.md
├── requirements.txt
├── .env.example          # copy to .env and fill in; .env itself is git-ignored
├── data/                  # the 9 Olist CSVs (git-ignored, not committed)
├── meltano_ingestion/      # tap-csv, tap-rest-api-msdk -> target-bigquery config
├── dbt_transform/
│   ├── models/
│   │   ├── staging/        # stg_* models
│   │   └── marts/          # fact_*, dim_* models
│   ├── macros/               # e.g. generate_schema_name override for marts dataset
│   └── tests/               # dbt + Great Expectations suites
├── gx/
│   ├── great_expectations.yml   # GX context config (git-ignored, generated locally)
│   ├── scripts/
│   │   └── validations.py       # reusable GX validation logic
│   └── uncommitted/              # generated suites/checkpoints/Data Docs (git-ignored)
├── .github/
│   └── workflows/
│       └── data_pipeline.yml    # GitHub Actions pipeline workflow
├── scripts/
│   └── run_gx_validation_gx.py  # CLI entrypoint run by the GitHub Actions workflow
└── notebooks/
    ├── 01_olist_eda.ipynb        # initial source-dataset exploration: table grain, structure
    ├── 02_rfm_eda_analysis.ipynb # RFM scoring methodology and distribution analysis
    ├── eda_finding.ipynb         # key/grain findings that informed the dbt model design
    ├── olist_GX.ipynb           # interactive development copy of gx/scripts/validations.py
    └── analysis/                  # Jupyter notebooks (owner: D)
        └── .env                   # Environment variables (no keyfile path)
        └── analysis.py            # Runs focused business analyses
        └── config.py              # Configuration (OAuth based)
        └── engine.py              # SQLAlchemy connection with OAuth
        └── queries.py             # Monthly Sales + Products + RFM + Holiday Impact
        └── check_csvs.py          # Validates generated analysis outputs
        └── visualizations.py       # Generates business charts from outputs
```

## Setup

### 1. Accounts (whole team)

- Google Cloud Platform project with BigQuery and billing enabled for the current ingestion configuration. Each team member needs Editor access.
- This GitHub repository, on a single `main` branch.

The configured BigQuery loader uses the Storage Write API by default. The BigQuery sandbox does not support streaming or DML, so it is not sufficient for this setup. Sandbox use would require a separately validated batch-loading and table-replacement configuration. See [BigQuery sandbox limitations](https://docs.cloud.google.com/bigquery/docs/sandbox#limitations).

### 2. Local environment (everyone)

```bash
conda create -n olist-pipeline python=3.11 -y
conda activate olist-pipeline
pip install -r requirements.txt
```

Conda creates and manages the isolated Python environment; pip installs the packages listed in `requirements.txt` inside it. Meltano installs its taps and target separately from the definitions in `meltano_ingestion/meltano.yml`.

You do not need every package in requirements.txt installed for your own work — see the "Who needs this" breakdown in the proposal document's Setup and Prerequisites section. At minimum, everyone needs Python and dbt-bigquery.

### 3. Local destination settings

From the repository root, copy `.env.example` to `.env` if you do not already have a local `.env`. This file stores the BigQuery destination settings and is git-ignored — never commit it.

```bash
cp .env.example .env
```

Set these values in the root `.env`, changing the project or dataset if needed:

```dotenv
GOOGLE_CLOUD_PROJECT=olist-data-pipeline-507001
BIGQUERY_DATASET=olist_raw
```

The loader in `meltano_ingestion/meltano.yml` references these variables. The ingestion commands in step 8 explicitly load this root `.env`. Google authentication is configured separately in step 5, while dbt uses its own `profiles.yml` from step 6.

### 4. Data

Download the 9 Olist CSVs from Kaggle into `data/` (this folder is git-ignored). Only the Meltano ingestion step reads from here directly.


### 5. GCP authentication

Run the following command in the terminal:

- gcloud auth application-default login

Follow the link provided in the terminal and authenticate with your Google account.


### 6. dbt profile setup

Create `dbt_transform/profiles.yml`. This file is git-ignored, so each team member maintains their own local configuration.

Use a unique development dataset for your local dbt runs, replacing `yourname` below with your own name or identifier.

```yaml
dbt_transform:
  target: dev

  outputs:
    dev:
      type: bigquery
      method: oauth
      project: olist-data-pipeline-507001
      dataset: dbt_<your_name>
      location: US
      threads: 4

    prod:
      type: bigquery
      method: oauth
      project: olist-data-pipeline-507001
      dataset: olist_staging
      location: US
      threads: 4
```

### 7. Meltano setup / Tap & Target setup for CSV and REST API

After cloning the repository, install the plugins from the existing project configuration:

- cd meltano_ingestion

- meltano install

The project initialization and `meltano add` commands below document how the project was originally set up. They are only needed when rebuilding the Meltano project from scratch.

- pip install meltano                                          # Install Meltano.

- meltano init meltano_ingestion                               # Create the meltano_ingestion project folder.

- cd meltano_ingestion                                         # Navigate to the meltano_ingestion project folder.


### Tap and Target for CSV

Run the following commands when adding the CSV tap and BigQuery target to a new Meltano project:

- meltano add tap-csv --variant meltanolabs                    # Add the MeltanoLabs implementation of the CSV tap for reading CSV files from the local directory.

- meltano add target-bigquery --variant=z3z1ma                 # Install the Singer target for loading extracted records into Google BigQuery.

Note:
The target keeps "setuptools<80" in `pip_url`: git+https://github.com/z3z1ma/target-bigquery.git setuptools<80

The target configuration in `meltano.yml` is:

    config:
      project: ${GOOGLE_CLOUD_PROJECT}
      dataset: ${BIGQUERY_DATASET}
      location: US
      denormalized: true
      threads: 1

The CSV tap configuration in `meltano.yml` is:

    config:
      add_metadata_columns: true
      files:
      - entity: raw_orders
        path: ../data/olist_orders_dataset.csv
        keys: [order_id]
        encoding: utf-8-sig
      - entity: raw_order_items
        path: ../data/olist_order_items_dataset.csv
        keys: [order_id, order_item_id]
        encoding: utf-8-sig
      - entity: raw_customers
        path: ../data/olist_customers_dataset.csv
        keys: [customer_id]
        encoding: utf-8-sig
      - entity: raw_sellers
        path: ../data/olist_sellers_dataset.csv
        keys: [seller_id]
        encoding: utf-8-sig
      - entity: raw_products
        path: ../data/olist_products_dataset.csv
        keys: [product_id]
        encoding: utf-8-sig
      - entity: raw_category_translation
        path: ../data/product_category_name_translation.csv
        keys: [product_category_name]
        encoding: utf-8-sig
      - entity: raw_geolocation_dataset
        path: ../data/olist_geolocation_dataset.csv
        keys: []
        encoding: utf-8-sig
      - entity: raw_order_payments_dataset
        path: ../data/olist_order_payments_dataset.csv
        keys: [order_id, payment_sequential]
        encoding: utf-8-sig
      - entity: raw_order_reviews_dataset
        path: ../data/olist_order_reviews_dataset.csv
        keys: [review_id, order_id]
        encoding: utf-8-sig


- meltano --env-file ../.env run tap-csv target-bigquery       # Extract the CSV data and load it into BigQuery.


### Tap and Target for REST API

Run the following commands when adding the REST API tap to a new Meltano project:

- meltano add tap-rest-api-msdk                                # Add the REST API tap to the Meltano project.

- meltano install tap-rest-api-msdk                            # Install the extractor and its required packages.

Note:
The tap keeps "setuptools<80" in `pip_url`: tap-rest-api-msdk setuptools<80

The REST API configuration in `meltano.yml` is:

    config:
      api_url: https://brasilapi.com.br/api
      streams:
      - name: raw_holidays_2017
        path: /feriados/v1/2017
        records_path: $[*]
        primary_keys: [date]
      - name: raw_holidays_2018
        path: /feriados/v1/2018
        records_path: $[*]
        primary_keys: [date]

- meltano --env-file ../.env run tap-rest-api-msdk target-bigquery  # Extract the REST API data and load it into BigQuery.

### 8. Running dbt models and tests

From `dbt_transform/` (profile set up per section 6):

- `dbt run` - build all staging, intermediate, and mart models.
- `dbt test` - run all schema tests (not_null, unique, relationships, accepted_values, compound-uniqueness, mart-to-staging row reconciliation) plus the unit tests below.
- `dbt test --select test_type:unit` - run only the unit tests (fixture-based, no warehouse data needed): `int_orders` delivery/customer-type logic, `dim_product` category-fallback logic.
- `dbt test --select test_type:singular` - run standalone tests, e.g. `assert_dim_customer_matches_unique_customer_count`, which checks `dim_customer` row count against `COUNT(DISTINCT customer_unique_id)` in `stg_customers` (a plain row-count match doesn't apply here since `dim_customer` collapses repeat customers).
- `dbt test --select stg_orders` (or any model name) - scope to one model while iterating.

### 9. Great Expectations validations

The GX checks live under `gx/` (context config, generated suites/checkpoints) and `gx/scripts/validations.py` (the reusable validation logic). `notebooks/olist_GX.ipynb` is the interactive development copy of the same logic; `scripts/run_gx_validation_gx.py` is the CLI entrypoint an orchestrator (or you, locally) actually runs.

#### Data quality testing strategy

Test ownership is split between dbt and Great Expectations, not duplicated:

- **dbt** owns deterministic warehouse correctness: primary/foreign keys, required fields, relationships, accepted values, model grain, join fanout, and reconciliation between staging and marts.
- **Great Expectations** owns business plausibility and monitoring on raw/staging data: numeric ranges, timestamp sequences, completeness rates, geographic plausibility, and distribution drift over time — plus a lightweight mart sanity check (row count and a value-column sum vs. a baseline) as an independent smoke test that a mart loaded correctly end-to-end.

Each GX check is one of two severities:

- **Critical** — zero-tolerance structural issues (e.g. review scores outside 1-5, negative monetary values, invalid state/status codes). A `RuntimeError` blocks the pipeline by default; set `GX_RAISE_ON_CRITICAL_FAILURE=false` to opt out (e.g. local/dev iteration).
- **Observation** — known or monitored imperfections that don't make the data unusable (e.g. a small percentage of missing approval timestamps, review comments). These are logged, not blocking.

Known baseline anomalies in the raw Olist data — profiled directly from source, not defects introduced by the transform layer, and not something a passing/failing test should be surprised by:

| Finding | Detail |
|---|---|
| Duplicate geolocation rows | 261,831 exact duplicate rows across 19,015 distinct ZIP prefixes in raw geolocation data — staging is a pass-through of the raw grain; dbt's `int_geolocation` model aggregates to one row per ZIP for the mart. |
| Repeated `review_id` values | 814 rows — correct review grain is the compound key `(review_id, order_id)`, so `review_id` alone is not expected to be unique. |
| Products missing category data | 623 rows use a category absent from the translation table; 610 rows are missing other descriptive fields. |
| Orphaned ZIP references | 278 customer rows and 7 seller rows reference a ZIP prefix absent from geolocation data. |
| Timestamp/payment inconsistencies | 166 carrier timestamps precede the purchase timestamp; 23 customer-delivery timestamps precede carrier delivery; 1,190 order payment totals differ from item price + freight by more than 1 cent. |

These are tracked as observation-level checks (or excluded from a `unique`/`not_null` test where the anomaly makes one inapplicable), not treated as bugs to silently "fix" in the transform layer, unless the team agrees on an explicit exception rule.

Run it from the repository root, with the `olist-pipeline` conda environment active:

```bash
GX_ENV=prod GX_DATA_LAYER=staging GX_RAISE_ON_CRITICAL_FAILURE=true python -m scripts.run_gx_validation_gx
```

Environment variables (all optional; defaults shown):

| Variable | Default | Purpose |
|---|---|---|
| `GX_ENV` | `dev` | `dev` / `staging` / `prod` — selects which dataset suffix to read. `prod` reads the bare dataset name (e.g. `olist_staging`); any other value reads `<dataset>_<env>` (e.g. `olist_staging_dev`). |
| `GX_DATA_LAYER` | `staging` | `raw` or `staging` — which layer's tables to validate. |
| `GX_SOURCE_MODE` | `bigquery` | `bigquery` or `csv`. `csv` reads the local files in `data/` instead of BigQuery, and only works with `GX_DATA_LAYER=raw`. |
| `GX_CONTEXT_MODE` | `file` | `file` persists suites/checkpoints/Data Docs under `gx/`; `ephemeral` writes nothing to disk. |
| `GX_RAISE_ON_CRITICAL_FAILURE` | `true` | Blocks by default: a critical check failure raises and exits non-zero. Set `false` to opt out (e.g. local/dev iteration). |
| `GX_RAISE_ON_MART_FAILURE` | `false` | Set `true` to also block if any mart sanity check (row count / value-column sum, see `MART_SANITY_CHECKS` in `validations.py`) fails. |
| `GOOGLE_CLOUD_PROJECT` | `olist-data-pipeline-507001` | Same variable as the root `.env` (step 3). |

Data Docs (a browsable HTML validation report) refresh under `gx/uncommitted/data_docs/` on every run — open `gx/uncommitted/data_docs/local_site/index.html` locally to inspect results.

Requires the same GCP authentication as dbt (step 5) — the script reads directly from BigQuery and does not set up its own credentials.

### 10. GitHub Actions orchestration

The complete data pipeline is orchestrated through a single GitHub Actions workflow: `.github/workflows/data_pipeline.yml`.

The workflow connects the ingestion, transformation, testing, and data quality stages:

```text
Kaggle CSVs
    ↓
Meltano → BigQuery raw (`olist_raw`)
    ↓
dbt → staging / intermediate / marts
    ↓
dbt tests
    ↓
Great Expectations validations
```

The workflow runs the following stages in sequence:

1. Checks out the repository and sets up the Python 3.11 environment.
2. Authenticates to Google Cloud using GitHub Actions Workload Identity Federation.
3. Downloads the Olist CSV files into the git-ignored `data/` directory.
4. Runs Meltano to ingest the Olist CSVs and BrasilAPI holiday data into the BigQuery raw layer.
5. Runs `dbt deps` to install the required dbt packages, followed by `dbt run` to build the staging, intermediate, and mart models.
6. Runs `dbt test` to validate the transformed data.
7. Runs Great Expectations to perform additional data quality validations.

Step 3 calls the Kaggle API directly and needs Kaggle credentials, which the workflow doesn't set up yet. Add `KAGGLE_USERNAME` and `KAGGLE_KEY` as repo secrets and pass them to the `curl` call (`-u "$KAGGLE_USERNAME:$KAGGLE_KEY"`) before this step will run successfully.

GitHub Actions provides the automation layer within the GitHub repository. It supports event-based and scheduled execution, dependency management between workflow steps, execution logs for monitoring, and workflow status and failure reporting. If a required step fails, the workflow is marked as failed and subsequent dependent steps do not proceed. The run logs can then be used to identify the failed stage and investigate the error.

#### GitHub Actions triggers

GitHub Actions supports different triggers depending on how a workflow should be executed. For example, scheduled execution can be configured using a cron schedule:

```
on:
  schedule:
    - cron: "0 0 * * *"
```

A workflow can also be configured to run automatically when code is pushed to the repository or when a pull request is opened or updated:

```
on:
  push:
    branches: [main]

  pull_request:
    branches: [main]
```

These triggers can be used to support continuous integration and continuous delivery (CI/CD), such as automatically testing code changes, validating the pipeline, or running scheduled data workflows.

For this project, the workflow is currently configured with `workflow_dispatch`, allowing the complete data pipeline to be triggered manually from the GitHub Actions interface:

```
on:
  workflow_dispatch:
```

### 11. Analysis setup.

Requires the same GCP authentication as dbt (step 5) — `engine.py` connects with the same application-default credentials.

The queried mart tables (`notebooks/analysis/config.py`): `dim_customer`, `dim_date`, `dim_geolocation`, `dim_product`, `dim_seller`, `fact_order_items`, `fact_orders`, `fact_payments`, `fact_reviews`, `fct_customer_rfm`.

- Add a .env file under the notebooks/analysis folder with below details

--GCP Configuration--

PROJECT_ID=olist-data-pipeline-507001
DATASET=olist_mart

--Pandas Display Settings--

PD_MAX_ROWS=100
PD_MAX_COLUMNS=20

--Analysis--

RFM_TOP_CUSTOMERS_LIMIT=100
OUTPUT_DIR=output
CHART_DIR=charts

- Run in the terminal "python analysis.py && python check_csvs.py && python visualizations.py"
