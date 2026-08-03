# settings_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

settings_bp = Blueprint("settings_bp", __name__)

# ============================
# BUSINESS SETTINGS (AdminSettings.vue)
# ============================

business_settings = {
    "businessName": "Traveling Star Service",
    "contact": "252 886-5996",
    "phone": "252 886-5996",
    "email": "hello@travelingstarservice.com",
    "serviceArea": "Rocky Mount, NC",
    "localAreas": ["Rocky Mount", "Nash County", "Wilson", "Greenville"],
    "services": ["Airport transfers", "Local rides", "Events and gatherings", "Custom routes"],
    "newsTopics": ["transportation", "travel", "local events"],
    "weatherEnabled": True,
    "newsEnabled": True,
    "videoEnabled": True,
    "logo": "",
    "hero": "Your gateway to unforgettable journeys.",
    "design": {
        "primaryColor": "#c61e1e",
        "secondaryColor": "#2e9f2f",
        "accentColor": "#e0b63a",
        "homeLayout": "hero-grid",
        "showBanner": True,
        "showFlagLogo": True
    },
    "podcast": {
        "enabled": True,
        "defaultStyle": "business",
        "voiceEnabled": True,
        "allowCustomerGeneration": True,
        "includeWeatherByDefault": True,
        "includeNewsByDefault": True,
        "includeVisualsByDefault": True
    },
    "payments": {
        "enableDebit": True,
        "enableCredit": True,
        "enableInstantBankTransfer": True,
        "enableSecureLink": True,
        "supportPhone": "252 886-5996"
    },
    "bankInfo": {
        "bankName": "",
        "accountHolder": "Traveling Star Service",
        "accountNumberLast4": "",
        "routingLast4": "",
        "zelleEmail": "",
        "cashAppTag": "",
        "paymentInstructions": "Call or text 252 886-5996 to confirm secure bank details."
    }
}


def _as_list(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]
    return []


def _coerce_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def _update_nested(target, incoming, expected_keys):
    if not isinstance(incoming, dict):
        return

    for key in expected_keys:
        if key in incoming:
            target[key] = incoming.get(key)


def _require_admin_claims():
    claims = get_jwt()
    if (claims.get("role") or "").lower() != "admin":
        return jsonify({"error": "admin access required"}), 403
    return None


@settings_bp.get("")
def get_settings():
    return jsonify(business_settings)


@settings_bp.post("")
@jwt_required()
def update_settings():
    denied = _require_admin_claims()
    if denied:
        return denied

    data = request.get_json() or {}

    business_settings["businessName"] = data.get("businessName", business_settings["businessName"])
    business_settings["contact"] = data.get("contact", business_settings["contact"])
    business_settings["phone"] = data.get("phone", business_settings["phone"])
    business_settings["email"] = data.get("email", business_settings["email"])
    business_settings["serviceArea"] = data.get("serviceArea", business_settings["serviceArea"])

    local_areas = _as_list(data.get("localAreas"))
    if local_areas:
        business_settings["localAreas"] = local_areas

    services = _as_list(data.get("services"))
    if services:
        business_settings["services"] = services

    news_topics = _as_list(data.get("newsTopics"))
    if news_topics:
        business_settings["newsTopics"] = news_topics

    if "weatherEnabled" in data:
        business_settings["weatherEnabled"] = _coerce_bool(data.get("weatherEnabled"), business_settings["weatherEnabled"])
    if "newsEnabled" in data:
        business_settings["newsEnabled"] = _coerce_bool(data.get("newsEnabled"), business_settings["newsEnabled"])
    if "videoEnabled" in data:
        business_settings["videoEnabled"] = _coerce_bool(data.get("videoEnabled"), business_settings["videoEnabled"])

    business_settings["hero"] = data.get("hero", business_settings.get("hero", "Your gateway to unforgettable journeys."))

    _update_nested(
        business_settings["design"],
        data.get("design"),
        {"primaryColor", "secondaryColor", "accentColor", "homeLayout", "showBanner", "showFlagLogo"}
    )
    _update_nested(
        business_settings["podcast"],
        data.get("podcast"),
        {
            "enabled",
            "defaultStyle",
            "voiceEnabled",
            "allowCustomerGeneration",
            "includeWeatherByDefault",
            "includeNewsByDefault",
            "includeVisualsByDefault"
        }
    )
    _update_nested(
        business_settings["payments"],
        data.get("payments"),
        {"enableDebit", "enableCredit", "enableInstantBankTransfer", "enableSecureLink", "supportPhone"}
    )
    _update_nested(
        business_settings["bankInfo"],
        data.get("bankInfo"),
        {
            "bankName",
            "accountHolder",
            "accountNumberLast4",
            "routingLast4",
            "zelleEmail",
            "cashAppTag",
            "paymentInstructions"
        }
    )

    if "logo" in data:
        business_settings["logo"] = data.get("logo")

    return jsonify({
        "message": "Settings updated",
        "settings": business_settings
    })


@settings_bp.get("/homepage")
def get_homepage_settings():
    return jsonify({"hero": business_settings.get("hero", "Your gateway to unforgettable journeys.")})


@settings_bp.post("/homepage")
@jwt_required()
def update_homepage_settings():
    denied = _require_admin_claims()
    if denied:
        return denied

    data = request.get_json() or {}
    business_settings["hero"] = data.get("hero", business_settings.get("hero", "Your gateway to unforgettable journeys."))
    return jsonify({
        "message": "Homepage updated",
        "hero": business_settings["hero"]
    })


@settings_bp.get("/logo")
def get_logo():
    return jsonify({"logo": business_settings.get("logo", "")})


@settings_bp.post("/logo")
@jwt_required()
def update_logo():
    denied = _require_admin_claims()
    if denied:
        return denied

    data = request.get_json() or {}
    business_settings["logo"] = data.get("logo", business_settings.get("logo", ""))
    return jsonify({
        "message": "Logo updated",
        "logo": business_settings["logo"]
    })


# ============================
# PAYMENTS & PRICING (Payments.vue)
# ============================

pricing = {
    "baseRate": 50,
    "perMile": 2.50
}


@settings_bp.get("/payments")
def get_payments():
    return jsonify({
        "pricing": pricing,
        "methods": business_settings.get("payments", {}),
        "bankInfo": business_settings.get("bankInfo", {})
    })


@settings_bp.post("/payments")
@jwt_required()
def update_payments():
    denied = _require_admin_claims()
    if denied:
        return denied

    data = request.get_json() or {}

    pricing["baseRate"] = float(data.get("baseRate", pricing["baseRate"]))
    pricing["perMile"] = float(data.get("perMile", pricing["perMile"]))

    _update_nested(
        business_settings["payments"],
        data.get("methods"),
        {"enableDebit", "enableCredit", "enableInstantBankTransfer", "enableSecureLink", "supportPhone"}
    )
    _update_nested(
        business_settings["bankInfo"],
        data.get("bankInfo"),
        {
            "bankName",
            "accountHolder",
            "accountNumberLast4",
            "routingLast4",
            "zelleEmail",
            "cashAppTag",
            "paymentInstructions"
        }
    )

    return jsonify({
        "message": "Pricing updated",
        "pricing": pricing,
        "methods": business_settings.get("payments", {}),
        "bankInfo": business_settings.get("bankInfo", {})
    })
