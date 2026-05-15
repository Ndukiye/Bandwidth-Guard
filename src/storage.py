import json
from datetime import date, timedelta
import os

# ALWAYS use /var/lib/bandwidth-guard for daemon
# Snap will read from here, daemon will write to here
DATA_DIR = "/var/lib/bandwidth-guard"

data_file_path = os.path.join(DATA_DIR, "data.json")
multi_process_tracker_path = os.path.join(DATA_DIR, "multi_tracker_history.json")

# Initialize files if they don't exist
# (This will only run when daemon starts, snap just reads)
# os.makedirs(DATA_DIR, exist_ok=True)

# paths = [data_file_path, multi_process_tracker_path]
# for path in paths:
#     try:
#         with open(path, "r") as file:
#             json.load(file)
#     except (FileNotFoundError, json.JSONDecodeError):
#         with open(path, "w") as file:
#             if path == multi_process_tracker_path:
#                 json.dump({}, file)
#             else:
#                 json.dump([], file)

# === System-wide tracking ===
def update_storage(new_data):
    with open(data_file_path, "w") as file:
        json.dump(new_data, file, indent=4)

def get_bandwith_data():
    try:
        with open(data_file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# === Per-process history ===
def get_today_str():
    return str(date.today())

def load_history():
    try:
        with open(multi_process_tracker_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_history(history):
    with open(multi_process_tracker_path, "w") as file:
        json.dump(history, file, indent=4)

def get_today_usage():
    history = load_history()
    today = get_today_str()
    return history.get(today, {})

def update_today_usage(process_name, send_mb, recv_mb):
    history = load_history()
    today = get_today_str()
    
    if today not in history:
        history[today] = {}
    
    if process_name not in history[today]:
        history[today][process_name] = {"send": 0, "recv": 0, "total": 0}
    
    history[today][process_name]["send"] = send_mb
    history[today][process_name]["recv"] = recv_mb
    history[today][process_name]["total"] = send_mb + recv_mb
    
    save_history(history)

def get_date_range_usage(start_date, end_date):
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
    history = load_history()
    cutoff_date = date.today() - timedelta(days=days_to_keep)
    
    cleaned = {
        date_str: data
        for date_str, data in history.items()
        if date_str >= str(cutoff_date)
    }
    
    save_history(cleaned)