import time, requests

# ─── CONFIG ────────────────────────────────────────────────────────────────
SECRET_KEY ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnRlcnByaXNlSWQiOiI0MDg4NmRhY2MiLCJ0ZWFtSWQiOiI2YzEwY2E5Mjc4IiwidXNlcklkIjoiMjQzZGIwYjUiLCJzZWNyZXRLZXkiOiJlNTY3YjViY2RlYTY0YTliYjU0ZTBhZDQ0MDQyYTY4OSIsImlhdCI6MTc0NzQ5MzcwMCwiZXhwIjoxODQyMTAxNzAwfQ.9njFzhNrwTRXl0bXqW1BbZDWVteks84r4qcQqdcnWwk"
IMAGE_URL  = "https://raw.githubusercontent.com/HassanRaz-A/images/main/CAR1.jpg"      # your hosted image
BACKGROUND = "923"

# 1) Submit the job
submit_url = "https://api.spyne.ai/api/pv1/image/replace-bg"
submit_payload = {
    "auth_key":    SECRET_KEY,
    "sku_name":    "my_car_bg_test",
    "category_id": "Automobile",
    "image_data": [{
        "category":   "Exterior",
        "image_urls": [IMAGE_URL]
    }],
    "background_type": "legacy",
    "background":      BACKGROUND,
    "number_plate_logo": ""
}
submit_resp = requests.post(submit_url, json=submit_payload)
submit_resp.raise_for_status()

new_sku = submit_resp.json()["data"]["sku_id"]
print("Job accepted — polling SKU:", new_sku)

# 2) Poll for completion
poll_url   = "https://api.spyne.ai/api/pv1/sku/get-ready-images/v2/"
headers    = {"Authorization": f"Bearer {SECRET_KEY}"}
params     = {"sku_id": new_sku}

while True:
    r = requests.get(poll_url, headers=headers, params=params)
    r.raise_for_status()
    record = r.json()["image_data"][0]

    status = record["status"]
    print("Status:", status)

    if status == "Done":
        output_url = record["output_image"]
        print("→ Ready at:", output_url)
        break
    elif status == "Failed":
        raise RuntimeError("Image processing failed: " + (record.get("reject_reason") or "no reason"))
    
    time.sleep(5)  # wait 5 seconds before checking again

# 3) Download the processed image
local_file = "processed_car.jpg"
with requests.get(output_url, stream=True) as dl:
    dl.raise_for_status()
    with open(local_file, "wb") as f:
        for chunk in dl.iter_content(8192):
            f.write(chunk)

print("✅ Downloaded to", local_file)
