# multi-tracker.py (UPDATED)

import subprocess
import psutil
from collections import defaultdict
from storage import update_multi_tracker, load_multi_tracker_data
from config_loader import load_enforcement_config
from enforcer import enforce_limit
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load existing data
proc_nd_usage = defaultdict(
    lambda: defaultdict(float),
    {
        process: defaultdict(float, metrics)
        for process, metrics in load_multi_tracker_data().items()
    }
)

# Load enforcement config
config = load_enforcement_config()

def increment_process_data(process_name, usage, proc_nd_usage, type):
    """Update process usage and save to disk"""
    proc_nd_usage[process_name][type] += usage
    
    clean = {
        process: dict(metrics)
        for process, metrics in proc_nd_usage.items()
    }
    update_multi_tracker(clean)

def normalize_bpftrace_line(line):
    """Parse bpftrace output line"""
    pid = int(line.split("]")[0].split("[")[1].split(",")[0])
    comm = line.split("]")[0].split("[")[1].split(",")[1].strip()
    mb_used = int(line.split(":")[1]) / (1024 * 1024)
    
    MAJOR_APPS = {'firefox', 'chrome', 'spotify', 'code', 'slack', 'teams'}
    
    try:
        proc = psutil.Process(pid)
        parent = proc.parent()
        if parent and parent.name() in MAJOR_APPS:
            name = parent.name()  # Bundle into parent
        else:
            name = proc.name()  # Use own name
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        name = comm
    
    return {"megabytes": mb_used, "name": name}

def check_and_enforce(process_name):
    """Check if process exceeded limit and enforce"""
    
    # Skip whitelisted processes
    if process_name in config.get('whitelist', []):
        return
    
    # Get process usage
    usage = proc_nd_usage.get(process_name, {})
    total_mb = usage.get('send', 0) + usage.get('recv', 0)
    
    # Get limit from config
    process_config = config.get('processes', {}).get(process_name)
    
    if process_config:
        limit_mb = process_config.get('limit_mb')
        action = process_config.get('action', 'kill')
        
        # Enforce
        enforce_limit(process_name, total_mb, limit_mb, action)

# Run bpftrace script for tracking
process = subprocess.Popen(
    ['sudo', 'bpftrace', BASE_DIR / 'scripts/network_tracker.bt'],
    stdout=subprocess.PIPE,
    universal_newlines=True
)

print("[Bandwidth Guard] Monitoring started...")

while True:
    line = process.stdout.readline()
    
    if not line:
        break
    
    line = line.strip()
    
    if "send" in line:
        line_data = normalize_bpftrace_line(line)
        increment_process_data(
            line_data["name"],
            float(line_data["megabytes"]),
            proc_nd_usage,
            "send"
        )
        # Check enforcement after updating
        check_and_enforce(line_data["name"])
    
    elif "recv" in line:
        line_data = normalize_bpftrace_line(line)
        increment_process_data(
            line_data["name"],
            float(line_data["megabytes"]),
            proc_nd_usage,
            "recv"
        )
        # Check enforcement after updating
        check_and_enforce(line_data["name"])