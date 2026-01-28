import httpx
import base64
import json
from datetime import datetime
import time

# Path to the CIF file
cif_file_path = "tests/data/1E2A.cif"

# Read and base64 encode the CIF file
with open(cif_file_path, "rb") as f:
    cif_content = base64.b64encode(f.read()).decode("utf-8")

# Build the request payload
payload = {
    "dataPool": [
        {
            "id": "cif_entry_1",
            "type": "cif",
            "name": "1E2A.cif",
            "description": "Hemoglobin structure for analysis",
            "content": cif_content,
            "addedBy": "test_user",
            "addedAt": datetime.now().isoformat(),
            "comments": []
        }
    ],
    "mainObjective": "increase hemoglobin efficiency in cold environment",
    "secondaryObjectives": [],
    "Notes": [],
    "Constraints": []
}

# Send the POST request
url = "http://localhost:8000/api/v1/retrieval/analyze"
headers = {"Content-Type": "application/json"}

timeout = httpx.Timeout(
    connect=10.0,
    read=300.0,         # max 5min to read response
    write=300.0,
    pool=None
)

try:
    start = time.time()
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Error Response:")
            print(response.text)
except Exception as e:
    print(f"Error: {e}")

end = time.time()
print(f"Request completed in {end - start:.2f} seconds")