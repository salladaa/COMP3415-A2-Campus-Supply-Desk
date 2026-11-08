# Submission and reproducibility

1. Read output/pdf/COMP3415-A2-Report.pdf and docs/AI-REVIEW.md. Task 6 records the actual decisions Accept, Modify, Reject. The third technical candidate was evaluated during final review.
2. The completed assignment is on the repository's default branch, main:
   https://github.com/salladaa/COMP3415-A2-Campus-Supply-Desk
3. With Python 3.10+ run `python -m unittest discover -s tests -v` from the root. Expect 32 tests, OK. Use python3 or py -3 as appropriate.
4. Try `python -m supplydesk --data .supplydesk/review.json`. Express costs $12; a student order of two hoodies totals $84. Menu placement and cancellation require confirmation.
5. The report describes application/test commit 70aadbe1b8bf33ee7b6e54fab99e2582f6615a50. Later documentation/experiment commits do not change the application or suite. Starter tag: assignment-starter.
6. Submit the PDF, public repository URL, test evidence and Task 6 interaction record through MyCourseLink as instructed. General disclosure text is provided separately in docs/SUBMISSION-COMMENTS.txt; no email or course submission has been sent.
7. docs/EXPLANATION-GUIDE.md provides a short walkthrough for explaining the implementation and evidence. It supplements, rather than substitutes for, reviewing the code yourself.
