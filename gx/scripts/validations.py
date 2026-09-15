import os
from pathlib import Path
import great_expectations as gx
import pandas as pd
from sqlalchemy import create_engine

TABLE_NAMES = {
    "raw": {
        "customers": "raw_customers",
        "orders": "raw_orders",
        "order_items": "raw_order_items",
        "payments": "raw_order_payments_dataset",
        "reviews": "raw_order_reviews_dataset",
        "products": "raw_products",
        "sellers": "raw_sellers",
        "geolocation": "raw_geolocation_dataset",
    },
    "staging": {
        "customers": "stg_customers",
        "orders": "stg_orders",
        "order_items": "stg_order_items",
        "payments": "stg_order_payments",
        "reviews": "stg_order_reviews",
        "products": "stg_products",
        "sellers": "stg_sellers",
        "geolocation": "stg_geolocation",
    },
}

COLUMN_RENAMES = {
    "staging": {
        "products": {
            "product_name_length": "product_name_lenght",
            "product_description_length": "product_description_lenght",
        },
        "geolocation": {
            "latitude": "geolocation_lat",
            "longitude": "geolocation_lng",
            "city": "geolocation_city",
            "state": "geolocation_state",
        },
    },
}

VALUE_CASE_FIXES = {
    "staging": {
        "orders": ["order_status"],
    },
}

CSV_FILES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
}

NUMERIC_COLUMNS = {
    "order_items": ["order_item_id", "price", "freight_value"],
    "payments": ["payment_sequential", "payment_installments", "payment_value"],
    "reviews": ["review_score"],
    "products": [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
    "geolocation": ["geolocation_lat", "geolocation_lng"],
}

DATETIME_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}

ZIP_COLUMNS = {
    "customers": "customer_zip_code_prefix",
    "sellers": "seller_zip_code_prefix",
    "geolocation": "geolocation_zip_code_prefix",
}

# values to verify comes from official domain values and profiling of the current Olist raw data
BRAZIL_STATES = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]

# values for order statuses and payment types coming from distinct values in dataset
ORDER_STATUSES = [
    "created", "approved", "invoiced", "processing", "shipped", "delivered", "unavailable", "canceled",
]
# since "not_defined" percentage is very small (i.e. only 3 in dataset for now), 
# we will monitor first and add a check to ensure it's less than 0.01%
PAYMENT_TYPES = ["credit_card", "boleto", "voucher", "debit_card"]

# having the baseline helps to detect problems where only a part of CSV was loaded
RAW_ROW_BASELINES = {
    "customers": 99_441,
    "orders": 99_441,
    "order_items": 112_650,
    "payments": 103_886,
    "reviews": 99_224,
    "products": 32_951,
    "sellers": 3_095,
    "geolocation": 1_000_163,
}

# staging views just rename/cast columns with no filtering or dedup, so these match
# RAW_ROW_BASELINES for now. geolocation will need a lower baseline once the pending
# one-row-per-ZIP aggregation fix lands.
STAGING_ROW_BASELINES = {
    "customers": 99_441,
    "orders": 99_441,
    "order_items": 112_650,
    "payments": 103_886,
    "reviews": 99_224,
    "products": 32_951,
    "sellers": 3_095,
    "geolocation": 1_000_163,
}

ROW_BASELINES_BY_LAYER = {"raw": RAW_ROW_BASELINES, "staging": STAGING_ROW_BASELINES}

MART_TABLE_NAME = "fact_orders"
MART_ROW_BASELINE = 99_441
MART_ORDER_TOTAL_VALUE_BASELINE = 15_843_553.24

# base dataset names per layer; env (dev/staging/prod) adjusts these via resolve_dataset()
DATASET_NAMES = {
    "raw": "olist_raw",
    "staging": "olist_staging",
    "mart": "olist_mart",
}

E = gx.expectations

def get_project_root():
    return Path(__file__).resolve().parent.parent.parent

def get_context():
    context_mode = os.getenv("GX_CONTEXT_MODE", "file")
    project_root = get_project_root()

    if(context_mode == "file"):
        return gx.get_context(mode="file", project_root_dir=str(project_root))
    return gx.get_context(mode="ephemeral")

