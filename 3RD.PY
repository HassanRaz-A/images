import time, requests

# ─── CONFIG ────────────────────────────────────────────────────────────────
SECRET_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnRlcnByaXNlSWQiOiI0MDg4NmRhY2MiLCJ0ZWFtSWQiOiI2YzEwY2E5Mjc4IiwidXNlcklkIjoiMjQzZGIwYjUiLCJzZWNyZXRLZXkiOiJlNTY3YjViY2RlYTY0YTliYjU0ZTBhZDQ0MDQyYTY4OSIsImlhdCI6MTc0NzQ5MzcwMCwiZXhwIjoxODQyMTAxNzAwfQ.9njFzhNrwTRXl0bXqW1BbZDWVteks84r4qcQqdcnWwk"
IMAGE_URL  = "https://raw.githubusercontent.com/HassanRaz-A/images/main/CAR1.jpg"
BACKGROUND = "900"

# ─── 1) Submit the job ─────────────────────────────────────────────────────
submit = requests.post(
    "https://api.spyne.ai/api/pv1/image/replace-bg",
    json={
        "auth_key":        SECRET_KEY,
        "sku_name":        "my_car_bg_test",
        "category_id":     "Automobile",
        "image_data":      [{"category":"Exterior","image_urls":[IMAGE_URL]}],
        "background_type": "legacy",
        "background":      BACKGROUND,
        "number_plate_logo": ""
    }
)
submit.raise_for_status()
sku = submit.json()["data"]["sku_id"]
print("Job accepted, SKU:", sku)

# ─── 2) Poll for completion ─────────────────────────────────────────────────
poll_url = "https://api.spyne.ai/api/pv1/sku/get-ready-images/v2/"
headers  = {"Authorization": f"Bearer {SECRET_KEY}"}
params   = {"sku_id": sku}

max_retries = 20
delay = 10  # seconds between polls

for attempt in range(1, max_retries+1):
    r = requests.get(poll_url, headers=headers, params=params)
    r.raise_for_status()
    rec = r.json()["image_data"][0]
    status = rec["status"]
    lowres = rec.get("lowres_output")
    print(f"[{attempt}/{max_retries}] Status: {status}")

    if lowres and attempt == 1:
        print("→ Low-res preview available at:", lowres)

    if status == "Done":
        output_url = rec["output_image"]
        print("→ Fully processed at:", output_url)
        break
    if status == "Failed":
        raise RuntimeError("Processing failed: " + (rec.get("reject_reason") or "no reason"))

    time.sleep(delay)
else:
    raise TimeoutError(f"Still not started after {max_retries*delay} seconds")

# ─── 3) Download the processed image ────────────────────────────────────────
local_file = "processed_car.jpg"
with requests.get(output_url, stream=True) as dl:
    dl.raise_for_status()
    with open(local_file, "wb") as f:
        for chunk in dl.iter_content(8192):
            f.write(chunk)

print("✅ Downloaded to", local_file)
