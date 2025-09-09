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
  #Adds a column to the input specifing the closest two hour marker.
  hourCol <- c(as_datetime(0)) #ensures data consistency in vector. otherwise all data will be converted to numeric
  for (timeEntry in dataDF$Time) {
    hourCol <- c(hourCol, closest_hour(timeEntry))
  }
  hourCol <- hourCol[2:length(hourCol)]
  hourCol <- dhours(hour(hourCol)) #convert to duration
  
  dataDF$Hour <- dataDF$Date + hourCol
  
  return(dataDF)
}

extract_interval_averages_expanded <- function(dataDF) {
  #find the average for each 2 hour mark. different between weather conditions at each 2 hour mark.
  intervals <- hms::as_hms(seq(8,20,2)*60*60)
  weatherConditions <- c("Clear Skies", "Partially Cloudy", "Overcast")
  avgDF <- data.frame(Time = hms::as_hms(0), Flat=0, Angled=0, Weather="")
  for (h in seq(8,20,2)) {
    hourEnteries <- subset(dataDF, hour(dataDF$Hour) == h)
    for (w in weatherConditions) {
      weatherEnteries <- subset(hourEnteries, hourEnteries$Weather == w)
      flatAvg <- mean(weatherEnteries$Flat, na.rm=TRUE)
      angledAvg <- mean(weatherEnteries$Angled, na.rm=TRUE)
      newRow <- data.frame(Time=hms::as_hms(h*60*60), Flat=flatAvg, Angled=angledAvg, Weather=w)
      avgDF <- rbind(avgDF, newRow)
    }
  }
  avgDF <- avgDF[-c(1),] #the first row is blank. this removes it
  return(avgDF)
}

hourlyDF <- read_csv("hourly_data.csv", col_types=cols(
  Date = col_datetime(),
  Time = col_time(),
  Location = col_character(),
  Angled = col_double(),
  Flat = col_double()
))

dailyDF <- read_csv("daily_data.csv",col_types=cols(
  Date = col_datetime(),
  Time = col_time(),
  Azemuthal = col_double(),
  Solar_Altitude = col_double(),
  Cloud_Coverage = col_double(),
  Weather = col_character(),
))

hourlyDF <- add_closet_hour(hourlyDF)

allDataDF <- merge(hourlyDF, dailyDF, by="Hour")


relevantDF <- data.frame(
  Hour=allDataDF$Hour, 
  Angled=allDataDF$Angled, 
  Flat=allDataDF$Flat, 
  Weather=allDataDF$Weather,
  Raining=allDataDF$Raining
)

averagesDF <- extract_interval_averages_expanded(relevantDF)
averagesDF$Ratio <- averagesDF$Angled / averagesDF$Flat

### Flat Graph ###
flatSpecific <- subset(averagesDF, !is.nan(Flat))
ggplot(
  data=flatSpecific,
  mapping=aes( x=Time, y=Flat, color=Weather)
) +
  geom_point(size = 3) +
  geom_line(linewidth=1) +
  labs(
    y=expression("Solar Irradiance (W/m"^2*")"),
    title= "Average Solar Irradiance (0°)"
  ) +
  theme_minimal(base_size=15)
  #theme_minimal()

### Angled Graph ###
angleSpecific <- subset(averagesDF, !is.nan(Angled))
ggplot(
  data=angleSpecific,
  mapping=aes( x=Time, y=Angled, color=Weather)
) +
  geom_point(size = 3) +
  geom_line(linewidth=1) +
  labs(
    y=expression("Solar Irradiance (W/m"^2*")"),
    title= "Average Solar Irradiance (42°)"
  ) +
  theme_minimal(base_size=15)


### Ratio Graph ###
ratioSpecific <- subset(averagesDF, (!is.nan(Flat) & !is.nan(Angled)))
ggplot(
  data=ratioSpecific,
  mapping=aes( x=Time, y=Ratio, color=Weather)
) +
  geom_point(size = 5) +
  geom_line(linewidth=2) +
  labs(
    y="Ratio",
    title= "Average Solar Irradiance (42° : 0°)"
  ) +
  theme_minimal(base_size=25) +
  geom_hline(yintercept = 1, linetype = "dashed")

             