# -*- coding: utf-8 -*-
"""
Rule-based, explainable severity scoring (English + Hindi). NOT a trained model:
there is no real ground truth for 'priority', so the officer sees exactly why a level was given.

Version 2 (rubric v2, see docs/priority_rubric.md): base risk re-set per category, plus a single
"policy_adjustment" line in the breakdown for the hygiene floor (High) and the footpath/stall rule.
Weights were tuned on a 48-complaint set A and checked once on a 52-complaint set B (see docs/priority_study).
"""
import re
import unicodedata

BASE_RISK = {"Roads": 55, "Drainage": 15, "Streetlight": 30, "Public Health": 15,
             "Water Supply": 30, "Garbage": 8, "Encroachment": 5, "Other": 30}
FOOTPATH_BASE = 5            # a broken/blocked footpath is not a carriageway hazard
HYGIENE_CATEGORIES = {"Garbage", "Public Health", "Drainage"}
HIGH_FLOOR, MEDIUM_FLOOR, LOW_CEILING = 55, 30, 29
POINTS_PER_DANGER_WORD, MAX_DANGER = 5, 25
LOC_SCHOOL_HOSPITAL, LOC_MAIN_ROAD = 20, 10
POINTS_PER_REPEAT, MAX_REPEAT = 3, 15
# "critical" is reserved for emergency phrases (find_critical) - points alone never reach it, so a
# routine pothole near a school stays High and the urgent queue is not flooded.
LEVELS = [(55, "high"), (30, "medium"), (0, "low")]


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFC", text).lower()
    return t.replace("\u093c", "")          # drop nukta so ज़/ज, बुज़ुर्ग/बुजुर्ग match


# ---- danger words (school/hospital are handled as LOCATION, not here, to avoid double counting)
_EN_DANGER = re.compile(r"\b(accidents?|injur\w*|child|children|kids?|elderly|dangerous|danger|unsafe|deep|crater|"
                        r"wires?|shock|slipp\w*|slip|falls?|falling|fell|diseases?|dengue|malaria|sick|fever|"
                        r"wiring|flood\w*|ambulances?|bites?|bitten|attack\w*)\b")
_HI_DANGER = ["दुर्घटना", "घायल", "बच्चे", "बच्चों", "बुजुर्ग", "खतरा", "खतरनाक", "असुरक्षित", "गहरा", "गहरे",
              "तार", "करंट", "फिसल", "गिर", "बीमार", "बीमारी", "डेंगू", "मलेरिया", "बुखार", "बाढ़", "बाढ",
              "जलभराव", "एम्बुलेंस", "एंबुलेंस", "काट", "हमला"]

# ---- critical emergencies: force 'critical' + urgent human queue
_CRITICAL = [
    (re.compile(r"\b(live|exposed|naked|hanging|loose|dangling)\b.{0,30}\bwires?\b"), "Exposed/live electric wire"),
    (re.compile(r"\bwires?\b.{0,25}\b(visible|exposed|hanging|dangling)\b"), "Exposed/live electric wire"),
    (re.compile(r"\b(open|uncovered)\s+manholes?\b|\bmanholes?\b.{0,30}\b(without|missing|uncovered|no cover)\b"), "Open manhole"),
    (re.compile(r"(sewage|sewer|sewerage|drain\w*).{0,40}(mix\w*|enter\w*|contaminat\w*).{0,30}(drinking|tap|water supply)"), "Sewage in drinking water"),
    (re.compile(r"(drinking|tap) water.{0,40}(sewage|sewer)"), "Sewage in drinking water"),
    (re.compile(r"\b(heavy|severe|major)\s+flood\w*"), "Major flooding"),
    (re.compile(r"electrocut\w*|electric shock"), "Electric shock risk"),
]
_HI_CRITICAL = [
    ("नंगे तार", "Exposed/live electric wire"), ("तार लटक", "Exposed/live electric wire"),
    ("तार दिख", "Exposed/live electric wire"), ("खुला मैनहोल", "Open manhole"),
    ("मैनहोल खुला", "Open manhole"), ("ढक्कन नहीं", "Open manhole / missing cover"),
    ("भारी जलभराव", "Major flooding"), ("करंट", "Electric shock risk"),
]
_HI_CRITICAL_RE = [(re.compile(r"सीवर.{0,40}पीने के पानी|पीने के पानी.{0,40}सीवर"), "Sewage in drinking water")]