def resolve_dataset(layer, env):
    base = os.getenv(f"GX_{layer.upper()}_DATASET", DATASET_NAMES[layer])
    return base if env == "prod" else f"{base}_{env}"

def resolve_config():
    env = os.getenv("GX_ENV", "dev")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "olist-data-pipeline-507001")
    data_layer = os.getenv("GX_DATA_LAYER", "staging")
    source_mode = os.getenv("GX_SOURCE_MODE", "bigquery")

    if data_layer not in TABLE_NAMES:
        raise ValueError(f"DATA_LAYER must be one of {list(TABLE_NAMES)}")
    if source_mode == "csv" and data_layer != "raw":
        raise ValueError("The local CSV option represents the raw layer only.")

    datasets = {layer: resolve_dataset(layer, env) for layer in DATASET_NAMES}

    return {
        "env": env,
        "project_id": project_id,
        "data_layer": data_layer,
        "source_mode": source_mode,
        "datasets": datasets,
    }

def load_frames(config):
    data_layer = config["data_layer"]
    source_mode = config["source_mode"]

    frames = {}
    if source_mode == "bigquery":
        dataset = config["datasets"][data_layer]
        engine = create_engine(f"bigquery://{config['project_id']}/{dataset}")
        for logical_name, table_name in TABLE_NAMES[data_layer].items():
            query = f"SELECT * FROM `{config['project_id']}.{dataset}.{table_name}`"
            frames[logical_name] = pd.read_sql(query, engine)
    elif source_mode == "csv":
        project_root = get_project_root()
        for logical_name, filename in CSV_FILES.items():
            frames[logical_name] = pd.read_csv(project_root / "data" / filename)
    else:
        raise ValueError("SOURCE_MODE must be 'bigquery' or 'csv'.")

    # columns that got renamed from raw -> staging
    renames = COLUMN_RENAMES.get(data_layer,{})
    for logical_name, rename_map in renames.items():
        frames[logical_name] = frames[logical_name].rename(columns=rename_map)

    case_fixes = VALUE_CASE_FIXES.get(data_layer, {})
    for logical_name, columns in case_fixes.items():
        for column in columns:
            frames[logical_name][column] = frames[logical_name][column].str.lower()


    return frames

def load_mart_frame(config):
    dataset = config["datasets"]["mart"]
    engine = create_engine(f"bigquery://{config['project_id']}/{dataset}")
    query = f"SELECT * FROM `{config['project_id']}.{dataset}.{MART_TABLE_NAME}`"
    return pd.read_sql(query, engine)

# normalise the validation types to ensure that GX can process them
def normalize_frames(frames):
    coercion_failures = []

    def record_coercion_failure(table_name, column, original, converted):
        new_nulls = int((original.notna() & converted.isna()).sum())
        if new_nulls:
            coercion_failures.append({"table": table_name, "column": column, "new_nulls": new_nulls})

    for table_name, columns in NUMERIC_COLUMNS.items():
        for column in columns:
            original = frames[table_name][column]
            converted = pd.to_numeric(original, errors="coerce").astype("float64")
            record_coercion_failure(table_name, column, original, converted)
            frames[table_name][column] = converted

    for table_name, columns in DATETIME_COLUMNS.items():
        for column in columns:
            original = frames[table_name][column]
            converted = pd.to_datetime(original, errors="coerce")
            record_coercion_failure(table_name, column, original, converted)
            frames[table_name][column] = converted

    for table_name, column in ZIP_COLUMNS.items():
        original = frames[table_name][column]
        numeric_zip = pd.to_numeric(original, errors="coerce").astype("Int64")
        record_coercion_failure(table_name, column, original, numeric_zip)
        frames[table_name][column] = numeric_zip.astype("string").str.zfill(5)

    orders = frames["orders"]
    orders["delivery_date_matches_status"] = ~(
        ((orders["order_status"] == "delivered") & orders["order_delivered_customer_date"].isna())
        | ((orders["order_status"] != "delivered") & orders["order_delivered_customer_date"].notna())
    )

    order_items = frames["order_items"]
    purchase_lookup = frames["orders"][["order_id", "order_purchase_timestamp"]]
    order_items = order_items.merge(purchase_lookup, on="order_id", how="left", suffixes=("", "_order"))
    order_items["shipping_after_purchase"] = ~(
        order_items["shipping_limit_date"].notna()
        & order_items["order_purchase_timestamp"].notna()
        & (order_items["shipping_limit_date"] < order_items["order_purchase_timestamp"])
    )
    order_items = order_items.drop(columns=["order_purchase_timestamp"])
    frames["order_items"] = order_items

    frames["order_reconciliation"] = build_order_reconciliation_frame(frames["order_items"], frames["payments"])

    return frames, coercion_failures

