""" Loading and saving the data to a json file."""

import json
from typing import Dict
from pathlib import Path

# Path to data file
DATA_FILE = Path(__file__).parent.parent / "data" / "data.json"


def load_data() -> Dict:
    
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
        
    except FileNotFoundError:

        initial_data = {
            "appointments": [],
            "bookings": [],
            "pending_confirmations": []
        }
        
        save_data(initial_data)
        
        return initial_data
    
    except json.JSONDecodeError as e:
        
        raise ValueError(f"Invalid JSON in data file: {str(e)}")


def save_data(data: Dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_data_file_path() -> Path:

    return DATA_FILE
