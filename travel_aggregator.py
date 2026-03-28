import asyncio
import aiohttp
from datetime import datetime, timedelta
import pandas as pd
import json
import os
from typing import List, Dict, Optional
import requests as sync_requests
from scraper_engine import ScraperEngine

# ---------- Airport Database ----------
AIRPORTS = {
    # India
    "BOM": "Mumbai", "DEL": "Delhi", "BLR": "Bengaluru", "MAA": "Chennai",
    "CCU": "Kolkata", "HYD": "Hyderabad", "GOI": "Goa", "PNQ": "Pune",
    "JAI": "Jaipur", "AMD": "Ahmedabad", "COK": "Kochi", "TRV": "Thiruvananthapuram",
    "GAU": "Guwahati", "SXR": "Srinagar", "IXC": "Chandigarh", "PAT": "Patna",
    "LKO": "Lucknow", "BBI": "Bhubaneswar", "IDR": "Indore", "NAG": "Nagpur",
    "VNS": "Varanasi", "IXB": "Bagdogra", "RAJ": "Rajkot", "UDR": "Udaipur",
    "IXR": "Ranchi", "RPR": "Raipur", "VTZ": "Visakhapatnam", "IXE": "Mangalore",
    "JDH": "Jodhpur", "BDQ": "Vadodara", "ATQ": "Amritsar", "DED": "Dehradun",
    "IXA": "Agartala", "IMF": "Imphal", "DIB": "Dibrugarh", "IXJ": "Jammu",
    "IXL": "Leh", "PBD": "Porbandar", "BHO": "Bhopal", "GWL": "Gwalior",
    # Middle East
    "DXB": "Dubai", "AUH": "Abu Dhabi", "SHJ": "Sharjah", "DOH": "Doha",
    "BAH": "Bahrain", "MCT": "Muscat", "KWI": "Kuwait", "RUH": "Riyadh",
    "JED": "Jeddah", "AMM": "Amman", "TLV": "Tel Aviv",
    # Southeast Asia
    "SIN": "Singapore", "BKK": "Bangkok", "DMK": "Don Mueang", "KUL": "Kuala Lumpur",
    "CGK": "Jakarta", "MNL": "Manila", "SGN": "Ho Chi Minh City", "HAN": "Hanoi",
    "RGN": "Yangon", "PNH": "Phnom Penh", "REP": "Siem Reap", "DPS": "Bali",
    "HKT": "Phuket", "CNX": "Chiang Mai",
    # East Asia
    "HKG": "Hong Kong", "NRT": "Tokyo Narita", "HND": "Tokyo Haneda",
    "KIX": "Osaka", "ICN": "Seoul Incheon", "PEK": "Beijing", "PVG": "Shanghai",
    "TPE": "Taipei", "MFM": "Macau",
    # Europe
    "LHR": "London Heathrow", "LGW": "London Gatwick", "STN": "London Stansted",
    "CDG": "Paris CDG", "ORY": "Paris Orly", "FRA": "Frankfurt", "MUC": "Munich",
    "AMS": "Amsterdam", "FCO": "Rome", "MXP": "Milan", "MAD": "Madrid",
    "BCN": "Barcelona", "LIS": "Lisbon", "ATH": "Athens", "IST": "Istanbul",
    "ZRH": "Zurich", "VIE": "Vienna", "CPH": "Copenhagen", "OSL": "Oslo",
    "ARN": "Stockholm", "HEL": "Helsinki", "WAW": "Warsaw", "PRG": "Prague",
    "BUD": "Budapest", "DUB": "Dublin", "EDI": "Edinburgh", "BRU": "Brussels",
    "GVA": "Geneva",
    # North America
    "JFK": "New York JFK", "EWR": "Newark", "LGA": "LaGuardia",
    "LAX": "Los Angeles", "SFO": "San Francisco", "ORD": "Chicago O'Hare",
    "MIA": "Miami", "ATL": "Atlanta", "DFW": "Dallas", "DEN": "Denver",
    "SEA": "Seattle", "BOS": "Boston", "IAD": "Washington Dulles",
    "YYZ": "Toronto", "YVR": "Vancouver", "YUL": "Montreal", "MEX": "Mexico City",
    "CUN": "Cancun",
    # Oceania
    "SYD": "Sydney", "MEL": "Melbourne", "BNE": "Brisbane", "PER": "Perth",
    "AKL": "Auckland", "WLG": "Wellington",
    # Africa
    "JNB": "Johannesburg", "CPT": "Cape Town", "NBO": "Nairobi",
    "CAI": "Cairo", "ADD": "Addis Ababa", "DAR": "Dar es Salaam",
    "CMN": "Casablanca", "LOS": "Lagos", "ACC": "Accra",
    # South America
    "GRU": "São Paulo", "GIG": "Rio de Janeiro", "EZE": "Buenos Aires",
    "SCL": "Santiago", "BOG": "Bogotá", "LIM": "Lima",
}