# one row per order_id, comparing summed payments against summed item price + freight.
# orders missing from either side are excluded (relationship completeness is dbt's job).
def build_order_reconciliation_frame(order_items, payments):
    item_totals = (order_items["price"] + order_items["freight_value"]).groupby(order_items["order_id"]).sum()
    payment_totals = payments.groupby("order_id")["payment_value"].sum()

    reconciliation = pd.DataFrame({
        "order_item_freight_total": item_totals,
        "order_payment_total": payment_totals,
    }).dropna().reset_index().rename(columns={"index": "order_id"})

    reconciliation["payment_matches_items"] = (
        (reconciliation["order_payment_total"] - reconciliation["order_item_freight_total"]).abs() <= 0.01
    )
    return reconciliation

def non_null(*columns):
    return [E.ExpectColumnValuesToNotBeNull(column=column) for column in columns]


def non_negative(*columns):
    return [E.ExpectColumnValuesToBeBetween(column=column, min_value=0.0) for column in columns]

def build_expectation_suites(config):
    critical_expectations = {
        "customers": [
            E.ExpectColumnValuesToBeInSet(column="customer_state", value_set=BRAZIL_STATES),
            E.ExpectColumnValuesToMatchRegex(column="customer_zip_code_prefix", regex=r"^\d{5}$"),
        ],
        "orders": [
            E.ExpectColumnValuesToBeInSet(column="order_status", value_set=ORDER_STATUSES),
            E.ExpectColumnValuesToNotBeNull(column="order_purchase_timestamp"),
            E.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A="order_approved_at", column_B="order_purchase_timestamp",
                or_equal=True, ignore_row_if="either_value_is_missing",
            ),
            E.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A="order_delivered_customer_date", column_B="order_purchase_timestamp",
                or_equal=True, ignore_row_if="either_value_is_missing",
            ),
        ],
        "order_items": [
            E.ExpectColumnValuesToBeBetween(column="order_item_id", min_value=1),
            E.ExpectColumnValuesToBeBetween(column="price", min_value=0.0, strict_min=True),
            E.ExpectColumnValuesToBeBetween(column="freight_value", min_value=0.0),
        ],
        "payments": [
            E.ExpectColumnValuesToBeBetween(column="payment_sequential", min_value=1.0),
            E.ExpectColumnValuesToBeBetween(column="payment_value", min_value=0.0),
            # check that the number of "not_defined" payment types is less than 0.01%
            E.ExpectColumnValuesToBeInSet(column="payment_type", value_set=PAYMENT_TYPES, mostly=0.9999),
        ],
        "reviews": [
            E.ExpectColumnValuesToBeBetween(column="review_score", min_value=1.0, max_value=5.0),
            E.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A="review_answer_timestamp", column_B="review_creation_date",
                or_equal=True, ignore_row_if="either_value_is_missing",
            ),
        ],
        "products": [
            *non_negative(
                "product_name_lenght", "product_description_lenght", "product_photos_qty",
                "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm",
            ),
        ],
        "sellers": [
            E.ExpectColumnValuesToBeInSet(column="seller_state", value_set=BRAZIL_STATES),
            E.ExpectColumnValuesToMatchRegex(column="seller_zip_code_prefix", regex=r"^\d{5}$"),
        ],
        "geolocation": [
            E.ExpectColumnValuesToBeBetween(column="geolocation_lat", min_value=-90.0, max_value=90.0),
            E.ExpectColumnValuesToBeBetween(column="geolocation_lng", min_value=-180.0, max_value=180.0),
            E.ExpectColumnValuesToBeInSet(column="geolocation_state", value_set=BRAZIL_STATES),
            E.ExpectColumnValuesToMatchRegex(column="geolocation_zip_code_prefix", regex=r"^\d{5}$"),
        ],
        "order_reconciliation": [],
    }

    # monitor changes or known imperfections that 
    # require investigation but do not necessarily make the data unusable
    observation_expectations = {
        "customers": [
            E.ExpectColumnValuesToNotBeNull(column="customer_city", mostly=0.99),
        ],
        "orders": [
            E.ExpectColumnValuesToNotBeNull(column="order_approved_at", mostly=0.98),
            E.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A="order_delivered_carrier_date", column_B="order_purchase_timestamp",
                or_equal=True, mostly=0.995, ignore_row_if="either_value_is_missing",
            ),
            E.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A="order_delivered_customer_date", column_B="order_delivered_carrier_date",
                or_equal=True, mostly=0.999, ignore_row_if="either_value_is_missing",
            ),
            E.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A="order_estimated_delivery_date", column_B="order_delivered_customer_date",
                or_equal=True, mostly=0.90, ignore_row_if="either_value_is_missing",
            ),
            E.ExpectColumnValuesToBeInSet(column="delivery_date_matches_status", value_set=[True], mostly=0.999),
        ],
        "order_items": [
            E.ExpectColumnMeanToBeBetween(column="price", min_value=95.0, max_value=145.0),
            E.ExpectColumnMeanToBeBetween(column="freight_value", min_value=16.0, max_value=24.0),
            E.ExpectColumnValuesToBeInSet(column="shipping_after_purchase", value_set=[True], mostly=0.999),
        ],
        "payments": [
            E.ExpectColumnValuesToBeBetween(column="payment_installments", min_value=1.0, mostly=0.9999),
            E.ExpectColumnValuesToBeBetween(column="payment_value", min_value=0.0, strict_min=True, mostly=0.9999),
            E.ExpectColumnMeanToBeBetween(column="payment_value", min_value=120.0, max_value=190.0),
        ],
        "reviews": [
            E.ExpectColumnValuesToNotBeNull(column="review_comment_title", mostly=0.10),
            E.ExpectColumnValuesToNotBeNull(column="review_comment_message", mostly=0.35),
            E.ExpectColumnMeanToBeBetween(column="review_score", min_value=3.8, max_value=4.3),
        ],
        "products": [
            E.ExpectColumnValuesToNotBeNull(column="product_category_name", mostly=0.97),
            E.ExpectColumnValuesToBeBetween(column="product_weight_g", min_value=0.0, max_value=50_000.0, mostly=0.999),
        ],
        "sellers": [
            E.ExpectColumnValuesToNotBeNull(column="seller_city", mostly=0.99),
        ],
        "geolocation": [
            E.ExpectColumnValuesToBeBetween(column="geolocation_lat", min_value=-34.0, max_value=6.0, mostly=0.9999),
            E.ExpectColumnValuesToBeBetween(column="geolocation_lng", min_value=-74.0, max_value=-34.0, mostly=0.9999),
            E.ExpectCompoundColumnsToBeUnique(
                column_list=[
                    "geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng",
                    "geolocation_city", "geolocation_state",
                ],
                # TODO: monitor if value needs to be tightened
                mostly=0.60,
            ),
        ],
        "order_reconciliation": [
            E.ExpectColumnValuesToBeInSet(column="payment_matches_items", value_set=[True], mostly=0.99),
        ],
    }

    if config["data_layer"] in ROW_BASELINES_BY_LAYER:
        for table_name, baseline in ROW_BASELINES_BY_LAYER[config["data_layer"]].items():
            observation_expectations[table_name].insert(
                0,
                E.ExpectTableRowCountToBeBetween(
                    min_value=int(baseline * 0.95),
                    max_value=int(baseline * 1.05),
                ),
            )

    return critical_expectations, observation_expectations

