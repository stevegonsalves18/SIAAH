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
# Your Twilio phone number in E.164 format
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
    phone="+919876543210",
    district="Nashik",
    commodity="Wheat",
    preferred_time="07:00"
)

# Dummy fetch functions (replace with real APIs)
def fetch_weather():
    # Example data
    return 32, 5, 0.9

def fetch_price():
    # Example data
    return 2200, 0.92

def send_sms(temp, rain, price, confidence):
    try:
        sms_body = (
            f"नमस्ते {farmer.name}! आज मौसम: {temp}°C, बारिश: {rain}mm.\n"
            f"{farmer.commodity} भाव: ₹{price}/qtl (विश्वास: {confidence})."
        )
        
        message = twilio_client.messages.create(
            to=farmer.phone,
            from_=TWILIO_FROM,
            body=sms_body
        )
        print(f"SMS sent successfully: {message.sid}")
        return True
        
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False

def place_call(temp, rain, price):
    try:
        twiml = f"""
        <Response>
            <Say voice="alice" language="hi-IN">
                नमस्ते {farmer.name}! आप कैसे हैं? आपने खाना खाया?
                आज {farmer.commodity} का भाव ₹{price}/क्विंटल है।
                मौसम: {temp} डिग्री सेल्सियस, बारिश {rain} मिलीमीटर।
                और कोई मदद चाहिए?
            </Say>
        </Response>
        """
        
        call = twilio_client.calls.create(
            to=farmer.phone,
            from_=TWILIO_FROM,
            twiml=twiml
        )
        print(f"Call placed successfully: {call.sid}")
        return True
        
    except Exception as e:
        print(f"Error placing call: {e}")
        return False

def job_daily():
    print("Running daily job...")
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    send_sms(temp, rain, price, conf)
    place_call(temp, rain, price)

# Schedule the daily job
hour, minute = map(int, farmer.preferred_time.split(":"))
scheduler.add_job(job_daily, 'cron', hour=hour, minute=minute, id='daily_notification')

# API Endpoints
@app.get("/start")
def start():
    return {
        "status": "Schedulers running", 
        "next_run": f"{farmer.preferred_time} daily",
        "farmer": farmer.name
    }

@app.post("/test_sms")
async def test_sms():
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    success = send_sms(temp, rain, price, conf)
    return {
        "status": "SMS sent successfully" if success else "SMS failed",
        "data": {"temp": temp, "rain": rain, "price": price, "confidence": conf}
    }

@app.post("/test_call")
async def test_call():
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    success = place_call(temp, rain, price)
    return {
        "status": "Call placed successfully" if success else "Call failed",
        "data": {"temp": temp, "rain": rain, "price": price}
    }

@app.post("/run_now")
async def run_now():
    try:
        job_daily()
        return {"status": "Daily job executed successfully"}
    except Exception as e:
        return {"status": "Job failed", "error": str(e)}

@app.get("/farmer_info")
def get_farmer_info():
    return {
        "name": farmer.name,
        "district": farmer.district,
        "commodity": farmer.commodity,
        "preferred_time": farmer.preferred_time,
        "phone": farmer.phone[-4:]  # Only show last 4 digits
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "scheduler_running": scheduler.running,
        "twilio_configured": bool(TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM),
        "scheduled_jobs": len(scheduler.get_jobs())
    }

@app.get("/")
def root():
    return {
        "message": "AgriBuddy Notification Service",
        "version": "1.0",
        "farmer": farmer.name,
        "endpoints": {
            "status": "/start",
            "test_sms": "/test_sms (POST)",
            "test_call": "/test_call (POST)", 
            "run_daily": "/run_now (POST)",
            "farmer_info": "/farmer_info",
            "health": "/health"
        }
    }

