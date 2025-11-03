import datetime, os, requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from pathlib import Path

DATA_FOLDER = Path(os.getcwd()) / "data"
ARCHIVE_FILE = DATA_FOLDER / "api_archive.csv"
METADATA_FILE = DATA_FOLDER / "metadata.csv"
SKY_FILE = DATA_FOLDER / "sky_data.csv"

class VisualCrossingClient:
    """
    A class for enriching solar data with weather information from Visual Crossing API.
    
    This class handles data preprocessing, API calls, and combining solar data with weather data.
    """
    BASE_ADDRESS = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    
    def __init__(self, api_key: str, zipcode: str, data_types: list[str], archive_location: Path | None =None):
        """Initialize the client. Load archived data.

        :param api_key: Visual Crossing API key
        :param zipcode: ZIP code of the location where whether data is needed
        :param data_types: Comma-separated weather data types (if None, will try to load from .env)
        """
        self.zipcode = zipcode
        self.api_key = api_key
        self.data_types = ",".join(data_types) #For additional types visit: https://www.visualcrossing.com/weather-query-builder/
        
        if archive_location: 
            self.archive_path = archive_location
            self.archive = pd.read_csv(archive_location)
            self.archive["timestamp"] = pd.to_datetime(self.archive["timestamp"])
            self.archive = self.archive.drop(columns="Unnamed: 0")

        else: 
            empty_df = {col_name:[] for col_name in data_types}
            empty_df["timestamp"] = []

            self.archive_path = Path(os.getcwd()) / "Data/api_archive.csv"
            self.archive = pd.DataFrame(empty_df)
            self.archive.to_csv(self.archive_location)
    
    @staticmethod
    def nearest_interval(dt_obj: datetime.datetime) -> datetime.datetime:
        """Find the nearest two hour interval.

        :param dt_obj: the original datetime object
         return: a new datetime object at nearest 2 hour mark
        """
        if dt_obj.hour % 2 == 0:  # round down if even
            return dt_obj.replace(minute=0, second=0)
        else:  # round up if odd
            return dt_obj.replace(hour=dt_obj.hour+1, minute=0, second=0)

    def retrieve_daily_data(self, day: str) -> pd.DataFrame:
        """Interface with Visual Crossing API to retrieve data for a single day.

        :param day: YYYY-MM-DD format
        :return: weather data from VisualCrossing
        :raises requests.RequestException: if API request fails
        """
        full_address = f"{self.BASE_ADDRESS}/{self.zipcode}/{day}"

        params = {
            "key": self.api_key,
            "contentType": "json",
            "elements": "datetimeEpoch," + self.data_types #ensures a timestamp is given for each reading
        }

        try:
            response = requests.get(url=full_address, params=params)
            response.raise_for_status()

            df = pd.DataFrame(response.json()["days"][0]["hours"])
            df = df.rename(columns={"datetimeEpoch":"timestamp"})
            df["timestamp"] = df["timestamp"].apply(datetime.datetime.fromtimestamp) #convert unix time to dt_obj

            return df

        except requests.RequestException as e:
            print(f"Error retrieving data from Visual Crossing server for {day}: {e}")
            raise

    def determine_data_needs(self, user_timestamps: pd.Series) -> np.ndarray[str]:
        """Determine days lacking an entry in cached data from Visual Crossing.

        :param user_timestamps: timestamps present in latest collection of data
        :return: the days lacking data in visual crossing cache
        """
        nearest_timestamps = user_timestamps.apply(self.nearest_interval)
        new_intervals = nearest_timestamps[~nearest_timestamps.isin(self.archive["timestamp"])]
        new_days = new_intervals.dt.strftime("%Y-%m-%d").unique()
        return new_days

    def utilize_existing_cache(self, user_data: pd.DataFrame, time_col: str = "timestamp") -> pd.DataFrame:
        """Access and pair archived data.

        :param user_data: manual retrieved data
        :param time_col: column name for time data
        :return: dataframe enriched with cached visual crossing data & missing datatypes
        """
        user_data["interval"] = user_data[time_col].apply(self.nearest_interval)
        enriched = pd.merge(user_data, self.archive, left_on="interval", right_on=time_col)

        enriched = enriched.rename(columns={f"{time_col}_x":time_col})
        enriched = enriched.drop(columns=["interval", f"{time_col}_y"])

        return enriched

    def enrich(self, user_data: pd.DataFrame, time_col: str = "timestamp") -> pd.DataFrame:
        """Pair manual data with data retrieved from Visual Crossing.
        
        :param user_data: most recent data collection
        :param time_col: column name for time data
        :param data_types: weather elements to be retrieved from Visual Crossing. more options available at https://www.visualcrossing.com/resources/documentation/weather-api/timeline-weather-api/
        :return: user data with added data points from api service
        """
        #Add cached data to current data set
        old_data_enriched = self.utilize_existing_cache(user_data)

        #Retrieve new Visual Crossing data
        new_days = self.determine_data_needs(user_data[time_col])
        if len(new_days) == 0: # end processing early when there is no new data 
            return old_data_enriched

        new_data =  pd.concat([self.retrieve_daily_data(day) for day in new_days], ignore_index=True)
        self.update_archive(new_data)

        #Match new manual data to Visual Crossing Data
        user_data["interval"] = user_data[time_col].apply(self.nearest_interval)
        new_data_enriched = pd.merge(user_data, new_data, left_on="interval", right_on=time_col)
        new_data_enriched = new_data_enriched.rename(columns={f"{time_col}_x":time_col})
        new_data_enriched = new_data_enriched.drop(columns=["interval", f"{time_col}_y"])

        #Combine new and old
        enriched_data = pd.concat([old_data_enriched, new_data_enriched], ignore_index=True)
        return enriched_data

    def update_archive(self, new_data: pd.DataFrame) -> None:
        """Adds new data to the archive (reduces costs).
        
        :param new_data: new data
        """
        self.archive = pd.concat([self.archive, new_data], ignore_index=True)
        self.archive.to_csv(self.archive_path)


