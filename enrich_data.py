import datetime, os, requests

import pandas as pd
import numpy as np

from dotenv import load_dotenv
from pathlib import Path



class VisualCrossingClient:
    """
    A class for enriching solar data with weather information from Visual Crossing API.
    
    This class handles data preprocessing, API calls, and combining solar data with weather data.
    """
    BASE_ADDRESS = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    
    def __init__(self, api_key: str, zipcode: str, data_types: list[str], archive_location: Path | None =None):
        """Initialize the client. Load archived data.

        : api_key str: Visual Crossing API key
        : zipcode str: ZIP code of the location where whether data is needed
        : data_types str: Comma-separated weather data types (if None, will try to load from .env)

        : return VisualCrossingClient: client object
        """
        self.zipcode = zipcode
        self.api_key = api_key
        self.data_types = ",".join(data_types) #For additional types visit: https://www.visualcrossing.com/weather-query-builder/
        
        if archive_location: 
            self.archive_path = archive_location
            self.archive = pd.read_csv(archive_location)
            self.archive["timestamp"] = pd.to_datetime(self.archive["timestamp"])

        else: 
            empty_df = {col_name:[] for col_name in data_types}
            empty_df["timestamp"] = []

            self.archive_path = Path(os.getcwd()) / "Data/api_archive.csv"
            self.archive = pd.DataFrame(empty_df)
            self.archive.to_csv(self.archive_location)
    
    @staticmethod
    def nearest_interval(dt_obj: datetime.datetime) -> datetime.datetime:
        """Find the nearest two hour interval.

        : dt_obj datetime.datetime: the original datetime object
        : return datetime.datetime: a new datetime object at nearest 2 hour mark
        """
        if dt_obj.hour % 2 == 0:  # round down if even
            return dt_obj.replace(minute=0, second=0)
        else:  # round up if odd
            return dt_obj.replace(hour=dt_obj.hour+1, minute=0, second=0)

    def retrieve_daily_data(self, day: str) -> pd.DataFrame:
        """Interface with Visual Crossing API to retrieve data for a single day.

        : day str: YYYY-MM-DD format
        : return pandas.DataFrame: weather data from VisualCrossing
        : raises requests.RequestException: if API request fails
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
        :return numpy.ndarray: the days lacking data in visual crossing cache
        """
        nearest_timestamps = user_timestamps.apply(self.nearest_interval)
        new_intervals = nearest_timestamps[~nearest_timestamps.isin(self.archive["timestamp"])]
        new_days = nearest_timestamps.dt.strftime("%Y-%m-%d").unique()
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
        :param return: user data with added data points from api service
        """
        # Use existing weather data or create empty DataFrame
        old_data_enriched = self.utilize_existing_cache(user_data)

        new_days = self.determine_data_needs(user_data[time_col])
        new_data =  pd.concat([self.retrieve_daily_data(day) for day in new_days], ignore_index=True)
        
        # Preprocess solar data
        solar_daily_df = self.preprocess_solar_data(solar_data.copy())
        
        # Determine what new data is needed
        days_to_retrieve = self.determine_data_needs(solar_daily_df, visual_crossing_df)
        
        # Retrieve new weather data
        new_vc_data = self.retrieve_new_weather_data(days_to_retrieve)
        
        # Update weather archive
        if not new_vc_data.empty:
            visual_crossing_df = pd.concat([visual_crossing_df, new_vc_data], ignore_index=True)
        
        # Combine data
        enriched_df = self.combine_data(solar_daily_df, visual_crossing_df)
        
        return enriched_df

    def update_archive(self, new_data: pd.DataFrame) -> None:
        """Adds new data to the archive (reduces costs).
        
        : new_data pandas.DataFrame: new data
        """
        self.archive = pd.concat([self.archive, new_data], ignore_index=True)
        self.archive.to_csv(self.archive_path)


if __name__ == "__main__":
    ### Settings ###
    load_dotenv()

    api_key = os.environ.get("API_KEY")
    zipcode = os.environ.get("ZIPCODE")
    data_types = ["cloudcover" , "solarradiation"] #For additional types visit: https://www.visualcrossing.com/weather-query-builder/
    data_folder = Path(os.getcwd()) / "Data"
    archive_path = data_folder / "api_archive.csv"

    ### Retrieve Screenshot Data ###
    months = os.listdir("Screenshots")
    solar_data = pd.concat([pd.read_csv(data_folder / f"{month}.csv") for month in months], ignore_index=True)
    solar_data = solar_data.rename(columns={"File": "filename"}).drop(columns="Unnamed: 0")


    ### Retrieve Meta Data ###
    metadata = pd.read_csv(data_folder / "metadata.csv")
    metadata = metadata[["filename", "photoshop:DateCreated"]]
    metadata = metadata.rename(columns={"photoshop:DateCreated": "timestamp"})
    metadata["timestamp"] = pd.to_datetime(metadata["timestamp"])

    merged_df = pd.merge(solar_data, metadata, on="filename")

    client = VisualCrossingClient(api_key, zipcode, data_types, archive_path)

    nearest = pd.DataFrame({"nearest_interval": merged_df["timestamp"].apply(VisualCrossingClient.nearest_interval)})
    #nearest = pd.concat([merged_df["timestamp"], nearest], axis = 1)
    print("Enriched data shape:", df.shape)
    print("Columns:", df.columns.tolist())


