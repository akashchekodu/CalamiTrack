import requests
import pandas as pd
import io
from datetime import datetime

MAP_KEY = "369aa8b3849fa2f9f3e6210359d9bc4e"
PRODUCT = "VIIRS_NOAA21_NRT" #"VIIRS_NOAA20_NRT"
AREA = "world"
DAY = 1
DATE = datetime.utcnow().strftime("%Y-%m-%d")

# https://firms.modaps.eosdis.nasa.gov/api/area/csv/369aa8b3849fa2f9f3e6210359d9bc4e/VIIRS_NOAA21_NRT/world/1/2025-06-15

url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{PRODUCT}/{AREA}/{DAY}/{DATE}"

try:
    response = requests.get(url)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text))
    print(f"✅ Fetched {len(df)} fire alerts.")
    print(df.head())
except Exception as e:
    print(f"❌ Error fetching data: {e}")
