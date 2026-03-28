# 🚀 QUICK START - 2 Minutes to Your First Search!

## Step 1: Install Dependencies (First Time Only)
```bash
pip install -r requirements.txt
```

## Step 2: Start the Application
```bash
python app.py
```
OR
```bash
./start.sh
```

## Step 3: Open in Browser
Go to: **http://localhost:5000**

---

## ✈️ First Search

1. **Origin**: BOM (Mumbai)
2. **Destination**: DEL (Delhi)
3. **Departure**: Pick a future date
4. **Return**: Pick a later date (optional)
5. Click **"Search Best Prices"**

**Wait 10-30 seconds** → See results from multiple sources!

---

## 📥 What You Get

✅ **Real-time prices** from multiple sources
✅ **Excel report** - Download with one click
✅ **Email capability** - Send directly to clients
✅ **Professional formatting** - Ready to present

---

## 🎯 Common Airport Codes

| City | Code |
|------|------|
| Mumbai | BOM |
| Delhi | DEL |
| Bangalore | BLR |
| Goa | GOI |
| Pune | PNQ |
| Hyderabad | HYD |
| Chennai | MAA |
| Dubai | DXB |
| Singapore | SIN |
| London | LHR |

---

## 📧 Send Email to Clients

### Gmail Setup (5 minutes)

1. **Enable 2-Factor Auth**
   - Visit: https://myaccount.google.com/security
   - Turn on 2-Step Verification

2. **Get App Password**
   - Visit: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the 16-digit password

3. **In the Web Interface**
   - Fill in client details
   - Your Email: your_gmail@gmail.com
   - App Password: paste the 16-digit code
   - Click "Send Email Report"

---

## ⚡ Features Overview

### Current (Working Now)
- ✅ Multi-source flight prices
- ✅ Multi-source hotel prices
- ✅ Excel report generation
- ✅ Email with attachments
- ✅ Professional templates
- ✅ Fast async processing

### Mock Data (Replace with Real APIs)
The app currently uses **mock/sample data** for demonstration.

**To get REAL data:**
1. Sign up for FREE APIs:
   - **Amadeus**: https://developers.amadeus.com (2000 calls/month FREE)
   - **Kiwi**: https://tequila.kiwi.com (Free tier available)

2. Add API keys to `travel_aggregator.py`
3. Replace mock data sections with actual API calls

**See README.md** for detailed API integration instructions.

---

## 🐛 Quick Troubleshooting

**Problem**: Module not found
**Solution**: `pip install -r requirements.txt --upgrade`

**Problem**: Can't send email
**Solution**: Use App Password, not regular Gmail password

**Problem**: Port 5000 already in use
**Solution**: Edit `app.py`, change port to 8080

**Problem**: No results
**Solution**: Check airport codes (must be 3 letters, e.g., BOM, DEL)

---

## 💡 Pro Tips

1. **Use 3-letter IATA codes** (not city names)
2. **Select future dates** (past dates won't work)
3. **Excel download** appears after search completes
4. **Email section** appears below the results
5. **One-way trips**: Leave return date empty

---

## 📞 Need More Help?

Read the full **README.md** for:
- Detailed API setup
- Production deployment
- Advanced features
- Complete troubleshooting

---

## 🎉 You're Ready!

```bash
python app.py
```

Then open **http://localhost:5000** and start searching! 🌍✈️