def build_mart_expectations():
    return [
        E.ExpectTableRowCountToBeBetween(
            min_value=int(MART_ROW_BASELINE * 0.95),
            max_value=int(MART_ROW_BASELINE * 1.05),
        ),
        E.ExpectColumnSumToBeBetween(
            column="order_total_value",
            min_value=MART_ORDER_TOTAL_VALUE_BASELINE * 0.95,
            max_value=MART_ORDER_TOTAL_VALUE_BASELINE * 1.05,
        ),
    ]



def register_checkpoints(context, frames, critical_expectations, observation_expectations):
    data_source = context.data_sources.add_or_update_pandas(name="olist_dataframes")
    validations = {"critical": {}, "observation": {}}
    checkpoints = {"critical": {}, "observation": {}}

    # create 2 GX objectis for each table
    def get_batch_definition(table_name):
        asset_name = f"{table_name}_dataframe_asset"
        batch_name = f"{table_name}_whole_dataframe"
        # GX 1.22 raises LookupError/KeyError here, not ValueError as some docs show -
        # confirmed against this project's installed version before relying on it.
        try:
            asset = data_source.get_asset(asset_name)
        except LookupError:
            asset = data_source.add_dataframe_asset(name=asset_name)
        try:
            return asset.get_batch_definition(batch_name)
        except KeyError:
            return asset.add_batch_definition_whole_dataframe(batch_name)

    # creates or updates the expectation suite and validation definition.
    # add_or_update fully replaces the suite's expectation list on every call (verified
    # empirically), so rerunning this cell always reflects the current expectations above.
    def replace_suite_and_validation(table_name, group, expectations, batch_definition):
        suite_name = f"{table_name}_{group}_suite"
        validation_name = f"{table_name}_{group}_validation"

        suite = gx.ExpectationSuite(name=suite_name)
        for expectation in expectations:
            expectation_copy = expectation.copy(deep=True)
            expectation_copy.id = None
            suite.add_expectation(expectation_copy)
        suite = context.suites.add_or_update(suite)

        validation = context.validation_definitions.add_or_update(
            gx.ValidationDefinition(data=batch_definition, suite=suite, name=validation_name)
        )
        return validation


    # wraps a validation definition in a Checkpoint with UpdateDataDocsAction, so every run
    # also refreshes the browsable HTML validation report under gx/uncommitted/data_docs/
    def replace_checkpoint(table_name, group, validation):
        checkpoint_name = f"{table_name}_{group}_checkpoint"
        return context.checkpoints.add_or_update(
            gx.Checkpoint(
                name=checkpoint_name,
                validation_definitions=[validation],
                actions=[gx.checkpoint.UpdateDataDocsAction(name="update_data_docs")],
                result_format={"result_format": "SUMMARY", "partial_unexpected_count": 10},
            )
        )


    batch_definitions = {table: get_batch_definition(table) for table in frames}
    
    for table_name in frames:
        validations["critical"][table_name] = replace_suite_and_validation(
            table_name, "critical", critical_expectations[table_name], batch_definitions[table_name]
        )
        validations["observation"][table_name] = replace_suite_and_validation(
            table_name, "observation", observation_expectations[table_name], batch_definitions[table_name]
        )
        checkpoints["critical"][table_name] = replace_checkpoint(
            table_name, "critical", validations["critical"][table_name]
        )
        checkpoints["observation"][table_name] = replace_checkpoint(
            table_name, "observation", validations["observation"][table_name]
        )

    return validations, checkpoints

