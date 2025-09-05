# IUN Solar Analysis 🌞

A toolkit for visualizing, cleaning, and working with solar irradiance data taken at Indiana University Northwest (IUN). This data was primarily captured through a handheld sensor that connected to the Pasco's [SPARKvue](https://www.pasco.com/products/software/sparkvue) app.

## 🗂️ Scripts Overview

### 📊 Visualization & Processing
These scripts focus on plotting, charting, and summarizing data visually.
* `location_difference.R`: Illustrates solar reading differenes seen in low, medium, and high shade areas.
* `daily_curve.R`: Displays changes in irradiance averaged over a 24 hour period.
* `tilt_and_weather.R`: Examines effect of daily conditions and sensor orientation on measurements.

### ⛅ Data Creation
These scripts connect with outside data sources adding additional information on a measure by measure basis.
* `data_enrichement.py`: By default, adds cloud coverage & averaged solar irradiation measures to all time enteries.
* `metadata.py`: Extracts metadata from SPARKvue screenshots. Utilize this in combination with vision-ai to automate data recording.
* `vision-ai.py`: Utilizes an open source vision model to extract solar irradiance and location informatin from SPARKvue screenshots.

### 📅 Input Formatting
* `location_details.csv` - Utilize this spreadsheet to store location data & qualitative descriptions of solar coverage.

| Column Name | Description |
| --- | --- |
| Location |Short hand name for point at which measurement occurs. |
| Latitude |Coordinate of measurement |
| Longitude |Coordinate of measurement |
|Category|Level of shade for the location. (Full Sun, Partial Shade, Full Shade)|

* `daily_data.csv` - Use this spreadsheet to store qualitative measures such as Weather for each _session_ of recording data. Before scripts for automating retrieval of altitude, azemuthal, and cloud coverage were created, these were manually recorded and stored here.

| Column Name | Description |
| --- | --- |
| Date | MM/dd/YYY Ex: 05/26/025 |
| Time | HH:mm Ex: 14:30 (Military Time) |
| Azemuthal | The angle of the sun across the sky. |
| Solar_Altitude | The angle of the sun in the sky. |
| Cloud_Coverage | Percentage of the sky obscured by clouds. Retrieved from Visual Crossing. |
| Weather | Qualitative description of sky (Clear skies, Partially Cloudy, Overcast, Night) |

* `hourly_data.csv` - Historic spreadsheet used to record measurements before automation was added.

| Column Name | Description |
| --- | --- |
| Date | MM/dd/YYY Ex: 05/26/025 |
| Time | HH:mm Ex: 14:30 (Military Time) |
| Location | Short hand name for point at which measurement occurs. |
| Angled | Solar irradiance at your latitude's optimal orientation |
| Flat | Solar irradiance at 0° |

