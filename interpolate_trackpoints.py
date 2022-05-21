from datetime import datetime, timedelta
from bs4 import BeautifulSoup
format = '%Y-%m-%dT%H:%M:%S.%fZ'

def interpolate_trackpoints(soup,error_begin,error_end):

  #get start and end trackpoints
  begin_trackpoint=soup.find('Time', string=error_begin).parent
  end_trackpoint=soup.find('Time', string=error_end).parent

  #get begin and end data 
  begin_lat=float(begin_trackpoint.Position.LatitudeDegrees.string)
  begin_lon=float(begin_trackpoint.Position.LongitudeDegrees.string)
  begin_time=datetime.strptime(begin_trackpoint.Time.string,format)

  end_lat=float(end_trackpoint.Position.LatitudeDegrees.string)
  end_lon=float(end_trackpoint.Position.LongitudeDegrees.string)
  end_time=datetime.strptime(end_trackpoint.Time.string,format)

  #get deltas
  lat_delta = end_lat - begin_lat
  lon_delta = end_lon - begin_lon
  time_delta = end_time - begin_time


  #cycle through points and interpolate
  trackpoint_to_interpolate=begin_trackpoint.find_next('Trackpoint')
  while datetime.strptime(trackpoint_to_interpolate.Time.string,format) < datetime.strptime(end_trackpoint.Time.string,format):
    #get time of the trackpoint
    trackpoint_to_interpolate_time=datetime.strptime(trackpoint_to_interpolate.Time.string,format)
    print(trackpoint_to_interpolate_time)
    #find the interpolated values
    new_lat = begin_lat + lat_delta * (trackpoint_to_interpolate_time - begin_time) / time_delta
    new_lon = begin_lon + lon_delta * (trackpoint_to_interpolate_time - begin_time) / time_delta
    print(str(new_lat)+ ', '+ str(new_lon))
    #assign the interpolated values, if they exist
    try: 
      trackpoint_to_interpolate.Position.LatitudeDegrees.string.replace_with(str(new_lat))
      trackpoint_to_interpolate.Position.LongitudeDegrees.string.replace_with(str(new_lon))
    except:
      print('no data')

    #get the next trackpoint
    trackpoint_to_interpolate=(trackpoint_to_interpolate.find_next('Trackpoint'))
    