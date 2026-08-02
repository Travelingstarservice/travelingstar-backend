from flask import Blueprint, request, jsonify

podcast_bp = Blueprint('podcast_bp', __name__)

@podcast_bp.route('/', methods=['POST'])
def generate_podcast():
    payload = request.get_json() or {}
    topic = (payload.get('topic') or '').strip()
    style = (payload.get('style') or 'business').strip().lower()

    if not topic:
        return jsonify({'error': 'Please enter a topic to generate a podcast.'}), 400

    intro = f"Welcome to your {style} podcast. Today we are exploring {topic}."
    points = [
        f"First, let’s break down the key idea behind {topic} in a practical way.",
        f"Next, we’ll look at the most useful opportunities and outcomes people can expect from {topic}.",
        f"Finally, we’ll close with a clear action step so the conversation stays useful and easy to apply."
    ]
    closing = f"That wraps up today’s {style} podcast on {topic}."

    script = " ".join([intro, *points, closing])

    return jsonify({
        'title': f'{topic.title()} Podcast',
        'style': style,
        'script': script
    })
