import subprocess
import psutil
from collections import defaultdict
from collections import defaultdict

proc_nd_usage = defaultdict(lambda: defaultdict(float))

def save_process_data(process_name, usage, proc_nd_usage, type):
    proc_nd_usage[process_name][type] += usage
    # clean = {
    # process: dict(metrics)
    # for process, metrics in proc_nd_usage.items()
    # }   
    # print(clean)

def normalize_bpftrace_line(line):
    pid = int(line.split("]")[0].split("[")[1].split(",")[0])
    comm = line.split("]")[0].split("[")[1].split(",")[1]
    mb_used = int(line.split(":")[1])/(1024*1024)
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
    
    return {"megabytes":mb_used,"name":name}

#run bpftrace script for tracking process and network
process = subprocess.Popen(
     ['sudo','bpftrace','scripts/network_tracker.bt'],
     stdout=subprocess.PIPE,
     universal_newlines=True    
)
while True:
    line = process.stdout.readline()
    if not line:
        break
    elif "send" in line:
        line_data = normalize_bpftrace_line(line)
        save_process_data(line_data["name"],float(line_data["megabytes"]),proc_nd_usage,"send")
    elif "recv" in line:
        line_data = normalize_bpftrace_line(line)
        save_process_data(line_data["name"],float(line_data["megabytes"]),proc_nd_usage,"recv")

