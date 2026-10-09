# Progress log

## 2026-10-08
**Data**
- Template dataset: 4800 train / 1200 test (phrase-disjoint). ChatGPT file cleaned: 6127 rows -> 3076 unique
  (half were exact duplicates; Drainage/Water Hindi looped). Balanced external test = 1344 rows (84 per category/language).
- Extra pool (761 rows) is lopsided, so only 40 rows per category are used for training (cap chosen on the template test).

**Model (Phase 1)** TF-IDF char n-grams (2-5) + Logistic Regression + sigmoid calibration
| Model | Template test (unseen phrases) | External test |
|---|---|---|
| A: template train only | 0.776 | 0.802 |
| B: + capped pool (deployed) | 0.815 | 0.853 (slightly optimistic: same generator as the pool) |
- Threshold 0.64 chosen on the template test: auto-routes 68.8% at 90.3% accuracy; on the external test 70.8% at 92.2%.
- ECE about 0.03 (confidence is reasonably honest). Weakest classes: Drainage (0.77) and Public Health (0.74).

**Backend (Phases 2-4)** FastAPI + SQLAlchemy (SQLite default, PostgreSQL via DATABASE_URL), JWT + bcrypt, roles,
complaint creation with prediction + severity + routing, officer workflow, citizen confirm/reopen, admin review queue,
category->department table editor, corrections table, audit log, analytics. 25 tests pass.

**Severity** rule-based (EN+HI lexicon, nukta-normalised). Against the reference column: exact 66%, within one level 99%,
critical caught 117/120. The reference column is circular, so the engine was NOT tuned to match it.

## Next
1. Frontend (React): login, complaint form with map pin, my complaints, officer dashboard, admin review queue + analytics.
2. MuRIL fine-tuning notebook (Colab) and comparison with the baseline.
3. Priority rubric + human ratings (Cohen's kappa), then tune severity weights.
4. Optional: repeat-report detection with embeddings, explainability, pothole YOLO demo.
