# PROJECT BRIEF: Multilingual Civic Complaint Triage System
B.Tech final year (Computer Engineering). Read this fully before doing anything.

## 0. How I want you to work
- I am a student. Explain what you are doing in simple words and say WHY.
- Work in small phases (section 14). Finish one phase, run the tests, summarise, then STOP and wait for me.
- Ask before deleting or overwriting any file. Never touch test data. Never train on test data.
- Use git. Commit after each working step with a clear message. Do not commit secrets or large model files.
- Everything must be FREE. No paid APIs, no paid services, no API keys needed to run the project.
- If something in this brief is unclear or seems wrong, ask me instead of guessing.
- Be honest in code comments, reports and READMEs about limitations (see section 16).

## 1. What the project is
A web system where citizens submit civic complaints (text, optional photo, map pin) in ENGLISH or HINDI (Devanagari).
The system:
1. Understands the complaint text (including spelling mistakes and different phrasing/languages).
2. Predicts the complaint CATEGORY with a calibrated confidence score.
3. Maps the category to a DEPARTMENT using an admin-editable database table.
4. Scores SEVERITY (low / medium / high / critical) with a transparent rule-based engine.
5. Auto-routes to an officer only when confident; otherwise sends it to a human review queue.
6. Lets officers update status, admins override routing, and citizens track and confirm resolution.

Why it is new compared with ordinary department-wise complaint forms: the citizen does not need to know which
department is responsible. The innovation is NOT "auto routing" by itself; it is confidence-aware, explainable,
multilingual triage with human-in-the-loop verification, evaluated per language.

## 2. Hard constraints
- Free tools only. Must run on a Lenovo LOQ laptop (assume 16 GB RAM; GPU may or may not be NVIDIA).
- Languages now: English + Hindi. Marathi and Hinglish are FUTURE WORK (design the code so adding a language is easy).
- Python 3.11 or 3.12. Node LTS. Docker for PostgreSQL.
- Text encoding: UTF-8 everywhere. Read CSVs with encoding="utf-8-sig". Hindi must render correctly in DB, API and UI.
- Privacy: no real personal data in datasets; mask phone numbers in UI; role-based access; passwords hashed.

## 3. Tech stack (use these unless I approve a change)
- Backend: Python, FastAPI, SQLAlchemy 2.x, Alembic migrations, Pydantic, JWT auth (python-jose or similar) + bcrypt/argon2 hashing, pytest.
- Database: PostgreSQL in Docker (docker-compose). PostGIS only later if needed.
- Frontend: React + Vite + TypeScript + Tailwind CSS; i18next for UI language (English/Hindi); Leaflet + OpenStreetMap for maps; Recharts or Chart.js for charts.
- ML: pandas, scikit-learn, joblib, Hugging Face transformers + datasets, PyTorch, sentence-transformers (optional), matplotlib.
- Maps/geo: Leaflet; OpenStreetMap Overpass API for nearby school/hospital/main-road context (cache results, respect rate limits); Nominatim only for light address lookup.
- Annotation (optional): Label Studio. Training compute: my laptop, or Google Colab / Kaggle free GPU for MuRIL.
- Version control: Git + GitHub. CI optional: GitHub Actions running pytest.

## 4. Repo structure to create
complaint-triage/
  CLAUDE.md                  (contains: @docs/PROJECT_BRIEF.md)
  docs/                      PROJECT_BRIEF.md, labelling_guide.md, priority_rubric.md, progress.md, report notes
  backend/                   FastAPI app (app/main.py, routers/, models/, schemas/, services/, tests/)
  frontend/                  React app
  ml/
    data/                    complaints_train.csv, complaints_test.csv, complaints_external_test.csv (+ raw/, processed/)
    src/                     validate_data.py, train_baseline.py, evaluate.py, calibrate.py, predict.py
    notebooks/               muril_finetune.ipynb (for Colab)
    models/                  saved models (gitignored if large)
    reports/                 metrics json, confusion matrices, plots
  docker-compose.yml
  README.md
Keep docs/progress.md updated (date, what was done, decisions). Add a .gitignore (venv, node_modules, models, .env, data/raw if large).

