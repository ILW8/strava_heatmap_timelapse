import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from PIL import Image
from datetime import datetime


# at zoom level 15, longitude 0 is tile 16384. Tile 0 starts at -180 degrees, the globe is split into 32,768 splits
X_RANGE = [1020, 1021, 1022, 1023, 1024, 1025, 1026]
Y_RANGE = [679, 680, 681, 682, 683]


def generate_filter_end_dates(start_year, start_month):
    """Generate list of first-of-month dates from start date to current date."""
    current_date = datetime.now()
    current_year, current_month = current_date.year, current_date.month

    filter_end_dates = []
    year, month = start_year, start_month

    while (year < current_year) or (year == current_year and month <= current_month):
        filter_end_dates.append(f"{year}-{month:02d}-01")
        month += 1
        if month > 12:
            month = 1
            year += 1

    # If current date is not the first of the month, add it
    if current_date.day != 1:
        filter_end_dates.append(current_date.strftime("%Y-%m-%d"))

    return filter_end_dates


def download_tile(url, params, headers, cookies, output_path, pbar):
    """Download a single tile and save it to disk."""
    response = requests.get(url, params=params, headers=headers, cookies=cookies)

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
    elif response.status_code == 404:
        # Create a transparent 512x512 PNG for tiles with no data
        transparent_tile = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
        transparent_tile.save(output_path)
    else:
        pbar.write(f"Failed to download tile: {response.status_code}")


def download_tiles_for_date(filter_end, x_range, y_range, headers, cookies):
    """Download all tiles for a given filter_end date."""
    output_dir = Path("tiles") / filter_end
    output_dir.mkdir(parents=True, exist_ok=True)

    total_tiles = len(x_range) * len(y_range)

    with tqdm(total=total_tiles, desc=f"Downloading tiles for {filter_end}", leave=False) as pbar:
        for tile_x in x_range:
            for tile_y in y_range:
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

                download_tile(url, params, headers, cookies, output_path, pbar)
                pbar.update(1)

    return output_dir


def stitch_tiles(output_dir, x_range, y_range):
    """Stitch individual tiles into a single image."""
    # Get tile dimensions from first available tile
    sample_tile = None
    for tile_x in x_range:
        for tile_y in y_range:
            tile_path = output_dir / f"{tile_x}_{tile_y}.png"
            if tile_path.exists():
                sample_tile = Image.open(tile_path)
                break
        if sample_tile:
            break

    if sample_tile is None:
        tqdm.write(f"No tiles found to stitch for {output_dir.name}!")
        return

    tile_width, tile_height = sample_tile.size

    # Create output image with transparency
    full_width = len(x_range) * tile_width
    full_height = len(y_range) * tile_height
    stitched_image = Image.new('RGBA', (full_width, full_height), (0, 0, 0, 0))

    # Place each tile in the correct position
    for i, tile_x in enumerate(x_range):
        for j, tile_y in enumerate(y_range):
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


def main():
    """Main function to download and stitch tiles for all dates."""
    load_dotenv()

    filter_end_dates = generate_filter_end_dates(2018, 10)

    cookies = {
        "_strava4_session": os.environ.get("STRAVA_SESSION_COOKIE", ""),
    }

    headers = {
        "accept": "image/webp,*/*",
        "accept-language": "en-US,en;q=0.9",
        "referer": "https://www.strava.com/"
    }

    # Process each filter_end date
    for filter_end in tqdm(filter_end_dates, desc="Processing dates"):
        output_dir = download_tiles_for_date(filter_end, X_RANGE, Y_RANGE, headers, cookies)
        stitch_tiles(output_dir, X_RANGE, Y_RANGE)

    print(f"\nAll downloads and stitching complete!")


if __name__ == '__main__':
    main()
