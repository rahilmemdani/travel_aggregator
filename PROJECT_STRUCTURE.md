# 📁 Travel Aggregator - Project Structure

```
travel-aggregator/
├── 📄 app.py                      # Flask web server (main application)
├── 📄 travel_aggregator.py        # Core aggregation logic
├── 📄 email_sender.py             # Email functionality
├── 📄 requirements.txt            # Python dependencies
├── 📄 start.sh                    # Quick startup script
├── 📄 README.md                   # Complete documentation
├── 📄 QUICKSTART.md              # 2-minute quick start guide
├── 📄 PROJECT_STRUCTURE.md       # This file
│
├── 📁 templates/                  # HTML templates
│   └── index.html                # Main web interface
│
├── 📁 reports/                    # Generated reports (auto-created)
│   ├── travel_report_*.xlsx     # Excel reports
│   └── travel_report_*.html     # HTML reports
│
└── 📁 sample_outputs/            # Example outputs
    ├── travel_report.xlsx       # Sample Excel
    └── travel_report.html       # Sample HTML
```

---

## 🎯 File Descriptions

### Core Application Files

#### `app.py` - Web Server (245 lines)
- Flask web application
- REST API endpoints
- Async request handling
- File download management
- Email sending coordination

**Key Routes:**
- `GET /` - Main interface
- `POST /search` - Trigger price search
- `GET /download/<file>` - Download reports
- `POST /send-email` - Email reports

---

#### `travel_aggregator.py` - Core Engine (360 lines)
- Multi-source data aggregation
- Async/await for parallel requests
- Web scraping logic
- API integration
- Excel report generation
- HTML report generation

**Classes:**
- `TravelAggregator` - Main aggregator class

**Key Methods:**
- `scrape_kayak()` - Kayak web scraping
- `get_amadeus_flights()` - Amadeus API integration
- `get_kiwi_flights()` - Kiwi API integration
- `scrape_booking_hotels()` - Booking.com scraping
- `get_hotels_combined()` - Hotel data aggregation
- `aggregate_all_data()` - Orchestrates all sources
- `create_excel_report()` - Generates Excel files
- `create_html_report()` - Generates HTML emails

**Data Flow:**
```
User Input → aggregate_all_data()
    ↓
Parallel Async Calls:
    - scrape_kayak()
    - get_amadeus_flights()
    - get_kiwi_flights()
    - scrape_booking_hotels()
    - get_hotels_combined()
    ↓
Aggregate Results → create_excel_report() + create_html_report()
    ↓
Return to User
```

---

#### `email_sender.py` - Email Module (185 lines)
- SMTP email functionality
- Professional email templates
- Attachment handling
- Gmail app password support

**Classes:**
- `EmailSender` - Email sending class

**Key Methods:**
- `send_report()` - Send email with attachments
- `create_client_email_template()` - Generate HTML email

**Email Template Features:**
- Gradient header design
- Trip details summary
- Flight options highlight
- Hotel options highlight
- Professional footer
- Responsive styling

---

#### `templates/index.html` - Web Interface (580 lines)
- Modern, responsive UI
- Real-time search status
- Results display
- Download functionality
- Email form
- Client-side validation

**Sections:**
- Search form with validation
- Loading indicator
- Results display (flights + hotels)
- Excel download button
- Email sending form
- Setup instructions

**JavaScript Features:**
- Form validation
- AJAX requests
- Dynamic results rendering
- Download handling
- Email sending

---

### Configuration Files

#### `requirements.txt`
```
flask==3.0.0           # Web framework
aiohttp==3.9.1         # Async HTTP client
pandas==2.1.4          # Data manipulation
openpyxl==3.1.2        # Excel file handling
beautifulsoup4==4.12.2 # HTML parsing
lxml==5.1.0            # XML/HTML parser
requests==2.31.0       # HTTP library
python-dotenv==1.0.0   # Environment variables
```

---

## 🔧 Technical Architecture

### Technology Stack
- **Backend**: Python 3.8+ with Flask
- **Async I/O**: asyncio + aiohttp
- **Data Processing**: pandas + openpyxl
- **Web Scraping**: BeautifulSoup4 + lxml
- **Email**: smtplib (built-in)
- **Frontend**: Vanilla JavaScript + HTML5 + CSS3

### Design Patterns
- **Async/Await**: Parallel data fetching
- **Factory Pattern**: Report generation
- **Template Method**: Email templates
- **Singleton**: TravelAggregator instance

