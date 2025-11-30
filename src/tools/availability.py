from typing import Dict, List, Any
from datetime import datetime, timedelta
from .data_manager import load_data
from dateutil import parser
from collections import defaultdict


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
    
    available_slots.sort(key=lambda x: (x["date"], x["time"]))
    
    limited_slots = available_slots[:5]
    
    if not limited_slots:
        message = "Unfortunately, no appointments are available on the requested dates."
    else:
        # Group by date
        slots_by_date = defaultdict(list)
        for slot in limited_slots:
            slots_by_date[slot["date"]].append(slot)
        
        # Format each date's slots
        date_messages = []
        for date_str in sorted(slots_by_date.keys()):
            slots = slots_by_date[date_str]
            
            # Format date
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            readable_date = date_obj.strftime("%B %d")  # "December 9"
            
            # Format times
            times = []
            for slot in slots:
                time_obj = datetime.strptime(slot["time"], "%H:%M")
                readable_time = time_obj.strftime("%I:%M %p").lstrip("0")  # "9:00 AM"
                times.append(readable_time)
            
            # Build message for this date
            count = len(slots)
            if count == 1:
                date_msg = f"{readable_date} at {times[0]}"
            elif count == 2:
                date_msg = f"{readable_date} at {times[0]} and {times[1]}"
            else:
                time_list = ", ".join(times[:-1]) + f", and {times[-1]}"
                date_msg = f"{readable_date} at {time_list}"
            
            date_messages.append(f"We have {count} {'slot' if count == 1 else 'slots'} available on {date_msg}")
        
        message = ". ".join(date_messages) + "."
        
        if len(available_slots) > 5:
            remaining = len(available_slots) - 5
            message += f" (Plus {remaining} more {'slot' if remaining == 1 else 'slots'} available.)"
    
    return {
        "status": "success",
        "message": message,
        "slot_ids": [slot["id"] for slot in limited_slots],  # Keep IDs for booking
        "total_available": len(available_slots)
    }


def get_all_available_slots() -> List[Dict[str, Any]]:
    """Get all available slots"""
    data = load_data()
    available_slots = [
        apt for apt in data["apartments"] 
        if apt["available"]
    ]
    
    available_slots.sort(key=lambda x: (x["date"], x["time"]))
    
    return available_slots


def get_next_available_slots(count: int = 5) -> Dict[str, Any]:
    data = load_data()
    today = datetime.now().date()
    
    upcoming_slots = [
        apt for apt in data["appointments"]
        if apt["available"] and datetime.strptime(apt["date"], "%Y-%m-%d").date() >= today
    ]
    
    upcoming_slots.sort(key=lambda x: (x["date"], x["time"]))
    
    limited_slots = upcoming_slots[:count]
    
    slots_by_date = defaultdict(list)
    for slot in limited_slots:
        slots_by_date[slot["date"]].append(slot)
    
    date_messages = []
    for date_str in sorted(slots_by_date.keys()):
        slots = slots_by_date[date_str]
        
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        readable_date = date_obj.strftime("%B %d")
        
        times = []
        for slot in slots:
            time_obj = datetime.strptime(slot["time"], "%H:%M")
            readable_time = time_obj.strftime("%I:%M %p").lstrip("0")
            times.append(readable_time)
        
        count_slots = len(slots)
        if count_slots == 1:
            date_msg = f"{readable_date} at {times[0]}"
        elif count_slots == 2:
            date_msg = f"{readable_date} at {times[0]} and {times[1]}"
        else:
            time_list = ", ".join(times[:-1]) + f", and {times[-1]}"
            date_msg = f"{readable_date} at {time_list}"
        
        date_messages.append(f"{readable_date}: {', '.join(times)}")
    
    message = "Next available slots: " + "; ".join(date_messages)
    
    return {
        "status": "success",
        "message": message,
        "slot_ids": [slot["id"] for slot in limited_slots],
        "total_available": len(upcoming_slots)
    }


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
        readable_date = date_obj.strftime("%B %d, %Y")
        
        time_obj = datetime.strptime(slot["time"], "%H:%M")
        readable_time = time_obj.strftime("%I:%M %p").lstrip("0")
        
        formatted.append(f"{readable_date} at {readable_time}")
    
    return "\n".join(f"- {item}" for item in formatted)


def parse_date_from_text(date_text: str) -> str:
    
    try:
        parsed_date = parser.parse(date_text, fuzzy=True)
        return parsed_date.strftime("%Y-%m-%d")
    except:
        return None
