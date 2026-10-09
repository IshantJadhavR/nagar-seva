from backend.app.services.routing import RoutingConfig, haversine_m, route_decision

CFG = RoutingConfig(threshold=0.7, margin=0.15, secondary_min=0.25)


def test_confident_auto_route():
    d = route_decision({"Roads": 0.9, "Garbage": 0.05, "Other": 0.05}, CFG)
    assert d["mode"] == "auto" and d["category"] == "Roads" and d["secondary"] is None


def test_low_confidence_goes_to_review():
    d = route_decision({"Roads": 0.6, "Garbage": 0.2, "Other": 0.2}, CFG)
    assert d["mode"] == "review" and any("below" in r for r in d["reasons"])


def test_close_call_goes_to_review():
    d = route_decision({"Water Supply": 0.52, "Drainage": 0.45, "Other": 0.03}, CFG)
    assert d["mode"] == "review" and any("too close" in r for r in d["reasons"])


def test_other_always_review():
    assert route_decision({"Other": 0.99, "Roads": 0.01}, CFG)["mode"] == "review"


def test_secondary_category_attached():
    d = route_decision({"Water Supply": 0.7, "Roads": 0.28, "Other": 0.02}, CFG)
    assert d["secondary"] == "Roads"


def test_haversine():
    assert haversine_m(19.0, 74.0, 19.0, 74.0) == 0
    assert 100 < haversine_m(19.0, 74.0, 19.0, 74.002) < 300
