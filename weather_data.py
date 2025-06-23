import requests
import pandas as pd
import datetime
from urllib.parse import quote
import dotenv
import os

DAILY_DATA_FILENAME = "daily_data.csv"
CORE_ADDRESS = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

if __name__ == "__main__":
    dotenv.load_dotenv()

    params = {
        "key": os.environ.get("API_KEY"),
        "contentType": os.environ.get("OUTPUT_TYPE"),
        "elements": os.environ.get("DATA"),
    }

    dailyDF = pd.read_csv(DAILY_DATA_FILENAME)
    dailyDF.head()

    zipcode = os.environ.get("ZIPCODE")
    date = os.environ.get("DATE")
    response = requests.get(url = f"{CORE_ADDRESS}/{zipcode}/{date}", params=params)

