import os
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from visualcrossing import VisualCrossingClient

DATA_FOLDER = Path(os.getcwd()) / "data"
ARCHIVE_FILE = DATA_FOLDER / "api_archive.csv"
METADATA_FILE = DATA_FOLDER / "metadata.csv"
LOCATION_DATA = DATA_FOLDER / "locations.csv"
SKY_FILE = DATA_FOLDER / "sky_data.csv"

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
    metadata = pd.read_csv(METADATA_FILE).drop(columns="Unnamed: 0")
    metadata["timestamp"] = pd.to_datetime(metadata["timestamp"])

    ### Enrich Manual Data W/ VC Data ###
    merged_df = pd.merge(solar_data, metadata, on="filename")
    client = VisualCrossingClient(api_key, zipcode, data_types, ARCHIVE_FILE)
    enriched_df = client.enrich(merged_df)

    ### Match Sky Status With Enriched Data ###
    sky_data = sky_data = pd.read_csv(SKY_FILE).drop(columns="Unnamed: 0")
    sky_data["timestamp"] = pd.to_datetime(sky_data["timestamp"])
    sky_data = sky_data.rename(columns={"timestamp": "interval"})
    enriched_df["interval"] = enriched_df["timestamp"].apply(client.nearest_interval)
    sky_enriched = pd.merge(enriched_df, sky_data, on="interval", how="left").drop(columns="interval")

    ### Add Location Data ###
    location_labels = pd.read_csv(LOCATION_DATA)

    sky_enriched = sky_enriched[["timestamp", "measurement", "cloudcover", "solarradiation", "sky", "filename", "latitude", "longitude"]]
    sky_enriched.to_csv("full_dataset.csv")