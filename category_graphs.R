library(lubridate)
library(readr)

closest_hour <- function(time) {
  if (is.na(time)) { #handles missing enteries
    return(as_datetime(0)) #ensures all enteries have the same type
  }
  if (hour(time) %% 2 == 0) { #always round down
    return(floor_date(as_datetime(time), unit="hour")) #hms format not supported by floor/ceiling functions. convert to ISO format first
  } else { #always round up
    return(ceiling_date(as_datetime(time), unit="hour"))
  }
}

plot_solar_noon <- function(dataDF) {
  avgDF <- data.frame(Time = unique(dataDF$Hour), Flat=0, Angled=0)
  for (hourValue in avgDF$Time) {
    hourEnteries <- subset(dataDF, dataDF$Hour == hourValue)
    flatAvg <- mean(hourEnteries$Flat, na.rm=TRUE)
    angledAvg <- mean(hourEnteries$Angled, na.rm=TRUE)
    avgDF$Flat[avgDF$Time == hourValue] = flatAvg
    avgDF$Angled[avgDF$Time == hourValue] = angledAvg
  }
  plot(avgDF$Time, avgDF$Flat)
  plot(avgDF$Time, avgDF$Angled)
  noonDF <- subset(avgDF, hour(avgDF$Time) == 12)
  plot(noonDF$Time, noonDF$Flat)
  plot(noonDF$Time, noonDF$Angled)
  fullSunSolarNoonDF
  fullSunAvgDF
  order(fullSunAvgDF[[1]])
  fullSunAvgDF[order(fullSunAvgDF[[1]]),]
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

mergedDF = merge(hourlyDF, locationsDF, by="Location")
relevantDF = subset(mergedDF, select=c(Location, Date, Time, Angled, Flat, Category))


hourCol <- c(as_datetime(0)) #ensures data consistency in vector. otherwise all data will be converted to numeric
for (timeEntry in relevantDF$Time) {
  hourCol <- c(hourCol, closest_hour(timeEntry))
}
hourCol <- hourCol[2:length(hourCol)]
hourCol <- dhours(hour(hourCol)) #convert to durations

relevantDF$Hour <- relevantDF$Date + hourCol

fullShadeDF <- subset(relevantDF, relevantDF$Category == "Full Shade")
fullSunDF <- subset(relevantDF, relevantDF$Category == "Full Sun")
partialShadeDF <- subset(relevantDF, relevantDF$Category == "Partial Shade")

plot_solar_noon(fullSunDF)
plot_solar_noon(fullShadeDF)
plot_solar_noon(partialShadeDF)
