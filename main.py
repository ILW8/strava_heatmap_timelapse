import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm


X_RANGE = [1020, 1021, 1022, 1023, 1024, 1025, 1026]
Y_RANGE = [679, 680, 681, 682, 683]


if __name__ == '__main__':
    load_dotenv()

    filter_end = "2019-01-01"

    cookies = {
        "_strava4_session": os.environ.get("STRAVA_SESSION_COOKIE", ""),
    }

    headers = {
        "accept": "image/webp,*/*",
        "accept-language": "en-US,en;q=0.9",
        "referer": "https://www.strava.com/"
    }


    output_dir = Path("tiles") / filter_end
    output_dir.mkdir(parents=True, exist_ok=True)

    total_tiles = len(X_RANGE) * len(Y_RANGE)

    with tqdm(total=total_tiles, desc="Downloading tiles") as pbar:
        for tile_x in X_RANGE:
            for tile_y in Y_RANGE:
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

                response = requests.get(url, params=params, headers=headers, cookies=cookies)

                if response.status_code == 200:
                    # Save with filename: tile_x_tile_y.png
                    output_path = output_dir / f"{tile_x}_{tile_y}.png"
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                elif response.status_code == 404:
                    pass  # silently ignore tiles with no data
                else:
                    pbar.write(f"Failed to download tile ({tile_x}, {tile_y}): {response.status_code}")

                pbar.update(1)

    print(f"\nDownload complete! Tiles saved to {output_dir}")