def run_validations(checkpoints, validations, frames):
    validation_results = []

    for group, table_checkpoints in checkpoints.items():
        for table_name, checkpoint in table_checkpoints.items():
            checkpoint_result = checkpoint.run(batch_parameters={"dataframe": frames[table_name]})
            result = next(iter(checkpoint_result.run_results.values()))
            validation_results.append(
                {
                    "group": group,
                    "table": table_name,
                    "validation": validations[group][table_name].name,
                    "success": bool(result.success),
                    "result": result,
                }
            )

    validation_summary = pd.DataFrame(
        [{key: item[key] for key in ["group", "table", "validation", "success"]} for item in validation_results]
    ).sort_values(["group", "table"]).reset_index(drop=True)

    return validation_results, validation_summary

def summarize_failures(validation_results):
    detail_rows = []
    for validation_item in validation_results:
        payload = validation_item["result"].to_json_dict()
        for expectation_result in payload["results"]:
            expectation_config  = expectation_result["expectation_config"]
            result = expectation_result.get("result", {})
            detail_rows.append(
                {
                    "group": validation_item["group"],
                    "table": validation_item["table"],
                    "expectation": expectation_config .get("type"),
                    "column": expectation_config .get("kwargs", {}).get("column", "<table or column pair>"),
                    "success": expectation_result.get("success"),
                    "observed_value": result.get("observed_value"),
                    "unexpected_count": result.get("unexpected_count"),
                    "unexpected_percent": result.get("unexpected_percent"),
                }
            )

    gx_details = pd.DataFrame(detail_rows)
    failed_details = gx_details[gx_details["success"] == False]

    return gx_details, failed_details


