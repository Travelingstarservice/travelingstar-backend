# settings_routes.py
import json

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from models.user import User
from models.site_config import SiteConfig
from extensions import db

settings_bp = Blueprint("settings_bp", __name__)


DEFAULT_SITE_CONFIG = {
    "brandName": "Traveling Star Service",
    "showBanner": True,
    "bannerImage": "/traveling-star-flag.jpeg",
    "services": [
        {
            "name": "Airport transfers",
            "description": "Efficient pickup and drop-off for early departures, late arrivals, and everything in between."
        },
        {
            "name": "Local rides",
            "description": "Quick trips across town for errands, appointments, and essential travel."
        },
        {
            "name": "Events and gatherings",
            "description": "Arrive together and leave on your own timeline with flexible service plans."
        },
        {
            "name": "Custom routes",
            "description": "Need something specific? Send the route details and we'll work around your schedule."
        }
    ],
    "fleet": [
        {
            "name": "Local Ride Team",
            "description": "Daily city and county pickup/drop-off service coverage."
        },
        {
            "name": "Airport Transfer Team",
            "description": "Dedicated airport schedule and long-distance trip windows."
        }
    ]
}


def _normalize_site_items(items, fallback):
    if not isinstance(items, list):
        return [dict(item) for item in fallback]

    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get('name', '')).strip()
        description = str(item.get('description', '')).strip()
        if not name or not description:
            continue
        normalized.append({"name": name, "description": description})

    return normalized if normalized else [dict(item) for item in fallback]


def _normalize_site_config(raw):
    base = json.loads(json.dumps(DEFAULT_SITE_CONFIG))
    if not isinstance(raw, dict):
        return base

    brand_name = str(raw.get('brandName', base['brandName'])).strip()
    banner_image = str(raw.get('bannerImage', base['bannerImage'])).strip()

    base['brandName'] = brand_name or base['brandName']
    base['showBanner'] = bool(raw.get('showBanner', True))
    base['bannerImage'] = banner_image or base['bannerImage']
    base['services'] = _normalize_site_items(raw.get('services'), DEFAULT_SITE_CONFIG['services'])
    base['fleet'] = _normalize_site_items(raw.get('fleet'), DEFAULT_SITE_CONFIG['fleet'])
    return base


def _get_persisted_site_config():
    row = SiteConfig.query.filter_by(key='public_site').first()
    if not row:
        return _normalize_site_config(DEFAULT_SITE_CONFIG)

    try:
        parsed = json.loads(row.value or '{}')
    except json.JSONDecodeError:
        parsed = DEFAULT_SITE_CONFIG

    return _normalize_site_config(parsed)


def _save_site_config(config):
    normalized = _normalize_site_config(config)
    row = SiteConfig.query.filter_by(key='public_site').first()
    if not row:
        row = SiteConfig(key='public_site', value='{}')
        db.session.add(row)

    row.value = json.dumps(normalized)
    db.session.commit()
    return normalized

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
    },
    "dispatch": {
        "enabled": True,
        "acceptLocalCalls": True,
        "serviceAreas": ["Rocky Mount", "Nash County", "Wilson", "Greenville"],
        "fleetSources": ["Amazon Flex", "Local Taxi", "Airport Shuttle", "Medical Ride"],
        "partnerChannels": ["uber_partner", "lyft_partner", "local_transport", "amazon_flex"],
        "dispatchPhone": "252 886-5996",
        "promotionMessage": "Ride with Traveling Star Service for fast local dispatch and reliable pickup windows.",
        "promotionCampaigns": [],
        "meter": {
            "baseFare": 4.5,
            "perMile": 2.75,
            "perMinute": 0.55,
            "minimumFare": 9.0,
            "surgeMultiplier": 1.0,
            "bookingFee": 1.5
        }
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


def _ensure_dispatch_settings():
    dispatch = business_settings.setdefault("dispatch", {})
    dispatch.setdefault("enabled", True)
    dispatch.setdefault("acceptLocalCalls", True)
    dispatch.setdefault("serviceAreas", ["Rocky Mount", "Nash County", "Wilson", "Greenville"])
    dispatch.setdefault("fleetSources", ["Amazon Flex", "Local Taxi", "Airport Shuttle", "Medical Ride"])
    dispatch.setdefault("partnerChannels", ["uber_partner", "lyft_partner", "local_transport", "amazon_flex"])
    dispatch.setdefault("dispatchPhone", business_settings.get("phone", "252 886-5996"))
    dispatch.setdefault("promotionMessage", "Ride with Traveling Star Service for fast local dispatch and reliable pickup windows.")
    dispatch.setdefault("promotionCampaigns", [])

    meter = dispatch.setdefault("meter", {})
    meter.setdefault("baseFare", 4.5)
    meter.setdefault("perMile", 2.75)
    meter.setdefault("perMinute", 0.55)
    meter.setdefault("minimumFare", 9.0)
    meter.setdefault("surgeMultiplier", 1.0)
    meter.setdefault("bookingFee", 1.5)


def _require_admin_claims():
    claims = get_jwt()
    if (claims.get("role") or "").lower() != "admin":
        return jsonify({"error": "admin access required"}), 403

    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"error": "invalid session"}), 401

    try:
        user = User.query.get(int(user_id))
    except (TypeError, ValueError):
        user = None

    if not user:
        return jsonify({"error": "user not found"}), 401
    if (user.role or "").lower() != "admin":
        return jsonify({"error": "admin access required"}), 403

    return None


@settings_bp.get("")
def get_settings():
    _ensure_dispatch_settings()
    return jsonify(business_settings)


@settings_bp.post("")
@jwt_required()
def update_settings():
    denied = _require_admin_claims()
    if denied:
        return denied

    data = request.get_json() or {}
    _ensure_dispatch_settings()

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
    _update_nested(
        business_settings["dispatch"],
        data.get("dispatch"),
        {"enabled", "acceptLocalCalls", "serviceAreas", "fleetSources", "partnerChannels", "dispatchPhone", "promotionMessage"}
    )

    if isinstance(data.get("dispatch"), dict):
        _update_nested(
            business_settings["dispatch"].setdefault("meter", {}),
            data.get("dispatch", {}).get("meter"),
            {"baseFare", "perMile", "perMinute", "minimumFare", "surgeMultiplier", "bookingFee"}
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


@settings_bp.get('/site-config')
def get_site_config():
    return jsonify({
        'config': _get_persisted_site_config()
    })


@settings_bp.post('/site-config')
@jwt_required()
def update_site_config():
    denied = _require_admin_claims()
    if denied:
        return denied

    data = request.get_json() or {}
    config = data.get('config', data)
    normalized = _save_site_config(config)

    business_settings['businessName'] = normalized.get('brandName', business_settings.get('businessName'))
    business_settings.setdefault('design', {})['showBanner'] = bool(normalized.get('showBanner', True))
    business_settings['services'] = [item.get('name') for item in normalized.get('services', []) if item.get('name')]

    return jsonify({
        'message': 'Site config updated',
        'config': normalized
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
