import json

def read_json(file_path):
    with open(file_path) as f:
        read_data = json.load(f)
    return read_data

def write_json(write_data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(obj= write_data, fp= json_file, indent= 4)