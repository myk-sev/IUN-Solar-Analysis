# IUN Solar Analysis 🌞

A toolkit for visualizing, cleaning, and working with solar irradiance taken at Indiana University Northwest (IUN).

## 🗂️ Scripts Overview

### 📊 Visualization & Processing
These scripts focus on plotting, charting, and summarizing data visually.
* `location_difference.R`: Illustrates solar reading differenes seen in low, medium, and high shade areas.
* `daily_curve.R`: Displays changes in irradiance averaged over a 24 hour period.
* `tilt_and_weather.R`: Examines effect of daily conditions and sensor orientation on measurements.

### ⛅ Data Enrichment
These scripts connect with outside data sources adding additional information on a measure by measure basis.
* `data_enrichement.py`: By default, adds cloud coverage & averaged solar irradiation measures to all time enteries.

### 📅 Input Formatting

`location_details.csv`
| Column Name | Description |
| --- | --- |
| Location |Short hand name for point at which measurement occurs. |
| Latitude |Coordinate of measurement |
| Longitude |Coordinate of measurement |
|Category|Level of shade for the location. (Full Sun, Partial Shade, Full Shade)|

`daily_data.csv`
Date	Time			Cloud_Coverage		
| Column Name | Description |
| --- | --- |
| Date | MM/dd/YYY Ex: 05/26/025 |
| Time | HH:mm Ex: 14:30 (Military Time) |
| Azemuthal | The angle of the sun across the sky. |
| Solar_Altitude | The angle of the sun in the sky. |
| Cloud_Coverage | Percentage of the sky obscured by clouds. Retrieved from Visual Crossing. |
| Weather | Qualitative description of sky (Clear skies, Partially Cloudy, Overcast, Night) |

`hourly_data.csv`
| Column Name | Description |
| --- | --- |
| Date | MM/dd/YYY Ex: 05/26/025 |
| Time | HH:mm Ex: 14:30 (Military Time) |
| Location | Short hand name for point at which measurement occurs. |
| Angled | Solar irradiance at your latitude's optimal orientation |
| Flat | Solar irradiance at 0° |

