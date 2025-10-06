import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from PIL import Image


# at zoom level 15, longitude 0 is tile 16384. Tile 0 starts at -180 degrees, the globe is split into 32,768 splits
X_RANGE = [1020, 1021, 1022, 1023, 1024, 1025, 1026]
Y_RANGE = [679, 680, 681, 682, 683]


if __name__ == '__main__':
    load_dotenv()

    filter_end = "2025-01-01"

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
                output_path = output_dir / f"{tile_x}_{tile_y}.png"

                # Skip if tile already exists
                if output_path.exists():
                    pbar.update(1)
                    continue

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
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                elif response.status_code == 404:
                    # Create a transparent 512x512 PNG for tiles with no data
                    transparent_tile = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
                    transparent_tile.save(output_path)
                else:
                    pbar.write(f"Failed to download tile ({tile_x}, {tile_y}): {response.status_code}")

                pbar.update(1)

    print(f"\nDownload complete! Tiles saved to {output_dir}")

    # Stitch tiles together
    print("Stitching tiles together...")

    # Get tile dimensions from first available tile
    sample_tile = None
    for tile_x in X_RANGE:
        for tile_y in Y_RANGE:
            tile_path = output_dir / f"{tile_x}_{tile_y}.png"
            if tile_path.exists():
                sample_tile = Image.open(tile_path)
                break
        if sample_tile:
            break

    if sample_tile is None:
        print("No tiles found to stitch!")
    else:
        tile_width, tile_height = sample_tile.size

        # Create output image with transparency
        full_width = len(X_RANGE) * tile_width
        full_height = len(Y_RANGE) * tile_height
        stitched_image = Image.new('RGBA', (full_width, full_height), (0, 0, 0, 0))

        # Place each tile in the correct position
        for i, tile_x in enumerate(X_RANGE):
            for j, tile_y in enumerate(Y_RANGE):
                tile_path = output_dir / f"{tile_x}_{tile_y}.png"
                if tile_path.exists():
                    tile = Image.open(tile_path)
                    # Convert palette images with transparency to RGBA
                    if tile.mode == 'P' and 'transparency' in tile.info:
                        tile = tile.convert('RGBA')
                    x_pos = i * tile_width
                    y_pos = j * tile_height
                    stitched_image.paste(tile, (x_pos, y_pos), tile if tile.mode == 'RGBA' else None)

        # Save stitched image
        output_image_path = output_dir / "stitched.png"
        stitched_image.save(output_image_path)
        print(f"Stitched image saved to {output_image_path}")
