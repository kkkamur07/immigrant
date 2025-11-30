import asyncio
from typing import Dict, Any
import json
from .data_manager import load_data, save_data, get_data_file_path

from .user_info import (
    collect_user_info,
    validate_email,
    validate_user_data,
    format_user_data_for_display
)

from .availability import (
    check_availability,
    get_all_available_slots,
    get_next_available_slots,
    is_slot_available,
    get_appointment_by_id,
    format_slots_for_display
)

from .booking import (
    reserve_slot_temporarily,
    book_appointment,
    get_pending_confirmation,
    get_booking_by_id,
    cancel_booking,
    cleanup_expired_confirmations
)

from .email_service import (
    send_confirmation_email,
    send_booking_confirmation_email
    # ✅ Removed sync wrappers
)

from .schemas import (
    TOOLS_SCHEMA,
    get_tools_schema,
    get_function_schema,
    get_all_function_names
)

AVAILABLE_FUNCTIONS = {
    "collect_user_info": collect_user_info,
    "check_availability": check_availability,
    "reserve_slot_temporarily": reserve_slot_temporarily,
    "book_appointment": book_appointment,
    "cancel_booking": cancel_booking,
    "send_confirmation_email": send_confirmation_email,
    "send_booking_confirmation_email": send_booking_confirmation_email,
}


async def get_function_by_name(function_name: str):
    """Get function by name - now async"""
    return AVAILABLE_FUNCTIONS.get(function_name)


async def execute_function_call(function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute function calls - handles both sync and async functions automatically
    """
    function = AVAILABLE_FUNCTIONS.get(function_name)
    
    if not function:
        return {
            "status": "error",
            "message": f"Function '{function_name}' not found"
        }
    
    try:
        # Handle both sync and async functions
        if asyncio.iscoroutinefunction(function):
            result = await function(**arguments)
        else:
            result = function(**arguments)
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Function execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "error",
            "message": f"Error executing function: {str(e)}",
            "exception_type": type(e).__name__
        }


__all__ = [
    # Data management
    "load_data",
    "save_data",
    "get_data_file_path",
    
    # User info
    "collect_user_info",
    "validate_email",
    "validate_user_data",
    "format_user_data_for_display",
    
    # Availability
    "check_availability",
    "get_all_available_slots",
    "get_next_available_slots",
    "is_slot_available",
    "get_appointment_by_id",
    "format_slots_for_display",
    
    # Booking
    "reserve_slot_temporarily",
    "book_appointment",
    "get_pending_confirmation",
    "get_booking_by_id",
    "cancel_booking",
    "cleanup_expired_confirmations",
    
    # Email (async only)
    "send_confirmation_email",
    "send_booking_confirmation_email",
    
    # Schemas
    "TOOLS_SCHEMA",
    "get_tools_schema",
    "get_function_schema",
    "get_all_function_names",
    
    # Function execution
    "AVAILABLE_FUNCTIONS",
    "get_function_by_name",
    "execute_function_call",
]