## 5. Categories and departments (stored in DB, admin-editable)
Roads -> Public Works Department
Garbage -> Solid Waste Management
Water Supply -> Water Supply Department
Drainage -> Drainage and Sewerage
Streetlight -> Electrical Department
Public Health -> Health Department
Encroachment -> Building Permission and Encroachment
Other -> Admin Review   (vague / off-topic / non-municipal; always goes to human review)
Category definitions (for labelling and docs):
- Roads: potholes, broken roads, damaged footpaths, uncovered manholes on roads, speed breakers.
- Garbage: uncollected waste, overflowing dustbins, illegal dumping, burning waste.
- Water Supply: no water, low pressure, dirty tap water, pipeline leaks, tanker problems.
- Drainage: blocked drains, sewage overflow, waterlogging, open/broken gutters.
- Streetlight: lights not working, flickering, broken poles, exposed wires on poles.
- Public Health: mosquito breeding, dead animals, stray dog attacks, unhygienic food, disease outbreaks.
- Encroachment: illegal hawkers, illegal construction, blocked footpaths, unauthorized structures.
- Other: noise, bus service, traffic signals, certificates, general feedback, unclear text.
Known hard case: a leaking water pipe flooding a road -> main category Water Supply, secondary_category Roads.

## 6. Dataset (ml/data/)
Files: complaints_train.csv (4800 rows), complaints_test.csv (1200 rows), complaints_external_test.csv (ChatGPT-written, independent; may be added later).
Columns: complaint_id, text, language (English|Hindi), category, department, secondary_category, priority,
location_type, duration_days, has_safety_risk, split, source.
Facts you must respect:
- Train/test are balanced: 750 rows per category, equal English/Hindi. Generated by ml/generate_dataset.py (template-based, seed 42).
- The TEST set uses DIFFERENT issue phrases and DIFFERENT openings/closings than train (phrase-disjoint). This is deliberate. Do not "fix" it.
- A random train/test split gives macro-F1 = 1.00 (meaningless: near-duplicates leak). The honest number is on complaints_test.csv.
- Baseline result so far: TF-IDF + LR, macro-F1 = 0.776 on complaints_test.csv (English 0.753, Hindi 0.788). Weakest class: Drainage (confused with Water Supply).
- The `priority` column was produced by simple rules; it is a REFERENCE for testing the rule engine only, and is circular. Never train the category model on it and never present it as ground truth.
- Data is synthetic. Do not tune the generator to hit a target accuracy.
Task for you first: write ml/src/validate_data.py that checks columns, allowed values, language-vs-script match (Hindi rows must contain Devanagari; English rows must not), duplicates, class balance, and train/test text overlap (must be zero).

## 7. Part 1: Semantic understanding of the text
Problems and solutions:
A) Spelling mistakes (potthole, pani/paani): character n-gram TF-IDF (analyzer="char_wb", ngram_range=(2,5), sublinear_tf=True) and transformer sub-word tokenizers.
B) Same meaning in different languages (pothole / खड्डा / गड्ढा): multilingual embeddings. Use MuRIL fine-tuning, and (optional experiment) frozen sentence embeddings (LaBSE or multilingual-e5 via sentence-transformers) + Logistic Regression.
C) Romanized Hindi (Hinglish): OUT OF SCOPE for now (future: IndicXlit transliteration to Devanagari).
Light cleaning only: Unicode normalisation (unicodedata NFC), trim spaces. Do NOT remove stopwords. Do not over-clean.
Add a small demo script ml/src/similarity_demo.py: encode "There is a big pothole on the road", "सड़क पर बड़ा गड्ढा है", and a garbage sentence, print cosine similarity matrix (shows cross-language meaning).
Note: this is learned semantic similarity, not human-level understanding. Say so in docs.

