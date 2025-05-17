import time
import requests

# ─── CONFIG ────────────────────────────────────────────────────────────────
# Classification (validation) API key
CLASSIFY_KEY = "bf3154da-cf31-4d61-bdee-ad3e1a74a5d4"  
# Background-replace (Darkroom) Secret Key
REPLACE_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnRlcnByaXNlSWQiOiI0MDg4NmRhY2MiLCJ0ZWFtSWQiOiI2YzEwY2E5Mjc4IiwidXNlcklkIjoiMjQzZGIwYjUiLCJzZWNyZXRLZXkiOiJlNTY3YjViY2RlYTY0YTliYjU0ZTBhZDQ0MDQyYTY4OSIsImlhdCI6MTc0NzQ5MzcwMCwiZXhwIjoxODQyMTAxNzAwfQ.9njFzhNrwTRXl0bXqW1BbZDWVteks84r4qcQqdcnWwk"  
IMAGE_URL    = "https://raw.githubusercontent.com/HassanRaz-A/images/main/CAR1.jpg"
BACKGROUND   = "923"  # Legacy background ID to apply

# ─── 1) CLASSIFY for tyre_mud_detection ────────────────────────────────────
cls_resp = requests.post(
    "https://api.spyne.ai/auto/classify/v1/image",
    data={
        "image_url":              IMAGE_URL,
        "tyre_mud_detection":     "true",
        # you can enable other flags here if desired…
    },
    headers={
        "Accept":        "application/json",
        "Authorization": f"Bearer {CLASSIFY_KEY}"
    }
)
cls_resp.raise_for_status()
cls_json = cls_resp.json()

# Extract tyre mud status
mud = cls_json.get("data", {}) \
             .get("validation_result", {}) \
             .get("tyre_mud_detection", {}) \
             .get("value")

print(f"Tyre mud detection: {mud or 'not available'}")

# ─── 2) SUBMIT background-replace job ───────────────────────────────────────
submit = requests.post(
    "https://api.spyne.ai/api/pv1/image/replace-bg",
    json={
        "auth_key":        REPLACE_KEY,
        "sku_name":        "main_pipeline_job",
        "category_id":     "Automobile",
        "image_data":      [{"category":"Exterior","image_urls":[IMAGE_URL]}],
        "background_type": "legacy",
        "background":      BACKGROUND,
        "number_plate_logo": ""
    }
)
submit.raise_for_status()
sku_id = submit.json()["data"]["sku_id"]
print("Background-replace job accepted, SKU:", sku_id)

# ─── 3) POLL for completion ────────────────────────────────────────────────
poll_url = "https://api.spyne.ai/api/pv1/sku/get-ready-images/v2/"
headers  = {"Authorization": f"Bearer {REPLACE_KEY}"}
params   = {"sku_id": sku_id}

while True:
    poll = requests.get(poll_url, headers=headers, params=params)
    poll.raise_for_status()
    record = poll.json()["image_data"][0]
    status = record["status"]
    print("Status:", status)

    # Optional: show low-res preview as soon as available
    if status != "Yet to Start" and record.get("lowres_output"):
        print("Low-res preview:", record["lowres_output"])

    if status == "Done":
        output_url = record["output_image"]
        print("→ Fully processed at:", output_url)
        break
    if status == "Failed":
        raise RuntimeError("Processing failed: " + (record.get("reject_reason") or "no reason"))
    time.sleep(5)

# ─── 4) DOWNLOAD the final image ───────────────────────────────────────────
local_file = "final_car.jpg"
with requests.get(output_url, stream=True) as dl:
    dl.raise_for_status()
    with open(local_file, "wb") as f:
        for chunk in dl.iter_content(8192):
            f.write(chunk)

print("✅ Download complete:", local_file)