# ---- location words in the text (used when the form has no map flags)
_SCHOOL = re.compile(r"school|college|स्कूल|विद्यालय|कॉलेज")
_HOSPITAL = re.compile(r"hospital|clinic|dispensary|अस्पताल|दवाखाना|क्लिनिक")
_MAIN_ROAD = re.compile(r"main road|highway|मुख्य सड़क|हाइवे|हाईवे")

_FOOTPATH = re.compile(r"footpath|pavement|sidewalk|फुटपाथ")
_INFO_REQUEST = re.compile(r"which (municipal )?office|where (to|do|can)|how (to|do) i|enquiry|inquiry|information|help desk|"
                           r"certificate|document|जानकारी|हेल्प डेस्क|दस्तावेज|प्रमाणपत्र")
# hygiene / public-health problems are High whenever present (rubric v2)
_WATER_CONTAMINATION = re.compile(r"yellow|odou?r|smell|dirty|muddy|contaminat|दुर्गंध|बदबू|गंदा|गंदगी|पीला")
_DRAIN_MILD = re.compile(r"silt|गाद")
_DRAIN_AGGRAVATOR = re.compile(r"overflow|flood|stagnant|mosquito|smell|odou?r|dirty|enter|मच्छर|बदबू|दुर्गंध|गंदा|जलभराव")
_NEAR_MISS = re.compile(r"(nearly|almost)\s+(fell|crashed|hit)|fell into|(was|got|were)\s+injured|दुर्घटना हो गई|गिर गया|गिर गई")
_LONG_STANDING = re.compile(r"for (a )?long time|since long|for months|long[- ]standing|लंबे समय|काफी समय|महीनों से|बहुत समय")

# ---- duration
_EN_NUM = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
           "eight": 8, "nine": 9, "ten": 10, "few": 3, "several": 3, "many": 3}
_HI_NUM = {"एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "छः": 6, "सात": 7, "आठ": 8,
           "नौ": 9, "दस": 10, "कई": 3, "कुछ": 3}
_EN_DUR = re.compile(r"\b(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|few|several|many)\s*\+?\s*"
                     r"(days?|weeks?|months?|years?)\b")
_HI_DUR = re.compile(r"(\d+|एक|दो|तीन|चार|पांच|पाँच|छह|छः|सात|आठ|नौ|दस|कई|कुछ)\s*(दिन\w*|हफ्त\w*|सप्ताह\w*|महीन\w*|माह|साल|वर्ष)")
_UNIT_DAYS = [("day", 1), ("week", 7), ("month", 30), ("year", 365)]


def _unit_days_en(u):
    return next(d for k, d in _UNIT_DAYS if u.startswith(k))


def _unit_days_hi(u):
    if u.startswith("दिन"):
        return 1
    if u.startswith(("हफ्त", "सप्ताह")):
        return 7
    if u.startswith(("महीन", "माह")):
        return 30
    return 365


def extract_duration_days(text: str):
    t = _norm(text)
    days = []
    for n, u in _EN_DUR.findall(t):
        days.append((int(n) if n.isdigit() else _EN_NUM[n]) * _unit_days_en(u))
    for n, u in _HI_DUR.findall(t):
        days.append((int(n) if n.isdigit() else _HI_NUM[n]) * _unit_days_hi(u))
    if re.search(r"last week|since last week|पिछले\s*(हफ्त|सप्ताह)", t):
        days.append(7)
    if re.search(r"last month|पिछले\s*(महीन|माह)", t):
        days.append(30)
    if re.search(r"since yesterday|कल से", t):
        days.append(1)
    if re.search(r"weekend", t):
        days.append(3)
    if _LONG_STANDING.search(t):
        days.append(30)
    return max(days) if days else None


