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

Conda creates and manages the isolated Python environment; pip installs the packages listed in `requirements.txt` inside it.

`requirements.txt` pins the direct package versions from the team's existing `olist-pipeline` Python 3.11 environment. Meltano installs its taps and target separately using the pinned `pip_url` entries in `meltano_ingestion/meltano.yml`:

- `tap-csv`: the installed Git commit `1331c4a4f3d2bd7b0757a9a7ea4d27b785c54e04` (version 1.2.0).
- `target-bigquery`: the installed Git commit `090dad0620711efae4b31031b10b0ea88744aef5` (version 0.7.2).
- `tap-rest-api-msdk`: release 1.4.2, installed and checked separately in a temporary Python 3.11 environment.
- The REST tap and BigQuery target also pin `setuptools==79.0.1`, preserving the existing `setuptools<80` compatibility constraint using the version installed with the target.

Validation covered dependency resolution of `requirements.txt`, imports and dependency checks in the existing main environment, and dependency checks and CLI version commands for all three plugins. These checks do not establish successful end-to-end BigQuery ingestion. Transitive dependencies are not fully locked and can still vary between installations.

When upgrading dependencies, update the relevant pins in `requirements.txt` or `meltano_ingestion/meltano.yml`, repeat the compatibility checks, and validate ingestion before sharing the change. The files under `meltano_ingestion/plugins/` store Meltano plugin definitions; the project's explicit `pip_url` entries select the plugin versions used here.

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

The loader in `meltano_ingestion/meltano.yml` references these variables. The ingestion commands in step 8 explicitly load this root `.env`; a separate `.env` inside `meltano_ingestion/` is unnecessary. Google authentication is configured separately through Application Default Credentials in step 5. dbt continues to use its own `profiles.yml` from step 6.

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

### 8. Run ingestion

Run the commands below from `meltano_ingestion/`. Complete Application Default Credentials authentication from step 5 first, and confirm the project and dataset values in the repository's root `.env`. The loader reads those values through the variable references in `meltano.yml`. The `--env-file ../.env` option explicitly loads the root `.env`.

Load the nine local CSVs:

```bash
meltano --env-file ../.env run tap-csv target-bigquery
```

The configured CSV paths point to `../data/`, so all nine files must be present in the repository's `data/` directory.

Load the 2017 and 2018 holidays from BrasilAPI:

```bash
meltano --env-file ../.env run tap-rest-api-msdk target-bigquery
```

The current loader configuration enables `overwrite: true`, so a successful rerun replaces the tables loaded by that run. After each command succeeds, check the corresponding raw tables in BigQuery and compare CSV table row counts with the source files.
