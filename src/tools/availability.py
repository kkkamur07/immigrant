from typing import Dict, List, Any
from datetime import datetime, timedelta
from .data_manager import load_data
from dateutil import parser


def check_availability(dates: List[str]) -> Dict[str, Any]:

    data = load_data()
    available_slots = []
    
    for appointment in data["appointments"]:
        if appointment["date"] in dates and appointment["available"]:
            available_slots.append({
                "id": appointment["id"],
                "date": appointment["date"],
                "time": appointment["time"],
                "type": appointment["type"]
            })
    
    # Sort by date and time
    available_slots.sort(key=lambda x: (x["date"], x["time"]))
    
    return {
        "status": "success",
        "requested_dates": dates,
        "available_slots": available_slots,
        "total_available": len(available_slots),
        "message": f"Found {len(available_slots)} available appointment(s)"
    }


def get_all_available_slots() -> List[Dict[str, Any]]:

    data = load_data()
    available_slots = [
        apt for apt in data["appointments"] 
        if apt["available"]
    ]
    
    # Sort by date and time
    available_slots.sort(key=lambda x: (x["date"], x["time"]))
    
    return available_slots


def get_next_available_slots(count: int = 5) -> List[Dict[str, Any]]:

    data = load_data()
    today = datetime.now().date()
    
    upcoming_slots = [
        apt for apt in data["appointments"]
        if apt["available"] and datetime.strptime(apt["date"], "%Y-%m-%d").date() >= today
    ]
    
    upcoming_slots.sort(key=lambda x: (x["date"], x["time"]))
    
    return upcoming_slots[:count]


def is_slot_available(appointment_id: str) -> bool:

    data = load_data()
    
    for appointment in data["appointments"]:
        if appointment["id"] == appointment_id:
            return appointment["available"]
    
    return False


def get_appointment_by_id(appointment_id: str) -> Dict[str, Any]:

    data = load_data()
    
    for appointment in data["appointments"]:
        if appointment["id"] == appointment_id:
            return appointment
    
    return None


def format_slots_for_display(slots: List[Dict[str, Any]]) -> str:
 
    if not slots:
        return "No available slots found."
    
    formatted = []
    for slot in slots:
        
        date_obj = datetime.strptime(slot["date"], "%Y-%m-%d")
        readable_date = date_obj.strftime("%B %d, %Y")  # e.g., "December 05, 2025"
        
        time_obj = datetime.strptime(slot["time"], "%H:%M")
        readable_time = time_obj.strftime("%I:%M %p")  # e.g., "09:00 AM"
        
        formatted.append(f"{readable_date} at {readable_time}")
    
    return "\n".join(f"- {item}" for item in formatted)


def parse_date_from_text(date_text: str) -> str:
        
    try:
        parsed_date = parser.parse(date_text, fuzzy=True)
        return parsed_date.strftime("%Y-%m-%d")
    
    except:
        return None
