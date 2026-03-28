from flask import Flask, render_template_string
import requests
import boto3
import json
import os
import threading
import time
from datetime import datetime
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# -------------------------------------------------------
# Load environment variables from .env file
# On EC2, variables are set as system environment variables
# Locally, they are loaded from the .env file
# -------------------------------------------------------
load_dotenv()

app = Flask(__name__)

# -------------------------------------------------------
# CONFIGURATION — Loaded securely from environment variables
# Never hardcode API keys or bucket names in source code!
# -------------------------------------------------------
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# -------------------------------------------------------
# Validate required environment variables on startup
# -------------------------------------------------------
if not TICKETMASTER_API_KEY:
    raise ValueError("Missing TICKETMASTER_API_KEY environment variable!")
if not S3_BUCKET_NAME:
    raise ValueError("Missing S3_BUCKET_NAME environment variable!")

# -------------------------------------------------------
# Global variable to store events in memory
# -------------------------------------------------------
events_cache = []

# -------------------------------------------------------
# HTML Template for the UniEvent Website
# -------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UniEvent - University Events</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f2f5;
            color: #333;
        }
        header {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: white;
            padding: 20px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        header h1 { font-size: 2rem; letter-spacing: 1px; }
        header p { font-size: 0.9rem; opacity: 0.7; }
        .badge {
            background: #e94560;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8rem;
        }
        .container { max-width: 1200px; margin: 40px auto; padding: 0 20px; }
        h2 {
            font-size: 1.8rem;
            margin-bottom: 30px;
            color: #1a1a2e;
            border-left: 5px solid #e94560;
            padding-left: 15px;
        }
        .events-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 25px;
        }
        .event-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease;
        }
        .event-card:hover { transform: translateY(-5px); }
        .event-card img {
            width: 100%;
            height: 200px;
            object-fit: cover;
        }
        .event-card .no-image {
            width: 100%;
            height: 200px;
            background: linear-gradient(135deg, #1a1a2e, #e94560);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 3rem;
        }
        .event-info { padding: 20px; }
        .event-info h3 {
            font-size: 1.1rem;
            margin-bottom: 10px;
            color: #1a1a2e;
        }
        .event-meta {
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-size: 0.85rem;
            color: #666;
        }
        .event-meta span { display: flex; align-items: center; gap: 8px; }
        .tag {
            display: inline-block;
            background: #f0f2f5;
            color: #e94560;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            margin-top: 10px;
            font-weight: 600;
        }
        .no-events {
            text-align: center;
            padding: 60px;
            color: #999;
            font-size: 1.1rem;
        }
        footer {
            text-align: center;
            padding: 20px;
            margin-top: 60px;
            background: #1a1a2e;
            color: white;
            font-size: 0.85rem;
            opacity: 0.8;
        }
        .last-updated {
            text-align: right;
            color: #999;
            font-size: 0.8rem;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <header>
        <div>
            <h1>🎓 UniEvent</h1>
            <p>Your University Events Hub</p>
        </div>
        <span class="badge">LIVE EVENTS</span>
    </header>

    <div class="container">
        <p class="last-updated">Last updated: {{ last_updated }}</p>
        <h2>University Events</h2>

        {% if events %}
        <div class="events-grid">
            {% for event in events %}
            <div class="event-card">
                {% if event.image %}
                <img src="{{ event.image }}" alt="{{ event.name }}" onerror="this.style.display='none'">
                {% else %}
                <div class="no-image">🎭</div>
                {% endif %}
                <div class="event-info">
                    <h3>{{ event.name }}</h3>
                    <div class="event-meta">
                        <span>📅 {{ event.date }}</span>
                        <span>📍 {{ event.venue }}</span>
                        <span>🏙️ {{ event.city }}</span>
                    </div>
                    <span class="tag">University Event</span>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="no-events">
            <p>🔄 Fetching events... Please refresh in a moment!</p>
        </div>
        {% endif %}
    </div>

    <footer>
        <p>UniEvent — Powered by AWS | EC2 + S3 + ALB | © 2024</p>
    </footer>
</body>
</html>
"""

# -------------------------------------------------------
# Fetch Events from Ticketmaster API
# -------------------------------------------------------
def fetch_events_from_api():
    print("Fetching events from Ticketmaster API...")
    try:
        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        params = {
            "apikey": TICKETMASTER_API_KEY,
            "keyword": "university",
            "size": 12,
            "sort": "date,asc"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        events = []
        if "_embedded" in data and "events" in data["_embedded"]:
            for item in data["_embedded"]["events"]:
                event = {
                    "name": item.get("name", "Unknown Event"),
                    "date": item.get("dates", {}).get("start", {}).get("localDate", "TBD"),
                    "venue": item.get("_embedded", {}).get("venues", [{}])[0].get("name", "TBD"),
                    "city": item.get("_embedded", {}).get("venues", [{}])[0].get("city", {}).get("name", "TBD"),
                    "image": item.get("images", [{}])[0].get("url", "") if item.get("images") else "",
                    "description": item.get("info", "No description available")
                }
                events.append(event)

        print(f"Fetched {len(events)} events successfully!")
        return events

    except Exception as e:
        print(f"Error fetching events: {e}")
        return []


# -------------------------------------------------------
# Save Events to S3
# -------------------------------------------------------
def save_events_to_s3(events):
    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"event-data/events_{timestamp}.json"

        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=filename,
            Body=json.dumps(events, indent=2),
            ContentType="application/json"
        )
        print(f"Events saved to S3: {filename}")

    except ClientError as e:
        print(f"Error saving to S3: {e}")


# -------------------------------------------------------
# Save Event Images to S3
# -------------------------------------------------------
def save_images_to_s3(events):
    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        for i, event in enumerate(events):
            if event.get("image"):
                try:
                    img_response = requests.get(event["image"], timeout=10)
                    if img_response.status_code == 200:
                        img_key = f"event-images/event_{i+1}.jpg"
                        s3.put_object(
                            Bucket=S3_BUCKET_NAME,
                            Key=img_key,
                            Body=img_response.content,
                            ContentType="image/jpeg"
                        )
                        print(f"Image saved to S3: {img_key}")
                except Exception as e:
                    print(f"Error saving image {i}: {e}")

    except Exception as e:
        print(f"Error in save_images_to_s3: {e}")


# -------------------------------------------------------
# Main Event Refresh Function
# Runs every hour automatically
# -------------------------------------------------------
def refresh_events():
    global events_cache
    while True:
        events = fetch_events_from_api()
        if events:
            events_cache = events
            save_events_to_s3(events)
            save_images_to_s3(events)
        time.sleep(3600)  # Refresh every hour


# -------------------------------------------------------
# Flask Routes
# -------------------------------------------------------
@app.route("/")
def home():
    last_updated = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    return render_template_string(
        HTML_TEMPLATE,
        events=events_cache,
        last_updated=last_updated
    )


@app.route("/health")
def health():
    return {"status": "healthy", "instance": "UniEvent EC2"}, 200


# -------------------------------------------------------
# Start the App
# -------------------------------------------------------
if __name__ == "__main__":
    # Start background thread to fetch events
    thread = threading.Thread(target=refresh_events, daemon=True)
    thread.start()

    # Give it 5 seconds to fetch first batch of events
    time.sleep(5)

    # Start Flask on port 80
    app.run(host="0.0.0.0", port=80, debug=False)
