import psutil
import subprocess
import time 
from storage import get_presets
MAJOR_APPS = {'firefox', 'chrome', 'spotify', 'code', 'teams'}

# Track what we've already notified about
notified_state = {}  # process_name → last notification level

def get_pids_by_name(process_name):
    process_pids = []
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            pid = proc.info['pid']
            process_pids.append(pid)
            
            # For major apps, also get children
            if process_name in MAJOR_APPS:
                try:
                    parent = psutil.Process(pid)
                    for child in parent.children(recursive=True):
                        process_pids.append(child.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    
    return process_pids

def kill_process(process_pids):
    """Terminate processes with error handling"""
    for pid in process_pids:
        try:
            psutil.Process(pid).terminate()
            print(f"[Enforcer] Killed PID {pid}")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"[Enforcer] Failed to kill PID {pid}: {e}")

def notify_user(title, message, urgency="normal"):
    """Send desktop notification"""
    subprocess.run([
        "notify-send",
        "-a", "Bandwidth-Guard",
        "-c", "network",
        "-u", f'{urgency}',
        f'{title}',
        f'{message}'
    ])


notified_state = {}  # process_name → {'level': str, 'timestamp': float}
def should_notify(process_name, level):
    """
    Check if we should send notification/take action
    Resets after 3 minutes to allow re-enforcement
    """
    RESET_INTERVAL = 180  # 3 minutes in seconds
    
    current_time = time.time()
    
    if process_name in notified_state:
        last_action = notified_state[process_name]
        
        # Check if same level and within reset interval
        if last_action['level'] == level:
            time_since_last = current_time - last_action['timestamp']
            
            if time_since_last < RESET_INTERVAL:
                return False  # Too soon, don't notify again
    
    # Either new level or enough time passed - take action
    notified_state[process_name] = {
        'level': level,
        'timestamp': current_time
    }
    return True

def reset_notification_state(process_name):
    """Reset notification state (call when usage drops below threshold)"""
    if process_name in notified_state:
        del notified_state[process_name]

def enforce_limit(process_name, usage_mb, limit_mb, action="kill"):
    # Enforce bandwidth limit on process
    
    if not limit_mb:
        return  # No limit configured
    
    percentage = (usage_mb / limit_mb) * 100
    pids = get_pids_by_name(process_name)
    
    if not pids:
        # Process not running, reset notification state
        reset_notification_state(process_name)
        return
    
    # 100% threshold - KILL
    if percentage >= 100:
        if action == "kill":
            if should_notify(process_name, "kill_100"):
                kill_process(pids)
                notify_user(
                    f'🔴 Killed {process_name}',
                    f'{process_name} exceeded limit ({usage_mb:.0f}MB / {limit_mb}MB)',
                    urgency="critical"
                )
        elif action == "warn":
            if should_notify(process_name, "warn_100"):
                notify_user(
                    f'⚠️ {process_name} Limit Exceeded',
                    f'{process_name} has used {usage_mb:.0f}MB of {limit_mb}MB limit',
                    urgency="critical"
                )
    
    # 80% threshold - WARN
    elif percentage >= 80:
        if should_notify(process_name, "warn_80"):
            notify_user(
                f'📊 {process_name} Warning',
                f'{process_name} at {percentage:.0f}% of limit ({usage_mb:.0f}MB / {limit_mb}MB)',
                urgency="normal"
            )   
    # Below 80% - reset notification state
    else:
        reset_notification_state(process_name)

#enforce global limit
def check_cap(total_mb):
    presets = get_presets()
    if not presets:
        return False
    cap = float(presets[0]["usage_limits"])
    percentage = (total_mb / cap) * 100
    if percentage >= 90:
        if should_notify("Global_system_99", "warn_90"):
            notify_user(
                '⚠️ System Network Usage Warning',
                f'System Network Usage at {percentage:.0f}% of limit ({total_mb:.0f}MB / {cap}MB)',
                urgency="critical"
            )   
    if total_mb >= cap: return True
    return False

