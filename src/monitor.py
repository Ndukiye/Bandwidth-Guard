import psutil
import time
from datetime import date, timedelta
from src.storage import update_storage,get_bandwith_data,get_presets


def check_cap(total_mb):
    presets = get_presets()
    if not presets:
        return False
    
    cap = presets[0]["usage_limits"]
    if total_mb >= cap: return True
    return False

def save_bandwith_data(total_mb,cap_reached,speed):
    current_date =  str(date.today())
    old_data = get_bandwith_data()
    if old_data != []:
        last_entry = old_data[-1]    
        if  last_entry["date"] == current_date:
            last_entry["total_mb"] = float(f'{total_mb:.2f}')
            last_entry["usage_limit"] = cap_reached
            last_entry["speed_mbps"] = float(f'{speed:.2f}')
            update_storage(old_data)
        else:
            new_data = {"date":current_date,"total_mb": float(f'{total_mb:.2f}'),"usage_limit":cap_reached,"speed_mbps":float(f'{speed:.2f}')}
            old_data.append(new_data)
            update_storage(old_data)
    else:
        new_data = {"date":current_date,"total_mb": float(f'{total_mb:.2f}'),"usage_limit":cap_reached,"speed_mbps":float(f'{speed:.2f}')}
        old_data.append(new_data)
        update_storage(old_data)


total_bytes = 0
total_mb = 0
while True: 
        old = psutil.net_io_counters().bytes_recv
        time.sleep(1)
        new = psutil.net_io_counters().bytes_recv
        speed_mbps = (new-old)/1048576
        total_bytes+=(new-old)
        total_mb = total_bytes/1048576
        save_bandwith_data(total_mb,check_cap(total_mb),speed_mbps)
        # print(f'Used in last second: {total_bytes} bytes | Total today: {total_mb:.2f} MB')
