import requests
import pandas as pd
import datetime
import dotenv
import os

DAILY_DATA_FILENAME = "daily_data.csv"
CORE_ADDRESS = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

def get_cloud_cover(month, day, year, hour):
    params = {
        "key": os.environ.get("API_KEY"),
        "contentType": os.environ.get("OUTPUT_TYPE"),
        "elements": os.environ.get("DATA"),
    }
    zipcode = os.environ.get("ZIPCODE")
    date = f"{year}-{month}-{day}"

    response = requests.get(url=f"{CORE_ADDRESS}/{zipcode}/{date}", params=params)
    data = response.json()["days"]
    for entry in data:
        dtobj = datetime.fromtimestamp(entry["datetimeEpoch"])
        if dtobj.hour == hour:
            return entry



if __name__ == "__main__":
    dotenv.load_dotenv()

    params = {
        "key": os.environ.get("API_KEY"),
        "contentType": os.environ.get("OUTPUT_TYPE"),
        "elements": os.environ.get("DATA"),
    }

    solarDailyDF = pd.read_csv(DAILY_DATA_FILENAME)

    zipcode = os.environ.get("ZIPCODE")
    date = os.environ.get("DATE")
    response = requests.get(url = f"{CORE_ADDRESS}/{zipcode}/{date}", params=params)
    relevantData = response.json()["days"][0]["hours"]
    visualCrossingDF = pd.DataFrame(relevantData)

    #The general workflow for working with time data is to keep time in the datatime obj format, converting to and from the various types as needed.
    #This includes Unix type and string formats.
    visualCrossingDF["datetimeEpoch"] = visualCrossingDF["datetimeEpoch"].apply(lambda entry: datetime.fromtimestamp(entry))
    visualCrossingDF.rename(columns={"datetimeEpoch": "Date Time"}, inplace=True)

    solarDailyDF["Date Time"] = pd.to_datetime(solarDailyDF["Date"] + "T" + solarDailyDF["Time"], format="%Y-%m-%dT%H:%M")

    daysToRetrieve = solarDailyDF["Date Time"].dt.strftime("%Y-%m-%d").unique()
    relevantData = []
    for day in daysToRetrieve:
        response = requests.get(url=f"{CORE_ADDRESS}/{zipcode}/{day}", params=params)
        relevantData += response.json()["days"][0]["hours"]

    visualCrossingDF = pd.DataFrame(relevantData)
    visualCrossingDF["datetimeEpoch"] = visualCrossingDF["datetimeEpoch"].apply(
        lambda entry: datetime.fromtimestamp(entry))
    visualCrossingDF.rename(columns={"datetimeEpoch": "Date Time"}, inplace=True)






