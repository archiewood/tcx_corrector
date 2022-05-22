import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import random

from tcx_decoder import get_dataframes
from interpolate_trackpoints import interpolate_trackpoints

'# TCX File Fixer'

st.write('Upload .tcx files from [Garmin](https://connect.garmin.com/modern/activities) with dodgy GPS data and fix it for Strava.')
st.write('This should also (to some extent) fix issues with erroneous pace.')

tcx_file=st.file_uploader('Upload a tcx file', type=['tcx'], accept_multiple_files=False, key=None, help='You can download the file from Garmin connect or Strava')


if tcx_file is not None:
    laps_df, points_df = get_dataframes(tcx_file)
    points_df['time_short']=(points_df.time.dt.strftime('%Y-%m-%d %H:%M:%S'))

    '## Original file'
    st.metric('# Waypoints', '{:,}'.format(points_df.size))
    'First 5 waypoints:'
    st.table(points_df.head())


    max_lon=points_df.longitude.max()
    max_lat=points_df.latitude.max()
    min_lon=points_df.longitude.min()
    min_lat=points_df.latitude.min()

    max_bound = max(abs(max_lon-min_lon), abs(max_lat-min_lat)) * 111
    zoom = 13 - np.log(max_bound)
    fig=px.scatter_mapbox(points_df,lat='latitude', lon='longitude', zoom=zoom, hover_data={'time'})
    fig.update_layout(mapbox_style="stamen-toner",margin={'b':0,'l':0,'r':0,'l':0})
    fig.update_traces(marker=dict(size=5))
    st.plotly_chart(fig)

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(tcx_file, 'xml')

    

    #Remove annoying fields that cause strava to miscalculate pace after editing
    all_speeds=soup.find_all('ns3:Speed')
    for speed in all_speeds:
        speed.decompose()
    avg_speeds=soup('ns3:AvgSpeed')
    for avg_speed in avg_speeds:
        avg_speed.decompose()
    all_distances=soup.find_all('DistanceMeters')
    for dist in all_distances:
        dist.decompose()

    '_All times are in UTC_'

    st.session_state['error_start_time_slider']=st.select_slider('Error start', points_df.time_short)
    st.session_state['error_end_time_slider']=st.select_slider('Error end', points_df.time_short)



    fig.add_trace(go.Scattermapbox(name='Error start', mode='markers',lat=points_df.latitude[0:1], lon=points_df.longitude[0:1] ,marker={'color':'green','size':30}))
    
    #rename so strava doesnt think its a duplicate
    soup.find('Id').string.replace_with(str(random.randint(1000,10000)))

    if soup is not None:

        
        '### Editing'

        'Use the chart above to find areas where the GPS track is erroneous. Record the start and end of the erroneous section with the sliders. A "constant-speed-straight-line" will be drawn between the start point and end point.'
        'Use the &larr; &rarr; keys for fine adjustments.'
    

        error_start_time=((datetime.strptime(str(st.session_state['error_start_time_slider']),'%Y-%m-%d %H:%M:%S')).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z')
        error_end_time=((datetime.strptime(str(st.session_state['error_end_time_slider']),'%Y-%m-%d %H:%M:%S')).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z')

        
        interpolate_trackpoints(soup,error_start_time,error_end_time)

        '## Edited file'

        if (st.session_state['error_end_time_slider']<=st.session_state['error_start_time_slider']):
            
            st.warning('Ensure **Error end** > **Error start** for edited output')          
        else: 


            
            with st.spinner('Processing file...'):
                with open("fixed.tcx", "w") as fixed_tcx_file:
                    fixed_tcx_file.write(str(soup))

                laps_df_fixed, points_df_fixed = get_dataframes("fixed.tcx")
                points_df_fixed['time_short']=(points_df_fixed.time.dt.strftime('%Y-%m-%d %H:%M:%S'))

                fig2=px.scatter_mapbox(points_df,lat='latitude', lon='longitude', zoom=zoom, hover_data={'time'})
                fig2.update_layout(mapbox_style="stamen-toner",margin={'b':0,'l':0,'r':0,'l':0})
                fig2.update_traces(marker=dict(size=5, opacity=1))
                fig2.data[-1].name = 'Original route'
                fig2.data[-1].showlegend = True
                fig2.update_layout(legend=dict(yanchor="top",y=0.99,xanchor="right",x=0.99, bordercolor="Black",borderwidth=0.5))

                fig2.add_trace(go.Scattermapbox(name='Edited route', mode='markers+text',lat=points_df_fixed.latitude, lon=points_df_fixed.longitude, hovertext=points_df_fixed.time ,marker={'color':'#FF4B4B','size':3}))

                #fig2.add_trace(go.Scattermapbox(name='Error start', mode='markers+text',lat=points_df_fixed.latitude[points_df_fixed.time_short==st.session_state['error_start_time_slider']], lon=points_df_fixed.longitude[points_df_fixed.time_short==error_start_time_slider] ,marker={'color':'#2ca02c','size':10}))
                #fig2.add_trace(go.Scattermapbox(name='Error end', mode='markers+text',lat=points_df_fixed.latitude[points_df_fixed.time_short==st.session_state['error_end_time_slider']], lon=points_df_fixed.longitude[points_df_fixed.time_short==error_end_time_slider] ,marker={'color':'#2ca02c','size':10}))
                st.plotly_chart(fig2)

            with open("fixed.tcx", "r") as fixed_tcx_file:
                st.download_button('Download fixed .tcx file', fixed_tcx_file, file_name='fixed.tcx')

            'Upload your fixed track [here](https://www.strava.com/upload/select)'

            '### Known Issues'
            'If you already have a version of the activity uploaded to Strava, it may not upload the new one as it thinks it is a duplicate. You can fix this by deleting the original from Strava (you can always get the original back from Garmin Connect if needed)'
 