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
├── meltano_ingestion/      # tap-csv, tap-rest-api-msdk -> target-bigquery config (owner: A)
├── dbt_transform/
│   ├── models/
│   │   ├── staging/        # stg_* models (owner: B)
│   │   └── marts/          # fact_*, dim_* models (owner: B)
│   ├── macros/               # e.g. generate_schema_name override for marts dataset
│   └── tests/               # dbt + Great Expectations suites (owner: C)
├── orchestration/
│   └── dagster/              # Dagster assets and schedule (owner: E)
└── notebooks/
    └── analysis/               # Jupyter notebooks (owner: D)
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

Download the 9 Olist CSVs from Kaggle into `data/` (this folder is git-ignored). Only the Meltano ingestion step (owner: A) reads from here directly.


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

### 7. Install the existing Meltano project

After cloning the repository and completing steps 1–6, activate the Python environment created in step 2. From the repository root, install the plugins already defined in the project:

```bash
conda activate olist-pipeline
cd meltano_ingestion
meltano install
```

`meltano install` installs `tap-csv`, `tap-rest-api-msdk`, and `target-bigquery` from the committed project configuration. The project and plugin definitions are already included in the repository; project initialization and plugin addition are not part of clone setup. See the [Meltano CLI documentation](https://docs.meltano.com/reference/command-line-interface#install).

Keep stream definitions, file paths, plugin dependencies, and loader settings in [`meltano_ingestion/meltano.yml`](meltano_ingestion/meltano.yml). This is the source of truth for ingestion configuration.

### 8. Tap and target for CSV

The project uses the MeltanoLabs variant of `tap-csv` to read local CSV files and the z3z1ma variant of `target-bigquery` to load them into BigQuery.

The following commands were used to add these plugins when the project was created. They are only needed if the Meltano project is rebuilt from scratch; after cloning, use `meltano install` from step 7.

```bash
meltano add tap-csv --variant meltanolabs
meltano add target-bigquery --variant=z3z1ma
```

The target keeps `setuptools<80` in its `pip_url`. Its configuration in `meltano.yml` is:

```yaml
config:
  project: ${GOOGLE_CLOUD_PROJECT}
  dataset: ${BIGQUERY_DATASET}
  location: US
  denormalized: true
  threads: 1
```

The CSV tap configuration is:

```yaml
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
```

Run the CSV ingestion command from `meltano_ingestion/`:

```bash
meltano --env-file ../.env run tap-csv target-bigquery
```

The CSV paths point to `../data/`, so all nine files must be present in the repository's `data/` directory.

### 9. Tap and target for REST API

The project uses `tap-rest-api-msdk` to extract Brazilian holidays. This command was used when the plugin was first added and is only needed if the project is rebuilt from scratch:

```bash
meltano add tap-rest-api-msdk
```

The tap keeps `setuptools<80` in its `pip_url`. Its configuration in `meltano.yml` is:

```yaml
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
```

Run the REST API ingestion command from `meltano_ingestion/`:

```bash
meltano --env-file ../.env run tap-rest-api-msdk target-bigquery
```

After each ingestion command succeeds, check the corresponding raw tables in BigQuery and compare the CSV table row counts with the source files.
