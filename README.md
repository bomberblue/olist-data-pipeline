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
├── data/
│   └── raw/               # the 9 Olist CSVs (git-ignored, not committed)
├── meltano/                # tap-csv -> target-bigquery config (owner: A)
├── dbt/
│   ├── models/
│   │   ├── staging/        # stg_* models (owner: B)
│   │   └── marts/          # fact_*, dim_* models (owner: B)
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

### 4. Data

Download the 9 Olist CSVs from Kaggle into `data/raw/` (this folder is git-ignored). Only the Meltano ingestion step (owner: A) reads from here directly.
