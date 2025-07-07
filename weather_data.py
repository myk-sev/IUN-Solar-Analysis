import requests
import pandas as pd
import datetime
import dotenv
import os

DAILY_DATA_FILENAME = "daily_data.csv"
VISUAL_CROSSING_ARCHIVE = "api_archive.csv"
COMBO_FILE = "combined_data.csv"

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


def retrieve_daily_data(day, zipcode, apikey, dataTypes="cloudcover"):
    """
    Interface with visualcrossing API to retrieve data for a single day.

    Output Columns: unix_time, dataTypes, ...

    """
    baseAddress = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    fullAddress = f"{baseAddress}/{zipcode}/{day}"

    params = {
        "key": apikey,
        "contentType": "json",  #csv can also be used
        "elements": dataTypes
    }

    response = requests.get(url=fullAddress, params=params)
    if response.status_code != 200:
        print("Error retrieving data from Visual Crossing server")
        raise

    df = pd.DataFrame(response.json()["days"][0]["hours"])
    return df

def determine_data_needs(dailyUserData, currentVCData=pd.DataFrame()):
    """
    Compare entries in user data to Visual Crossings archive. Returns a list of days to pull further data for.

    :param dailyUserData:
    :param currentVCData:

    :return: days(set of strings) format: {"YYYY-MM-DD", ...}
    """
    if "Date Time" in currentVCData:
        userDays = set(dailyUserData["Date Time"].dt.strftime("%Y-%m-%d")) #converts datetime objs to YYY-MM-DD string removing duplicate entries
        archivedDays = set(currentVCData["Date Time"].dt.strftime("%Y-%m-%d"))

        newDays = userDays - archivedDays
        return newDays

    else:
        return dailyUserData["Date Time"].dt.strftime("%Y-%m-%d").unique()

if __name__ == "__main__":
    dotenv.load_dotenv()

    ### Load Data ###
    solarDailyDF = pd.read_csv(DAILY_DATA_FILENAME)

    if os.path.exists(VISUAL_CROSSING_ARCHIVE):
        visualCrossingDF = pd.read_csv(VISUAL_CROSSING_ARCHIVE)
        visualCrossingDF["Date Time"] = visualCrossingDF["Date Time"].apply(lambda entry: pd.to_datetime(entry)) # Datetime objects are converted to strings when saved to csv. They must be reconverted back to dtobj.
    else:
        visualCrossingDF = pd.DataFrame()
    print("Data Sets Loaded")

    ### Preprocess Data ###
    #The general workflow for working with time data is to keep time in the datatime obj format, converting to and from the various types as needed.
    #This includes Unix type and string formats.
    solarDailyDF["Date Time"] = pd.to_datetime(solarDailyDF["Date"] + "T" + solarDailyDF["Time"], format="%Y-%m-%dT%H:%M") #convert text entries to datetime obj
    solarDailyDF["Date Time"] = solarDailyDF["Date Time"].apply(lambda entry: to_nearest_interval(entry))
    print("Preprocessing Complete")

    ### Retrieve New Data ###
    daysToRetrieve = determine_data_needs(solarDailyDF, visualCrossingDF)

    if len(daysToRetrieve) != 0:
        newVCData = pd.DataFrame()
        print("Retrieving Data...")
        for day in daysToRetrieve:
            print('\t', day)
            response = retrieve_daily_data(
                day, #format YYYY-MM-DD
                os.environ.get("ZIPCODE"),
                os.environ.get("API_KEY"),
                os.environ.get("DATA") + ',datetimeEpoch'
            )
            newVCData = pd.concat([newVCData, response], ignore_index=True)
        print("Data Retrieval Complete")

        newVCData["datetimeEpoch"] = newVCData["datetimeEpoch"].apply(
            lambda entry: datetime.datetime.fromtimestamp(entry))  #convert from unix to datetime obj
        newVCData.rename(columns={"datetimeEpoch": "Date Time"}, inplace=True) #rename the column to match the new format

        visualCrossingDF = pd.concat([visualCrossingDF, newVCData], ignore_index=True)
    else:
        print("No New Data To Retrieve")

    ### Combine Data ###
    for dataType in os.environ.get("DATA").split(','):
        solarDailyDF[dataType] = visualCrossingDF[dataType][
            visualCrossingDF["Date Time"].isin(solarDailyDF["Date Time"])].values #pulls data values where time objects match across dataframes
    print('Data Processing Complete')


    ### Save Data ###
    visualCrossingDF.to_csv(VISUAL_CROSSING_ARCHIVE)
    solarDailyDF.to_csv(COMBO_FILE)
    print("Results Saved")
