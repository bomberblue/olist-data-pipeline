from gx.scripts.validations import run_gx_validations


def main():
    try:
        result = run_gx_validations()
    except RuntimeError as exc:
        print(exc)
        return 1

    print(f"Critical failures: {len(result['critical_failures'])}")
    print(f"Observation failures: {len(result['observation_failures'])}")
    print(f"Mart sanity check success: {result['mart_sanity_success']}")

    if result["coercion_failures"]:
        print("Coercion failures (values nulled during type coercion):")
        for failure in result["coercion_failures"]:
            print(f"  {failure['table']}.{failure['column']}: {failure['new_nulls']} new nulls")
    else:
        print("Coercion failures: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
