import json
import csv
import os


def parse_response(response_text, filename):
    data = {"Reference": filename}

    # Check if the response is in JSON format
    try:
        response_json = json.loads(response_text.strip('<json>').strip('</json>'))
        data.update(response_json)
    except (ValueError, AttributeError):
        # If the response is not in JSON format, parse it as a regular string
        for line in response_text.strip().split('\n'):
            line = line.strip()
            if line:
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip()] = value.strip().strip('"')
                else:
                    # Handle lines without a colon
                    data[line] = None

    # Convert any numerical values to appropriate types
    for key, value in data.items():
        if value is not None:
            try:
                data[key] = float(value)
            except ValueError:
                try:
                    data[key] = int(value)
                except ValueError:
                    data[key] = value
    return data


def write_data_to_csv(data, csv_file_path, fieldnames):
    # Ensure the directory exists before writing to the file
    os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)

    with open(csv_file_path, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header if the file is empty
        if os.path.getsize(csv_file_path) == 0:
            writer.writeheader()

        writer.writerow({key: data.get(key, "") for key in fieldnames})
    # print(f"Data written to CSV: {data}")  # Log confirmation of data written to Streamlit interface


def create_csv(file_path):
    # Function to create a new empty CSV file
    with open(file_path, "w") as f:
        pass


def update_csv(file_path):
    # Function to update an existing CSV file
    # if os.path.exists(file_path):
    #     df = pd.read_csv(file_path)
    #     edited_df = st.experimental_data_editor(df)
    #     edited_df.to_csv(file_path, index=False)
    #     print(f"File {file_path} updated successfully.")    
        
    pass


def delete_csv(file_path):
    # Function to delete a CSV file
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File {file_path} deleted successfully.")
    else:
        print("File not found.")
