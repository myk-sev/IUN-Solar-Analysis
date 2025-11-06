import os
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from visualcrossing import VisualCrossingClient
from location_labels import add_location_labels

DATA_FOLDER = Path(os.getcwd()) / "data"
ARCHIVE_FILE = DATA_FOLDER / "api_archive.csv"
METADATA_FILE = DATA_FOLDER / "metadata.csv"
LOCATION_DATA = DATA_FOLDER / "locations.csv"
SKY_FILE = DATA_FOLDER / "sky_data.csv"

def add_location_labels(data: pd.DataFrame, location_labels: pd.DataFrame) -> pd.DataFrame:
    """Match each data point to its closet label.

    :param data: data to be labeled
    :param location_labels: labels to be used for matching
    :return: data with added location labels
    """
    n_locations = location_labels.shape[0]

    # add labels to the data that will be sorted
    # this ensures the output of Kmeans is matched with the correct location name
    amendment = []
    for i, data_row in location_labels.iterrows():
        formatted_row = {
            "filename": data_row["name"],
            "longitude": data_row["longitude"],
            "latitude": data_row["latitude"]
        }
        amendment.append(formatted_row)
    combined_data = pd.concat([data, pd.DataFrame(amendment)], ignore_index=True)

    # remove rows with no location data
    mask = (combined_data["latitude"] == 0) & (combined_data["longitude"] == 0)
    blank_rows = combined_data[mask].index
    clean_data = combined_data.drop(blank_rows)

    # group coordinates
    coordinate_data = clean_data[["latitude", "longitude"]]

    print("Location clustering begun...")
    kmeans = KMeans(n_clusters=n_locations).fit(coordinate_data)
    group_map = kmeans.labels_
    centroids = kmeans.cluster_centers_ #scikitlearn ends attributes derived from learned data in _
    print("Complete.")

    plt.scatter(coordinate_data["latitude"], coordinate_data["longitude"], c=group_map, cmap="viridis", s=50)
    plt.show()

    # match location name to coordinate data
    combined_data["location"] = -1
    combined_data.loc[~mask, "location"] = group_map

    location_key = {}
    location_key[-1] = "Missing"
    for i, row in combined_data.iloc[-n_locations:].iterrows():
        location_key[row["location"]] = row["filename"] #actually location name, filename as column header used for compatibility
    

    output = combined_data.iloc[:-n_locations]
    output["location"] = output["location"].apply(lambda entry: location_key[entry])
    return output

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
    location_enriched = add_location_labels(sky_enriched, location_labels)

    core_data = location_enriched[["timestamp", "location", "measurement", "cloudcover", "solarradiation", "sky", "filename", "latitude", "longitude"]]
    core_data.to_csv("full_dataset.csv")