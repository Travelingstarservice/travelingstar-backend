# settings_routes.py
from flask import Blueprint, request, jsonify

settings_bp = Blueprint("settings_bp", __name__)

# ============================
# BUSINESS SETTINGS (AdminSettings.vue)
# ============================

business_settings = {
    "businessName": "Traveling Star Service",
    "phone": "252 886-5996",
    "serviceArea": "Rocky Mount, NC",
    "logo": "",
    "hero": "Your gateway to unforgettable journeys."
}


@settings_bp.get("")
def get_settings():
    return jsonify(business_settings)


@settings_bp.post("")
def update_settings():
    data = request.get_json() or {}

    business_settings["businessName"] = data.get("businessName", business_settings["businessName"])
    business_settings["phone"] = data.get("phone", business_settings["phone"])
    business_settings["serviceArea"] = data.get("serviceArea", business_settings["serviceArea"])
    business_settings["hero"] = data.get("hero", business_settings.get("hero", "Your gateway to unforgettable journeys."))
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
def update_homepage_settings():
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
def update_logo():
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
    return jsonify(pricing)


@settings_bp.post("/payments")
def update_payments():
    data = request.get_json() or {}

    pricing["baseRate"] = float(data.get("baseRate", pricing["baseRate"]))
    pricing["perMile"] = float(data.get("perMile", pricing["perMile"]))

    return jsonify({
        "message": "Pricing updated",
        "pricing": pricing
    })
