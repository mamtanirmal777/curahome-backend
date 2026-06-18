from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime

load_dotenv()

app = FastAPI()
api_router = APIRouter(prefix="/api")

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client[os.environ.get('DB_NAME', 'curahome')]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Doctor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    specialty: str
    experience: int
    rating: float = 4.5
    image: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_name: str
    user_phone: str
    doctor_id: str
    doctor_name: str
    date: str
    time: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Routes
@api_router.get("/")
async def root():
    return {"message": "CuraHome API", "version": "1.0.0"}

@api_router.get("/doctors", response_model=List[Doctor])
async def get_doctors():
    doctors = await db.doctors.find().to_list(100)
    return [Doctor(**doc) for doc in doctors]

@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking: Booking):
    await db.bookings.insert_one(booking.dict())
    return booking

@api_router.get("/bookings")
async def get_bookings(phone: Optional[str] = None):
    if phone:
        bookings = await db.bookings.find({"user_phone": phone}).to_list(100)
    else:
        bookings = await db.bookings.find().to_list(100)
    return bookings

app.include_router(api_router)

@app.on_event("startup")
async def startup_db():
    # Add sample doctors if empty
    count = await db.doctors.count_documents({})
    if count == 0:
        sample_doctors = [
            {"name": "Dr. Priya Sharma", "specialty": "Cardiologist", "experience": 12, "rating": 4.8, "image": ""},
            {"name": "Dr. Raj Verma", "specialty": "Dermatologist", "experience": 8, "rating": 4.6, "image": ""},
            {"name": "Dr. Anita Singh", "specialty": "Pediatrician", "experience": 15, "rating": 4.9, "image": ""}
        ]
        await db.doctors.insert_many(sample_doctors)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
