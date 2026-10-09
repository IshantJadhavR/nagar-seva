# Multilingual Civic Complaint Triage System (English + Hindi)

Citizens describe a civic problem in their own words. The system predicts the **category**, maps it to a
**department**, scores **severity** with transparent rules, and **auto-routes only when confident**;
uncertain, "Other" and critical-safety cases go to a human review queue.

## Run it (Windows PowerShell, from this folder)
```powershell
python -m venv .venv
.venv\Scripts\activate                      # if blocked:  Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
python ml/src/validate_data.py              # checks the CSV files
python ml/src/train_baseline.py             # trains + saves ml/models/model.joblib (about a minute)
pytest backend/tests -q                     # 25 tests
uvicorn backend.app.main:app --reload       # API at http://127.0.0.1:8000/docs
```
Always retrain on your own machine (the model file depends on your scikit-learn version).

## Run the website (second terminal)
```powershell
cd frontend
npm install        # first time, or after package.json changes
npm run dev        # http://localhost:5173
```
Optional: copy `.env.example` to `.env` and set a long `SECRET_KEY`. Set `VITE_SHOW_DEMO=false` in `frontend/.env` to hide the demo-login box.

## Accounts and where they live
- **Citizens** sign up themselves at `/register`. Anyone can have an account; each sees only their own complaints.
- **Officers and admin** are created by the project team (seeded in `backend/app/seed.py`). They log in on the same page.
- All accounts are rows in the `users` table (`backend/complaints.db`). Passwords are stored as bcrypt hashes, never as text.
- Times are stored in UTC and shown in IST (Asia/Kolkata) in the browser.

## Database
Default is SQLite (a real SQL database in one file, no install). **PostgreSQL is recommended** (tested end to end with PostgreSQL 16):
1. Create an empty database called `complaints` (pgAdmin: right-click Databases, Create).
2. `pip install -r requirements.txt` (includes the PostgreSQL driver).
3. In `.env` set `DATABASE_URL=postgresql+psycopg2://postgres:YOURPASSWORD@localhost:5432/complaints`
   (if the password has special characters such as `@` or `#`, URL-encode them, e.g. `@` becomes `%40`).
4. Start the backend. Tables and demo accounts are created automatically. Browse the data in pgAdmin (Schemas, public, Tables).
The automated tests always use a temporary SQLite file, never your real database. `python -m backend.export_data` writes every table to CSV files for Excel.
`docker compose up -d` also starts a ready-made PostgreSQL if you prefer Docker.

## Login pages and user guide
The home page shows three role cards (Citizen, Officer, Admin). The login page has the same three tabs (`/login?as=officer`), and if someone picks the wrong tab the server says which kind of account it is. Only citizens can sign up; officer and admin accounts are created by the administration. A public, bilingual **User guide** is at `/guide` (`/guide?for=officer`, `?for=admin`).

## Demo logins (demo only, change before any real use)
| Role | Email | Password |
|---|---|---|
| Admin | admin@example.com | Admin@123 |
| Citizen | citizen@example.com | Citizen@123 |
| Officer | see the list below | Officer@123 |

Officer emails: `public.officer1@example.com`, `solid.officer1@example.com`, `water.officer1@example.com`,
`drainage.officer1@example.com`, `electrical.officer1@example.com`, `health.officer1@example.com`,
`building.officer1@example.com` (each department also has `officer2`; officer1 = Ward-1, officer2 = Ward-2).

In `/docs` click **Authorize** and log in with email as the username. Try `POST /predict` first (no login needed).

## Location intelligence (free, OpenStreetMap)
When a citizen drops a pin, the server (never the browser) asks OpenStreetMap:
- **Nominatim** (reverse geocoding): pin to address, shown as "Map says this place is...". Typed address is geocoded the other way and compared with the pin (flag if more than 500 m apart).
- **Overpass**: nearest school/college, hospital/clinic and main road. School/hospital within 150 m gives +20 priority points, within 300 m gives +10, main road within 30 m gives +10. This only ADDS location points (never above what the checkbox gives) and never makes a complaint Critical.
- **Photo EXIF**: the photo's own GPS (if the phone saved it) is compared with the pin; more than 300 m apart raises a flag.
- **Safety nets**: pin outside Maharashtra is rejected (422); an officer can press "Location is wrong"; the admin sees a "Location problems" list and moves the pin (priority is recalculated).
- If OSM is down or slow, everything still works (fail-soft). Answers are cached in the `geo_cache` table for 30 days to respect the free usage policy (max 1 request per second).
- Photos are saved in `backend/uploads/<random>.jpg`; only that file name is stored in the database. After pulling these changes run `pip install -r requirements.txt` (adds Pillow). New database columns are added automatically at startup (`ensure_columns`).
- Limits: OSM coverage is thinner in villages, many apps strip photo GPS, and the Maharashtra bounding box is rough.

### When the officer cannot find the place
- **Wrong location**: the officer presses "Location is wrong"; the admin moves the pin on a map.
- **Ask for help**: "I cannot find the place" sends a message to the admin. The admin can reply, and can choose to share the citizen's phone number with that one officer for that one complaint (it is recorded in the audit log, hidden again once the complaint is resolved, and never shown to other officers or to anyone else). Citizens add an optional mobile number when they sign up or on their Profile page.
- **Reject / remove**: the admin can reject a fake, duplicate or unreachable complaint with a written reason. The record is kept (status "rejected", reason visible to the citizen) instead of being erased, so there is always an audit trail.

## How routing works
1. Model gives a probability per category (TF-IDF char n-grams + Logistic Regression, calibrated).
2. Auto-route only if confidence >= threshold (0.64, chosen on a validation set), top-2 gap >= 0.10, and the
   category is not "Other". Otherwise the complaint waits in the admin review queue.
3. Critical phrases (live wire, open manhole, sewage in drinking water, major flooding) always go to the urgent
   human queue, whatever the model says.
4. Category -> department comes from a database table the admin can edit (no retraining).
5. Officer = same department, preferring the same ward, with the fewest open complaints.
6. Every admin decision is stored in `corrections` (future training data).

## Folder map
`ml/` data, training scripts, saved reports | `backend/` FastAPI app + tests | `docs/` notes and progress log

## Honest limitations
- All data is synthetic (template script + ChatGPT-written). Scores measure generalisation to unseen phrasings in
  our data, not real-world accuracy.
- The `priority` column in the CSVs is a reference for testing the rule engine only (it is circular).
- English + Hindi (Devanagari) only. Marathi and Hinglish are future work.
- Demo database is SQLite for zero setup; set `DATABASE_URL` to use PostgreSQL.
