import json
from urllib import parse, request as urllib_request
from xml.etree import ElementTree as ET

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from routes.settings_routes import business_settings

podcast_bp = Blueprint('podcast_bp', __name__)


def _fetch_weather_summary(area):
    if not area:
        return None

    query = parse.quote(area)
    url = f'https://wttr.in/{query}?format=j1'

    try:
        with urllib_request.urlopen(url, timeout=6) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except Exception:
        return None

    current = (payload.get('current_condition') or [{}])[0]
    if not current:
        return None

    description = ((current.get('weatherDesc') or [{}])[0].get('value') or '').strip()
    temp_f = current.get('temp_F')
    humidity = current.get('humidity')
    wind = current.get('windspeedMiles')

    parts = []
    if description:
        parts.append(description.lower())
    if temp_f:
        parts.append(f'{temp_f}F')
    if humidity:
        parts.append(f'humidity {humidity}%')
    if wind:
        parts.append(f'wind {wind} mph')

    if not parts:
        return None

    return ', '.join(parts)


def _fetch_news_headlines(area, topic):
    query = f'Traveling Star Service {area or ""} {topic or "travel"}'.strip()
    encoded = parse.quote(query)
    url = f'https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en'

    try:
        with urllib_request.urlopen(url, timeout=6) as response:
            xml_text = response.read().decode('utf-8', errors='ignore')
    except Exception:
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    headlines = []
    for item in root.findall('./channel/item')[:3]:
        title = (item.findtext('title') or '').strip()
        if title:
            headlines.append(title)

    return headlines


def _build_visual_storyboard(topic, area, style):
    locale = area or 'your service area'
    vibe = style or 'business'
    return [
        f'Opening shot: branded Traveling Star vehicle in {locale} during golden hour with title card for {topic}.',
        f'Mid sequence: customer pickup and route planning montage with {vibe} tone, showing reliability and professionalism.',
        f'Closing shot: happy drop-off, logo lockup, and clear call-to-action to call or text 252-886-5996.'
    ]

@podcast_bp.route('/', methods=['POST'])
def generate_podcast():
    payload = request.get_json() or {}
    podcast_settings = business_settings.get('podcast', {})

    claims = {}
    try:
        verify_jwt_in_request(optional=True)
        parsed_claims = get_jwt()
        if isinstance(parsed_claims, dict):
            claims = parsed_claims
    except Exception:
        claims = {}
    is_admin = (claims.get('role') or '').lower() == 'admin'

    if not bool(podcast_settings.get('enabled', True)):
        return jsonify({'error': 'Podcast generation is currently disabled by admin.'}), 403

    if not bool(podcast_settings.get('allowCustomerGeneration', True)) and not is_admin:
        return jsonify({'error': 'Customer podcast generation is disabled by admin.'}), 403

    topic = (payload.get('topic') or '').strip()
    style = (payload.get('style') or podcast_settings.get('defaultStyle') or 'business').strip().lower()
    area = (payload.get('area') or '').strip()
    target_date = (payload.get('target_date') or '').strip()
    include_weather = bool(payload.get('include_weather', podcast_settings.get('includeWeatherByDefault', True)))
    include_news = bool(payload.get('include_news', podcast_settings.get('includeNewsByDefault', True)))
    include_visuals = bool(payload.get('include_visuals', podcast_settings.get('includeVisualsByDefault', True)))

    if not topic:
        return jsonify({'error': 'Please enter a topic to generate a podcast.'}), 400

    intro_parts = [f"Welcome to your {style} podcast. Today we are exploring {topic}."]
    if area:
        intro_parts.append(f"We are focusing this episode on {area}.")
    if target_date:
        intro_parts.append(f"This production plan is aligned for {target_date}.")
    intro = ' '.join(intro_parts)

    weather_summary = _fetch_weather_summary(area) if include_weather else None
    news_headlines = _fetch_news_headlines(area, topic) if include_news else []

    points = [
        f"First, let’s break down the key idea behind {topic} in a practical way.",
        f"Next, we’ll look at the most useful opportunities and outcomes people can expect from {topic}.",
        f"Finally, we’ll close with a clear action step so the conversation stays useful and easy to apply."
    ]

    if weather_summary:
        points.append(f"Weather snapshot for {area}: {weather_summary}. Use this in customer planning updates.")

    if news_headlines:
        points.append("Local and industry news highlights: " + " | ".join(news_headlines))

    closing = f"That wraps up today’s {style} podcast on {topic}."

    script = " ".join([intro, *points, closing])

    visual_storyboard = _build_visual_storyboard(topic, area, style) if include_visuals else []

    return jsonify({
        'title': f'{topic.title()} Podcast',
        'style': style,
        'area': area,
        'target_date': target_date,
        'weather': weather_summary,
        'news_headlines': news_headlines,
        'visual_storyboard': visual_storyboard,
        'script': script
    })
