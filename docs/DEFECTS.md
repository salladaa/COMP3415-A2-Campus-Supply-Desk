# Defect corrections (not refactorings)

The exact five Task 3 diagnoses remain the three selected smells, the test gap, and repeated cancellation. The two extra findings below are recorded as additional test discoveries, not extra Task 3 diagnoses.

1. Repeated cancellation: original cancel_order restores quantities unconditionally. A second cancellation produces 22 notebooks from an initial 20 after purchasing two. Return an already cancelled order before restoration or saving. Required by FUNCTIONAL_SPEC.md, Cancellation.
2. Student threshold: original `subtotal > 5000` excludes exactly $50; the Prices section requires at least $50. Change `>` to `>=`. The original arithmetic and half-up rounding remain unchanged. This is a deliberate specification correction before CR-01, not part of refactoring or express delivery.
3. Duplicate item stock: original quote and placement check each line separately. Two notebook lines requesting 11 and 10 both pass a stock of 20. Accumulate requested quantity per product before deciding stock sufficiency. Keep result lines separate and validate fully before writing state. Required by Requests and validation.

Regression tests initially reported five failed assertions (two each for threshold and combined stock, one for cancellation). Refactoring preserved all five failures. These fixes make all 23 tests pass with unchanged expectations. See evidence/02-before-refactoring.txt, 03-after-refactoring.txt and 04-after-defect-fixes.txt.
