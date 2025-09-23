import os, requests
import pandas as pd
import datetime
from dotenv import load_dotenv
from typing import Set, Optional
from pathlib import Path


class VisualCrossingClient:
    """
    A class for enriching solar data with weather information from Visual Crossing API.
    
    This class handles data preprocessing, API calls, and combining solar data with weather data.
    """
    BASE_ADDRESS = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    
    def __init__(self, api_key: str, zipcode: str, data_types: list[str], archive_location: Optional[Path]=None):
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
        else: 
            empty_df = {col_name:[] for col_name in data_types}
            empty_df["timestamp"] = []

            self.archive_path = Path(os.getcwd()) / "Data/api_archive.csv"
            self.archive = pd.DataFrame(empty_df)
            self.archive.to_csv(self.archive_location)
    
    @staticmethod
    def nearest_interval(dtobj: datetime.datetime) -> datetime.datetime:
        """
        Find the nearest two hour interval.

        Args:
            dtobj: The original datetime object.

        Returns:
            A new datetime object with the nearest 2 hour mark.
        """
        if dtobj.hour % 2 == 0:  # round down if even
            return dtobj.replace(minute=0, second=0)
        else:  # round up if odd
            return dtobj.replace(hour=dtobj.hour+1, minute=0, second=0)

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

    def determine_data_needs(self, daily_user_data: pd.DataFrame) -> Set[str]:
        """
        Compare entries in user data to Visual Crossing archive. 
        Returns a list of days to pull further data for.

        Args:
            daily_user_data: DataFrame with solar data
            current_vc_data: Existing Visual Crossing data (optional)

        Returns:
            Set of days in YYYY-MM-DD format that need new data
        """
        archived_days = set(self.archive["timestamp"].dt.strftime("%Y-%m-%d"))
            
        if "Date Time" in current_vc_data.columns and not current_vc_data.empty:
            user_days = set(daily_user_data["Date Time"].dt.strftime("%Y-%m-%d"))
            archived_days = set(current_vc_data["Date Time"].dt.strftime("%Y-%m-%d"))
            new_days = user_days - archived_days
            return new_days
        else:
            return set(daily_user_data["Date Time"].dt.strftime("%Y-%m-%d").unique())


    def preprocess_solar_data(self, solar_daily_df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess solar data by converting date/time columns and aligning to intervals.
        
        Args:
            solar_daily_df: Raw solar data DataFrame
            
        Returns:
            Preprocessed solar data DataFrame
        """
        # Convert text entries to datetime objects
        solar_daily_df["Date Time"] = pd.to_datetime(
            solar_daily_df["Date"] + "T" + solar_daily_df["Time"], 
            format="%Y-%m-%dT%H:%M"
        )
        
        # Align to nearest two-hour interval
        solar_daily_df["Date Time"] = solar_daily_df["Date Time"].apply(
            lambda entry: self.to_nearest_interval(entry)
        )
        
        print("Preprocessing Complete")
        return solar_daily_df

    def retrieve_new_weather_data(self, days_to_retrieve: Set[str]) -> pd.DataFrame:
        """
        Retrieve new weather data for specified days.
        
        Args:
            days_to_retrieve: Set of days in YYYY-MM-DD format
            
        Returns:
            DataFrame with new weather data
        """
        if not days_to_retrieve:
            print("No New Data To Retrieve")
            return pd.DataFrame()
            
        new_vc_data = pd.DataFrame()
        print("Retrieving Data...")
        
        for day in days_to_retrieve:
            print(f'\t{day}')
            try:
                response = self.retrieve_daily_data(
                    day, 
                    self.data_types + ',datetimeEpoch'
                )
                new_vc_data = pd.concat([new_vc_data, response], ignore_index=True)
            except Exception as e:
                print(f"Failed to retrieve data for {day}: {e}")
                continue
                
        if not new_vc_data.empty:
            # Convert from unix timestamp to datetime
            new_vc_data["datetimeEpoch"] = new_vc_data["datetimeEpoch"].apply(
                lambda entry: datetime.datetime.fromtimestamp(entry)
            )
            # Rename column to match expected format
            new_vc_data.rename(columns={"datetimeEpoch": "Date Time"}, inplace=True)
            print("Data Retrieval Complete")
        
        return new_vc_data

    def combine_data(self, solar_daily_df: pd.DataFrame, 
                    visual_crossing_df: pd.DataFrame) -> pd.DataFrame:
        """
        Combine solar data with weather data.
        
        Args:
            solar_daily_df: Solar data DataFrame
            visual_crossing_df: Weather data DataFrame
            
        Returns:
            Combined DataFrame
        """
        for data_type in self.data_types.split(','):
            if data_type in visual_crossing_df.columns:
                solar_daily_df[data_type] = visual_crossing_df[data_type][
                    visual_crossing_df["Date Time"].isin(solar_daily_df["Date Time"])
                ].values
                
        print('Data Processing Complete')
        return solar_daily_df


    def run_enrichment(self, solar_data: pd.DataFrame, 
                       existing_weather_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Run the complete data enrichment process.
        
        Args:
            solar_data: DataFrame containing solar data with 'Date' and 'Time' columns
            existing_weather_data: Optional DataFrame with existing weather data
        
        Returns:
            Enriched DataFrame with solar data combined with weather data
        """
        # Use existing weather data or create empty DataFrame
        visual_crossing_df = existing_weather_data.copy() if existing_weather_data is not None else pd.DataFrame()
        
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
    solar_data = solar_data.rename(columns={"File": "filename"})

    ### Retrieve Meta Data ###
    metadata = pd.read_csv(data_folder / "metadata.csv")
    metadata = metadata[["filename", "photoshop:DateCreated"]]
    metadata = metadata.rename(columns={"photoshop:DateCreated": "timestamp"})
    metadata["timestamp"] = pd.to_datetime(metadata["timestamp"])

    merged_df = pd.merge(solar_data, metadata, on="filename")


    
    client = VisualCrossingClient(api_key, zipcode, data_types, archive_path)
    day = "2025-09-15"
    df = client.retrieve_daily_data(day)

    nearest = pd.DataFrame({"nearest_interval": merged_df["timestamp"].apply(VisualCrossingClient.nearest_interval)})
    #nearest = pd.concat([merged_df["timestamp"], nearest], axis = 1)
    print("Enriched data shape:", df.shape)
    print("Columns:", df.columns.tolist())