## 8. Part 2: Classification and routing
Models to compare (same train data, evaluate on same test data):
- M1 baseline: TfidfVectorizer(char_wb, 2-5, sublinear_tf, min_df=2) + LogisticRegression(class_weight="balanced", C=5, max_iter=2000), wrapped in CalibratedClassifierCV(method="sigmoid", cv=5).
- M2 (optional experiment): frozen LaBSE / multilingual-e5 embeddings + LogisticRegression.
- M3: fine-tuned google/muril-base-cased (Hugging Face Trainer, fp16 if GPU, epochs ~3-5, lr ~2e-5, batch 16-32, max_len 128, stratified train/validation split from TRAIN only) + temperature scaling on the validation set. Provide as a Colab-ready notebook since my laptop may lack a GPU. Do not use XLM-R unless I ask.
Decision rule: deploy the model with the better macro-F1 on complaints_test.csv; if within ~1-2 points, deploy the simpler one (M1) and say so honestly.
Calibration: calibrate probabilities, then show a reliability diagram and ECE.
Threshold: choose the confidence threshold from a coverage-vs-accuracy curve computed on a VALIDATION set (not the test set), then report the final numbers on the test set. Save curve plots to ml/reports/.
Reference numbers (M1, test set): threshold 0.70 -> 75% auto-routed at 88% accuracy; 0.85 -> 59% at 95%; 0.90 -> 51% at 96%.
Routing logic (backend/app/services/routing.py, plain Python, unit-tested):
  probs = model.predict_proba(text); top = argmax; conf = max
  category -> department via DB table (SQL lookup, never hard-coded)
  if category == "Other" -> review queue
  if conf < THRESHOLD or (top1 - top2) < MARGIN -> review queue (suggest the predicted department)
  else auto-route: pick officer in that department and ward with the fewest open complaints
  if second-best probability > SECONDARY_MIN -> store as secondary_category / secondary department note
  THRESHOLD, MARGIN, SECONDARY_MIN live in a config file, not in code.
Every admin/officer correction is saved in a `corrections` table (text, predicted, corrected) as future training data.
Report metrics with sklearn: classification_report, macro-F1 (overall and PER LANGUAGE), confusion matrix. Never report accuracy alone.

## 9. Part 3: Severity (rule-based, explainable)
Do NOT train an ML model for priority (no real ground truth exists). Use a transparent points system; show the officer the breakdown.
Config file (backend/app/config/severity.yaml), all values tunable:
- Category base risk: Roads 15, Drainage 15, Streetlight 15, Public Health 15, Water Supply 10, Garbage 8, Encroachment 5, Other 0.
- Danger words (English + Hindi lexicon): +5 each, max 25. Examples: accident, injured, children, school, hospital, deep, wire, electric shock, open manhole, flood, disease, dengue, दुर्घटना, बच्चे, स्कूल, अस्पताल, गहरा, तार, बिजली, खुला मैनहोल, बाढ़, बीमारी, डेंगू. Match by substring so Hindi suffixes still match.
- Location context: +20 if pin within ~200 m of a school or hospital, +10 if on a main road (Overpass API, cached); if no pin, use location_type words in text.
- Duration (regex over text: "2 days", "last week", "3 months", "दो दिन", "एक हफ्ते", "तीन महीने"): +5 if >= 3 days, +10 if >= 7 days.
- Repeat reports (similar complaints nearby via sentence embeddings + haversine distance): +3 each, max 15 (stretch feature; start with 0).
- Image evidence (stretch): +0..10.
- Levels: 0-29 low, 30-54 medium, 55-74 high, 75+ critical.
- CRITICAL OVERRIDE: phrases such as live/exposed electric wire, open manhole on a road, sewage mixing with drinking water, major flooding force "critical" and go to an urgent human queue regardless of classifier confidence.
- Do NOT use sentiment/anger as a priority signal (unfair to quiet or less articulate citizens).
Function signature idea: priority_score(text, category, loc_context, duration_days, similar_nearby) -> (level, score, breakdown_dict).
Validation: docs/priority_rubric.md defines low/medium/high/critical; later 2-3 teammates rate ~300 complaints independently; compute Cohen's kappa (sklearn.metrics.cohen_kappa_score) and agreement with the engine. The dataset `priority` column may be used as a quick sanity test only, and is not expected to match exactly.

## 10. Database (PostgreSQL via SQLAlchemy + Alembic)
users(id, name, email, password_hash, role[citizen|officer|admin], department_id, ward)
departments(id, name)
categories(id, name, department_id)
complaints(id, citizen_id, text, language, category_pred, confidence, category_final, department_id, secondary_category,
  priority_level, priority_score, priority_breakdown JSON, status[submitted|in_review|assigned|in_progress|resolved|reopened|closed],
  route_mode[auto|review], assigned_officer_id, lat, lng, address, ward, image_path, created_at, updated_at)
status_history(id, complaint_id, old_status, new_status, changed_by, note, proof_image_path, created_at)
corrections(id, complaint_id, text, predicted_category, corrected_category, corrected_by, created_at)
audit_log(id, user_id, action, entity, entity_id, details JSON, created_at)
Seed script: departments and categories from section 5, one admin, a few officers per department/ward, a few citizens.