class TravelAggregator:
    def __init__(self, amadeus_client_id=None, amadeus_client_secret=None, serpapi_key=None, headless=True):
        self.amadeus_client_id = amadeus_client_id or os.getenv('AMADEUS_CLIENT_ID')
        self.amadeus_client_secret = amadeus_client_secret or os.getenv('AMADEUS_CLIENT_SECRET')
        self.serpapi_key = serpapi_key or os.getenv('SERPAPI_KEY')
        self.headless = headless

        self._amadeus_token = None
        self._amadeus_token_expiry = None
        
        self.scraper = ScraperEngine(headless=self.headless)

    # ------------------------------------------------------------------ #
    #                       Amadeus OAuth2 Helper                         #
    # ------------------------------------------------------------------ #
    def _get_amadeus_token(self):
        """Obtain or reuse an Amadeus OAuth2 bearer token."""
        if not self.amadeus_client_id or not self.amadeus_client_secret:
            return None
        if self.amadeus_client_id.startswith('your_'):
            return None

        now = datetime.utcnow()
        if self._amadeus_token and self._amadeus_token_expiry and now < self._amadeus_token_expiry:
            return self._amadeus_token

        try:
            resp = sync_requests.post(
                'https://test.api.amadeus.com/v1/security/oauth2/token',
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.amadeus_client_id,
                    'client_secret': self.amadeus_client_secret,
                },
                timeout=10,
            )
            resp.raise_for_status()
            body = resp.json()
            self._amadeus_token = body['access_token']
            self._amadeus_token_expiry = now + timedelta(seconds=body.get('expires_in', 1799) - 60)
            return self._amadeus_token
        except Exception as e:
            print(f"⚠️  Amadeus token error: {e}")
            return None

    # ------------------------------------------------------------------ #
    #             Source 1 — Amadeus Flight Offers Search                  #
    # ------------------------------------------------------------------ #
    async def get_amadeus_flights(self, session, origin, destination, departure_date, return_date=None):
        """Fetch real flight offers from Amadeus Self-Service API."""
        token = self._get_amadeus_token()
        if not token:
            print("ℹ️  Amadeus API key not configured — skipping.")
            return None

        try:
            dep_date = departure_date.strftime('%Y-%m-%d')
            params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': dep_date,
                'adults': 1,
                'currencyCode': 'INR',
                'max': 10,
            }
            if return_date:
                params['returnDate'] = return_date.strftime('%Y-%m-%d')

            headers = {'Authorization': f'Bearer {token}'}

            async with session.get(
                'https://test.api.amadeus.com/v2/shopping/flight-offers',
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"⚠️  Amadeus API {resp.status}: {text[:200]}")
                    return None

                data = await resp.json()
                offers = data.get('data', [])
                dictionaries = data.get('dictionaries', {})
                carriers = dictionaries.get('carriers', {})

                results = []
                for offer in offers:
                    price = float(offer['price']['total'])
                    currency = offer['price']['currency']

                    # Parse first itinerary for display
                    itinerary = offer['itineraries'][0]
                    segments = itinerary['segments']
                    first_seg = segments[0]
                    last_seg = segments[-1]

                    airline_code = first_seg['carrierCode']
                    airline_name = carriers.get(airline_code, airline_code)

                    results.append({
                        'source': 'Amadeus',
                        'type': 'Flight',
                        'origin': origin,
                        'destination': destination,
                        'departure_date': dep_date,
                        'return_date': return_date.strftime('%Y-%m-%d') if return_date else None,
                        'airline': airline_name,
                        'airline_code': airline_code,
                        'price': price,
                        'currency': currency,
                        'departure_time': first_seg['departure']['at'],
                        'arrival_time': last_seg['arrival']['at'],
                        'duration': itinerary.get('duration', ''),
                        'stops': len(segments) - 1,
                        'cabin_class': offer['travelerPricings'][0]['fareDetailsBySegment'][0].get('cabin', 'ECONOMY'),
                    })

                if results:
                    print(f"✅ Amadeus: {len(results)} flights found")
                return results if results else None

        except Exception as e:
            print(f"⚠️  Amadeus error: {e}")
            return None

    # ------------------------------------------------------------------ #
    #          Source 2 — SerpAPI Google Flights                           #
    # ------------------------------------------------------------------ #
    async def get_serpapi_flights(self, session, origin, destination, departure_date, return_date=None):
        """Fetch real flight data from Google Flights via SerpAPI."""
        if not self.serpapi_key or self.serpapi_key.startswith('your_'):
            print("ℹ️  SerpAPI key not configured — skipping.")
            return None

        try:
            dep_date = departure_date.strftime('%Y-%m-%d')
            params = {
                'engine': 'google_flights',
                'api_key': self.serpapi_key,
                'departure_id': origin,
                'arrival_id': destination,
                'outbound_date': dep_date,
                'currency': 'INR',
                'hl': 'en',
                'type': '2' if return_date else '1',
            }
            if return_date:
                params['return_date'] = return_date.strftime('%Y-%m-%d')

            # SerpAPI doesn't support aiohttp natively, run in executor
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: sync_requests.get('https://serpapi.com/search', params=params, timeout=30)
            )

            if resp.status_code != 200:
                print(f"⚠️  SerpAPI {resp.status_code}: {resp.text[:200]}")
                return None

            data = resp.json()

            results = []

            # Process best_flights + other_flights
            for group_key in ('best_flights', 'other_flights'):
                for flight_group in data.get(group_key, []):
                    price = flight_group.get('price')
                    if not price:
                        continue

                    flights_list = flight_group.get('flights', [])
                    if not flights_list:
                        continue

                    first_flight = flights_list[0]
                    last_flight = flights_list[-1]

                    airline = first_flight.get('airline', 'Unknown')
                    dep_airport = first_flight.get('departure_airport', {})
                    arr_airport = last_flight.get('arrival_airport', {})

                    total_duration = flight_group.get('total_duration', 0)
                    hours = total_duration // 60
                    mins = total_duration % 60

                    results.append({
                        'source': 'Google Flights',
                        'type': 'Flight',
                        'origin': origin,
                        'destination': destination,
                        'departure_date': dep_date,
                        'return_date': return_date.strftime('%Y-%m-%d') if return_date else None,
                        'airline': airline,
                        'airline_code': first_flight.get('airline_logo', ''),
                        'price': price,
                        'currency': 'INR',
                        'departure_time': dep_airport.get('time', ''),
                        'arrival_time': arr_airport.get('time', ''),
                        'duration': f'PT{hours}H{mins}M' if total_duration else '',
                        'stops': len(flights_list) - 1,
                        'cabin_class': flight_group.get('type', 'Economy'),
                    })

            if results:
                print(f"✅ Google Flights: {len(results)} flights found")
            return results if results else None

        except Exception as e:
            print(f"⚠️  SerpAPI error: {e}")
            return None

    # ------------------------------------------------------------------ #
    #                       Aggregate All Sources                          #
    # ------------------------------------------------------------------ #
    async def aggregate_all_data(self, origin, destination, departure_date, return_date=None,
                                 checkin_date=None, checkout_date=None):
        """Aggregate data from all configured sources concurrently."""

        async with aiohttp.ClientSession() as session:
            tasks = [
                self.get_amadeus_flights(session, origin, destination, departure_date, return_date),
                self.get_serpapi_flights(session, origin, destination, departure_date, return_date),
                self.scraper.scrape_easemytrip(origin, destination, departure_date),
                self.scraper.scrape_cleartrip(origin, destination, departure_date),
                # self.scraper.scrape_makemytrip(origin, destination, departure_date) # Skipped for now
            ]

            raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten: each source returns a list of flight dicts (or None)
        all_flights = []
        for result in raw_results:
            if isinstance(result, Exception):
                print(f"⚠️  Source error: {result}")
                continue
            if result is None:
                continue
            if isinstance(result, list):
                all_flights.extend(result)
            else:
                all_flights.append(result)

        # Sort by price ascending
        all_flights.sort(key=lambda x: x.get('price', float('inf')))

        # Mark cheapest
        if all_flights:
            all_flights[0]['is_cheapest'] = True

        return all_flights

    # ------------------------------------------------------------------ #
    #                       Excel Report                                   #
    # ------------------------------------------------------------------ #
    def create_excel_report(self, data, filename='travel_report.xlsx'):
        """Create detailed Excel report with multiple sheets."""

        flights = [item for item in data if item.get('type') == 'Flight']
        hotels = [item for item in data if item.get('type') == 'Hotel']

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            if flights:
                # Clean up for Excel
                flight_rows = []
                for f in flights:
                    flight_rows.append({
                        'Source': f.get('source', ''),
                        'Airline': f.get('airline', ''),
                        'Route': f'{f.get("origin", "")} → {f.get("destination", "")}',
                        'Departure Date': f.get('departure_date', ''),
                        'Departure Time': self._format_time(f.get('departure_time', '')),
                        'Arrival Time': self._format_time(f.get('arrival_time', '')),
                        'Duration': self._format_duration(f.get('duration', '')),
                        'Stops': f.get('stops', 0),
                        'Price (₹)': f.get('price', 0),
                        'Cabin': f.get('cabin_class', ''),
                        'Booking Link': f.get('booking_url', ''),
                    })

                flight_df = pd.DataFrame(flight_rows)
                flight_df.to_excel(writer, sheet_name='Flights', index=False)

                worksheet = writer.sheets['Flights']
                for i, column in enumerate(flight_df.columns):
                    max_len = max(flight_df[column].astype(str).map(len).max(), len(column))
                    worksheet.column_dimensions[chr(65 + i)].width = max_len + 3

            if hotels:
                hotel_df = pd.DataFrame(hotels)
                hotel_df.to_excel(writer, sheet_name='Hotels', index=False)

            # Summary
            summary_data = {
                'Metric': [
                    'Total Flights Found',
                    'Cheapest Flight Price (₹)',
                    'Most Expensive Flight (₹)',
                    'Average Flight Price (₹)',
                    'Sources Used',
                    'Report Generated',
                ],
                'Value': [
                    len(flights),
                    min(f.get('price', 0) for f in flights) if flights else 'N/A',
                    max(f.get('price', 0) for f in flights) if flights else 'N/A',
                    round(sum(f.get('price', 0) for f in flights) / len(flights), 2) if flights else 'N/A',
                    ', '.join(set(f.get('source', '') for f in flights)),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ],
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            ws = writer.sheets['Summary']
            ws.column_dimensions['A'].width = 30
            ws.column_dimensions['B'].width = 40

        print(f"✅ Excel report created: {filename}")
        return filename

    # ------------------------------------------------------------------ #
    #                       HTML Report                                    #
    # ------------------------------------------------------------------ #
    def create_html_report(self, data):
        """Create HTML report for email."""

        flights = [item for item in data if item.get('type') == 'Flight']
        report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 20px; color: #1a1a2e; }}
                h1 {{ color: #16213e; }}
                h2 {{ color: #0f3460; border-bottom: 3px solid #e94560; padding-bottom: 10px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th {{ background: linear-gradient(135deg, #0f3460, #16213e); color: white; padding: 14px; text-align: left; }}
                td {{ padding: 12px; border-bottom: 1px solid #eee; }}
                tr:nth-child(even) {{ background-color: #f8f9fa; }}
                tr:hover {{ background-color: #e8f4fd; }}
                .price {{ color: #27ae60; font-weight: bold; font-size: 1.15em; }}
                .cheapest {{ background-color: #d4edda; }}
                .source {{ color: #6c757d; font-size: 0.9em; }}
                .stops-0 {{ color: #27ae60; }}
                .stops-1 {{ color: #f39c12; }}
                .stops-2 {{ color: #e74c3c; }}
            </style>
        </head>
        <body>
            <h1>🌍 Travel Price Report</h1>
            <p><strong>Generated:</strong> {report_date}</p>
        """

        if flights:
            html += "<h2>✈️ Flight Options</h2><table>"
            html += "<tr><th>Source</th><th>Airline</th><th>Route</th><th>Departure</th><th>Arrival</th><th>Duration</th><th>Stops</th><th>Price</th></tr>"
            for flight in flights:
                is_cheapest = flight.get('is_cheapest', False)
                row_class = ' class="cheapest"' if is_cheapest else ''
                stops = flight.get('stops', 0)
                stops_class = f'stops-{min(stops, 2)}'
                cheapest_badge = ' 🏷️ BEST' if is_cheapest else ''

                html += f"""
                <tr{row_class}>
                    <td class='source'>{flight.get('source', 'N/A')}</td>
                    <td><strong>{flight.get('airline', 'N/A')}</strong></td>
                    <td>{flight.get('origin', '')} → {flight.get('destination', '')}</td>
                    <td>{self._format_time(flight.get('departure_time', ''))}</td>
                    <td>{self._format_time(flight.get('arrival_time', ''))}</td>
                    <td>{self._format_duration(flight.get('duration', ''))}</td>
                    <td class='{stops_class}'>{stops} stop{'s' if stops != 1 else ''}</td>
                    <td class='price'>₹{flight.get('price', 'N/A'):,.0f}{cheapest_badge}</td>
                </tr>
                """
            html += "</table>"
        else:
            html += "<p>No flight data was returned. Please check your API keys.</p>"

        html += "</body></html>"
        return html

    # ------------------------------------------------------------------ #
    #                       Helpers                                        #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _format_duration(iso_dur: str) -> str:
        """Convert ISO 8601 duration (PT2H30M) to readable string."""
        if not iso_dur:
            return '—'
        import re
        m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', iso_dur)
        if m:
            hours = int(m.group(1) or 0)
            mins = int(m.group(2) or 0)
            return f'{hours}h {mins}m'
        return iso_dur

    @staticmethod
    def _format_time(time_str: str) -> str:
        """Extract HH:MM from ISO datetime or time string."""
        if not time_str:
            return '—'
        # Handle ISO datetime like "2026-05-01T14:30:00"
        if 'T' in time_str:
            try:
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                return dt.strftime('%H:%M')
            except Exception:
                pass
        # Handle plain time like "14:30"
        if ':' in time_str:
            return time_str[:5]
        return time_str


async def main():
    """Test the aggregator."""
    aggregator = TravelAggregator()

    origin = "BOM"
    destination = "DEL"
    departure_date = datetime.now() + timedelta(days=30)
    return_date = departure_date + timedelta(days=7)

    print("🔍 Fetching travel data from real APIs...")
    print("⏳ This may take 10-30 seconds...\n")

    results = await aggregator.aggregate_all_data(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        checkin_date=departure_date,
        checkout_date=return_date,
    )

    print(f"\n✅ Found {len(results)} flights\n")

    for r in results[:5]:
        print(f"  {r.get('airline', '?'):20s}  ₹{r.get('price', 0):>8,.0f}  {r.get('source')}")

    if results:
        aggregator.create_excel_report(results)
        print("\n📄 Excel report created: travel_report.xlsx")


if __name__ == "__main__":
    asyncio.run(main())
