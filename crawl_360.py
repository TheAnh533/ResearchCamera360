import requests
import os
import time

# API và base URL
API_URL = "https://api.polyhaven.com"
DOWNLOAD_URL = "https://dl.polyhaven.org/file/ph-assets/HDRIs"

# Chọn độ phân giải (1k, 2k, 4k, 8k, 16k)
RESOLUTION = "4k"  # 👈 đổi ở đây
SAVE_DIR = f"hdri_{RESOLUTION}"
os.makedirs(SAVE_DIR, exist_ok=True)


def get_asset_list():
    """Lấy danh sách HDRI từ PolyHaven API"""
    try:
        response = requests.get(f"{API_URL}/assets?t=hdris")
        response.raise_for_status()
        hdris = list(response.json().keys())
        print(f"🔎 Tìm thấy {len(hdris)} HDRIs")
        return hdris
    except Exception as e:
        print(f"⚠️ Lỗi khi gọi API: {e}")
        return []


def get_hdri_link(asset_name, resolution=RESOLUTION):
    """Tạo link HDRI với độ phân giải chỉ định"""
    return {
        "hdr": f"{DOWNLOAD_URL}/hdr/{resolution}/{asset_name}_{resolution}.hdr",
        "exr": f"{DOWNLOAD_URL}/exr/{resolution}/{asset_name}_{resolution}.exr",
        "jpg": f"{DOWNLOAD_URL}/jpg/{resolution}/{asset_name}_{resolution}.jpg",
    }


def download_file(url, save_dir=SAVE_DIR):
    filename = url.split("/")[-1]
    path = os.path.join(save_dir, filename)
    if os.path.exists(path):
        print(f"⏭️ Bỏ qua (đã có): {filename}")
        return

    try:
        r = requests.get(url, stream=True, timeout=60)
        if r.status_code == 200:
            with open(path, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            print(f"✅ Downloaded: {filename}")
        else:
            print(f"❌ Not found: {url}")
    except Exception as e:
        print(f"⚠️ Error {url}: {e}")


def main():
    assets = get_asset_list()
    if not assets:
        return

    # Giới hạn số lượng tải về (ví dụ 1000 cái)
    max_downloads = 10
    assets = assets[:max_downloads]

    for asset in assets:
        print(f"\n📥 Đang xử lý: {asset}")
        links = get_hdri_link(asset)

        # chọn định dạng cần tải
        url = links["hdr"]  # hoặc "exr", "jpg"

        download_file(url)
        time.sleep(1)  # tránh bị rate-limit


if __name__ == "__main__":
    main()
