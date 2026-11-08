# CR-01 prediction recorded BEFORE implementation

The preceding defect-fix commit has 23 passing tests. No express implementation or express tests have been added at this point.

## Behavior to change
Accept express for quote/place via service, CLI, and menu. Charge 1200 cents for every express order regardless of value. Apply the existing merchandise-only student discount and rounding. Keep regular/pickup defaults, standard delivery's post-discount free threshold, existing validation, persistence, history, and cancellation rules.

## Expected files/methods
- supplydesk/service.py: add EXPRESS_DELIVERY_FEE_CENTS, extend _prepare_quote fulfillment validation and delivery pricing. quote/place already share the helper; no duplicated pricing edits expected.
- supplydesk/cli.py: build_parser fulfillment choices/help.
- supplydesk/menu.py: read_request fulfillment prompt. Existing extracted flows should pass the selected option through without further edits.
- README.md and FUNCTIONAL_SPEC.md: document the option, fixed fee, examples, and current tests.
- tests/test_express.py: acceptance tests using service, real CLI subprocesses, and scripted terminal menu input.
- No storage schema or cancellation code changes expected: orders already snapshot fulfillment/items/prices, and cancellation was corrected separately.

## Planned tests
1. Service quote/place: all three CR-01 examples, fee above free-standard threshold, and quote/order agreement.
2. Student threshold and half-up rounding with express; discount excludes shipping.
3. Retrieval, reopening and history preserve order snapshots even after catalog changes; repeated cancellation restores stock only once and preserves amounts; next ID is not reused.
4. Invalid customer/fulfillment/items/quantities and combined stock leave state intact; quote does not reserve stock; placement revalidates.
5. Real CLI quote/place/show/orders/cancel/catalog, exit codes, unknown fulfillment, and help.
6. Menu quote/place, decline/confirm/cancel, saved state and CAD output, discovery prompt, errors and defaults.
7. Full regression suite protects pickup/standard delivery and validation.

## Expected refactoring benefit
The shared helper provides one pricing change for both operations. Named constants state fee units. Extracted menu flows allow the prompt change without mixing delivery pricing into user-interface handling.

After implementation, compare this prediction with the actual diff; do not retrospectively rewrite the prediction.
