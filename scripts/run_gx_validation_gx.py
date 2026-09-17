import logging

from gx.scripts.validations import run_gx_validations

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    try:
        result = run_gx_validations()
    except RuntimeError as exc:
        logger.error(exc)
        return 1

    logger.info("Critical failures: %d", len(result["critical_failures"]))
    logger.info("Observation failures: %d", len(result["observation_failures"]))
    logger.info("Mart sanity check success: %s", result["mart_sanity_success"])
    for table_name, (success, _) in result["mart_results"].items():
        logger.info("  %s: %s", table_name, "OK" if success else "FAILED")

    if result["coercion_failures"]:
        logger.warning("Coercion failures (values nulled during type coercion):")
        for failure in result["coercion_failures"]:
            logger.warning("  %s.%s: %d new nulls", failure["table"], failure["column"], failure["new_nulls"])
    else:
        logger.info("Coercion failures: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
