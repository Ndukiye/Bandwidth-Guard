import json
data_file_path = "storage/data.json"
presets_file_path = "storage/user-presets.json"
multi_process_tracker_path = "storage/multi_tracker.json"
paths = [data_file_path,presets_file_path]

for path in paths:
    try:
        with open(path, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        with open(path, "w") as file:
            data =[]
            json.dump(data,file)

def update_storage(new_data):
    with open(data_file_path,"w") as file:
        json.dump(new_data,file,indent=4)

def get_bandwith_data():
    with open(data_file_path, "r") as file:
       data = json.load(file)
       return data

def save_presets(presets):
    with open(presets_file_path,"w") as file:
        json.dump(presets,file,indent=4)

def get_presets():
    with open(presets_file_path,"r") as file:
        data = json.load(file)
        return data

def update_multi_tracker(new_data):
    with open(multi_process_tracker_path,"w") as file:
        json.dump(new_data,file,indent=4)