### Performance Optimizations
- ✅ Concurrent API calls (5-8 simultaneous)
- ✅ Async I/O (non-blocking)
- ✅ Minimal CPU usage
- ✅ Streaming responses
- ✅ Efficient Excel writing

---

## 🚀 Deployment Options

### Development (Current)
```bash
python app.py
```
- Runs on http://localhost:5000
- Debug mode enabled
- Auto-reload on code changes

### Production Options

#### Option 1: Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Option 2: Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

#### Option 3: Cloud Deploy
- **Heroku**: `git push heroku main`
- **AWS**: Elastic Beanstalk
- **Google Cloud**: Cloud Run
- **Azure**: App Service

---

## 📊 Data Sources

### Current Implementation

| Source | Type | Method | Status |
|--------|------|--------|--------|
| Kayak | Flights | Scraping | Mock (Network restricted) |
| Amadeus | Flights | API | Mock (Needs API key) |
| Kiwi | Flights | API | Mock (Needs API key) |
| Booking.com | Hotels | Scraping | Mock (Network restricted) |
| HotelsCombined | Hotels | API | Mock (Needs API key) |

### To Enable Real Data

1. **Sign up for APIs**:
   - Amadeus: https://developers.amadeus.com
   - Kiwi: https://tequila.kiwi.com

2. **Add API keys** to `travel_aggregator.py`

3. **Replace mock data** with actual API calls

---

## 🔐 Security Considerations

### Current
- ✅ Input validation (airport codes)
- ✅ Date validation
- ✅ Email validation
- ✅ Password not stored
- ✅ HTTPS for external calls

### Production Needed
- [ ] Rate limiting
- [ ] API key encryption
- [ ] CSRF protection
- [ ] Input sanitization
- [ ] SQL injection prevention (if DB added)
- [ ] Environment variables for secrets

---

## 📈 Scalability

### Current Limits
- **Concurrent Users**: 1-10 (Flask dev server)
- **Requests/Second**: 5-10
- **Memory**: ~100MB
- **CPU**: Low (async I/O)

### Scale Up Options
1. **Multiple Workers**: Gunicorn with 4-8 workers
2. **Load Balancer**: Nginx → Multiple app instances
3. **Caching**: Redis for search results
4. **Queue**: Celery for background jobs
5. **Database**: PostgreSQL for history
6. **CDN**: CloudFlare for static assets

---

## 🧪 Testing

### Manual Testing
```bash
# Test core aggregator
python travel_aggregator.py

# Test email sender
python email_sender.py

# Test web server
python app.py
# Then visit http://localhost:5000
```

### Future: Unit Tests
```python
# tests/test_aggregator.py
def test_amadeus_api():
    aggregator = TravelAggregator()
    result = await aggregator.get_amadeus_flights(...)
    assert result is not None

def test_excel_generation():
    # Test Excel report creation
    pass

def test_email_sending():
    # Test email functionality
    pass
```

---

## 📝 Adding New Features

### Add New Data Source

1. **Create method in `travel_aggregator.py`**:
```python
async def get_source_name(self, session, origin, destination, date):
    # API call or scraping logic
    return {
        'source': 'SourceName',
        'type': 'Flight',
        # ... other data
    }
```

2. **Add to `aggregate_all_data()`**:
```python
tasks.append(self.get_source_name(session, origin, destination, departure_date))
```

3. **Done!** Results automatically included in reports.

---

## 🎓 Learning Resources

### Understanding the Code
1. **Async Python**: Official docs on asyncio
2. **Flask**: Flask mega-tutorial
3. **Web Scraping**: BeautifulSoup documentation
4. **pandas**: Excel generation with pandas

### Extending Functionality
1. Add API: See Amadeus/Kiwi integration
2. Add scraping: See Kayak/Booking examples
3. Modify reports: See `create_excel_report()`
4. Change UI: Edit `templates/index.html`

---

## 🤝 Contributing

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings
- Keep functions small (<50 lines)

### Before Committing
1. Test all features
2. Update documentation
3. Check for errors
4. Verify requirements.txt

---

## 📄 License

**Educational/Personal Use**

This project demonstrates:
- Async programming in Python
- Web scraping techniques
- API integration
- Report generation
- Email automation

**Important**: Web scraping may violate Terms of Service. Use official APIs for production.

---

## ✅ Next Steps

1. **Get it running**: Follow QUICKSTART.md
2. **Understand the code**: Read this document
3. **Add real APIs**: See README.md
4. **Customize**: Modify for your needs
5. **Deploy**: Choose production option above

---

**Happy Coding! 🚀**
