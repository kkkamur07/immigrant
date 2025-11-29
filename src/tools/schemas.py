from typing import Dict, List

# OpenAI Function Calling Schemas
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "collect_user_info",
            "description": "Collect user information (name, email, reason) for the appointment booking. Call this function as the user provides each piece of information during the conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "User's full name (first and last name)"
                    },
                    "email": {
                        "type": "string",
                        "description": "User's valid email address for confirmation"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Detailed reason for the emergency appointment request (e.g., 'visa expires next week', 'work permit renewal urgent')"
                    }
                },
                "required": [] 
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check available appointment slots for specific dates. Use this when the user mentions their preferred dates or asks about availability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dates": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                        },
                        "description": "List of dates in YYYY-MM-DD format. Example: ['2025-12-05', '2025-12-06']",
                        "minItems": 1
                    }
                },
                "required": ["dates"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reserve_slot_temporarily",
            "description": "Temporarily reserve a specific appointment slot after the user selects their preferred time. This generates a confirmation token and triggers an email to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "string",
                        "description": "The unique ID of the appointment slot to reserve (e.g., 'apt_001')",
                        "pattern": "^apt_\\d+$"
                    },
                    "user_data": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "User's full name"
                            },
                            "email": {
                                "type": "string",
                                "description": "User's email address"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for emergency appointment"
                            }
                        },
                        "required": ["name", "email", "reason"],
                        "description": "Complete user information collected during the conversation"
                    }
                },
                "required": ["appointment_id", "user_data"]
            }
        }
    }
]


def get_tools_schema() -> List[Dict]:
    
    return TOOLS_SCHEMA


def get_function_schema(function_name: str) -> Dict:
    
    for tool in TOOLS_SCHEMA:
        if tool["function"]["name"] == function_name:
            return tool
    return None


def get_all_function_names() -> List[str]:
    
    return [tool["function"]["name"] for tool in TOOLS_SCHEMA]
