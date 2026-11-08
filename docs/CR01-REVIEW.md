# CR-01 implementation review

Prediction: docs/CR01-PREDICTION.md was committed as 4b6a209 before express changes.

Actual application changes matched the prediction: service.py (_prepare_quote and a fee constant), cli.py (build_parser choices/help), and menu.py (read_request prompt). README.md and FUNCTIONAL_SPEC.md document the new option. tests/test_express.py adds 9 test methods with parameterized cases. No storage changes or additional cancellation changes were needed.

The shared pricing helper made quote/order agreement a single implementation concern. Named monetary constants made the 1200-cent fee explicit. Menu extraction helped readability but had little direct impact on CR-01: only the shared request prompt changed. The previous separate cancellation fix was necessary for the required repeat-cancellation behavior but was not a refactoring benefit.

## Acceptance traceability

| Official CR-01 requirement | Tests and evidence |
| --- | --- |
| 1. Accept express through service, CLI, menu | test_official_examples_quote_and_place; test_cli_express_lifecycle_and_help; test_menu_quote_place_retrieve_cancel |
| 2. Fixed 1200 cents, never waived | test_express_fee_never_waived; official examples include 2200, 8400 and 13200 totals |
| 3. Preserve student rules and rounding; merchandise only | test_discount_threshold_and_rounding_exclude_delivery; 4500 subtotal + fee does not trigger a discount; 5005 subtotal rounds discount to 501 |
| 4. Preserve pickup and standard | test_standard_delivery_boundary; test_express_fee_never_waived; all 4 unchanged smoke tests |
| 5. Quote/order agreement and lifecycle snapshots | test_official_examples_quote_and_place; test_lifecycle_snapshot_history_and_repeat_cancel; CLI lifecycle test |
| 6. Validation, stock, IDs, history, cancellation | test_invalid_express_requests_preserve_state; test_quote_does_not_reserve_and_place_revalidates; lifecycle tests plus regression suite |
| 7. Discovery, help/docs and defaults | CLI help asserts express and 1200; menu output asserts express prompt; test_menu_decline_invalid_and_defaults; regression CLI defaults; README section 7 and updated functional spec |

All test names above belong to ExpressTests in tests/test_express.py except the boundary/default regression tests in tests/test_regression.py and starter tests in tests/test_smoke.py. Full result: evidence/05-after-cr01.txt, 32 tests, OK, exit 0. Tests are automated scripted terminal sessions, not a claim of manual user acceptance testing.
