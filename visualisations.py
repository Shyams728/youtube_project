import streamlit as st
import sqlite3
import pandas as pd
# from transformers import pipeline
import time
import matplotlib.pyplot as plt
import os
from sql_queries import (
    DROPDOWN_OPTIONS, QUERY_ALL_CHANNEL_NAMES, QUERY_SELECT_CHANNELS,
    QUERY_VIDEOS_BY_CHANNELS, QUERY_SELECT_VIDEOS, QUERY_SELECT_COMMENTS
)

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

    @st.cache_resource
    def get_classifier(_self):
        """Load and cache the sentiment analysis pipeline."""
        return pipeline("sentiment-analysis")

    def nlp_analysis(self, comments_result):
        data = []
        classifier = self.get_classifier()
        
        # Ensure we are iterating over a DataFrame column or a list
        if isinstance(comments_result, pd.DataFrame):
            comments_list = comments_result['comment_text'].tolist()
        else:
            comments_list = comments_result

        if not comments_list:
            st.warning("No comments found for analysis.")
            return []

        total = len(comments_list)
        progress_bar = st.progress(0, text="Analyzing sentiments...")
        
        for i, comment in enumerate(comments_list):
            # Truncate comment to 512 tokens approx (transformers limit) to avoid errors
            truncated_comment = str(comment)[:512] 
            sentiment = classifier(truncated_comment)
            data.append({
                "comment": comment, 
                "sentiment": sentiment[0]['label'], 
                "score": sentiment[0]['score']
            })
            progress_bar.progress((i + 1) / total)
        
        progress_bar.empty()

        st.subheader("Sentiment Analysis Results")
        # Create a summary of sentiments
        sentiments_df = pd.DataFrame(data)
        summary_counts = sentiments_df['sentiment'].value_counts()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("**Sentiment Breakdown**")
            st.dataframe(summary_counts)
        
        with col2:
            st.write("**Recent Samples**")
            for entry in data[:10]: # Show first 10
                with st.expander(f"Comment (Sentiment: {entry['sentiment']})"):
                    st.write(f"**Text:** {entry['comment']}")
                    st.write(f"**Score:** {entry['score']:.4f}")

        return data
    
    
    def close_connections(self):
        self.sqlite_connection.close()


    def create_filter_container(self):
        filter_container = st.container(border=True)
        col3, col4 = filter_container.columns([2, 4])

        # Select Channels
        channel_data_q = self.sql_query(QUERY_ALL_CHANNEL_NAMES)['channel_name'].tolist()
        selected_channel = filter_container.multiselect('Select Channel:', sorted(channel_data_q), help='Select the Channel')

        # Construct the SQL query for selected channels
        if selected_channel:
            if len(selected_channel) == 1:
                select_channels_query = f"{QUERY_SELECT_CHANNELS} WHERE channel_name = '{selected_channel[0]}'"
            else:
                select_channels_query = f"{QUERY_SELECT_CHANNELS} WHERE channel_name IN {tuple(selected_channel)}"
        else:
            select_channels_query = QUERY_SELECT_CHANNELS

        # Execute the query and display the data for selected channels
        data_channels = self.sql_query(select_channels_query)
        filter_container.dataframe(data_channels)

        if selected_channel:
            # Select Videos based on selected channels
            if len(selected_channel) == 1:
                video_names_query = QUERY_VIDEOS_BY_CHANNELS.format(f"('{selected_channel[0]}')")
            else:
                video_names_query = QUERY_VIDEOS_BY_CHANNELS.format(tuple(selected_channel))

            # Execute the query and display the video names for selected channels
            video_names_q = self.sql_query(video_names_query)['video_name'].tolist()
            selected_video = filter_container.multiselect('Select video:', sorted(video_names_q), max_selections=5, help='Select the Video')
            
            if selected_video:
                # Construct the SQL query for selected videos
                if len(selected_video) == 1:
                    select_videos_query = f"{QUERY_SELECT_VIDEOS} WHERE video_name = '{selected_video[0]}'"
                else:
                    select_videos_query = f"{QUERY_SELECT_VIDEOS} WHERE video_name IN {tuple(selected_video)}"

                # Execute the query and display the data for selected videos
                data_videos = self.sql_query(select_videos_query)
                filter_container.dataframe(data_videos)

                # Construct the SQL query for comments
                video_ids = data_videos['video_id'].tolist()
                if len(video_ids) == 1:
                    select_comments_query = f"{QUERY_SELECT_COMMENTS} WHERE video_id = '{video_ids[0]}'"
                else:
                    select_comments_query = f"{QUERY_SELECT_COMMENTS} WHERE video_id IN {tuple(video_ids)}"
                
                comments_data = self.sql_query(select_comments_query)
            else:
                comments_data = None
        else:
            comments_data = None

        return comments_data


    def create_dropdown_container(self):
        # User interface for selecting and displaying SQL queries
        selected_option = st.selectbox("Select SQL Query:", list(DROPDOWN_OPTIONS.keys()), index=1)
        query = DROPDOWN_OPTIONS[selected_option]
        dropdown_data = self.sql_query(query)
        return dropdown_data

