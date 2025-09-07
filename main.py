import os
from fastapi import FastAPI
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
    sms_body = (
        f"नमस्ते {farmer.name}! आज मौसम: {temp}°C, बारिश: {rain}mm.\n"
        f"{farmer.commodity} भाव: ₹{price}/qtl (विश्वास: {confidence})."
    )
    twilio_client.messages.create(
        to=farmer.phone,
        from_=TWILIO_FROM,
        body=sms_body
    )


def place_call(temp, rain, price):
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
    twilio_client.calls.create(
        to=farmer.phone,
        from_=TWILIO_FROM,
        twiml=twiml
    )


def job_daily():
    temp, rain, _ = fetch_weather()
    price, conf = fetch_price()
    send_sms(temp, rain, price, conf)
    place_call(temp, rain, price)


hour, minute = map(int, farmer.preferred_time.split(":"))
scheduler.add_job(job_daily, 'cron', hour=hour, minute=minute)


@app.get("/start")
def start():
    return {"status": "Schedulers running"}
