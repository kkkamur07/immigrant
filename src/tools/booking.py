import secrets
from typing import Dict, Any
from datetime import datetime, timedelta
from .data_manager import load_data, save_data
from .user_info import validate_user_data
from .availability import get_appointment_by_id
from .email_service import send_confirmation_email_sync, send_booking_confirmation_email_sync


def reserve_slot_temporarily(
    appointment_id: str, 
    user_data: Dict[str, str]
) -> Dict[str, Any]:

    data = load_data()
    
    validation = validate_user_data(user_data)
    if not validation["valid"]:
        return {
            "status": "error",
            "message": "Invalid user data",
            "errors": validation["errors"]
        }
    
    # Validate that appointment exists and is available
    appointment = None
    for apt in data["appointments"]:
        if apt["id"] == appointment_id:
            if not apt["available"]:
                return {
                    "status": "error",
                    "message": "This appointment slot is no longer available",
                    "appointment_id": appointment_id
                }
            appointment = apt
            break
    
    if not appointment:
        return {
            "status": "error",
            "message": "Appointment not found",
            "appointment_id": appointment_id
        }
    
    # Generate secure confirmation token
    token = secrets.token_urlsafe(32)
    created_at = datetime.now()
    expires_at = created_at + timedelta(minutes=30)
    
    # Create pending confirmation record
    pending_confirmation = {
        "token": token,
        "appointment_id": appointment_id,
        "user_data": {
            "name": user_data["name"],
            "email": user_data["email"],
            "reason": user_data["reason"]
        },
        "appointment_details": {
            "date": appointment["date"],
            "time": appointment["time"],
            "type": appointment["type"]
        },
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "status": "pending"
    }
    
    data["pending_confirmations"].append(pending_confirmation)
    save_data(data)
    
    # Send confirmation email
    email_result = send_confirmation_email_sync(
        recipient_email=user_data["email"],
        recipient_name=user_data["name"],
        appointment_details={
            "date": appointment["date"],
            "time": appointment["time"],
            "type": appointment["type"]
        },
        confirmation_token=token,
        reason=user_data["reason"]
    )
    
    print(email_result)
    
    return {
        "status": "success",
        "message": "Appointment slot reserved temporarily",
        "confirmation_token": token,
        "appointment_details": {
            "id": appointment["id"],
            "date": appointment["date"],
            "time": appointment["time"],
            "type": appointment["type"]
        },
        "user_email": user_data["email"],
        "expires_in_minutes": 30,
        "expires_at": expires_at.isoformat(),
        "email_sent": email_result["status"] == "success"
    }


def book_appointment(token: str) -> Dict[str, Any]:

    data = load_data()
    
    # Find the pending confirmation
    pending = None
    pending_index = None
    for idx, conf in enumerate(data["pending_confirmations"]):
        if conf["token"] == token and conf["status"] == "pending":
            pending = conf
            pending_index = idx
            break
    
    if not pending:
        return {
            "status": "error",
            "message": "Invalid or already used confirmation token"
        }
    
    # Check if token has expired
    expires_at = datetime.fromisoformat(pending["expires_at"])
    if datetime.now() > expires_at:
        data["pending_confirmations"][pending_index]["status"] = "expired"
        save_data(data)
        return {
            "status": "error",
            "message": "Confirmation token has expired. Please request a new appointment."
        }
    
    appointment = None
    appointment_index = None
    for idx, apt in enumerate(data["appointments"]):
        if apt["id"] == pending["appointment_id"]:
            if not apt["available"]:
                return {
                    "status": "error",
                    "message": "This appointment slot is no longer available"
                }
            appointment = apt
            appointment_index = idx
            break
    
    if not appointment:
        return {
            "status": "error",
            "message": "Appointment not found"
        }
    
    data["appointments"][appointment_index]["available"] = False
    
    booking_id = f"BKG_{secrets.token_hex(4).upper()}"
    
    booking = {
        "booking_id": booking_id,
        "appointment_id": pending["appointment_id"],
        "user_data": pending["user_data"],
        "appointment_details": pending["appointment_details"],
        "booked_at": datetime.now().isoformat(),
        "status": "confirmed"
    }
    
    data["bookings"].append(booking)
    data["pending_confirmations"][pending_index]["status"] = "confirmed"
    data["pending_confirmations"][pending_index]["booking_id"] = booking_id
    
    save_data(data)
    
    # Send final booking confirmation email
    email_result = send_booking_confirmation_email_sync(
        recipient_email=pending["user_data"]["email"],
        recipient_name=pending["user_data"]["name"],
        booking_id=booking_id,
        appointment_details=pending["appointment_details"],
        reason=pending["user_data"]["reason"]
    )
    
    return {
        "status": "success",
        "message": "Appointment confirmed successfully!",
        "booking": booking,
        "email_sent": email_result["status"] == "success"
    }


def get_pending_confirmation(token: str) -> Dict[str, Any]:

    data = load_data()
    
    for conf in data["pending_confirmations"]:
        if conf["token"] == token:
            return conf
    
    return None


def get_booking_by_id(booking_id: str) -> Dict[str, Any]:

    data = load_data()
    
    for booking in data["bookings"]:
        if booking["booking_id"] == booking_id:
            return booking
    
    return None


def cancel_booking(booking_id: str) -> Dict[str, Any]:

    data = load_data()
    
    booking = None
    booking_index = None
    for idx, bkg in enumerate(data["bookings"]):
        if bkg["booking_id"] == booking_id and bkg["status"] == "confirmed":
            booking = bkg
            booking_index = idx
            break
    
    if not booking:
        return {
            "status": "error",
            "message": "Booking not found or already cancelled"
        }
    
    # Mark appointment as available again
    for apt in data["appointments"]:
        if apt["id"] == booking["appointment_id"]:
            apt["available"] = True
            break
    
    # Update booking status
    data["bookings"][booking_index]["status"] = "cancelled"
    data["bookings"][booking_index]["cancelled_at"] = datetime.now().isoformat()
    
    save_data(data)
    
    return {
        "status": "success",
        "message": "Booking cancelled successfully",
        "booking_id": booking_id
    }


def cleanup_expired_confirmations() -> int:

    data = load_data()
    now = datetime.now()
    cleaned_count = 0
    
    for conf in data["pending_confirmations"]:
        if conf["status"] == "pending":
            expires_at = datetime.fromisoformat(conf["expires_at"])
            if now > expires_at:
                conf["status"] = "expired"
                cleaned_count += 1
    
    if cleaned_count > 0:
        save_data(data)
    
    return cleaned_count
