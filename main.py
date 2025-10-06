import requests
import os
from pathlib import Path
from dotenv import load_dotenv


X_RANGE = [1020, 1021, 1022, 1023, 1024, 1025, 1026]
Y_RANGE = [679, 680, 681, 682, 683]


if __name__ == '__main__':
    load_dotenv()

    tile_x = 1020
    tile_y = 679
    filter_end = "2019-01-01"

    url = f"https://personal-heatmaps-external.strava.com/tiles/27736053/hot/11/{tile_x}/{tile_y}.png"

    params = {
        "filter_type": "all",
        "include_everyone": "true",
        "include_followers_only": "true",
        "include_only_me": "true",
        "respect_privacy_zones": "false",
        "filter_start": "2018-08-01",
        "filter_end": filter_end
    }

    headers = {
        "accept": "image/webp,*/*",
        "accept-language": "en-US,en;q=0.9",
        "referer": "https://www.strava.com/"
    }

    cookies = {
        "_strava4_session": os.environ.get("STRAVA_SESSION_COOKIE", ""),
    }

    response = requests.get(url, params=params, headers=headers, cookies=cookies)

    if response.status_code == 200:
        # Create directory structure: tiles/filter_end/
        output_dir = Path("tiles") / filter_end
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save with filename: tile_x_tile_y.png
        output_path = output_dir / f"{tile_x}_{tile_y}.png"
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"Heatmap tile saved to {output_path}")
    elif response.status_code == 404:
        print(f"No data for tile ({tile_x}, {tile_y}) found")
    else:
        print(f"Failed to download: {response.status_code}")
        print(response.text)
