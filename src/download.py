"""Download the hourly GH Archive files for one day.

Usage:
    python3 src/download.py <YYYY-MM-DD> <raw_dir>
"""
import sys
import time
import urllib.error
import urllib.request
import shutil
from pathlib import Path

BASE_URL = "https://data.gharchive.org"
MAX_RETRIES = 3


def download_hour(day: str, hour: int, raw_dir: Path) -> Path:
    """Download one hourly file, skipping it if it already exists.

    Args:
        day (str): The date in YYYY-MM-DD format.
        hour (int): The hour of the day (0-23).
        raw_dir (Path): The directory to save the downloaded file.

    Returns:
        Path: The path to the downloaded file.

    Raises:
        RuntimeError: If the download fails after MAX_RETRIES attempts.
    """
    name = f"{day}-{hour}.json.gz"
    target = raw_dir / name
    if target.exists():
        return target

    raw_dir.mkdir(parents=True, exist_ok=True)
    partial = raw_dir / f"{name}.part"
    url = f"{BASE_URL}/{name}"
    request = urllib.request.Request(
        url,
        headers = {"User-Agent": "gharchive-pipeline/0.1 (learning project)"},
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout = 60) as response, \
                    open(partial, "wb") as out_file:
                shutil.copyfileobj(response, out_file)
            partial.rename(target)
            return target
        except (urllib.error.URLError, TimeoutError) as error:
            print(f"{name}: attempt {attempt} failed ({error})")
            time.sleep(2 * attempt)

    raise RuntimeError(f"Could not download {url}")

def download_day(day: str, raw_dir: Path) -> list[Path]:
    """Download all 24 hourly files of a day.
    
    Args:
        day (str): The date in YYYY-MM-DD format.
        raw_dir (Path): The directory to save the downloaded files.
    
    Returns:
        Paths to the 24 local files, ordered by hour.
    """
    return [download_hour(day, hour, raw_dir) for hour in range(24)]

if __name__ == "__main__":
    day, raw_dir = sys.argv[1], Path(sys.argv[2])
    files = download_day(day, raw_dir)
    print(f"{len(files)} files available in {raw_dir}")
