# Task 6: recommendations, decisions, and evidence

Codex proposed these recommendations. Original selected exchanges and superseded wording are preserved in [AI-INTERACTION-ARCHIVE.md](AI-INTERACTION-ARCHIVE.md); this document consolidates the current decisions.

## 1. Shared validation/pricing - ACCEPT

Actual question presented:
> Task 6 recommendation 1: Extract one shared request-validation/pricing helper used by quote() and place_order(), passing in the state already loaded for that operation. Both original methods repeat this logic; test_quote_and_order_agree checks matching items and totals, and test_placement_rechecks_stock_after_quote protects fresh stock checks. Do you Accept, Modify, or Reject this recommendation, and why?

Later personal explanation, quoted as supplied:
> Recommendations 1
> _prepare_quote() checks request is valid and calculates
> but, doesn't save anything or change
> share it so that a quote and order always follows the same rules instead of 2 copies that could get out of sync
> placement check stock coz quote doesn't reserve any items, stock may have changed since quote was made


Action: implemented in 54648e5. See baseline and refactoring logs 02-03; the same five assertions failed before and after refactoring. The report edits this explanation for grammar and technical precision.

## 2. Scope of menu extraction - MODIFY

Actual question presented:
> Task 6 recommendation 2: Extract every interactive menu branch into its own function to shorten run_menu(). The original mixes prompts, dispatch, confirmation, and errors; test_menu_defaults_decline_and_confirmation and test_menu_errors_and_exit protect behavior. A narrower alternative is to extract only the quote/place and cancellation flows, leaving short branches inline. Do you Accept, Modify, or Reject the broad recommendation, and why? I’ll use the narrower extraction for the draft.

Later personal explanation, quoted as supplied:
> recommendations 2
> two flows have severas steps ask,confirm[y,N], act , print, i moved them into handle_quote_or_place() and handle_cancellation() that kept run_menu() small and flow read easy. catalog,lookup and hisotry on small lines


Action: implemented in 54648e5. See baseline and refactoring logs 02-03; the same five assertions failed before and after refactoring. The report edits this explanation for grammar and technical precision.

## 3. Quantity-validation candidate - REJECT

Codex proposed replacing `type(quantity) is not int` with `not isinstance(quantity, int)` during final review specifically for evaluation, with the boolean caveat disclosed. It was tested only in a temporary copy. The exact original proposal and replies are in the linked archive.

Decision: Reject; retain the exact-type check.

Evidence-based explanation (edited by Codex from the observed output): `isinstance(True, int)` printed True, so a boolean passed as quantity and the quote cost 500 cents. The candidate suite produced 28 failure reports, including cascading state and ID failures. The unchanged application passed all 32 tests.

The student ran the experiment and application suite on 8 November 2026: [experiment screenshot](../evidence/11-student-experiment.png), [application screenshot](../evidence/12-student-suite.png). The original Codex experiment is [07-original-codex-run.txt](../evidence/07-original-codex-run.txt); the student rerun is [07-quantity-candidate.txt](../evidence/07-quantity-candidate.txt). The student experiment log identifies Xcode Python but did not record its version. A subsequent Codex verification on Python 3.12 records the version in [13-versioned-candidate.txt](../evidence/13-versioned-candidate.txt). These later runs do not change the recommendation's origin.
