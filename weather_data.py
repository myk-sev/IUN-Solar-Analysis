import requests
import pandas as pd
import datetime
import dotenv
import os
import time

DAILY_DATA_FILENAME = "daily_data.csv"
CORE_ADDRESS = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

def to_nearest_interval(dtobj):
    """
    Modifies datetime object to align with nearest two hour interval.

    Parameters:
        dtobj (datetime): The original datetime object.

    Returns:
        datetime: A new datetime object with the modified time.
    """
    if dtobj.hour % 2 == 0: #round down if even
        return dtobj.replace(minute=0)

    else: #round up if odd
        return dtobj.replace(hour=dtobj.hour+1, minute=0)


if __name__ == "__main__":
    dotenv.load_dotenv()

    params = {
        "key": os.environ.get("API_KEY"),
        "contentType": os.environ.get("OUTPUT_TYPE"),
        "elements": os.environ.get("DATA"),
    }
    zipcode = os.environ.get("ZIPCODE")

    solarDailyDF = pd.read_csv(DAILY_DATA_FILENAME)

    #The general workflow for working with time data is to keep time in the datatime obj format, converting to and from the various types as needed.
    #This includes Unix type and string formats.
    solarDailyDF["Date Time"] = pd.to_datetime(solarDailyDF["Date"] + "T" + solarDailyDF["Time"], format="%Y-%m-%dT%H:%M") #convert text enteries to datetime obj

    solarDailyDF["Date Time"] = solarDailyDF["Date Time"].apply(lambda entry: to_nearest_interval(entry))
    daysToRetrieve = solarDailyDF["Date Time"].dt.strftime("%Y-%m-%d").unique() #convert dtobj to visualcrossing format and find unique enteries

    relevantData = []
    for day in daysToRetrieve:
        print(day)
        response = requests.get(url=f"{CORE_ADDRESS}/{zipcode}/{day}", params=params)
        relevantData += response.json()["days"][0]["hours"]

    visualCrossingDF = pd.DataFrame(relevantData)
    visualCrossingDF["datetimeEpoch"] = visualCrossingDF["datetimeEpoch"].apply(
        lambda entry: datetime.datetime.fromtimestamp(entry))  #convert from unix to datetime obj
    visualCrossingDF.rename(columns={"datetimeEpoch": "Date Time"}, inplace=True) #rename the column to match the new format

    solarDailyDF["cloudcover"] = visualCrossingDF["cloudcover"][
        visualCrossingDF["Date Time"].isin(solarDailyDF["Date Time"])].values