# IUN Solar Analysis 🌞

A toolkit for visualizing, cleaning, and working with solar irradiance taken at Indiana University Northwest (IUN).

## 🗂️ Scripts Overview

### 📊 Visualization & Processing
These scripts focus on plotting, charting, and summarizing data visually.
* `category_graphs.R`
* `daily_curve_graphs.R`: Averages all enteries across a 24 hour period. Graphs generated focus on angle of incidence.
* `weather_graphs.R`

### ⛅ Data Enrichment
These scripts connect with outside data sources adding additional information on a measure by measure basis.
* `weather_data.py`: By default, adds cloud coverage & averaged solar irradiation measures to all time enteries. 
