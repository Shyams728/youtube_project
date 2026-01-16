import streamlit as st
import sqlite3
import pandas as pd
import pymongo
import plotly.express as px
import isodate
import datetime
# from transformers import pipeline
import time
from extra_streamlit_components import tab_bar,TabBarItemData
from streamlit_shadcn_ui import table

from youtube_data import YouTubeDataPipeline
from visualisations import YouTubeDataVisualisation
from sql_queries import (
    QUERY_NUM_VIDEOS, QUERY_TOP_VIEWED_VIDEOS, QUERY_TOP_CHANNELS_SUBS, QUERY_TIMELINE,
    QUERY_KPI_TOTAL_CHANNELS, QUERY_KPI_TOTAL_VIDEOS, QUERY_KPI_TOTAL_VIEWS, 
    QUERY_KPI_TOTAL_LIKES, QUERY_KPI_TOTAL_COMMENTS, QUERY_KPI_TOTAL_SUBS,
    QUERY_ENGAGEMENT_SCATTER, QUERY_UPLOAD_SCHEDULE
)


def main():
    st.set_page_config(page_title="Youtube Dashboard",
                       page_icon=":tv:",
                       layout="wide",
                       initial_sidebar_state="expanded",)

    st.markdown("""
        <style>
            body {
                background-color: #f0f0f0; /* Light gray background */
            }
            h1 {
                color: #005b96;
                font-size: 40px;
            }
            h2 {
                color: #005b96;
                font-size: 30px;
            }
            .title {
                color: #005b96;
                font-size: 40px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("CREDENTIALS ")
    st.sidebar.markdown("---")
    credentials = st.sidebar.button('Use Default Credentials ')
    st.sidebar.markdown("---")
    if not credentials:
        st.sidebar.subheader("Youtube API ")
        # Input API key and channel ID
        api_key = st.sidebar.text_input("Enter your YouTube API key:", type='password')
        st.sidebar.markdown("---")

        # MongoDB options
        st.sidebar.subheader("MongoDB API")
        mongodb_connection_string = st.sidebar.text_input("Enter MongoDB API:", type='password')
        mongodb_database = st.sidebar.text_input("Enter MongoDB database name:", "moonwalker")
        mongodb_collection = st.sidebar.text_input("Enter MongoDB collection name:", "youtube_data")
        st.sidebar.markdown("---")
    else:
        # Access environment variables
        mongodb_connection_string = st.secrets["MONGODB_URI"]
        # mongodb_connection_string = mongodb_connection.replace("'", "")
        api_key = st.secrets["API_KEY"]
        mongodb_database = st.secrets["mongodb_database"]
        mongodb_collection = st.secrets["mongodb_collection"]

    # SQLite path
    sqlite_path = 'youtube_data.sqlite'

    # Instantiate the YouTubeDataVisualisation class
    visualise = YouTubeDataVisualisation(sqlite_path)

    st.title('YouTube Dashboard')

    selected_tab = tab_bar(data=[
    TabBarItemData(id='Main', title="Main", description="About the project and input"),
    TabBarItemData(id='Dashboard', title="Dashboard", description="KPIs & Analytics"),
    TabBarItemData(id= 'Tables', title="Tables", description="view the data"),
    TabBarItemData(id='Visualisation', title="Visualisation", description="Overview "),
    TabBarItemData(id='NLP Analysis', title="NLP Analysis", description="translation and sentiment of the comments"),], default='Main')
    # st.info(f"{selected_tab=}")

    if selected_tab == 'Main':

        st.markdown("""
            <div style="background-color: #d8e2dc; padding: 10px; border-radius: 5px;">
                <p style="font-size: 16px; color: #005b96;"><strong>YouTube Data Dashboard:</strong> A comprehensive system designed to gather valuable insights from YouTube. 
                The project employs a multi-step process that begins with extracting pertinent information from YouTube using a designated API key. 
                The extracted data is then stored in a MongoDB cloud server, functioning as a data lake for efficient and secure data management.
                Prior to being stored in MongoDB, the raw data undergoes preprocessing steps to ensure its quality and coherence. Subsequently, the processed data is also stored in a SQLite database, 
                facilitating structured querying and retrieval of specific information.
                The project incorporates various functionalities to enhance user interaction and exploration of the YouTube data. 
                These include the ability to input a YouTube channel ID, triggering the execution of a comprehensive data pipeline. 
                This pipeline collects channel-related data, video details, and comments, offering a holistic view of the YouTube presence.
                Furthermore, the project features a user-friendly interface with tabs for distinct functionalities, such as displaying tables, 
                charts, visualizations, and conducting NLP (Natural Language Processing) analysis on comments. 
                Users can execute SQL queries to retrieve specific datasets and visualize the data through informative charts and graphs.
                In summary, the YouTube Data Dashboard provides a centralized hub for users to effortlessly navigate and analyze YouTube data, 
                leveraging MongoDB, SQLite, and advanced NLP techniques for a comprehensive and insightful user experience.</p>
            </div>
            """,
            unsafe_allow_html=True)



        st.markdown("---")
        # Get channel ID from user input
        channel_ids = st.text_area("Enter YouTube channel IDs (comma-separated):")

        show_info = st.button("Display Data")


        # If channel IDs are provided
        if channel_ids or show_info:
            channel_ids = [channel_id.strip() for channel_id in channel_ids.split(",")]

            # Create a single info_box for all channels
            info_box = st.container(border=True)
            info_box.subheader("Channel Information")

            
            for channel_id in channel_ids:
                # If channel IDs are provided, execute the pipeline
                data_box = info_box.container(border=True)  
                col1, col2 = data_box.columns([4, 2])

                if channel_id:
                    # Instantiate the YouTubeDataPipeline class
                    youtube_pipeline = YouTubeDataPipeline(api_key, sqlite_path, mongodb_connection_string, mongodb_database, mongodb_collection)

                    # Get and display channel information
                    channel_info = youtube_pipeline.get_channel_info(channel_id)

                    col1.write(f"**Channel Name:** {channel_info['Channel_Name']}")
                    col1.write(f"**Channel ID:** {channel_info['Channel_ID']}")
                    data_box.write(f"**Description:** {channel_info['Channel_Description']}")
                    col2.write(f"**Subscribers:** {channel_info['Subscription_Count']}")
                    col2.write(f"**Views:** {channel_info['Channel_Views']}")
                    # Execute the pipeline
                    button_save_data = info_box.button(f"Save Data of {channel_info['Channel_Name']} Channel", key=f"save_data_{channel_id}")
                    info_box.write('\n\n')
                    if button_save_data:
                        progress_bar = st.progress(0, text="Starting pipeline...")
                        
                        # 1. Channel Pipeline
                        progress_bar.progress(10, text="Executing Channel Pipeline...")
                        youtube_pipeline.run_channel_pipeline(channel_id)
                        
                        # 2. Videos Pipeline
                        progress_bar.progress(40, text="Executing Videos Pipeline (this may take a while)...")
                        youtube_pipeline.run_videos_pipeline(channel_id)
                        
                        # 3. Comments Pipeline
                        progress_bar.progress(70, text="Executing Comments Pipeline...")
                        youtube_pipeline.run_comments_pipeline(channel_id)
                        
                        progress_bar.progress(100, text="Pipeline execution complete!")
                        time.sleep(1) # Brief pause for user to see 100%
                        progress_bar.empty()

                        st.success(f"Data for {channel_info['Channel_Name']} has been successfully processed and saved.")

                        st.markdown(""" **Pipeline involved the following steps:**  
                                        - Extracting data from YouTube  
                                        - Preprocessing data  
                                        - Storing data in MongoDB (Data Lake) 
                                        - Querying data from MongoDB  
                                        - Creating tables using SQL  
                                        - Storing data in SQLite Database""")


                    
                    # Close the connections when done with the current channel
                    youtube_pipeline.close_connections()

        else:
            # If no channel ID is provided, clear the screen
            st.empty()

    elif selected_tab == 'Dashboard':
        st.header("KPIs & Analytics")

        # --- Row 1: KPI Cards ---
        st.subheader("High-Level Metrics")
        
        col1, col2, col3, col4 = st.columns(4)

        total_channels = visualise.sql_query(QUERY_KPI_TOTAL_CHANNELS).iloc[0, 0]
        total_videos = visualise.sql_query(QUERY_KPI_TOTAL_VIDEOS).iloc[0, 0]
        total_subs = visualise.sql_query(QUERY_KPI_TOTAL_SUBS).iloc[0, 0]
        total_views = visualise.sql_query(QUERY_KPI_TOTAL_VIEWS).iloc[0, 0]
        
        with col1:
            st.metric(label="Total Channels", value=total_channels)
        with col2:
            st.metric(label="Total Subscribers", value=f"{total_subs:,}")
        with col3:
            st.metric(label="Total Videos", value=f"{total_videos:,}")
        with col4:
            st.metric(label="Total Views", value=f"{total_views:,}")
        
        st.markdown("---")
        col5, col6 = st.columns(2)
        total_likes = visualise.sql_query(QUERY_KPI_TOTAL_LIKES).iloc[0, 0]
        total_comments = visualise.sql_query(QUERY_KPI_TOTAL_COMMENTS).iloc[0, 0]
        
        with col5:
             st.metric(label="Total Likes", value=f"{total_likes:,}")
        with col6:
             st.metric(label="Total Comments", value=f"{total_comments:,}")

        st.markdown("---")

        # --- Row 2: Analytics ---
        st.subheader("Data Analytics")

        # Scatter Plot
        engagement_data = visualise.sql_query(QUERY_ENGAGEMENT_SCATTER)
        if not engagement_data.empty:
            fig_scatter = px.scatter(
                engagement_data, 
                x="view_count", 
                y="like_count", 
                color="channel_name",
                hover_data=['video_name', 'comment_count'],
                title="Correlation: Views vs Likes",
                labels={"view_count": "Views", "like_count": "Likes"}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Additional Chart: Engagement Rate (Likes + Comments) / Views
            # Avoid division by zero
            engagement_data['engagement_rate'] = ((engagement_data['like_count'] + engagement_data['comment_count']) / engagement_data['view_count']) * 100
            
            # Avg Engagement Rate per Channel
            avg_eng_rate = engagement_data.groupby('channel_name')['engagement_rate'].mean().reset_index()
            
            fig_bar = px.bar(
                avg_eng_rate, 
                x='channel_name', 
                y='engagement_rate', 
                color='channel_name',
                title="Average Engagement Rate per Channel (%)",
                labels={"channel_name": "Channel", "engagement_rate": "Avg Engagement Rate (%)"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)


        # Upload Schedule
        schedule_data = visualise.sql_query(QUERY_UPLOAD_SCHEDULE)
        if not schedule_data.empty:
            # Map day numbers to names
            day_map = {'0': 'Sunday', '1': 'Monday', '2': 'Tuesday', '3': 'Wednesday', '4': 'Thursday', '5': 'Friday', '6': 'Saturday'}
            schedule_data['day_name'] = schedule_data['day_of_week'].map(day_map)
            
            fig_schedule = px.bar(
                schedule_data, 
                x='day_name', 
                y='num_videos',
                title="Upload Frequency by Day of Week",
                labels={"day_name": "Day of Week", "num_videos": "Number of Uploads"},
                category_orders={"day_name": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}
            )
            st.plotly_chart(fig_schedule, use_container_width=True)


    if selected_tab == 'Tables':
        a, b = st.tabs(["Predefined SQL queries charts", "SQL query"])

        with b:
            # SQL query
            query = st.text_input("Enter SQL Query for Channels:", "SELECT * FROM channels")
            channel_data_result = visualise.sql_query(query)
            # Display the full channel data
            st.dataframe(channel_data_result)  # Use st.dataframe to display a DataFrame

        with a:
            
            container_view = st.container(border=True)
            col1, col2 = container_view.columns([6, 2])
            with col1:
                dropdown_data = visualise.create_dropdown_container()
            with col2:
                container_toggle = st.container(border=True)
                container_toggle.write('\n')
                filter_data = container_toggle.toggle('Filter data')

            if filter_data:
                comments_data = visualise.create_filter_container()
                st.dataframe(comments_data)
            else:
                # Display the results of the selected predefined query
                table(data=dropdown_data, maxHeight=1000, key="dropdown_data")
                # st.dataframe(dropdown_data,use_container_width=True)


    elif selected_tab == 'Visualisation':
        st.set_option('deprecation.showPyplotGlobalUse', False)


        # Bar chart for the number of videos for each channel
        result_num_videos = visualise.sql_query(QUERY_NUM_VIDEOS)
        st.title('Top chart for the number of videos for each channel')

        display_result_top_channels = st.container(border=True)
        df_col, charts_col = display_result_top_channels.columns([1, 3])

        with df_col:
            table(data=result_num_videos, maxHeight=500, key="result_num_videos")

        with charts_col:
            # Create a bar chart using Plotly Express
            fig = px.bar(result_num_videos, x='num_videos', y='channel_name',  # Swap x and y to have the channel names on the y-axis
                        labels={'channel_name': 'Channel Name', 'num_videos': 'Number of Videos'},
                        title='Number of Videos for Each Channel',
                        orientation='h',  # Horizontal bar chart
                        color='num_videos',  # Color the bars based on the number of videos
                        color_continuous_scale=px.colors.sequential.Viridis,  # Choose a color scale
                        text='num_videos')  # Add the number of videos as text on the bars

            # Display the chart in Streamlit
            st.plotly_chart(fig)



        #88888888888888888888888888'Top 10 most viewed videos'8888888888888888888888888888888888888

        # Top 10 most viewed videos
        result_top_viewed_videos = visualise.sql_query(QUERY_TOP_VIEWED_VIDEOS)

        display_result_top_viewed_videos = st.container(border=True)
        

        with display_result_top_viewed_videos: 
            # Plotly bar chart
            # Create a bar chart using Plotly Express
            fig = px.bar(result_top_viewed_videos, y='video_name', x='view_count',  # Swap x and y to have the video names on the y-axis
                        labels={'video_name': 'Video Name', 'view_count': 'View Count'},
                        title='Top 10 Most Viewed Videos',
                        orientation='h',  # Horizontal bar chart
                        color='view_count',  # Color the bars based on the view count
                        color_continuous_scale=px.colors.sequential.Plasma,  # Choose a sequential color scale
                        text='view_count')  # Add the view count as text on the bars


            # Display the chart in Streamlit
            st.plotly_chart(fig, use_container_width=True)

#*********************************** Top 10 channels by subscription count ***********************
        # Top 10 channels by subscription count
        result_top_channels = visualise.sql_query(QUERY_TOP_CHANNELS_SUBS)

        display_box_df_charts = st.container(border=True)
        df_col, charts_col = display_box_df_charts.columns([2, 3])

        with df_col:
            table(data=result_top_channels, maxHeight=500, key="result_top_channels")

        with charts_col:
            # Plotly pie chart
            # Create a bar chart using Plotly Express
            # Create a pie chart using Plotly Express
            fig = px.pie(result_top_channels, names='channel_name', values='subscription_count',
                        labels={'channel_name': 'Channel Name', 'subscription_count': 'Subscription Count'},
                        title='Top 10 Channels by Subscription Count',
                        hole=0.4,  # This creates a donut-like pie chart with a hole in the center
                        color_discrete_sequence=px.colors.sequential.Viridis)  # Choose a color sequence

            # Customize the layout to make the chart more readable
            fig.update_layout(
                title_x=0.5,  # Center the title
                showlegend=True,  # show the legend
                plot_bgcolor='white',  # Set the background color to white
                font=dict(size=12),  # Set the font size
                annotations=[dict(text='Channels', x=0.5, y=0.5, font_size=20, showarrow=False)]  # Add a text annotation in the center
            )

            # Display the chart in Streamlit
            st.plotly_chart(fig, use_container_width=True)

#*******************************************timeline line chart************************************
        
        # Timeline chart for videos published in 2022
        result_timeline = visualise.sql_query(QUERY_TIMELINE)

        display_result_timeline = st.container(border=True)

        timeline_data = result_timeline.groupby('month_published').size().reset_index(name='num_videos')

        # Create a timeline chart using Plotly Express
        fig = px.line(timeline_data, x='month_published', y='num_videos',
                    labels={'month_published': 'Month Published', 'num_videos': 'Number of Videos'},
                    title='Overall Month-wise Timeline of Videos Published',
                    markers=True)  # Add markers to the line to indicate the data points


        # Display the chart in Streamlit
        display_result_timeline.plotly_chart(fig, use_container_width=True)



    # NLP Analysis tab
    elif selected_tab == 'NLP Analysis':

        st.subheader("Query Selection and Analysis")

        # Radio buttons for selecting query type
        query_type = st.radio(
            "Select type of query",
            ["***Filter data***", "***Enter SQL Query for Comments***"],
            captions = ["By using selection.", " Write the SQL Quary",],
            horizontal= True ,
            index=1  # Default selection index
        )
        
        comments_result = None

        if query_type == "***Filter data***":
            st.write("You selected Filter data.")
            comments_result = visualise.create_filter_container()
            if comments_result is not None:
                st.dataframe(comments_result)
            

        elif query_type == "***Enter SQL Query for Comments***":
            # NLP analysis on comments
            comments_query = st.text_input("Enter SQL Query for Comments", "SELECT * FROM comments WHERE video_id = 'E-RJbdTJX-4'")
            # Integrate sentiment analysis using transformers pipeline
            comments_result = visualise.sql_query(comments_query)
            if comments_result is not None:
                st.dataframe(comments_result)
        else:
            st.write("You didn't select any Query.")

        analyse = st.button('Analyse the Sentiment of the selected comments')

        if analyse and comments_result is not None and not comments_result.empty:
            # Perform sentiment analysis
            visualise.nlp_analysis(comments_result)
            st.success("Sentiments Analysis Completed.")
        elif analyse:
            st.warning("Please select valid comments to analyse.")

    # Close connections
    visualise.close_connections()

# Run the main script
if __name__ == "__main__":
    main()
  
