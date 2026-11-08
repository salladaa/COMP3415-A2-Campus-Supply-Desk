# Explaining the assignment

Use this as a reading guide. Confirm each answer against the named method and test before submitting.

## What did the refactoring change?

- Shared helper: quote and placement used to repeat validation/pricing. `_prepare_quote` now calculates the same fields for both. Each operation loads current state; placement then deducts stock, allocates an ID, appends history and saves. The helper does not save or reserve stock.
- Constants: names explain that 5000 is the student threshold, 10000 is the free-standard-delivery threshold and 600 is the standard fee, all in cents. Naming them did not repair the original comparison; that happened in the separate fix.
- Menu: the longer quote/place and cancellation interactions were extracted. `run_menu` retains dispatch and error handling; confirmation and default behavior remain covered by tests.

## Why did the refactored suite still fail?

The expanded suite exposed existing defects. A behavior-preserving refactor kept those failures visible. The separate fix then changed `>` to `>=` for student eligibility, accumulated duplicate-line quantities before stock validation, and returned already-cancelled orders without restoring stock again. Logs distinguish those changes from refactoring.

## How is express priced?

`total = subtotal - discount + delivery`. Student discount applies only to merchandise, using integer half-up rounding: `(subtotal * 10 + 50) // 100`. Express delivery is always 1200 cents; only standard delivery can be waived. For two student hoodies: 8000 - 800 + 1200 = 8400 cents.

## What do the test categories protect?

- Normal: successful orders have the right ID, total, inventory and saved history.
- Boundary: eligibility and delivery-fee comparisons behave correctly at their limits; rounding is correct without floating-point money.
- Invalid: rejected requests cannot consume stock or IDs or mutate saved orders.
- Preserve behavior: a shared pricing refactor must not change quote/order agreement or interface confirmation/defaults. Expected amounts are asserted independently, because two wrong calculations might still agree.

## Why reject isinstance(quantity, int)?

Python's bool inherits from int. `isinstance(True, int)` is true, so True passes that type check and behaves like 1 in arithmetic. The specification disallows boolean quantities. The isolated candidate run accepted a 500-cent notebook quote and an invalid placement; that extra saved order caused subsequent saved-state and ID assertions to fail. Keeping the exact-type check rejects True and False. The candidate was tested only in a temporary copy and was never applied to the real application.

## Why are there 28 failures in that experiment?

The test loops use subtests sharing one temporary saved state per test method. Once the modified implementation accepts the boolean placement, later subtests compare that altered save against the original bytes. Those failures have the same root cause. They are not evidence of 28 separate production bugs. The real application still passes all 32 test methods.

## What remains outside scope?

The JSON store is for one running instance per save file. Crash-safe writes, concurrent writers, payments, addresses and shipping integrations are not implemented. Automated tests support the tested cases; they are not a proof of all possible behaviors.

## Commands

Run the production suite: `python -m unittest discover -s tests -v` (Python 3.10+).
Run the rejected candidate experiment: `python evidence/evaluate_quantity_check.py`.
View original source: `git show assignment-starter:supplydesk/service.py`.
Inspect the refactor: `git show 54648e5 -- supplydesk`.
Inspect separate fixes: `git show a9ddcaf -- supplydesk/service.py`.
Inspect express changes: `git show 70aadbe -- supplydesk`.
