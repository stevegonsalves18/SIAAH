import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AgriBuddy Notifications")
scheduler = AsyncIOScheduler()
scheduler.start()

# Twilio credentials from .env
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")

twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)

# Farmer data
class Farmer(BaseModel):
    name: str
    phone: str  # E.164 format e.g. +919876543210
    district: str
    commodity: str
    preferred_time: str  # HH:MM 24-hour format

farmer = Farmer(
    name="Ram",
    phone="+919876543210",  # Default farmer
    district="Nashik",
    commodity="Wheat",
    preferred_time="07:00"
)

# Dummy fetch functions (replace with real APIs)
def fetch_weather():
    return 32, 5, 0.9

def fetch_price():
    return 2200, 0.92

def send_sms_to_phone(phone, name, temp, rain, price, confidence):
    try:
        sms_body = f"नमस्ते {name}! आज मौसम: {temp}°C, बारिश: {rain}mm.\n{farmer.commodity} भाव: ₹{price}/qtl (विश्वास: {confidence})"
        
        message = twilio_client.messages.create(
            to=phone,
            from_=TWILIO_FROM,
            body=sms_body
        )
        print(f"SMS sent to {phone}: {message.sid}")
        return True
    except Exception as e:
        print(f"Error sending SMS to {phone}: {e}")
        return False

def make_call_to_phone(phone, name, temp, rain, price):
    try:
        twiml = f"""
        <Response>
            <Say voice="alice" language="hi-IN">
                नमस्ते {name}! आप कैसे हैं? आपने खाना खाया?
                आज {farmer.commodity} का भाव ₹{price}/क्विंटल है।
                मौसम: {temp} डिग्री सेल्सियस, बारिश {rain} मिलीमीटर।
                और कोई मदद चाहिए?
            </Say>
        </Response>
        """
        
        call = twilio_client.calls.create(
            to=phone,
            from_=TWILIO_FROM,
            twiml=twiml
        )
        print(f"Call placed to {phone}: {call.sid}")
        return True
    except Exception as e:
        print(f"Error calling {phone}: {e}")
        return False

# Original functions for scheduled job
def send_sms(temp, rain, price, confidence):
    return send_sms_to_phone(farmer.phone, farmer.name, temp, rain, price, confidence)

def place_call(temp, rain, price):
    return make_call_to_phone(farmer.phone, farmer.name, temp, rain, price)

def job_daily():
    print("Running scheduled daily job...")
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    send_sms(temp, rain, price, conf)
    place_call(temp, rain, price)

# Schedule the daily job
hour, minute = map(int, farmer.preferred_time.split(":"))
scheduler.add_job(job_daily, 'cron', hour=hour, minute=minute, id='daily_notification')

# API ENDPOINTS
@app.get("/")
def root():
    return {
        "message": "AgriBuddy Notification Service",
        "version": "2.0",
        "features": ["Scheduled notifications", "On-demand SMS", "Dynamic phone numbers"],
        "ai_agent_endpoints": {
            "send_sms_get": "/send_sms_get?phone=+91XXXXXXXXXX&name=FarmerName",
            "call_get": "/call_get?phone=+91XXXXXXXXXX&name=FarmerName",
            "status": "/start"
        },
        "post_endpoints": {
            "send_sms_to": "/send_sms_to (POST)",
            "call_number": "/call_number (POST)"
        }
    }

@app.get("/start")
def start():
    return {
        "status": "AgriBuddy system running",
        "scheduler_active": scheduler.running,
        "next_scheduled_run": f"{farmer.preferred_time} daily",
        "default_farmer": farmer.name
    }

# ORIGINAL ENDPOINTS (for default farmer)
@app.post("/test_sms")
async def test_sms():
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    success = send_sms(temp, rain, price, conf)
    return {
        "status": "SMS sent successfully" if success else "SMS failed",
        "sent_to": farmer.phone,
        "data": {"temp": temp, "rain": rain, "price": price}
    }

@app.post("/test_call")
async def test_call():
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    success = place_call(temp, rain, price)
    return {
        "status": "Call placed successfully" if success else "Call failed",
        "called": farmer.phone,
        "data": {"temp": temp, "rain": rain, "price": price}
    }

@app.post("/run_now")
async def run_now():
    try:
        job_daily()
        return {"status": "Daily job executed successfully", "farmer": farmer.name}
    except Exception as e:
        return {"status": "Job failed", "error": str(e)}

# DYNAMIC ENDPOINTS (for any phone number) - POST VERSION
@app.post("/send_sms_to")
async def send_sms_to(request: Request):
    data = await request.json()
    phone = data.get("phone", farmer.phone)
    name = data.get("name", "Farmer")
    
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    
    success = send_sms_to_phone(phone, name, temp, rain, price, conf)
    return {
        "status": "SMS sent successfully" if success else "SMS failed",
        "sent_to": phone,
        "name": name,
        "message_content": f"Weather: {temp}°C, Rain: {rain}mm, Price: ₹{price}/qtl"
    }

@app.post("/call_number")
async def call_number(request: Request):
    data = await request.json()
    phone = data.get("phone", farmer.phone)
    name = data.get("name", "Farmer")
    
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    
    success = make_call_to_phone(phone, name, temp, rain, price)
    return {
        "status": "Call placed successfully" if success else "Call failed",
        "called": phone,
        "name": name,
        "call_content": f"Weather info and price: ₹{price}/qtl"
    }

# AI AGENT FRIENDLY GET ENDPOINTS (to fix "Method Not Allowed" error)
@app.get("/send_sms_get")
async def send_sms_get(phone: str, name: str = "Farmer"):
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    success = send_sms_to_phone(phone, name, temp, rain, price, conf)
    return {
        "status": "SMS sent successfully" if success else "SMS failed",
        "sent_to": phone,
        "name": name,
        "message": f"Weather update sent: {temp}°C, Rain: {rain}mm, Price: ₹{price}/qtl",
        "ai_agent_success": True
    }

@app.get("/call_get")
async def call_get(phone: str, name: str = "Farmer"):
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    success = make_call_to_phone(phone, name, temp, rain, price)
    return {
        "status": "Call placed successfully" if success else "Call failed",
        "called": phone,
        "name": name,
        "message": f"Voice call placed with weather and price info",
        "ai_agent_success": True
    }

# UTILITY ENDPOINTS
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "scheduler_running": scheduler.running,
        "twilio_configured": bool(TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM),
        "scheduled_jobs": len(scheduler.get_jobs())
    }

@app.get("/farmer_info")
def get_farmer_info():
    return {
        "default_farmer": {
            "name": farmer.name,
            "district": farmer.district,
            "commodity": farmer.commodity,
            "preferred_time": farmer.preferred_time,
            "phone_last_4": farmer.phone[-4:]
        }
    }