## 11. Backend API (FastAPI)
GET /health
POST /auth/register, POST /auth/login (JWT), role-based dependencies (citizen/officer/admin)
POST /predict (text -> category, confidence, top-3 probs, department, priority) [uses the saved model]
POST /complaints (text, optional image, lat/lng, address) -> runs predict + severity + routing, stores everything
GET /complaints/mine, GET /complaints/{id}
Officer: GET /officer/complaints, PATCH /officer/complaints/{id}/status (with note and proof image)
Citizen: POST /complaints/{id}/confirm or /reopen, optional feedback
Admin: GET /admin/review-queue, POST /admin/complaints/{id}/route (correct department; writes `corrections`),
  CRUD for categories/departments/officers, GET /admin/analytics (counts, per-department workload, auto vs review rate, hotspot data)
Load the model once at startup. Write pytest tests for routing, severity and auth. Start with a DUMMY predictor that returns ("Roads", 0.90) so the rest of the app can be built before ML is plugged in; then swap in the real model behind the same interface (predict(text) -> category, confidence, probs).

## 12. Frontend (React + Vite + TS + Tailwind)
Pages: login/register; citizen complaint form (text, photo upload, Leaflet map pin, address, language auto-detected by script); my complaints with status timeline;
officer dashboard (assigned list, map, AI prediction + confidence + priority breakdown, status update + proof upload);
admin dashboard (review queue with suggested department, override control, category/department editor, analytics charts, hotspot map, model-performance page).
UI language switch English/Hindi with i18next. Show an explanation of why a priority was given. Mobile-friendly layout.

## 13. Evaluation to produce (for the report)
- Per-language macro-F1, confusion matrix, classification_report for every model, on complaints_test.csv (and on complaints_external_test.csv when available).
- Coverage-vs-accuracy curve and reliability diagram/ECE.
- Learning curve: train on 10/25/50/100% of train data, plot macro-F1.
- Model comparison table M1 vs M2 vs M3; final model decision with reasoning.
- Severity: agreement with human ratings (Cohen's kappa) once ratings exist.
- Optional small user study: people pick a department from a dropdown for ~20 complaints; compare their misrouting rate with the model.
Save all numbers to ml/reports/ as JSON/CSV/PNG so the report can cite them.

## 14. Phases (do ONE, then stop and report)
Phase 0: repo scaffolding, git init, .gitignore, docker-compose with PostgreSQL, Python venv + requirements, README, empty tests running.
Phase 1: ml/src/validate_data.py; reproduce the M1 baseline and the 0.776 macro-F1; add per-language metrics, confusion matrix, calibration check, coverage-vs-accuracy plot; save model with joblib.
Phase 2: backend core (DB models, migrations, seed, auth, complaints CRUD) using the DUMMY predictor.
Phase 3: routing service + officer assignment + review queue + corrections + tests; plug in the real M1 model.
Phase 4: severity engine + EN/HI lexicon + critical overrides + tests.
Phase 5: frontend (citizen, officer, admin) connected to the API.
Phase 6: MuRIL Colab notebook (+ temperature scaling), comparison table, final model decision, update the backend if M3 wins.
Phase 7 (only if time): analytics/hotspots, duplicate detection (LaBSE + haversine), explainability (LIME/SHAP or LR weights), officer-feedback retraining script.
Phase 8 (last, optional): pothole-only YOLO demo using Ultralytics YOLO fine-tuned on an Indian pothole dataset (e.g. BharatPotHole on Kaggle; check licences). Test on ~100 photos taken by us and report mAP50/precision/recall honestly. Note Ultralytics is AGPL-3.0. Skip entirely if time is short.

## 15. Out of scope for now (future work, mention in report)
Marathi and Hinglish, voice complaints (Whisper / AI4Bharat ASR), Telegram/WhatsApp bot, SLA breach prediction, more image classes, real municipal integration.

## 16. Honesty rules (also write these into README/report notes)
- The dataset is synthetic; results measure generalisation to unseen phrasings in OUR data, not real-world accuracy.
- Semantic "understanding" means learned similarity, not human comprehension.
- Severity weights are expert-defined starting values, validated against a small human sample; the dataset `priority` column is circular.
- Cross-language transfer is imperfect; Hindi is Devanagari only.
- The AI never makes unsafe automatic decisions: low confidence, close calls, "Other", and critical cases go to humans.

## 17. Current status
Done: dataset generated (6000 rows), M1 baseline trained (macro-F1 0.776 on the unseen-phrasing test set), plan finalised.
Pending: complaints_external_test.csv (ChatGPT-written test set), everything else in section 14.