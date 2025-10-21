import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans
import os

SOURCE_DATA = Path(os.getcwd()) / "full_dataset.csv"

# Labels can on occasion be incorrect. Double check the output. Run again if this happens.

if __name__ == "__main__":
    # retrieve records
    all_data = pd.read_csv(SOURCE_DATA)
    core_data = all_data.loc[:, ["filename", "longitude", "latitude"]]

    # remove rows with no location data
    mask = (core_data["latitude"] == 0) & (core_data["longitude"] == 0)
    blank_rows = core_data[mask].index
    clean_data = core_data.drop(blank_rows)

    coordinate_data = clean_data[["latitude", "longitude"]]

    kmeans = KMeans(n_clusters=11).fit(coordinate_data)
    group_map = kmeans.labels_
    centroids = kmeans.cluster_centers_ #scikitlearn ends attributes derived from learned data in _

    plt.scatter(coordinate_data["latitude"], coordinate_data["longitude"], c=group_map, cmap="viridis", s=50)
    plt.show()

    core_data["location"] = -1
    core_data.loc[~mask, "location"] = group_map

    ### stuff

    core_data.to_csv(SOURCE_DATA)

