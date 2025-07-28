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

**Input Formats**
`location_details.csv`

`daily_data.csv`
`hourly_data.csv`
