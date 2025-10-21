import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans
import os

DATA_FOLDER = Path(os.getcwd()) / "data"
SOURCE_DATA = DATA_FOLDER / "full_dataset.csv"
LOCATION_DATA = DATA_FOLDER / "locations.csv"
OUTPUT_FILE = DATA_FOLDER / "location_labeled.csv"

# Labels can on occasion be incorrect. Double check the output. Run again if this happens.

if __name__ == "__main__":
    # retrieve records
    all_data = pd.read_csv(SOURCE_DATA)
    core_data = all_data.loc[:, ["filename", "longitude", "latitude"]]

    # load labels
    locations = pd.read_csv(LOCATION_DATA)
    n_locations = locations.shape[0]
    amendment = []
    for i, data_row in locations.iterrows():
        formatted_row = {
            "filename": data_row["name"],
            "longitude": data_row["longitude"],
            "latitude": data_row["latitude"]
        }
        amendment.append(formatted_row)
    combined_data = pd.concat([core_data, pd.DataFrame(amendment)], ignore_index=True)

    # remove rows with no location data
    mask = (combined_data["latitude"] == 0) & (combined_data["longitude"] == 0)
    blank_rows = combined_data[mask].index
    clean_data = combined_data.drop(blank_rows)

    # group coordinates
    coordinate_data = clean_data[["latitude", "longitude"]]

    kmeans = KMeans(n_clusters=n_locations).fit(coordinate_data)
    group_map = kmeans.labels_
    centroids = kmeans.cluster_centers_ #scikitlearn ends attributes derived from learned data in _

    plt.scatter(coordinate_data["latitude"], coordinate_data["longitude"], c=group_map, cmap="viridis", s=50)
    plt.show()

    # match location name to coordinate data
    combined_data["location"] = -1
    combined_data.loc[~mask, "location"] = group_map

    location_key = {}
    location_key[-1] = "Missing"
    for i, row in combined_data.iloc[-n_locations:].iterrows():
        location_key[row["location"]] = row["filename"] #actually location name, row name used to compatibility
    

    core_data = combined_data.iloc[:-n_locations]
    core_data["location"] = core_data["location"].apply(lambda entry: location_key[entry])
    ### stuff

    #core_data.to_csv(SOURCE_DATA)