def find_danger_words(text: str):
    t = _norm(text)
    found = {m.group(0) for m in _EN_DANGER.finditer(t)}
    found |= {w for w in _HI_DANGER if w in t}
    return sorted(found)


def find_critical(text: str):
    t = _norm(text)
    for rx, label in _CRITICAL:
        if rx.search(t):
            return label
    for phrase, label in _HI_CRITICAL:
        if phrase in t:
            return label
    for rx, label in _HI_CRITICAL_RE:
        if rx.search(t):
            return label
    return None


def level_for(score: int) -> str:
    return next(name for floor, name in LEVELS if score >= floor)


def priority_score(text, category, near_school=False, near_hospital=False, on_main_road=False,
                   duration_days=None, similar_nearby=0, map_places=None) -> dict:
    """map_places = what the map says is around the pin (see services/geo.py), e.g.
    {"school": {"name": "...", "distance_m": 80}, "hospital": None, "main_road": None}. It can only ADD location
    points (never more than the +20 a ticked checkbox gives) and never makes a complaint Critical on its own."""
    t = _norm(text)
    base = BASE_RISK.get(category, 0)
    if category == "Roads" and _FOOTPATH.search(t):
        base = FOOTPATH_BASE
    if category == "Other" and _INFO_REQUEST.search(t):
        base = 0                               # a pure information request is not a service failure
    parts = {"category_base_risk": base}
    words = find_danger_words(text)
    parts["danger_words"] = min(MAX_DANGER, POINTS_PER_DANGER_WORD * len(words))

    school = near_school or bool(_SCHOOL.search(t))
    hospital = near_hospital or bool(_HOSPITAL.search(t))
    road = on_main_road or bool(_MAIN_ROAD.search(t))
    text_or_form = LOC_SCHOOL_HOSPITAL if (school or hospital) else (LOC_MAIN_ROAD if road else 0)
    from .geo import evidence, map_points          # local import: severity stays usable without the geo module's deps
    from_map = map_points(map_places)
    parts["location_context"] = max(text_or_form, from_map)
    location_evidence = evidence(map_places) if from_map > text_or_form or (from_map and not text_or_form) else []

    days = duration_days if duration_days is not None else extract_duration_days(text)
    parts["duration"] = 10 if (days or 0) >= 7 else (5 if (days or 0) >= 3 else 0)
    parts["repeat_reports"] = min(MAX_REPEAT, POINTS_PER_REPEAT * max(0, similar_nearby))

    subtotal = sum(parts.values())
    adjustment, note = 0, None
    if category in HYGIENE_CATEGORIES or (category == "Water Supply" and _WATER_CONTAMINATION.search(t)):
        mild = category == "Drainage" and _DRAIN_MILD.search(t) and not _DRAIN_AGGRAVATOR.search(t)
        if not mild and subtotal < HIGH_FLOOR:
            adjustment, note = HIGH_FLOOR - subtotal, "Hygiene / public-health problem: at least High"
    elif category == "Encroachment":
        long_standing = (days or 0) >= 7
        if long_standing and subtotal < MEDIUM_FLOOR:
            adjustment, note = MEDIUM_FLOOR - subtotal, "Long-standing obstruction: at least Medium"
        elif not long_standing and subtotal > LOW_CEILING:
            adjustment, note = LOW_CEILING - subtotal, "Short or unstated duration obstruction: Low"
    parts["policy_adjustment"] = adjustment

    score = subtotal + adjustment
    level = level_for(score)
    critical = find_critical(text)
    if not critical and category == "Roads" and _NEAR_MISS.search(t):
        critical = "Injury or near-miss reported"
    if critical:
        level, score = "critical", max(score, 75)
    return {"level": level, "score": score, "breakdown": parts, "danger_words": words,
            "duration_days": days, "near_school_or_hospital": bool(school or hospital) or from_map >= LOC_SCHOOL_HOSPITAL,
            "location_evidence": location_evidence, "location_from_map": from_map > text_or_form,
            "policy_note": note, "critical_reason": critical, "critical": bool(critical)}
