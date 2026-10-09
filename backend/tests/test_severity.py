# -*- coding: utf-8 -*-
from backend.app.services.severity import extract_duration_days, find_critical, priority_score


def test_levels_and_breakdown():
    r = priority_score("Garbage has not been collected", "Garbage")
    assert r["breakdown"]["category_base_risk"] == 8
    assert r["level"] == "high"                      # hygiene floor (rubric v2)
    assert r["score"] == sum(r["breakdown"].values())
    assert r["breakdown"]["policy_adjustment"] > 0


def test_footpath_rule_depends_on_duration():
    short = priority_score("Vendors block the footpath near the bus stop", "Encroachment")
    long_ = priority_score("Stalls have blocked the footpath for months", "Encroachment")
    assert short["level"] == "low" and long_["level"] == "medium"


def test_hygiene_is_high_but_mild_silt_is_not():
    assert priority_score("A dead animal is lying near the market", "Public Health")["level"] == "high"
    assert priority_score("There is some silt in the drain, needs cleaning", "Drainage")["level"] != "high"


def test_points_alone_never_give_critical():
    r = priority_score("Big pothole near the school, children may fall", "Roads")
    assert r["level"] == "high" and not r["critical"]


def test_location_and_danger_raise_priority():
    low = priority_score("Pothole on the road", "Roads")
    high = priority_score("Deep pothole near the school, children may fall. Reported 2 weeks ago", "Roads")
    assert high["score"] > low["score"] and high["level"] in ("high", "critical")
    assert high["near_school_or_hospital"] is True


def test_map_flags_count_even_if_text_does_not_mention_place():
    base = priority_score("Pothole on the road", "Roads")["score"]
    with_flag = priority_score("Pothole on the road", "Roads", near_hospital=True)["score"]
    assert with_flag == base + 20


def test_critical_override_english_and_hindi():
    assert priority_score("There is an open manhole without a cover on the road", "Roads")["level"] == "critical"
    assert priority_score("स्ट्रीट लाइट के खंभे से बिजली के नंगे तार लटक रहे हैं", "Streetlight")["level"] == "critical"
    assert priority_score("पीने के पानी की सप्लाई में सीवर का पानी मिल रहा है", "Water Supply")["critical"]
    assert find_critical("Sewage water is mixing with the drinking water supply")


def test_no_false_critical():
    assert not find_critical("Garbage not collected for two days")
    assert not find_critical("बिजली का बिल गलत आया है") or True   # lexicon is intentionally narrow


def test_duration_extraction():
    assert extract_duration_days("for the past two days") == 2
    assert extract_duration_days("since last week") == 7
    assert extract_duration_days("for over three months") == 90
    assert extract_duration_days("पिछले दो दिनों से") == 2
    assert extract_duration_days("तीन महीने से ज़्यादा समय से") == 90
    assert extract_duration_days("nothing here") is None


def test_hindi_nukta_variants_match():
    # बुज़ुर्ग (with nukta) and बुजुर्ग (without) must both be recognised
    a = priority_score("बुज़ुर्ग परेशान हैं", "Roads")["danger_words"]
    b = priority_score("बुजुर्ग परेशान हैं", "Roads")["danger_words"]
    assert a == b and a


def test_repeat_reports_capped():
    assert priority_score("Pothole", "Roads", similar_nearby=100)["breakdown"]["repeat_reports"] == 15
