import json


def load_json(filename="update.json"):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        data = {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in '{filename}': {e}")
        data = {}
    except Exception as e:
        print(f"Error loading JSON file '{filename}': {e}")
        data = {}
    return data

def save_json(new_data, filename="update.json"):
    try:
        existing_data = load_json(filename)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        existing_data = {}

    updated_data = {**existing_data, **new_data}

    with open(filename, "w") as file:
        json.dump(updated_data, file)
