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
