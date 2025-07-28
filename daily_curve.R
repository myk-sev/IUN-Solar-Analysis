library(lubridate)
library(readr)
library(ggplot2)

closest_hour <- function(time) {
  #All data is recorded in two hour intervals. This finds the closest interval.
  if (is.na(time)) { #handles missing enteries
    return(as_datetime(0)) #ensures all enteries have the same type
  }
  if (hour(time) %% 2 == 0) { #always round down
    return(floor_date(as_datetime(time), unit="hour")) #hms format not supported by floor/ceiling functions. convert to ISO format first
  } else { #always round up
    return(ceiling_date(as_datetime(time), unit="hour"))
  }
}

add_closet_hour <- function(dataDF) {
  #Adds a column to the input spcificy the closest two hour marker.
  hourCol <- c(as_datetime(0)) #ensures data consistency in vector. otherwise all data will be converted to numeric
  for (timeEntry in dataDF$Time) {
    hourCol <- c(hourCol, closest_hour(timeEntry))
  }
  hourCol <- hourCol[2:length(hourCol)]
  hourCol <- dhours(hour(hourCol)) #convert to durations
  
  dataDF$Hour <- dataDF$Date + hourCol
  
  return(dataDF)
}

extract_interval_averages <- function(dataDF) {
  #find the average for each 2 hour mark
  intervals <- hms::as_hms(seq(8,20,2)*60*60)
  avgDF <- data.frame(Time = intervals, Flat=0, Angled=0)
  for (h in seq(8,20,2)) {
    hourEnteries <- subset(dataDF, hour(dataDF$Hour) == h)
    flatAvg <- mean(hourEnteries$Flat, na.rm=TRUE)
    angledAvg <- mean(hourEnteries$Angled, na.rm=TRUE)
    avgDF$Flat[avgDF$Time == hms::as_hms(h*60*60)] = flatAvg
    avgDF$Angled[avgDF$Time == hms::as_hms(h*60*60)] = angledAvg
  }
  return(avgDF)
}

locationsDF <- read_csv("location_details.csv", col_types = cols(
  Location = col_character(),
  Latitude = col_double(),
  Longitude = col_double(),
  Tangential = col_character(),
  Lighting = col_character(),
  Foliage_Shadow = col_character(),
  Building_Shadow = col_character(),
  Category = col_character()
))

hourlyDF <- read_csv("hourly_data.csv", col_types=cols(
  Date = col_datetime(),
  Time = col_time(),
  Location = col_character(),
  Angled = col_double(),
  Flat = col_double()
))

hourlyDF <- add_closet_hour(hourlyDF)
expandedHourlyDF <- merge(hourlyDF, locationsDF, by=c("Location"))

fullShadeDF <- subset(expandedHourlyDF, expandedHourlyDF$Category == "Full Shade")
fullSunDF <- subset(expandedHourlyDF, expandedHourlyDF$Category == "Full Sun")
partialShadeDF <- subset(expandedHourlyDF, expandedHourlyDF$Category == "Partial Shade")

allAveragesDF <- extract_interval_averages(hourlyDF)
fullShadeAvgsDF <- extract_interval_averages(fullShadeDF)
fullSunAvgsDF <- extract_interval_averages(fullSunDF)
partialShadeAvgsDF <- extract_interval_averages(partialShadeDF)

allAveragesDF$Category = "All"
fullShadeAvgsDF$Category = "Full Shade"
fullSunAvgsDF$Category = "Full Sun"
partialShadeAvgsDF$Category = "Partial Shade"

avgByCategoryDF <- rbind(fullShadeAvgsDF, fullSunAvgsDF, partialShadeAvgsDF)

ggplot(
  data = avgByCategoryDF,
  mapping = aes(x=Time, y=Angled, color=Category)
) +
  geom_point() +
  geom_smooth(se=FALSE) +
  labs(
    color="Location Type", 
    y=expression("Solar Irradiance (W/m"^2*")"),
    title= "Average Daily Solar Irradiance (42°)"
  )

ggplot(
  data = avgByCategoryDF,
  mapping = aes(x=Time, y=Flat, color=Category)
) +
  geom_point() +
  geom_smooth(se=FALSE) +
  labs(
    color="Location Type", 
    y=expression("Solar Irradiance (W/m"^2*")"),
    title= "Average Daily Solar Irradiance (0°)"
  )

allAveragesFlatDF <- data.frame(
  Time=allAveragesDF$Time,
  Value=allAveragesDF$Flat,
  Position="0°"
)

allAveragesAngeledDF <- data.frame(
  Time=allAveragesDF$Time,
  Value=allAveragesDF$Angled,
  Position="42°"
)

allAveragesSplitDf <- rbind(allAveragesFlatDF, allAveragesAngeledDF)

ggplot(
  data = allAveragesSplitDf,
  mapping = aes(x=Time, y=Value, color=Position)
) +
  geom_point() +
  geom_smooth(se=FALSE) +
  labs(
    color="Angle", 
    y=expression("Solar Irradiance (W/m"^2*")"),
    title= "Average Daily Solar Irradiance (All)"
  )
