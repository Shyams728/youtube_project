import streamlit as st
import sqlite3
import pandas as pd
from transformers import pipeline
import time
import matplotlib.pyplot as plt
import os

class YouTubeDataVisualisation:
    def __init__(self, sqlite_path):
        # Initialize connection
        self.sqlite_path = sqlite_path
        self.sqlite_connection = sqlite3.connect(self.sqlite_path)
        self.sqlite_cursor = self.sqlite_connection.cursor()

    def sql_query(self, query):
        try:
            result = pd.read_sql_query(query, self.sqlite_connection)
            return result
        except Exception as e:
            st.error(f"Error executing SQL query: {e}")
            return None

    def nlp_analysis(self, comments_result):
        data = []

        classifier = pipeline("sentiment-analysis")
        for comment in comments_result['comment_text']:
            sentiment = classifier(comment)
            data.append({"comment": comment, "sentiment": sentiment[0]['label'], "score": sentiment[0]['score']})

        st.subheader("Sentiment Analysis")
        for entry in data:
            st.write(f"Comment: {entry['comment']}")
            st.write(f"Sentiment: {entry['sentiment']}")
            st.write(f"Score: {entry['score']}")
            st.write("---")

        return data
    
    
    def close_connections(self):
        self.sqlite_connection.close()




    def create_filter_container(self):
        filter_container = st.container(border=True)
        col3, col4 = filter_container.columns([2, 4])

        # Select Channels
        channel_data_q = self.sql_query('SELECT channel_name FROM channels')['channel_name'].tolist()
        selected_channel = filter_container.multiselect('Select Channel:', sorted(channel_data_q), help='Select the Channel')

        # Construct the SQL query for selected channels
        if len(selected_channel) == 1:
            select_channels_query = f"SELECT * FROM channels WHERE channel_name == '{selected_channel[0]}'"
        elif len(selected_channel) > 1:
            selected_channels_tuple = tuple(selected_channel)
            select_channels_query = f"SELECT * FROM channels WHERE channel_name IN {selected_channels_tuple}"
        else:
            select_channels_query = 'SELECT * FROM channels'

        # Execute the query and display the data for selected channels
        data_channels = self.sql_query(select_channels_query)
        filter_container.dataframe(data_channels)

        # Select Videos based on selected channels
        if len(selected_channel) == 1:
            video_names_query = f"""
                SELECT v.video_name
                FROM videos v
                INNER JOIN channels c ON v.playlist_id = c.playlist_id
                WHERE c.channel_name == '{selected_channel[0]}'
            """
        elif len(selected_channel) > 1:
            video_names_query = f"""
                SELECT v.video_name
                FROM videos v
                INNER JOIN channels c ON v.playlist_id = c.playlist_id
                WHERE c.channel_name IN {tuple(selected_channel)}
            """
        else:
            # Handle the case when no channels are selected
            video_names_query = 'SELECT * FROM videos'

        # Execute the query and display the video names for selected channels
        video_names_q = self.sql_query(video_names_query)['video_name'].tolist()
        selected_video = filter_container.multiselect('Select video:', sorted(video_names_q), max_selections=5, help='Select the Video')

        # Construct the SQL query for selected videos
        if len(selected_video) == 1:
            select_videos_query = f"SELECT * FROM videos WHERE video_name == '{selected_video[0]}'"
        elif len(selected_video) > 1:
            selected_videos_tuple = tuple(selected_video)
            select_videos_query = f"SELECT * FROM videos WHERE video_name IN {selected_videos_tuple}"
        else:
            # Handle the case when no videos are selected
            select_videos_query = 'SELECT * FROM videos'

        # Execute the query and display the data for selected videos
        data_videos = self.sql_query(select_videos_query)
        filter_container.dataframe(data_videos)

        # Construct the SQL query for selected videos
        if len(data_videos['video_id']) == 1:
            select_comments_query = f"SELECT * FROM comments WHERE video_id == '{data_videos['video_id'][0]}'"
            comments_data = self.sql_query(select_comments_query)
        elif len(data_videos['video_id']) > 1:
            video_ids = tuple(data_videos['video_id'])
            select_comments_query = f"SELECT * FROM comments WHERE video_id IN {video_ids}"
            comments_data = self.sql_query(select_comments_query)
        else:
            # Handle the case when no videos are selected
            comments_data = None
        return comments_data


    def create_dropdown_container(self):
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
        selected_option = st.selectbox("Select SQL Query:", list(dropdown_options.keys()), index=1)
        query = dropdown_options[selected_option]
        dropdown_data = self.sql_query(query)
        return dropdown_data