if __name__ == "__main__":
    ### Settings ###
    load_dotenv()

    api_key = os.environ.get("API_KEY")
    zipcode = os.environ.get("ZIPCODE")
    data_types = ["cloudcover" , "solarradiation"] #For additional types visit: https://www.visualcrossing.com/weather-query-builder/

    ### Retrieve Screenshot Data ###
    months = os.listdir("Screenshots")
    solar_data = pd.concat([pd.read_csv(DATA_FOLDER / f"{month}.csv") for month in months], ignore_index=True)
    solar_data = solar_data.drop(columns="Unnamed: 0")

    ### Retrieve Meta Data ###
    metadata = pd.read_csv(METADATA_FILE)
    metadata = metadata[["filename", "photoshop:DateCreated"]]
    metadata = metadata.rename(columns={"photoshop:DateCreated": "timestamp"})
    metadata["timestamp"] = pd.to_datetime(metadata["timestamp"])

    ### Enrich Manual Data W/ VC Data
    merged_df = pd.merge(solar_data, metadata, on="filename")
    client = VisualCrossingClient(api_key, zipcode, data_types, ARCHIVE_FILE)
    enriched_df = client.enrich(merged_df)

    ### Match Hand Recorded Sky Data with Enriched Data ###
    sky_data = sky_data = pd.read_csv(SKY_FILE).drop(columns="Unnamed: 0")
    sky_data["timestamp"] = pd.to_datetime(sky_data["timestamp"])
    sky_data = sky_data.rename(columns={"timestamp": "interval"})
    enriched_df["interval"] = enriched_df["timestamp"].apply(client.nearest_interval)
    sky_enriched = pd.merge(sky_data, enriched_df, on="interval").drop(columns="interval")


    sky_enriched = sky_enriched[["timestamp", "measurement", "cloudcover", "solarradiation", "sky", "filename", "latitude", "longitude"]]
    sky_enriched.to_csv("full_dataset.csv")