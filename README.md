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

- Google Cloud Platform project with BigQuery enabled — free sandbox tier is sufficient. Each team member needs Editor access.
- This GitHub repository, on a single `main` branch.

### 2. Local environment (everyone)

```bash
conda create -n olist-pipeline python=3.11 -y
conda activate olist-pipeline
pip install -r requirements.txt
```

Note: conda is used here only to create and manage the isolated Python environment. The packages themselves (Meltano, dbt, Great Expectations, Dagster) are installed via pip inside that environment rather than via conda install, since these tools are pip-first and not reliably up to date on conda-forge. requirements.txt remains the single source of truth for package versions.

You do not need every package in requirements.txt installed for your own work — see the "Who needs this" breakdown in the proposal document's Setup and Prerequisites section. At minimum, everyone needs Python and dbt-bigquery.

### 3. Credentials

Copy `.env.example` to `.env` and fill in your BigQuery service account or OAuth credential. `.env` is git-ignored — never commit it.

```bash
cp .env.example .env
```

Update the GCP ID "olist-data-pipeline-507001" under .env

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

Run the following commands in the terminal:

 
- pip install meltano                                          # Install Meltano.

- meltano init meltano_ingestion                               # Create the meltano_ingestion project folder.

- cd meltano_ingestion                                         # Navigate to the meltano_ingestion project folder.

 

### Tap and Target for CSV

Run the following commands in the terminal:


- meltano add tap-csv --variant meltanolabs                    # Add the MeltanoLabs implementation of the CSV tap for reading CSV files from the local directory.

- meltano add target-bigquery --variant=z3z1ma                 # Install the Singer target for loading extracted records into Google BigQuery.

Note: 
Add below data under meltano.yml file before running the target code.
1) Add "setuptools<80" in pip_url: git+https://github.com/z3z1ma/target-bigquery.git setuptools<80

2) Add below config data under pip_url: git+https://github.com/z3z1ma/target-bigquery.git setuptools<80

   config:
      project: olist-data-pipeline-507001
      dataset: olist_raw
      location: US
      denormalized: true
      threads: 1

3) Add below config data under pip_url: git+https://github.com/MeltanoLabs/tap-csv.git

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
        keys: [geolocation_zip_code_prefix, geolocation_lat, geolocation_lng]
        encoding: utf-8-sig
      - entity: raw_order_payments_dataset
        path: ../data/olist_order_payments_dataset.csv
        keys: [order_id, payment_sequential]
        encoding: utf-8-sig
      - entity: raw_order_reviews_dataset
        path: ../data/olist_order_reviews_dataset.csv
        keys: [review_id]
        encoding: utf-8-sig




- meltano run tap-csv target-bigquery                         # to extract the CSV data and load it into BigQuery


### Tap and Target for REST API

Run the following commands in the terminal:

 
- meltano add tap-rest-api-msdk                                        # Add the REST API tap to the Meltano project.

- meltano install extractor tap-rest-api-msdk                          # Install the extractor and its required packages.

Note: 
Add below data under meltano.yml file before running the target code.
1) Add "setuptools<80" in pip_url: tap-rest-api-msdk setuptools<80
2) Add below config data under pip_url: tap-rest-api-msdk setuptools<80

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


- meltano run tap-rest-api-msdk target-bigquery                        # to extract data from the REST API and load it into BigQuery

 