def run_mart_sanity_check(context, config):
    data_source = context.data_sources.add_or_update_pandas(name="olist_mart_dataframes")

    try:
        asset = data_source.get_asset(f"{MART_TABLE_NAME}_dataframe_asset")
    except LookupError:
        asset = data_source.add_dataframe_asset(name=f"{MART_TABLE_NAME}_dataframe_asset")
    try:
        batch_definition = asset.get_batch_definition(f"{MART_TABLE_NAME}_whole_dataframe")
    except KeyError:
        batch_definition = asset.add_batch_definition_whole_dataframe(f"{MART_TABLE_NAME}_whole_dataframe")

    suite = gx.ExpectationSuite(name=f"{MART_TABLE_NAME}_sanity_suite")
    for expectation in build_mart_expectations():
        suite.add_expectation(expectation.copy(deep=True))
    suite = context.suites.add_or_update(suite)

    validation = context.validation_definitions.add_or_update(
        gx.ValidationDefinition(data=batch_definition, suite=suite, name=f"{MART_TABLE_NAME}_sanity_validation")
    )
    checkpoint = context.checkpoints.add_or_update(
        gx.Checkpoint(
            name=f"{MART_TABLE_NAME}_sanity_checkpoint",
            validation_definitions=[validation],
            actions=[gx.checkpoint.UpdateDataDocsAction(name="update_data_docs")],
            result_format={"result_format": "SUMMARY", "partial_unexpected_count": 10},
        )
    )

    mart_frame = load_mart_frame(config)
    checkpoint_result = checkpoint.run(batch_parameters={"dataframe": mart_frame})
    result = next(iter(checkpoint_result.run_results.values()))
    return bool(result.success), result

def run_gx_validations():
    config = resolve_config()
    context = get_context()
    frames = load_frames(config)
    frames, coercion_failures = normalize_frames(frames)
    critical_expectations, observation_expectations = build_expectation_suites(config)
    validations, checkpoints = register_checkpoints(context, frames, critical_expectations, observation_expectations)
    results, summary = run_validations(checkpoints, validations, frames)
    details, failed = summarize_failures(results)

    mart_success, mart_result = run_mart_sanity_check(context, config)

    critical_failures = summary[(summary["group"] == "critical") & (~summary["success"])]
    observation_failures = summary[(summary["group"] == "observation") & (~summary["success"])]

    raise_on_critical_failure = os.getenv("GX_RAISE_ON_CRITICAL_FAILURE", "false").lower() == "true"
    if raise_on_critical_failure and not critical_failures.empty:
        raise RuntimeError("Critical GX checks failed. Review critical_failures and failed_details.")

    raise_on_mart_failure = os.getenv("GX_RAISE_ON_MART_FAILURE", "false").lower() == "true"
    if raise_on_mart_failure and not mart_success:
        raise RuntimeError("Mart sanity check failed. Review mart_result for details.")

    return {
        "summary": summary,
        "failed": failed,
        "coercion_failures": coercion_failures,
        "critical_failures": critical_failures,
        "observation_failures": observation_failures,
        "mart_sanity_success": mart_success,
        "mart_result": mart_result,
    }
