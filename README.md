# Olist E-Commerce Data Pipeline

Module 2 Assignment — a complete data pipeline for the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce): ingestion, a star-schema warehouse, data quality testing, and business analysis.

This README covers setup and repo structure only.

## Architecture

```
Kaggle CSVs -> Meltano -> BigQuery (raw) -> dbt (star schema) -> dbt tests + Great Expectations -> DuckDB/Polars + SQLAlchemy analysis
```

The whole pipeline is orchestrated by Dagster.

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
│   ├── great_expectations.yml   # GX context config (tracked)
│   ├── scripts/
│   │   └── validations.py       # reusable GX validation logic
│   └── uncommitted/              # generated suites/checkpoints/Data Docs (git-ignored)
├── scripts/
│   └── run_gx_validation_gx.py  # CLI entrypoint an orchestrator triggers
├── orchestration/
│   └── dagster/              # Dagster assets and schedule
└── notebooks/
    ├── olist_GX.ipynb           # interactive development copy of gx/scripts/validations.py
    └── analysis/               # Jupyter notebooks
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


### 8. Great Expectations validations

The GX checks live under `gx/` (context config, generated suites/checkpoints) and `gx/scripts/validations.py` (the reusable validation logic). `notebooks/olist_GX.ipynb` is the interactive development copy of the same logic; `scripts/run_gx_validation_gx.py` is the CLI entrypoint an orchestrator (or you, locally) actually runs.

#### Data quality testing strategy

Test ownership is split between dbt and Great Expectations, not duplicated:

- **dbt** owns deterministic warehouse correctness: primary/foreign keys, required fields, relationships, accepted values, model grain, join fanout, and reconciliation between staging and marts.
- **Great Expectations** owns business plausibility and monitoring on raw/staging data: numeric ranges, timestamp sequences, completeness rates, geographic plausibility, and distribution drift over time — plus a lightweight mart sanity check (row count and a value-column sum vs. a baseline) as an independent smoke test that a mart loaded correctly end-to-end.

Each GX check is one of two severities:

- **Critical** — zero-tolerance structural issues (e.g. review scores outside 1-5, negative monetary values, invalid state/status codes). A `RuntimeError` blocks the pipeline when `GX_RAISE_ON_CRITICAL_FAILURE=true`.
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
| `GX_RAISE_ON_CRITICAL_FAILURE` | `false` | Set `true` to make a critical check failure exit non-zero. Required for a critical failure to actually block an orchestrator/CI run — without it the script always exits `0`. |
| `GX_RAISE_ON_MART_FAILURE` | `false` | Set `true` to also block if any mart sanity check (row count / value-column sum, see `MART_SANITY_CHECKS` in `validations.py`) fails. |
| `GOOGLE_CLOUD_PROJECT` | `olist-data-pipeline-507001` | Same variable as the root `.env` (step 3). |

Data Docs (a browsable HTML validation report) refresh under `gx/uncommitted/data_docs/` on every run — open `gx/uncommitted/data_docs/local_site/index.html` locally to inspect results.

Requires the same GCP authentication as dbt (step 5) — the script reads directly from BigQuery and does not set up its own credentials.
