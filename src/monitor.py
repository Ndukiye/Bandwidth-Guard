# monitor.py (TOP OF FILE)
import socket
from datetime import date
from storage import update_storage, get_bandwith_data
import psutil
from collections import defaultdict
from storage import get_today_usage, update_today_usage
from config_loader import load_enforcement_config
from enforcer import enforce_limit, check_cap
from pathlib import Path
import asyncio
import sys
import os

# CRITICAL FIX: Add src directory to Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Point to scripts directory
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # /opt/bandwidth-guard

# Rest of your code...

def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


def save_bandwith_data(total_mb,cap_reached,speed):
    current_date =  str(date.today())
    old_data = get_bandwith_data()
    if old_data != []:
        last_entry = old_data[-1]    
        if  last_entry["date"] == current_date:
            last_entry["total_mb"] = float(f'{total_mb}')
            last_entry["usage_limit"] = cap_reached
            last_entry["speed_mbps"] = float(f'{speed}')
            update_storage(old_data)
        else:
            new_data = {"date":current_date,"total_mb": float(f'{total_mb}'),"usage_limit":cap_reached,"speed_mbps":float(f'{speed}')}
            old_data.append(new_data)
            update_storage(old_data)
    else:
        new_data = {"date":current_date,"total_mb": float(f'{total_mb}'),"usage_limit":cap_reached,"speed_mbps":float(f'{speed}')}
        old_data.append(new_data)
        update_storage(old_data)


#===== multi-process monitoring =======

# Load existing data
proc_nd_usage = defaultdict(
    lambda: defaultdict(float),
    {
        process: defaultdict(float, metrics)
        for process, metrics in get_today_usage().items()
    }
)

# Load enforcement config
config = load_enforcement_config()

def increment_process_data(process_name, usage, type):
    #Update process usage and save to disk
    proc_nd_usage[process_name][type] += usage
    # Save to history
    send_mb = proc_nd_usage[process_name]['send']
    recv_mb = proc_nd_usage[process_name]['recv']
    update_today_usage(process_name, send_mb, recv_mb)

def normalize_bpftrace_line(line):
    #Parse bpftrace output line
    pid = int(line.split("]")[0].split("[")[1].split(",")[0])
    comm = line.split("]")[0].split("[")[1].split(",")[1].strip()
    mb_used = int(line.split(":")[1]) / (1024 * 1024)

    try: 
        proc = psutil.Process(pid)
        owner = get_process_owner(pid)
        if owner:
            name = owner # Bundle into parent
        else:
            name = proc.name()  # Use own name
    except (psutil.NoSuchProcess, psutil.AccessDenied):
            name = comm
    return {"megabytes": mb_used, "name": name}

def get_process_owner(pid):
    MAJOR_APPS = {'firefox', 'chrome', 'spotify', 'code'}

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] not in MAJOR_APPS:
                continue
            children = proc.children(recursive=True)
            child_pids = {child.pid for child in children}

            if pid in child_pids or pid == proc.pid:
                return proc.info['name']
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return None

def check_and_enforce(process_name):
    #Check if process exceeded limit and enforce
    
    # Skip whitelisted processes
    if process_name in config.get('whitelist', []):
        return
    
    # Get process usage
    usage = proc_nd_usage.get(process_name, {})
    total_mb = usage.get('send', 0) + usage.get('recv', 0)
    
    # Get limit from config
    process_config = config.get('processes', {}).get(process_name)
    
    if process_config:
        # print(f"checking {process_name}")
        limit_mb = process_config.get('limit_mb')
        action = process_config.get('action', 'kill')
        
        # Enforce
        enforce_limit(process_name, total_mb, limit_mb, action)


async def main_multi_process_tracker():
    # Run bpftrace script for tracking
    bt_script = os.path.join(BASE_DIR, 'scripts', 'network_tracker.bt')
    process = await asyncio.create_subprocess_exec(
        'bpftrace',
        bt_script,
        stdout=asyncio.subprocess.PIPE,
    )

    print("[Bandwidth Guard] Monitoring started...")

    while True:
        line = await process.stdout.readline()
    
        if not line:
            break  

        line = line.decode().strip()  

        if "send" in line:
            line_data = normalize_bpftrace_line(line)
            increment_process_data(
                line_data["name"],
                float(line_data["megabytes"]),
                "send"
            )
            check_and_enforce(line_data["name"])   
        elif "recv" in line:
            line_data = normalize_bpftrace_line(line)
            increment_process_data(
                line_data["name"],
                float(line_data["megabytes"]),
            "   recv"
            )
            # Check enforcement after updating
            check_and_enforce(line_data["name"])


async def main_system_usage_tracker():
    total_bytes = 0
    total_mb = 0
    while True: 
        old = psutil.net_io_counters().bytes_recv
        await asyncio.sleep(1)
        new = psutil.net_io_counters().bytes_recv
        speed_mbps = (new-old)/1048576
        total_bytes+=(new-old)
        total_mb = total_bytes/1048576
        save_bandwith_data(total_mb,check_cap(total_mb),speed_mbps)
        # print(f'Used in last second: {total_bytes} bytes | Total today: {total_mb:.2f} MB')

async def main():
    await asyncio.gather(
        main_multi_process_tracker(),
        main_system_usage_tracker()
    )

if __name__ == "__main__":
    asyncio.run(main())
