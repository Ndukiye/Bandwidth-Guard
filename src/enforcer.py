# enforcer.py (UPDATED)

from storage import load_multi_tracker_data
import psutil
import os
import signal
import subprocess

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

def should_notify(process_name, level):
    """
    Check if we should send notification
    Only notify once per level to avoid spam
    
    Args:
        process_name: Name of process
        level: "warn_80" | "kill_100"
    
    Returns:
        bool: True if should notify
    """
    global notified_state
    
    last_level = notified_state.get(process_name)
    
    if last_level != level:
        notified_state[process_name] = level
        return True
    
    return False

def reset_notification_state(process_name):
    """Reset notification state (call when usage drops below threshold)"""
    if process_name in notified_state:
        del notified_state[process_name]

def enforce_limit(process_name, usage_mb, limit_mb, action="kill"):
    """
    Enforce bandwidth limit on process
    
    Args:
        process_name: Name of process
        usage_mb: Current total usage in MB
        limit_mb: Configured limit in MB
        action: "warn" | "kill"
    """
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