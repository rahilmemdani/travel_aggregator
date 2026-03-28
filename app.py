from flask import Flask, render_template, request, send_file, jsonify
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
from travel_aggregator import TravelAggregator, AIRPORTS
from email_sender import EmailSender
import json

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'reports')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Headless mode for scrapers (can be toggled for debugging)
HEADLESS = os.getenv('SCRAPER_HEADLESS', 'true').lower() == 'true'

aggregator = TravelAggregator(headless=HEADLESS)
email_sender = EmailSender()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/airports')
def airports():
    """Return airport list for autocomplete."""
    query = request.args.get('q', '').upper().strip()
    results = []
    for code, city in AIRPORTS.items():
        if query in code or query.lower() in city.lower():
            results.append({'code': code, 'city': city, 'label': f'{code} — {city}'})
    results.sort(key=lambda x: (0 if x['code'].startswith(query) else 1, x['code']))
    return jsonify(results[:20])


@app.route('/api-status')
def api_status():
    """Check which APIs and scrapers are configured."""
    return jsonify({
        'amadeus': bool(aggregator.amadeus_client_id and not aggregator.amadeus_client_id.startswith('your_')),
        'serpapi': bool(aggregator.serpapi_key and not aggregator.serpapi_key.startswith('your_')),
        'scraper': True, # Browser scraping is always available if playwright is installed
    })


@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.json

        departure_date = datetime.strptime(data['departure_date'], '%Y-%m-%d')
        return_date = datetime.strptime(data['return_date'], '%Y-%m-%d') if data.get('return_date') else None

        # Run async aggregation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        results = loop.run_until_complete(
            aggregator.aggregate_all_data(
                origin=data['origin'],
                destination=data['destination'],
                departure_date=departure_date,
                return_date=return_date,
                checkin_date=departure_date,
                checkout_date=return_date,
            )
        )
        loop.close()

        # Create Excel report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_filename = f"travel_report_{timestamp}.xlsx"
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
        aggregator.create_excel_report(results, excel_path)

        # Create HTML report
        html_report = aggregator.create_html_report(results)

        flights = [r for r in results if r.get('type') == 'Flight']
        hotels = [r for r in results if r.get('type') == 'Hotel']

        return jsonify({
            'success': True,
            'flights': flights,
            'hotels': hotels,
            'excel_file': excel_filename,
            'html_report': html_report,
            'total_results': len(results),
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
        }), 400


@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(file_path, as_attachment=True)


@app.route('/send-email', methods=['POST'])
def send_email():
    try:
        data = request.json

        trip_details = {
            'origin': data['origin'],
            'destination': data['destination'],
            'departure_date': data['departure_date'],
            'return_date': data.get('return_date', 'One-way'),
            'travelers': data.get('travelers', 1),
        }

        html_email = email_sender.create_client_email_template(
            client_name=data['client_name'],
            trip_details=trip_details,
            flight_summary=data['flight_summary'],
            hotel_summary=data['hotel_summary'],
        )

        excel_file = os.path.join(app.config['UPLOAD_FOLDER'], data['excel_file'])

        success = email_sender.send_report(
            sender_email=data['sender_email'],
            sender_password=data['sender_password'],
            recipient_email=data['recipient_email'],
            subject=f"Travel Itinerary: {data['origin']} to {data['destination']}",
            html_content=html_email,
            attachments=[excel_file] if os.path.exists(excel_file) else [],
        )

        return jsonify({'success': success})

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 400


if __name__ == '__main__':
    print("🚀 Starting Travel Aggregator Server with Scraping Engine...")
    print("📍 Open http://localhost:5000 in your browser")

    # Show API status
    if aggregator.amadeus_client_id and not aggregator.amadeus_client_id.startswith('your_'):
        print("✅ Amadeus API: Configured")
    else:
        print("⚠️  Amadeus API: Not configured")

    if aggregator.serpapi_key and not aggregator.serpapi_key.startswith('your_'):
        print("✅ SerpAPI: Configured")
    else:
        print("⚠️  SerpAPI: Not configured")
        
    print(f"✅ Web Scraper: Enabled (Headless: {HEADLESS})")

    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
