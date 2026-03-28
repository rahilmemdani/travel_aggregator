import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List

class EmailSender:
    def __init__(self, smtp_server='smtp.gmail.com', smtp_port=587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
    
    def send_report(self, 
                    sender_email: str,
                    sender_password: str,
                    recipient_email: str,
                    subject: str,
                    html_content: str,
                    attachments: List[str] = None):
        """
        Send email with HTML content and attachments
        
        For Gmail: 
        - Use App Password (not regular password)
        - Enable 2-factor authentication
        - Generate app password: https://myaccount.google.com/apppasswords
        """
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        filename = os.path.basename(file_path)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        msg.attach(part)
            
            # Connect and send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            return False
    
    def create_client_email_template(self, client_name: str, trip_details: dict, 
                                     flight_summary: str, hotel_summary: str):
        """Create professional email template for clients"""
        
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .section {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border-left: 4px solid #667eea;
                }}
                .trip-details {{
                    background: white;
                    padding: 15px;
                    border-radius: 6px;
                    margin: 10px 0;
                }}
                .price-highlight {{
                    color: #27ae60;
                    font-size: 1.3em;
                    font-weight: bold;
                }}
                .footer {{
                    text-align: center;
                    color: #7f8c8d;
                    padding: 20px;
                    border-top: 2px solid #ecf0f1;
                    margin-top: 30px;
                }}
                ul {{
                    list-style-type: none;
                    padding-left: 0;
                }}
                li {{
                    padding: 8px 0;
                    border-bottom: 1px solid #ecf0f1;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✈️ Your Travel Itinerary</h1>
                <p>Prepared exclusively for {client_name}</p>
            </div>
            
            <div class="section">
                <h2>📍 Trip Details</h2>
                <div class="trip-details">
                    <ul>
                        <li><strong>🛫 Origin:</strong> {trip_details.get('origin', 'N/A')}</li>
                        <li><strong>🛬 Destination:</strong> {trip_details.get('destination', 'N/A')}</li>
                        <li><strong>📅 Departure:</strong> {trip_details.get('departure_date', 'N/A')}</li>
                        <li><strong>📅 Return:</strong> {trip_details.get('return_date', 'N/A')}</li>
                        <li><strong>👥 Travelers:</strong> {trip_details.get('travelers', 1)}</li>
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h2>✈️ Flight Options</h2>
                {flight_summary}
            </div>
            
            <div class="section">
                <h2>🏨 Hotel Options</h2>
                {hotel_summary}
            </div>
            
            <div class="section">
                <h2>📎 Attachments</h2>
                <p>Please find the detailed Excel report attached with comprehensive pricing from multiple sources.</p>
                <p><strong>💡 Pro Tip:</strong> Book early for better prices! Prices shown are real-time and may change.</p>
            </div>
            
            <div class="footer">
                <p><strong>Need help booking?</strong></p>
                <p>Contact us anytime - we're here to make your travel planning effortless!</p>
                <p style="font-size: 0.9em; margin-top: 20px;">
                    This report was generated using our automated travel aggregator system.<br>
                    All prices are in INR and subject to availability.
                </p>
            </div>
        </body>
        </html>
        """
        
        return html


# Example usage
if __name__ == "__main__":
    sender = EmailSender()
    
    # Example email
    trip_details = {
        'origin': 'Mumbai (BOM)',
        'destination': 'Delhi (DEL)',
        'departure_date': '2025-05-15',
        'return_date': '2025-05-22',
        'travelers': 2
    }
    
    flight_summary = """
    <p class="price-highlight">Best Price: ₹4,500 per person</p>
    <p>We found flights from multiple carriers including Air India, IndiGo, and Vistara.</p>
    <p>Direct flights available with flexible timing options.</p>
    """
    
    hotel_summary = """
    <p class="price-highlight">Starting from: ₹1,200 per night</p>
    <p>150+ hotels available ranging from budget to luxury options.</p>
    <p>Central locations with great reviews included in the report.</p>
    """
    
    html_email = sender.create_client_email_template(
        client_name="Valued Client",
        trip_details=trip_details,
        flight_summary=flight_summary,
        hotel_summary=hotel_summary
    )
    
    print("✅ Email template created!")
    print("\nTo send emails, configure your SMTP credentials:")
    print("  - For Gmail: Use App Password (Settings > Security > App Passwords)")
    print("  - For Outlook: Use regular password with 'Less secure apps' enabled")
