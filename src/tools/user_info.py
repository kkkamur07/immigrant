from typing import Dict, Optional, Any
from datetime import datetime
import re


def collect_user_info(
    name: Optional[str] = None, 
    email: Optional[str] = None, 
    reason: Optional[str] = None
) -> Dict[str, Any]:

    collected_data = {}
    
    # Collect provided information
    
    if name:
        collected_data["name"] = name.strip()
    if email:
        collected_data["email"] = email.strip().lower()
    if reason:
        collected_data["reason"] = reason.strip()
    
    return {
        "status": "success",
        "message": "Information collected successfully",
        "collected_data": collected_data,
        "timestamp": datetime.now().isoformat()
    }


def validate_email(email: str) -> bool:

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_user_data(user_data: Dict[str, str]) -> Dict[str, Any]:

    required_fields = ["name", "email", "reason"]
    errors = []
    
    # Validations
    for field in required_fields:
        if field not in user_data or not user_data[field]:
            errors.append(f"Missing required field: {field}")
    
    if "email" in user_data and user_data["email"]:
        if not validate_email(user_data["email"]):
            errors.append("Invalid email format")
    
    if "name" in user_data and user_data["name"]:
        name_parts = user_data["name"].strip().split()
        if len(name_parts) < 2:
            errors.append("Please provide both first and last name")
    
    if "reason" in user_data and user_data["reason"]:
        if len(user_data["reason"].strip()) < 10:
            errors.append("Please provide a more detailed reason (at least 10 characters)")
    
    if errors:
        return {
            "valid": False,
            "errors": errors
        }
    
    return {
        "valid": True,
        "message": "All user data is valid"
    }


def format_user_data_for_display(user_data: Dict[str, str]) -> str:

    name = user_data.get("name", "N/A")
    email = user_data.get("email", "N/A")
    reason = user_data.get("reason", "N/A")
    
    return f"""

        Name: {name}
        Email: {email}
        Reason: {reason}
        
    """.strip()
