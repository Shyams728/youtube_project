import streamlit as st
import sqlite3
import pandas as pd
import pymongo
import plotly.express as px
import isodate
import datetime
from transformers import pipeline
import time
from extra_streamlit_components import tab_bar,TabBarItemData
from streamlit_shadcn_ui import table

from youtube_data import YouTubeDataPipeline
from visualisations import YouTubeDataVisualisation

def main():
    st.set_page_config(page_title="Youtube Dashboard",
                       page_icon=":tv:",
                       layout="wide",
                       initial_sidebar_state="expanded",)

    # st.markdown("""
    #     <style>
    #         body {
    #             background-color: #f0f0f0; /* Light gray background */
    #         }
    #         h1 {
    #             color: #005b96;
    #             font-size: 40px;
    #         }
    #         h2 {
    #             color: #005b96;
    #             font-size: 30px;
    #         }
    #         .title {
    #             color: #005b96;
    #             font-size: 40px;
    #         }
    #     </style>
    # """, unsafe_allow_html=True)


    st.sidebar.title("CREDENTIALS ")
    st.sidebar.markdown("---")

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

    # SQLite path
    sqlite_path = 'youtube_data.sqlite'

    # Instantiate the YouTubeDataVisualisation class
    visualise = YouTubeDataVisualisation(sqlite_path)

    st.markdown('<p class="title">YouTube Dashboard</p>', unsafe_allow_html=True)

    selected_tab = tab_bar(data=[
    TabBarItemData(id='Main', title="Main", description="About the project and input"),
    TabBarItemData(id= 'Tables', title="Tables", description="view the data"),
    TabBarItemData(id='Visualisation', title="Visualisation", description="Some charts "),
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

        # If channel IDs are provided
        if channel_ids:
            channel_ids = [channel_id.strip() for channel_id in channel_ids.split(",")]

            # Create a single info_box for all channels
            info_box = st.container(border=True)
            info_box.subheader("Channel Information")
            data_box = info_box.container(border=True)
            description_box = info_box.container(border=True)
            col1, col2 = data_box.columns([4, 2])

            for channel_id in channel_ids:
                # If channel IDs are provided, execute the pipeline
                if channel_id:
                    # Instantiate the YouTubeDataPipeline class
                    youtube_pipeline = YouTubeDataPipeline(api_key, sqlite_path, mongodb_connection_string, mongodb_database, mongodb_collection)

                    # Get and display channel information
                    channel_info = youtube_pipeline.get_channel_info(channel_id)

                    col1.write(f"**Channel Name:** {channel_info['Channel_Name']}")
                    col1.write(f"**Channel ID:** {channel_info['Channel_ID']}")
                    col1.markdown('___')
                    description_box.write(f"**Description:** {channel_info['Channel_Description']}")
                    description_box.markdown('___')
                    col2.write(f"**Subscribers:** {channel_info['Subscription_Count']}")
                    col2.write(f"**Views:** {channel_info['Channel_Views']}")
                    col2.markdown('___')
                    # Execute the pipeline
                    button_save_data = info_box.button(f"Save Data of {channel_info['Channel_Name']}", key=f"save_data_{channel_id}")
                    
                    if button_save_data:
                        with st.spinner("Executing pipeline..."):
                            time.sleep(2)  # Simulating pipeline execution time
                            youtube_pipeline.run_channel_pipeline(channel_id)
                            youtube_pipeline.run_videos_pipeline(channel_id)
                            youtube_pipeline.run_comments_pipeline(channel_id)

                        st.markdown(""" **Pipeline involves the following steps:**
                                    1. Extracting data from YouTube
                                    2. Preprocessing data
                                    3. Storing data in MongoDB
                                    4. Querying data from MongoDB
                                    5. Creating tables in SQL
                                    6. Storing data in SQL""")

                    # Close the connections when done with the current channel
                    youtube_pipeline.close_connections()

        else:
            # If no channel ID is provided, clear the screen
            st.empty()


    # Tables tab
    if selected_tab == 'Tables':


        a,b = st.tabs( ["Predefined SQL queries","SQL query"])

        with b:
            #SQL query     
            query = st.text_input("Enter SQL Query for Channels:", "SELECT * FROM channels")
            channel_data_result = visualise.sql_query(query)
            # Display the full channel data 
            st.write("Channel Data:", channel_data_result)

        with a:

            drop_down_box = st.container(border=True)
            col1, col2 = drop_down_box.columns([6, 1])

            with col1:
                # Create tabs
                    
                # Define SQL queries
                dropdown_options = {
                    "What are the names of all the videos and their corresponding channels?":
                        """SELECT v.video_name, c.channel_name
                        FROM videos v
                        INNER JOIN channels c ON v.playlist_id = c.playlist_id;
                        """,

                    "Which channels have the most number of videos, and how many videos do they have?":
                        """SELECT c.channel_name, COUNT(*) AS num_videos
                        FROM channels c
                        INNER JOIN videos v ON v.playlist_id = c.playlist_id
                        GROUP BY c.channel_name
                        ORDER BY num_videos DESC;
                        """,

                    "What are the top 10 most viewed videos and their respective channels?":
                        """SELECT v.video_name, c.channel_name, v.view_count
                        FROM videos v
                        INNER JOIN channels c ON v.playlist_id = c.playlist_id
                        ORDER BY v.view_count DESC
                        LIMIT 10;""",

                    "How many comments were made on each video, and what are their corresponding video names?":    
                        """SELECT v.video_name, COUNT(*) AS num_comments 
                        FROM videos v INNER JOIN comments c ON v.video_id = c.video_id 
                        GROUP BY v.video_name;""",

                    "Which videos have the highest number of likes, and what are their corresponding channel names?" :    
                        """SELECT v.video_name, c.channel_name, v.like_count 
                        FROM videos v INNER JOIN channels c ON v.playlist_id = c.playlist_id 
                        ORDER BY v.like_count DESC 
                        LIMIT 10;""",

                    "What is the total number of views for each channel, and what are their corresponding channel names?" :    
                        """SELECT c.channel_name, SUM(v.view_count) AS total_views 
                        FROM channels c INNER JOIN videos v ON v.playlist_id = c.playlist_id 
                        GROUP BY c.channel_name;""",

                    "What are the names of all the channels that have published videos in the year 2022?" :    
                        """
                        SELECT c.channel_name FROM channels c 
                        INNER JOIN videos v ON v.playlist_id = c.playlist_id 
                        WHERE v.published_at BETWEEN '2022-01-01 00:0000' AND '2022-12-31 00:00:00';
                            """,

                        "What is the average duration of all videos in each channel, and what are their corresponding channel names?":    
                            """SELECT c.channel_name, AVG(v.duration) AS average_duration 
                            FROM channels c INNER JOIN videos v ON v.playlist_id = c.playlist_id 
                            GROUP BY c.channel_name;""",

                        "Which videos have the highest number of comments, and what are their corresponding channel names?" :    
                            """SELECT v.video_name, c2.channel_name, COUNT(*) AS num_comments 
                            FROM videos v INNER JOIN comments c ON v.video_id = c.video_id INNER JOIN channels c2 ON v.playlist_id = c2.playlist_id 
                            GROUP BY v.video_name, c2.channel_name;""",

                    }


                # User interface for selecting and displaying SQL queries
                selected_option = st.selectbox("Select SQL Query:", list(dropdown_options.keys()))
                query = dropdown_options[selected_option]
                
                    
            with col2:
                st.write('\n')
                show_data = st.button("Display SQL Data")

            if show_data:

                query_result = visualise.sql_query(query)
                st.subheader(f'Displaying Data For \n {selected_option}')
                st.dataframe(query_result,use_container_width=True)



    elif selected_tab == 'Visualisation':
        st.set_option('deprecation.showPyplotGlobalUse', False)

        # Top 5 channels by subscription count
        query_top_channels = """
        SELECT channel_name, subscription_count
        FROM channels
        ORDER BY subscription_count DESC
        LIMIT 10
        """
        result_top_channels = visualise.sql_query(query_top_channels)
        st.title('Top 10 channels by subscription count')

        display_box_df_charts = st.container(border=True)
        df_col, charts_col = display_box_df_charts.columns([1, 3])

        with df_col:
            table(data=result_top_channels, maxHeight=500, key="result_top_channels")

        with charts_col:
            # Plotly pie chart
            fig = px.pie(result_top_channels, names='channel_name', values='subscription_count',
                        labels={'channel_name': 'Channel Name', 'subscription_count': 'Subscription Count'},
                        title='Top 5 Channels by Subscription Count')
            # Display the chart
            st.plotly_chart(fig)

        # Bar chart for the number of videos for each channel
        query_num_videos = """
        SELECT c.channel_name, COUNT(*) AS num_videos
        FROM channels c
        INNER JOIN videos v ON v.playlist_id = c.playlist_id
        GROUP BY c.channel_name
        ORDER BY num_videos DESC
        LIMIT 10;
        """
        result_num_videos = visualise.sql_query(query_num_videos)
        st.title('Top chart for the number of videos for each channel')

        display_result_top_channels = st.container(border=True)
        df_col, charts_col = display_result_top_channels.columns([1, 3])

        with df_col:
            table(data=result_num_videos, maxHeight=500, key="result_num_videos")

        with charts_col:
            # Plotly bar chart
            fig = px.bar(result_num_videos, x='channel_name', y='num_videos',
                        labels={'channel_name': 'Channel Name', 'num_videos': 'Number of Videos'},
                        title='Number of Videos for Each Channel')

            # Display the chart
            st.plotly_chart(fig)

        # Top 10 most viewed videos
        query_top_viewed_videos = """
        SELECT v.video_name, c.channel_name, v.view_count
        FROM videos v
        INNER JOIN channels c ON v.playlist_id = c.playlist_id
        ORDER BY v.view_count DESC
        LIMIT 10;
        """
        result_top_viewed_videos = visualise.sql_query(query_top_viewed_videos)
        st.title('Top 10 most viewed videos')

        display_result_top_viewed_videos = st.container(border=True)
        

        with display_result_top_viewed_videos: 
            # Plotly bar chart
            fig = px.bar(result_top_viewed_videos, y='video_name', x='view_count',orientation= 'h',
                        labels={'video_name': 'Video Name', 'view_count': 'View Count'},
                        title='Top 10 Most Viewed Videos')


            # Display the chart
            st.plotly_chart(fig,theme="streamlit", use_container_width=True)

        # Timeline chart for videos published in 2022
        query_timeline = """
        SELECT c.channel_name, strftime('%Y-%m', v.published_at) as month_published
        FROM channels c 
        INNER JOIN videos v ON v.playlist_id = c.playlist_id 
        WHERE v.published_at BETWEEN '2023-01-01 00:00:00' AND '2023-12-31 00:00:00';
        """
        result_timeline = visualise.sql_query(query_timeline)
        st.title('Timeline chart for videos published in 2022')

        display_result_timeline = st.container(border=True)
        df_col, charts_col = display_result_timeline.columns([1, 3])

        with df_col:
            table(data=result_timeline.head(10), maxHeight=500, key="result_timeline")

        with charts_col: 
            timeline_data = result_timeline.groupby('month_published').size().reset_index(name='num_videos')

            # Plotly timeline chart
            fig = px.line(timeline_data, x='month_published', y='num_videos',
                        labels={'month_published': 'Month Published', 'num_videos': 'Number of Videos'},
                        title='Month-wise Timeline of Videos Published in 2023')

            # Display the chart
            st.plotly_chart(fig)



    # NLP Analysis tab
    elif selected_tab == 'NLP Analysis':
        # NLP analysis on comments
        comments_query = st.text_input("Enter SQL Query for Comments:", "SELECT * FROM comments where video_id = 'E-RJbdTJX-4'")
        # Integrate sentiment analysis using transformers pipeline
        comments_result = visualise.sql_query(comments_query)

        visualise.nlp_analysis(comments_result)
        st.success("Sentiments Analysis Completed.")

    # Close connections
    visualise.close_connections()

# Run the main script
if __name__ == "__main__":
    main()
