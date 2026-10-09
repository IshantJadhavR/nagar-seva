# Nagar Seva – Multilingual Civic Complaint Triage System (English + Hindi)

> A citizen writes a civic problem (pothole, garbage, water leak…) in **English or Hindi**.
> The system reads it, picks the **department**, decides the **priority**, checks the **location**,
> and sends it to the right officer. **When it is not sure, or the problem is dangerous, a human decides.**

Built as a B.Tech final-year project. Everything used is **free and open source**.

---

## Table of contents

1. [What problem does it solve?](#1-what-problem-does-it-solve)
2. [Main features](#2-main-features)
3. [The three roles](#3-the-three-roles)
4. [How a complaint travels (the logic)](#4-how-a-complaint-travels-the-logic)
5. [Architecture](#5-architecture)
6. [Technology used (and why)](#6-technology-used-and-why)
7. [Project folder structure](#7-project-folder-structure)
8. [Quick start (Windows)](#8-quick-start-windows)
9. [Configuration (`.env`)](#9-configuration-env)
10. [Database](#10-database)
11. [Demo logins](#11-demo-logins)
12. [The AI model in detail](#12-the-ai-model-in-detail)
13. [Priority engine in detail](#13-priority-engine-in-detail)
14. [Location intelligence in detail](#14-location-intelligence-in-detail)
15. [Complaint status life-cycle](#15-complaint-status-life-cycle)
16. [Privacy and safety rules](#16-privacy-and-safety-rules)
17. [API endpoints](#17-api-endpoints)
18. [Database tables](#18-database-tables)
19. [Tests](#19-tests)
20. [Frontend pages](#20-frontend-pages)
21. [Glossary – every term explained](#21-glossary--every-term-explained)
22. [Troubleshooting](#22-troubleshooting)
23. [Honest limitations](#23-honest-limitations)
24. [Future work](#24-future-work)
25. [Working with GitHub](#25-working-with-github)

---

## 1. What problem does it solve?

In a city office, hundreds of complaints arrive every day.

- Staff read each complaint by hand and decide which department should get it. This is **slow**.
- A dangerous problem (an open drain next to a school) waits in the **same line** as a small one.
- Citizens do not know **who is handling** their complaint or what happened to it.
- Addresses written in words are often **wrong or unclear**, so officers waste time finding the place.

**Nagar Seva** fixes this with: automatic department selection, an **explainable** priority score,
map-based location checks, a human review step for anything risky, and a full status history that the
citizen can see.

---

## 2. Main features

| Feature | In simple words |
|---|---|
| English + Hindi | The whole website and the complaint reading work in both languages. Switch with the **EN / हिन्दी** button. |
| Automatic department | The AI reads the text and picks one of **8 categories**, each linked to a department. |
| Explained priority | High / Medium / Low / Critical, with a **points breakdown** so nobody has to trust a black box. |
| Human in the loop | Low confidence, category "Other", and critical complaints always go to a person. |
| Map pin | The citizen drops a pin on an OpenStreetMap map. |
| Location checks | Nearby school / hospital / main road add priority points. Typed address vs pin and photo GPS vs pin are compared. |
| Photo upload | Optional photo of the problem. |
| Wrong-location flow | An officer can report a wrong location; the admin fixes the pin. |
| Ask admin for help | An officer who cannot find the place can ask the admin, who may share the citizen's phone for that one complaint. |
| Reject option | The admin can reject fake or duplicate complaints with a written reason (the record is kept). |
| Status tracking | The citizen sees every change in a history timeline. |
| Rate and reopen | After resolution the citizen can confirm, rate, or reopen. |
| Role-based entry points | Separate Citizen / Officer / Admin cards on the front page and tabs on the login page. |
| User guide | Public bilingual guide at `/guide`. |
| Analytics | Admin charts: counts by category, priority and status. |
| Real database | PostgreSQL (SQLite for tests), plus a CSV export script. |

---

## 3. The three roles

| Role | Who | What they can do |
|---|---|---|
| **Citizen** | Any person | Sign up, report a problem (text, map pin, optional photo and phone), track status, confirm / rate / reopen, edit profile and phone. Sees **only their own** complaints. |
| **Officer** | Department staff | See complaints assigned to them (most urgent first), move status `assigned → in_progress → resolved` (a note is required to resolve), report a wrong location, ask the admin for help. Sees the citizen's phone **only if the admin shared it**. |
| **Admin** | Control-room head | Review the queue of complaints the AI was unsure about, assign a department / officer, fix locations, reject complaints, answer help requests, edit the category → department table, see analytics. Always sees the citizen's phone. |

Only **citizens** can sign up themselves. Officer and admin accounts are created by the administration
(seeded in `backend/app/seed.py`). A login attempt through the wrong role tab returns a clear message.

---

## 4. How a complaint travels (the logic)

```
 Citizen writes complaint (text + map pin + optional photo)
            │
            ▼
 1. LANGUAGE   detect English or Hindi (Devanagari letters)
            │
            ▼
 2. AI CLASSIFIER  → probability for each of the 8 categories
            │
            ▼
 3. PRIORITY ENGINE (rules)  → points → High / Medium / Low   (+ Critical for emergencies)
            │      uses: category risk, danger words, location, days open, repeat reports
            ▼
 4. LOCATION CHECKS  → school/hospital/main road nearby, address vs pin, photo GPS vs pin
            │
            ▼
        Sure and safe?
       ┌───────┴────────┐
      YES               NO  (low confidence, close top-2, "Other", critical)
       │                 │
       ▼                 ▼
 AUTO-ROUTE        ADMIN REVIEW QUEUE
 category→department   admin decides category / department
 → officer with the     → officer assigned
   fewest open cases
       └───────┬────────┘
               ▼
 OFFICER visits → in_progress → resolved   (can report wrong location / ask admin for help)
               ▼
 CITIZEN sees every status change → confirms (closed) or reopens
```

**The routing rule in one sentence:** a complaint is auto-routed only if the AI confidence is
**≥ 0.64**, the best category beats the second best by **≥ 0.10**, the category is **not "Other"**, and
the text has **no critical emergency phrase**. Otherwise a human decides.

**Officer choice:** an officer of the same department, preferring the same ward, with the **fewest open
complaints** (`assigned`, `in_progress`, `reopened`).

Every admin correction is stored in the `corrections` table so it can become **future training data**.

---

## 5. Architecture

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Citizen    │   │   Officer    │   │    Admin     │      (web browser)
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       └──────────────────┼──────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│ FRONTEND  React 18 + TypeScript + Vite + Tailwind        │
│ i18next (EN/हिन्दी) · Leaflet map · role-based pages      │
└──────────────────────────┬──────────────────────────────┘
                           │  HTTPS · JSON · JWT login token
                           ▼
┌─────────────────────────────────────────────────────────┐
│ BACKEND  FastAPI (Python)                                │
│  routers:  auth · complaints · officer · admin · geo ·   │
│            public                                        │
│  services: classifier · severity (priority) · routing ·  │
│            geo (location) · common                       │
└───────┬───────────────┬─────────────────┬───────────────┘
        ▼               ▼                 ▼
 PostgreSQL DB     Photo files       Free outside services
 (users, complaints, (backend/uploads) OpenStreetMap tiles,
  history, audit,                     Nominatim, Overpass
  geo_cache …)
        ▲
 ML model file  ml/models/model.joblib  (loaded by the classifier service)
```

The **browser never calls OpenStreetMap services directly for lookups**; the **server** does, so results
can be cached and rate-limited.

---

## 6. Technology used (and why)

| Part | Tool | Why we chose it |
|---|---|---|
| Server | **FastAPI** (Python) | Fast, simple, gives automatic API documentation at `/docs` |
| Database | **PostgreSQL** (SQLite for tests / zero-setup) | Real multi-user database, free |
| Database access | **SQLAlchemy 2** | Python classes instead of hand-written SQL |
| Login | **JWT** tokens + **bcrypt** password hashes | Standard and safe; passwords are never stored as text |
| Frontend | **React 18 + TypeScript + Vite** | Modern, fast, errors caught while coding |
| Styling | **Tailwind CSS v4** | Quick, consistent design |
| Languages | **i18next / react-i18next** | Switch English ↔ Hindi on every page |
| Maps | **Leaflet** + **OpenStreetMap** | Free, no API key needed |
| Icons | **lucide-react** | Clean icon set |
| ML | **scikit-learn** (TF-IDF + Logistic Regression), **joblib**, pandas, matplotlib | Light, explainable, runs on a laptop |
| Images | **Pillow** | Reads GPS data stored inside a photo (EXIF) |
| Tests | **pytest**, **httpx** | Automatic checking of the backend |
| Config | **python-dotenv** | Reads secrets from a `.env` file |

---

## 7. Project folder structure

```
complaint-triage/
├── README.md                  ← this file
├── .env.example               ← template for your secrets (copy to .env)
├── .gitignore                 ← files Git must NOT upload (.env, node_modules, uploads…)
├── requirements.txt           ← all Python packages
├── docker-compose.yml         ← optional ready-made PostgreSQL in Docker
├── CLAUDE.md                  ← notes file used during development
│
├── backend/                   ← the server (FastAPI)
│   ├── export_data.py         ← writes every table to CSV files (open in Excel)
│   ├── app/
│   │   ├── main.py            ← starts the app, connects routers, seeds data on start-up
│   │   ├── config.py          ← settings read from environment / .env
│   │   ├── database.py        ← database connection, sessions, adds new columns automatically
│   │   ├── models.py          ← database tables (users, complaints, …)
│   │   ├── schemas.py         ← rules for incoming/outgoing data (validation)
│   │   ├── auth.py            ← password hashing, JWT tokens, role checks
│   │   ├── seed.py            ← creates departments, categories and demo users
│   │   ├── routers/           ← the web addresses (endpoints)
│   │   │   ├── auth_router.py ← register, login, profile, phone, password
│   │   │   ├── complaints.py  ← predict, create, my complaints, photo, confirm, reopen
│   │   │   ├── officer.py     ← officer list, status update, wrong location, ask for help
│   │   │   ├── admin.py       ← review queue, route, reject, fix location, analytics, settings
│   │   │   ├── geo_router.py  ← map check and photo GPS check
│   │   │   └── public.py      ← public statistics for the front page
│   │   └── services/          ← the "brains"
│   │       ├── classifier.py  ← loads the AI model and predicts the category
│   │       ├── severity.py    ← priority engine (rules and points)
│   │       ├── routing.py     ← auto-route vs human, officer choice, repeat-report count
│   │       ├── geo.py         ← OpenStreetMap lookups, caching, photo GPS
│   │       └── common.py      ← shared helpers (output format, history, audit log)
│   └── tests/                 ← 41 automatic tests
│       ├── conftest.py        ← test set-up (uses a temporary SQLite file)
│       ├── test_api.py        ← end-to-end API tests
│       ├── test_geo.py        ← location feature tests (OSM replaced by fakes)
│       └── test_severity.py   ← priority engine tests
│
├── frontend/                  ← the website (React)
│   ├── package.json           ← JavaScript packages and scripts
│   ├── vite.config.ts         ← build tool settings
│   ├── public/images/         ← front-page photos (hero-office, pothole, drainage, garbage, streetlight, water-leak)
│   └── src/
│       ├── main.tsx, App.tsx  ← start-up and page routes
│       ├── api.ts             ← all calls to the backend
│       ├── auth.tsx           ← login state and token handling
│       ├── i18n.ts            ← language set-up
│       ├── types.ts           ← TypeScript types
│       ├── locales/en.json, hi.json  ← every text on the site, in both languages
│       ├── lib/               ← helpers (geo, roles, time in IST)
│       ├── components/        ← reusable parts (Layout, ComplaintCard, MapView, LocationPanel, Breakdown, Badges, Photo…)
│       └── pages/             ← one file per screen (Landing, Login, NewComplaint, MyComplaints, Officer,
│                                 AdminQueue, AdminAnalytics, AdminSettings, Profile, Guide)
│
├── ml/                        ← machine learning
│   ├── generate_dataset.py    ← creates the template complaint dataset (EN + HI)
│   ├── data/                  ← training and test CSV files
│   ├── src/
│   │   ├── validate_data.py   ← checks the CSV files
│   │   └── train_baseline.py  ← trains the model, picks the threshold, writes reports
│   ├── models/                ← model.joblib, model_template_only.joblib, routing_config.json
│   └── reports/               ← metrics.json and charts (confusion matrix, reliability, coverage)
│
└── docs/progress.md           ← progress log with numbers
```

---

## 8. Quick start (Windows)

You need: **Python 3.10+**, **Node.js 18+**, and (recommended) **PostgreSQL**.

### A. Get the code
```powershell
git clone https://github.com/IshantJadhavR/nagar-seva.git
cd nagar-seva
```

### B. Backend (first terminal)
```powershell
python -m venv .venv
.venv\Scripts\activate                       # if blocked:  Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
copy .env.example .env                       # then edit .env (see section 9)
pytest backend/tests -q                      # optional: 41 tests should pass
uvicorn backend.app.main:app --reload        # API at http://127.0.0.1:8000/docs
```
The **trained model is already included** in `ml/models/`. If the server complains about the model
(this can happen if your scikit-learn version is different), retrain it:
```powershell
python ml/src/validate_data.py
python ml/src/train_baseline.py              # about a minute
```

### C. Frontend (second terminal)
```powershell
cd frontend
npm install                                  # first time, or after package.json changes
npm run dev                                  # website at http://localhost:5173
```
Open **http://localhost:5173**. The website talks to the API on port **8000**, so keep both running.
Use port **5173** for the website, because the API only allows that address (CORS).

> Optional: put `VITE_SHOW_DEMO=false` in `frontend/.env` to hide the demo-login box.

---

## 9. Configuration (`.env`)

Copy `.env.example` to **`.env`** in the project root. **`.env` is never uploaded to GitHub** (it is in
`.gitignore`). Keep only the `.env` file with your real values; `.env.example` stays as the template.

| Setting | Meaning | Default |
|---|---|---|
| `SECRET_KEY` | Long random text used to sign login tokens. Make one with `python -c "import secrets; print(secrets.token_hex(32))"` | `dev-secret-change-me` (change it!) |
| `DATABASE_URL` | Which database to use | SQLite file `backend/complaints.db` |
| `TOKEN_MINUTES` | How long a login stays valid | `480` (8 hours) |
| `UPLOAD_DIR` | Where photos are saved | `backend/uploads` |
| `MODEL_DIR` | Where the model files are | `ml/models` |
| `CORS_ORIGINS` | Websites allowed to call the API | `http://localhost:5173,http://127.0.0.1:5173` |

Example PostgreSQL line:
```
DATABASE_URL=postgresql+psycopg2://postgres:YOURPASSWORD@localhost:5432/complaints
```
If the password has special characters, URL-encode them (`@` becomes `%40`, `#` becomes `%23`).

Photo rules: JPG, PNG or WebP, maximum **5 MB**.

---

## 10. Database

- **PostgreSQL (recommended).** Create an empty database called `complaints` (pgAdmin: right-click
  *Databases → Create*), set `DATABASE_URL` in `.env`, and start the backend. All tables and the demo
  accounts are **created automatically** on start-up.
- **SQLite (zero setup).** If `DATABASE_URL` is not set, a single file `backend/complaints.db` is used.
  The automatic tests **always** use a temporary SQLite file, never your real database.
- **Docker option.** `docker compose up -d` starts a ready-made PostgreSQL (user, password and database
  are all `complaints`).
- **See your data.** Use pgAdmin (*Schemas → public → Tables*), or run
  `python -m backend.export_data` to write every table to CSV files in an `exports/` folder
  (password hashes are **not** exported).
- **Seeding is safe to repeat.** `seed.py` checks every row individually, so restarting never creates
  duplicates. New columns added in later versions are added automatically (`ensure_columns`).
- **Times** are stored in UTC and shown in IST (Asia/Kolkata) in the browser.
- **Photos** are stored as files in `backend/uploads/<random-name>.jpg`; the database stores only the file name.

---

## 11. Demo logins

*(Demo only. Change these before any real use.)*

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `Admin@123` |
| Citizen | `citizen@example.com` | `Citizen@123` |
| Officer | see below | `Officer@123` |

Officer emails: `public.officer1@example.com`, `solid.officer1@example.com`, `water.officer1@example.com`,
`drainage.officer1@example.com`, `electrical.officer1@example.com`, `health.officer1@example.com`,
`building.officer1@example.com`. Each department also has `officer2` (officer1 = Ward-1, officer2 = Ward-2).

New citizens can sign up at `/register`. In the API docs (`/docs`) click **Authorize** and use the email as the username.
Try `POST /predict` first; it needs no login.

---

## 12. The AI model in detail

**Job:** read the complaint text and say which of the **8 categories** it belongs to.

**Labels (targets):** `Roads`, `Garbage`, `Water Supply`, `Drainage`, `Streetlight`, `Public Health`,
`Encroachment`, `Other`.

**Category → department** (editable by the admin without retraining):

| Category | Department |
|---|---|
| Roads | Public Works Department |
| Garbage | Solid Waste Management |
| Water Supply | Water Supply Department |
| Drainage | Drainage and Sewerage |
| Streetlight | Electrical Department |
| Public Health | Health Department |
| Encroachment | Building Permission and Encroachment |
| Other | Admin Review (always a human) |

**How the model works (3 steps):**

1. **TF-IDF with character n-grams (2 to 5 letters).** Turns text into numbers by counting small pieces of
   letters. Because it uses letter pieces, spelling mistakes, mixed Hindi-English words and different word
   forms still match.
2. **Logistic Regression.** The classifier that learns which letter pieces point to which category.
   Fast, small, and easy to explain.
3. **Calibration** (`CalibratedClassifierCV`, sigmoid, 5-fold). Makes the confidence number honest: if the
   model says 80 %, it should be right about 80 % of the time.

**Thresholds (when to trust the model)** – stored in `ml/models/routing_config.json`:

| Setting | Value | Meaning | How it was set |
|---|---|---|---|
| `threshold` | **0.64** | Below this confidence a human decides | The **lowest** value that still gave **90 % accuracy** on the validation set (scanned 0.40 to 0.99) |
| `margin` | **0.10** | The best category must beat the second best by this much | Set by hand |
| `secondary_min` | **0.25** | A second category is mentioned only if above this | Set by hand |
| Other / Critical | always human | Never auto-routed | Safety rule |

**Data:**
- **Template dataset** generated by `ml/generate_dataset.py`: 4800 training + 1200 test complaints, English and
  Hindi, balanced across the 8 categories. Train and test use **different phrases** (phrase-disjoint split),
  so the score is less inflated than a random split.
- **External set** (written separately and cleaned of duplicates): a capped pool (40 per category) is added to
  training, and a separate balanced external test set (1344 rows) is used only for final checking.

**Two models were compared** (macro-F1: average score across classes, higher is better):

| Model | Trained on | Template test | External test |
|---|---|---|---|
| A | Template data only | 0.776 | 0.802 |
| **B (used)** | Template + capped external pool | **0.815** | **0.853** |

- At the 0.64 threshold, model B handles **70.8 %** of external-test complaints automatically with
  **92.2 %** accuracy; the other ~29 % go to a human (the safe choice).
- **ECE** (calibration error) ≈ **0.03**, so the confidence numbers are reasonably honest.
- Hindi scores are as good as English, or better.
- Charts are in `ml/reports/`: confusion matrix, reliability diagram, coverage vs accuracy.

Re-train and re-create the reports any time with `python ml/src/train_baseline.py`.

---

## 13. Priority engine in detail

Priority is **not** guessed by the AI. It is a **rule-based point system** (`backend/app/services/severity.py`),
so the reason can always be shown to the citizen, officer and admin.

**Points that are added**

| Part | Points |
|---|---|
| Category base risk | Roads 55 · Streetlight 30 · Water Supply 30 · Other 30 · Drainage 15 · Public Health 15 · Garbage 8 · Encroachment 5 (a footpath problem counts as 5; a pure information request counts as 0) |
| Danger words (English + Hindi), e.g. accident, injured, child, wire, flood, dengue | 5 each, maximum 25 |
| Location context (school / hospital) | +20 within the text or on the form; from the map: **+20 within 150 m, +10 within 300 m** |
| Location context (main road) | +10 (map: within 30 m) |
| Days open (read from the text, e.g. "for 5 days") | 3+ days → +5 · 7+ days → +10 |
| Repeat reports (similar open complaints within 300 m) | 3 each, maximum 15 |
| Policy adjustment | Hygiene / public-health problems (Garbage, Public Health, Drainage, dirty/smelly water) are lifted to **at least High**; long-standing encroachment to **at least Medium**; short-term encroachment held at **Low** |

**Levels**

| Level | Rule |
|---|---|
| **High** | 55 points or more |
| **Medium** | 30 – 54 points |
| **Low** | below 30 points |
| **Critical** | Only from an **emergency phrase** (exposed / live wire, open manhole, sewage in drinking water, major flooding, electric shock; also in Hindi) or a **road near-miss / injury**. Always goes to the urgent human queue. |

The **map never creates a Critical** by itself, and a routine pothole near a school stays High, so the
urgent queue is not flooded. The breakdown is shown on every complaint card.

---

## 14. Location intelligence in detail

When a citizen drops a pin, the **server** (never the browser) asks free OpenStreetMap services:

- **Nominatim** (reverse geocoding): pin → address, shown as "Map says this place is…". The typed address is
  geocoded the other way and compared with the pin; **more than 500 m apart → flag** for review.
- **Overpass**: finds the nearest school/college, hospital/clinic and main road, which feed the priority points above.
- **Photo EXIF GPS**: if the phone saved the location inside the photo, it is compared with the pin;
  **more than 300 m apart → flag**.
- **Supported-area check**: a pin outside the rough bounding box set in `services/geo.py` is rejected (HTTP 422).
- **Fail-soft**: if OpenStreetMap is slow or down, the complaint is still accepted, just without the extra points.
- **Cache**: answers are saved in the `geo_cache` table for 30 days and calls are spaced out
  (about one per second for Nominatim) to respect the free usage policy.

**When the officer cannot find the place**
1. **Location is wrong** → the officer reports it; the complaint appears in the admin's *Location problems*
   list; the admin moves the pin on a map and priority is recalculated.
2. **I cannot find the place** → the officer sends a help request. The admin can reply and may **share the
   citizen's phone with that one officer for that one complaint**. Each share is written to the audit log.
3. **Reject / remove** → the admin can reject a fake, duplicate or unreachable complaint with a written
   reason. It is a **soft delete**: status becomes `rejected`, the record and reason stay for the audit trail.

---

## 15. Complaint status life-cycle

| Status | Meaning |
|---|---|
| `in_review` | Waiting in the admin queue (AI unsure, "Other", or critical) |
| `assigned` | Sent to an officer |
| `in_progress` | Officer is working on it |
| `resolved` | Officer finished (a note is required) |
| `closed` | Citizen confirmed the fix |
| `reopened` | Citizen says it is not fixed; goes back to an officer |
| `rejected` | Admin rejected it, with a reason |

Allowed officer moves: `assigned → in_progress`, `reopened → in_progress`, `in_progress → resolved`.
Every change is saved in `status_history` with who did it and a note.

---

## 16. Privacy and safety rules

- Only the **citizen, the assigned officer and the admin** can see a complaint.
- **Passwords** are stored as bcrypt hashes, never as text. Secrets live in `.env`, which is not uploaded to GitHub.
- The citizen's **phone number is optional**. The admin always sees it. An officer sees it **only if** the
  admin shared it, the complaint is still open, **and** that officer is the assigned one. Every share is audit-logged.
- Nothing risky is auto-routed: **Other**, low confidence, close top-2 and **critical** complaints go to a human.
- Login checks the **role**: using the wrong role tab returns a clear message instead of logging in.
- Photos are served by random file names. This is fine for a demo; a real deployment should use signed URLs.

---

## 17. API endpoints

Interactive documentation with a "Try it out" button: **http://127.0.0.1:8000/docs**

| Group | Method and path | Who | What it does |
|---|---|---|---|
| auth | `POST /auth/register` | public | Citizen sign-up (phone optional) |
| auth | `POST /auth/login` | public | Login (optional `role` check) → token |
| auth | `GET /auth/me`, `POST /auth/password`, `PUT /auth/phone` | logged in | Profile, change password, change phone |
| complaints | `POST /predict` | public | Try the classifier + priority on a text |
| complaints | `POST /complaints` | citizen | Create a complaint |
| complaints | `GET /complaints/mine`, `GET /complaints/{id}` | citizen / allowed viewers | List and details |
| complaints | `POST /complaints/{id}/image` | citizen | Upload a photo |
| complaints | `POST /complaints/{id}/confirm`, `/reopen` | citizen | Confirm fix (with rating) or reopen |
| officer | `GET /officer/complaints` | officer | Assigned complaints, most urgent first |
| officer | `PATCH /officer/complaints/{id}/status` | officer | Update status |
| officer | `POST /officer/complaints/{id}/wrong-location`, `/help` | officer | Report wrong location, ask admin for help |
| admin | `GET /admin/review-queue`, `/location-problems` | admin | Work lists |
| admin | `POST /admin/complaints/{id}/route`, `/location`, `/help-reply`, `/reject` | admin | Route, fix location, reply to help, reject |
| admin | `GET /admin/departments`, `/categories`, `/officers`, `/analytics` | admin | Reference data and charts |
| admin | `PATCH /admin/categories/{id}` | admin | Change category → department |
| geo | `POST /geo/check`, `/geo/photo-gps` | citizen | Map check, read photo GPS |
| public | `GET /public/stats` | public | Numbers for the front page |
| system | `GET /health` | public | "ok" |

---

## 18. Database tables

| Table | Holds |
|---|---|
| `users` | name, email, password hash, role (citizen / officer / admin), department, ward, optional phone |
| `departments` | the 7 departments plus "Admin Review" |
| `categories` | the 8 categories and the department each belongs to |
| `complaints` | text, language, predicted + final category, confidence, probabilities, priority level / score / breakdown, status, route mode and reason, assigned officer, pin (lat, lng), address, ward, photo name, map check results, location flag, help request, rating, feedback, times |
| `status_history` | every status change: old → new, who, note, optional proof photo |
| `corrections` | admin fixes of the AI category (future training data) |
| `audit_log` | important actions (status updates, phone sharing, rejections…) |
| `geo_cache` | saved OpenStreetMap answers (30 days) |

---

## 19. Tests

```powershell
pytest backend/tests -q        # 41 tests
```
- `test_api.py` (15): registration, login, role rules, create, route, officer flow, reject, help and phone privacy.
- `test_geo.py` (15): location points, flags, caching, fail-soft behaviour. Real OpenStreetMap is replaced by fake answers.
- `test_severity.py` (11): priority rules, Hindi phrases, critical overrides.

Tests use a temporary SQLite file and never touch your real database.

---

## 20. Frontend pages

| Page | Address | For |
|---|---|---|
| Landing | `/` | Everyone: three role cards, photo gallery, how it works |
| Login / Sign up | `/login`, `/register` | Role tabs (`/login?as=officer`); only citizens can sign up |
| User guide | `/guide` | Everyone (`?for=officer`, `?for=admin`) |
| New complaint | `/new` | Citizen: text, map pin, photo, phone |
| My complaints | `/mine` | Citizen: list, status timeline, confirm / reopen |
| Officer dashboard | `/officer` | Officer |
| Admin queue | `/admin/queue` | Admin: review queue, location problems, help requests |
| Analytics | `/admin/analytics` | Admin |
| Settings | `/admin/settings` | Admin: category → department table |
| Profile | `/profile` | Any logged-in user |

Photos on the front page are in `frontend/public/images/`. If a photo is missing, a drawn illustration is
shown instead. **The sample photos are AI-generated illustrations, not real complaint photos.**

---

## 21. Glossary – every term explained

| Term | Simple meaning |
|---|---|
| **Triage** | Sorting problems by type and urgency, like a hospital emergency desk. |
| **Classifier** | A program that puts text into one of a fixed set of groups. |
| **Label / category** | One of the 8 groups (Roads, Garbage…). |
| **TF-IDF** | A way to turn text into numbers by counting how often pieces of text appear and how special they are. |
| **Character n-gram** | A small piece of 2–5 letters. Matching on pieces survives spelling mistakes. |
| **Logistic Regression** | A simple, fast classifier that gives a probability for each category. |
| **Probability / confidence** | How sure the model is (0 to 1). |
| **Calibration** | Adjusting confidence so "80 %" really means right 80 % of the time. |
| **ECE** | Expected Calibration Error: how far confidence is from reality (lower is better; ours ≈ 0.03). |
| **Threshold** | A cut-off. Below it, a human decides. |
| **Margin** | The gap between the best and the second-best category. Small gap = unsure. |
| **Macro-F1** | A score from 0 to 1 averaging how well the model does on every class equally. |
| **Accuracy** | Share of answers that are correct. |
| **Coverage** | Share of complaints the system handles automatically. |
| **Validation set / test set** | Data used to choose settings / to check the final result honestly. |
| **Phrase-disjoint split** | Train and test use different sentences, so the test is harder and fairer. |
| **Human in the loop** | A person makes the final call when the system is unsure or the case is risky. |
| **Rule-based** | Decisions made by written rules, not learned. Easy to explain. |
| **Priority breakdown** | The list of points that explains why a complaint is High, Medium or Low. |
| **Critical** | An emergency (live wire, open manhole…). Always seen by a human first. |
| **Geocoding** | Turning an address into a map point (forward) or a map point into an address (reverse). |
| **Nominatim** | Free OpenStreetMap service for geocoding. |
| **Overpass** | Free OpenStreetMap service to search nearby places (schools, hospitals, roads). |
| **OpenStreetMap (OSM)** | The free, community-made map of the world. |
| **EXIF** | Extra data a phone stores inside a photo, sometimes including GPS. |
| **Haversine distance** | The formula for distance in metres between two map points. |
| **Fail-soft** | If an outside service is down, the app keeps working with fewer features. |
| **Cache** | A saved copy of an earlier answer so the same question is not asked twice. |
| **JWT** | A signed login token the browser sends with each request. |
| **bcrypt** | A method that scrambles passwords so they cannot be read back. |
| **Role** | citizen, officer or admin: decides what a person can see and do. |
| **CORS** | A browser rule; the API only accepts calls from the allowed website address. |
| **API / endpoint** | The web address the website uses to ask the server for something. |
| **FastAPI** | The Python tool that builds our API. |
| **ORM / SQLAlchemy** | Lets Python classes stand for database tables. |
| **Soft delete** | Marking a record as removed (`rejected`) instead of erasing it. |
| **Audit log** | A permanent record of important actions and who did them. |
| **Seed** | Starter data created automatically (departments, categories, demo users). |
| **i18n** | "Internationalisation": supporting several languages. |
| **Ward** | A small area of the city; officers are matched to a ward when possible. |
| **Virtual environment (`.venv`)** | A private folder of Python packages for this project only. |
| **`.env`** | A private settings file with secrets. Never uploaded to GitHub. |

---

## 22. Troubleshooting

| Problem | Fix |
|---|---|
| "Cannot reach the server. Is the backend running on http://127.0.0.1:8000?" | Start the backend (`uvicorn backend.app.main:app --reload`) and keep that window open. Open the website on **port 5173**. |
| Backend crashes on start with `UniqueViolation` | Pull the latest code; seeding is now safe to repeat. |
| `password authentication failed` | The password in `DATABASE_URL` is wrong. Encode special characters (`@` → `%40`). |
| `database "complaints" does not exist` | Create an empty database named `complaints` in pgAdmin. |
| Model file error / scikit-learn version warning | Retrain: `python ml/src/train_baseline.py`. |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope Process Bypass`, then activate again. |
| Map does not show places or addresses | OpenStreetMap may be slow or down; complaints still work. Try again later. |
| Login says "This is a citizen / officer / admin account" | Use the matching role tab on the login page. |
| Old SQLite complaints missing after moving to PostgreSQL | The two databases are separate; data is not copied automatically. |
| Page looks old after an update | Hard refresh with `Ctrl + F5`. |

---

## 23. Honest limitations

- **Data is mostly generated** (template script plus a separately written set). Scores show how well the model
  handles unseen phrasings in our data, **not** real-world accuracy.
- The `priority` column in the CSV files is a reference for testing only; the priority engine was **not** tuned to match it.
- **English and Hindi only.** Marathi and mixed Hindi-English (Hinglish) are not covered.
- OpenStreetMap coverage is **thin in villages**, so nearby school / hospital checks can miss places.
- Many phones **remove GPS from photos**, so the photo check does not always work.
- The supported-area bounding box is rough.
- Sample photos on the front page are **AI-generated**.
- Uploaded photos are served by random file name, not behind login (acceptable for a demo only).
- Demo passwords are public; change them before any real use.

---

## 24. Future work

- Stronger language model for Indian languages (for example MuRIL), compared with the current baseline.
- Marathi and Hinglish support.
- Duplicate-complaint detection (for example with text embeddings).
- Admin page to manage staff and see all users.
- SMS / WhatsApp updates to citizens.
- A mobile app.
- A script to copy old SQLite data into PostgreSQL.
- Retraining the model regularly from the `corrections` table.

---

## 25. Working with GitHub

First upload (already done for this project):
```powershell
cd D:\complaint-triage
git init
git add .
git commit -m "message"
git branch -M main
git remote add origin https://github.com/IshantJadhavR/nagar-seva.git
git push -u origin main
```
After any change:
```powershell
git add .
git commit -m "what you changed"
git push
```
Check `git status` before committing: `.env` must **not** appear in the list.
