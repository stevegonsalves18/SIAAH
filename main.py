import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, Request
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AgriBuddy Email Notifications")
scheduler = AsyncIOScheduler()
scheduler.start()

# Email credentials from .env
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))

# Farmer data
class Farmer(BaseModel):
    name: str
    email: str
    district: str
    commodity: str
    preferred_time: str

farmer = Farmer(
    name="Ram",
    email="farmer@example.com",
    district="Nashik",
    commodity="Wheat",
    preferred_time="07:00"
)

# Dummy fetch functions (replace with real APIs)
def fetch_weather():
    return 32, 5, 0.9

def fetch_price():
    return 2200, 0.92

def send_email_to_farmer(email, name, temp, rain, price, confidence):
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = email
        msg['Subject'] = f"🌾 AgriBuddy: Weather & Price Update for {name}"
        
        # Email body in HTML format
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
              <h1>🌾 AgriBuddy Weather Update</h1>
            </div>
            
            <div style="padding: 20px; background: #f9f9f9; border-radius: 0 0 10px 10px;">
              <h2 style="color: #4CAF50;">नमस्ते {name}!</h2>
              
              <div style="background: white; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #4CAF50;">
                <h3 style="color: #333; margin: 0 0 10px 0;">🌡️ आज का मौसम</h3>
                <p style="font-size: 18px; margin: 5px 0;"><strong>तापमान:</strong> {temp}°C</p>
                <p style="font-size: 18px; margin: 5px 0;"><strong>बारिश:</strong> {rain}mm</p>
              </div>
              
              <div style="background: white; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #FF9800;">
                <h3 style="color: #333; margin: 0 0 10px 0;">💰 आज की कीमत</h3>
                <p style="font-size: 20px; margin: 5px 0; color: #FF9800;"><strong>{farmer.commodity}:</strong> ₹{price}/क्विंटल</p>
                <p style="font-size: 14px; color: #666;">विश्वसनीयता: {confidence:.0%}</p>
              </div>
              
              <div style="background: #e3f2fd; padding: 15px; margin: 15px 0; border-radius: 8px;">
                <h3 style="color: #1976d2; margin: 0 0 10px 0;">📱 सुझाव</h3>
                <ul style="color: #333; line-height: 1.6;">
                  <li>मौसम के अनुसार फसल की देखभाल करें</li>
                  <li>उचित कीमत पर बिक्री का समय तय करें</li>
                  <li>किसी भी समस्या के लिए हमसे संपर्क करें</li>
                </ul>
              </div>
              
              <div style="text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
                <p style="color: #666; font-size: 14px;">
                  यह संदेश AgriBuddy द्वारा भेजा गया है<br>
                  रोज सुबह 7 बजे आपको अपडेट मिलेगा
                </p>
              </div>
            </div>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, email, text)
        server.quit()
        
        print(f"Email sent successfully to {email} for {name}")
        return True
        
    except Exception as e:
        print(f"Error sending email to {email}: {e}")
        return False

# Scheduled job function
def job_daily():
    print("Running scheduled daily email job...")
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    send_email_to_farmer(farmer.email, farmer.name, temp, rain, price, conf)

# Schedule the daily job
hour, minute = map(int, farmer.preferred_time.split(":"))
scheduler.add_job(job_daily, 'cron', hour=hour, minute=minute, id='daily_email_notification')

# API ENDPOINTS
@app.get("/")
def root():
    return {
        "message": "AgriBuddy Email Notification Service",
        "version": "3.0",
        "features": ["Email notifications", "Scheduled daily emails", "AI agent integration"],
        "ai_agent_endpoint": {
            "send_email": "/send_email_get?email=farmer@example.com&name=FarmerName"
        },
        "test_endpoint": "/send_email_get?email=your-email@gmail.com&name=YourName",
        "system_status": "Email-only, No SMS restrictions"
    }

@app.get("/start")
def start():
    return {
        "status": "AgriBuddy Email system running",
        "scheduler_active": scheduler.running,
        "next_scheduled_run": f"{farmer.preferred_time} daily",
        "default_farmer": farmer.name,
        "email_configured": bool(EMAIL_USER and EMAIL_PASSWORD),
        "sms_status": "Disabled (Email-only mode)"
    }

# EMAIL ENDPOINT FOR AI AGENT
@app.get("/send_email_get")
async def send_email_get(email: str, name: str = "Farmer"):
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    success = send_email_to_farmer(email, name, temp, rain, price, conf)
    
    return {
        "status": "Email sent successfully" if success else "Email failed",
        "sent_to": email,
        "name": name,
        "message": f"Weather update sent via email: {temp}°C, Rain: {rain}mm, Price: ₹{price}/qtl",
        "delivery_method": "Email",
        "ai_agent_success": True
    }

# POST ENDPOINT (alternative for AI agent)
@app.post("/send_email_to")
async def send_email_to(request: Request):
    data = await request.json()
    email = data.get("email", farmer.email)
    name = data.get("name", "Farmer")
    
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    
    success = send_email_to_farmer(email, name, temp, rain, price, conf)
    return {
        "status": "Email sent successfully" if success else "Email failed",
        "sent_to": email,
        "name": name,
        "message_content": f"Weather: {temp}°C, Rain: {rain}mm, Price: ₹{price}/qtl"
    }

# UTILITY ENDPOINTS
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "scheduler_running": scheduler.running,
        "email_configured": bool(EMAIL_USER and EMAIL_PASSWORD),
        "scheduled_jobs": len(scheduler.get_jobs()),
        "service_type": "Email-only"
    }

@app.get("/test_email")
async def test_email(email: str = "test@example.com", name: str = "Test User"):
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    success = send_email_to_farmer(email, name, temp, rain, price, conf)
    return {
        "status": "Email sent successfully" if success else "Email failed",
        "test_email": email,
        "configured": bool(EMAIL_USER and EMAIL_PASSWORD),
        "message": "Check your email inbox for AgriBuddy update!"
    }

@app.get("/farmer_info")
def get_farmer_info():
    return {
        "default_farmer": {
            "name": farmer.name,
            "district": farmer.district,
            "commodity": farmer.commodity,
            "preferred_time": farmer.preferred_time,
            "email": farmer.email
        },
        "system_info": {
            "scheduled_notifications": "Active",
            "delivery_method": "Email only",
            "sms_disabled": "No Indian numbers available"
        }
    }
