import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import random

from tcx_decoder import get_dataframes
from interpolate_trackpoints import interpolate_trackpoints

st.header('TCX file fixer')

st.write('Upload tcx files with dodgy gps data and fix it for Strava.')
st.write('This will also fix (to some extent) any issues with erroneous pace and segments.')

tcx_file=st.file_uploader('Upload a tcx file', type=['tcx'], accept_multiple_files=False, key=None, help='You can download the file from Garmin connect or Strava')
if tcx_file is not None:
    laps_df, points_df = get_dataframes(tcx_file)


    st.header('Uploaded file:')
    st.metric('# Waypoints', '{:,}'.format(points_df.size))
    'First 5 waypoints:'
    st.table(points_df.head())

    'Map:'

    max_lon=points_df.longitude.max()
    max_lat=points_df.latitude.max()
    min_lon=points_df.longitude.min()
    min_lat=points_df.latitude.min()
    
    max_lon
    max_lat
    min_lon
    min_lat

    max_bound = max(abs(max_lon-min_lon), abs(max_lat-min_lat)) * 111
    zoom = 12.8 - np.log(max_bound)

    fig=px.scatter_mapbox(points_df,lat='latitude', lon='longitude', zoom=zoom, hover_data={'time'})
    fig.update_layout(mapbox_style="stamen-toner")
    fig.update_traces(marker=dict(size=5))
    st.plotly_chart(fig)

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(tcx_file, 'xml')

    

    #REMOVE annoying crap
    all_speeds=soup.find_all('ns3:Speed')
    for speed in all_speeds:
        speed.decompose()
    avg_speeds=soup('ns3:AvgSpeed')
    for avg_speed in avg_speeds:
        avg_speed.decompose()
    all_distances=soup.find_all('DistanceMeters')
    for dist in all_distances:
        dist.decompose()

    #rename so strava doesnt think its a duplicate
    soup.find('Id').string.replace_with(str(random.randint(1000,10000)))

    if soup is not None:
        'Use the chart above to find where the gpx track becomes very jumpy.'
        'Find the beginning and the end of the bad areas, and record the times below.'
        'We will interpolate these areas, assuming a constant speed between the beginning and end of the segments.'

        st.metric('Start time:', (datetime.strptime(str(points_df.time.iloc[0]),'%Y-%m-%d %H:%M:%S%z')).strftime('%Y-%m-%dT%H:%M:%SZ'))
        st.metric('End time:', (datetime.strptime(str(points_df.time.iloc[-1]),'%Y-%m-%d %H:%M:%S%z')).strftime('%Y-%m-%dT%H:%M:%SZ'))
  


        'Enter times in the format'
        #error_start_time=st.text_input('Start time')
        #error_end_time=st.text_input('End time', )

        error_start_time_slider=st.select_slider('Start time', points_df.time)
        error_end_time_slider=st.select_slider('End time', points_df.time)

        error_start_time=((datetime.strptime(str(error_start_time_slider),'%Y-%m-%d %H:%M:%S%z')).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z')
        error_end_time=((datetime.strptime(str(error_end_time_slider),'%Y-%m-%d %H:%M:%S%z')).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z')

        if error_end_time is not '':
            st.metric('Start time', str(error_start_time))
            st.metric('End time', str(error_end_time))

            interpolate_trackpoints(soup,error_start_time,error_end_time)


            with open("fixed.tcx", "w") as fixed_tcx_file:
                fixed_tcx_file.write(str(soup))

                laps_df_fixed, points_df_fixed = get_dataframes("fixed.tcx")

                fig2=px.scatter_mapbox(points_df_fixed,lat='latitude', lon='longitude', zoom=zoom, hover_data={'time'})
                fig2.update_layout(mapbox_style="stamen-toner")
                fig2.update_traces(marker=dict(size=3))
                st.plotly_chart(fig2)

            with open("fixed.tcx", "r") as fixed_tcx_file:
                    st.download_button('Download fixed tcx', fixed_tcx_file, file_name='fixed.tcx')
                    print('done!')