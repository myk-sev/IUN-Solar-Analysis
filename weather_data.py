import requests
import pandas as pd
import datetime
from urllib.parse import quote

DAILY_DATA_FILENAME = "daily_data.csv"
CORE_ADDRESS = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
ZIPCODE = "46404" #the location for which data will be retrieved
DAY = "2025-06-02" #format: YYY-MM-DD
API_LOCATION = "api-key.txt"

def retrieve_api_key(file_name: str) -> str:
    """Retrieves the contents of the specified file."""
    api_key = ""
    with open(file_name, "r") as file:
        api_key = file.read()

    assert api_key != ""

    return api_key

def custom_encoder(params):
    """
        Visual Crossing does not follow the standard encoding utilized by the request library.
        This function recreates that encoding utilizing the html value for commas, "2%C",
        to group arguments targeting the same parameter.
    """
    cleaned_parts = []
    for key, value in params.items():
        clean_key = quote(str(key), safe='')
        if isinstance(value, (list, tuple)):
            clean_values = ",".join(quote(str(arg), safe='') for arg in value)
        else:
            clean_values = quote(str(value), safe='')
        cleaned_parts.append(f"{clean_key}={clean_key}")

    return "?" + "&".join(cleaned_parts)


if __name__ == "__main__":
    apiKey = retrieve_api_key(API_LOCATION)
    outputType = "json"
    dailyDF = pd.read_csv(DAILY_DATA_FILENAME)
    dailyDF.head()

    params = {
        "key": apiKey,
        "contentType": "json", #csv can also be used
        "elements": ",".join(["datetimeEpoch", "cloudcover", "solarradiation"]),
    }
    columns = ["timestamp", "cloudcover"]

    #url = f"{CORE_ADDRESS}/{ZIPCODE}/{DAY}?key={apiKey}&contentType={outputType}"
    #url = f"{CORE_ADDRESS}/{ZIPCODE}/{DAY}?key={apiKey}&contentType={outputType}"
    response = requests.get(url = f"{CORE_ADDRESS}/{ZIPCODE}/{DAY}", params=params)

