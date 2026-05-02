import json
from pathlib import Path
from datetime import date, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
data_file_path = BASE_DIR / "storage/data.json"
presets_file_path = BASE_DIR / "storage/user-presets.json"
multi_process_tracker_path = BASE_DIR / "storage/multi_tracker_history.json"  # Renamed

# Initialize files
paths = [data_file_path, presets_file_path, multi_process_tracker_path]
for path in paths:
    try:
        with open(path, "r") as file:
            json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(path, "w") as file:
            json.dump({}, file)  # Empty dict for history

# === System-wide tracking (original monitor.py) ===

def update_storage(new_data):
    with open(data_file_path, "w") as file:
        json.dump(new_data, file, indent=4)

def get_bandwith_data():
    with open(data_file_path, "r") as file:
        return json.load(file)

# === Per-process history tracking ===

def get_today_str():
    """Get today's date as string"""
    return str(date.today())

def load_history():
    """Load entire history"""
    try:
        with open(multi_process_tracker_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_history(history):
    """Save entire history"""
    with open(multi_process_tracker_path, "w") as file:
        json.dump(history, file, indent=4)

def get_today_usage():
    """Get today's per-process usage"""
    history = load_history()
    today = get_today_str()
    return history.get(today, {})

def update_today_usage(process_name, send_mb, recv_mb):
    """Update usage for a specific process today"""
    history = load_history()
    today = get_today_str()
    
    # Initialize today if doesn't exist
    if today not in history:
        history[today] = {}
    
    # Initialize process if doesn't exist
    if process_name not in history[today]:
        history[today][process_name] = {"send": 0, "recv": 0, "total": 0}
    
    # Update values
    history[today][process_name]["send"] = send_mb
    history[today][process_name]["recv"] = recv_mb
    history[today][process_name]["total"] = send_mb + recv_mb
    
    save_history(history)

def get_date_range_usage(start_date, end_date):
    """
    Get usage across date range
    
    Args:
        start_date: datetime.date object
        end_date: datetime.date object
    
    Returns:
        dict: Aggregated usage per process
    """
    history = load_history()
    aggregated = {}
    
    current = start_date
    while current <= end_date:
        date_str = str(current)
        day_data = history.get(date_str, {})
        
        for process_name, usage in day_data.items():
            if process_name not in aggregated:
                aggregated[process_name] = {"send": 0, "recv": 0, "total": 0}
            
            aggregated[process_name]["send"] += usage["send"]
            aggregated[process_name]["recv"] += usage["recv"]
            aggregated[process_name]["total"] += usage["total"]
        
        current += timedelta(days=1)
    
    return aggregated

def cleanup_old_history(days_to_keep=30):
    """Remove history older than X days"""
    history = load_history()
    cutoff_date = date.today() - timedelta(days=days_to_keep)
    
    # Filter out old dates
    cleaned = {
        date_str: data
        for date_str, data in history.items()
        if date_str >= str(cutoff_date)
    }
    
    save_history(cleaned)