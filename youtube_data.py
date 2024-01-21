import streamlit as st
import sqlite3
import pandas as pd
import pymongo
from googleapiclient.discovery import build
import isodate
import datetime
import time
import matplotlib.pyplot as plt
import os


class YouTubeDataPipeline:
    def __init__(self, api_key, sqlite_path, mongodb_connection_string, mongodb_database, mongodb_collection):
        # Initialize connections
        self.api_key = api_key
        self.sqlite_path = sqlite_path
        self.mongodb_connection_string = mongodb_connection_string
        self.mongodb_database = mongodb_database
        self.mongodb_collection_name = mongodb_collection
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.sqlite_connection = sqlite3.connect(self.sqlite_path)
        self.sqlite_cursor = self.sqlite_connection.cursor()
        self.mongodb_client = pymongo.MongoClient(self.mongodb_connection_string)
        self.mongodb_db = self.mongodb_client[self.mongodb_database]
        self.mongodb_collection = self.mongodb_db[self.mongodb_collection_name]

    # Generic function to make YouTube API requests
    def make_youtube_api_request(self, api_function, **kwargs):
        try:
            response = api_function.execute(**kwargs)
            return response
        except Exception as e:
            print(f"Error making YouTube API request: {e}")
            return None

    def get_channel_info(self, channel_id):
        api_function = self.youtube.channels().list(
            part="snippet,statistics,contentDetails", id=channel_id)
        channel_response = self.make_youtube_api_request(api_function)

        if channel_response:
            channel_information = {
                "Channel_Name": channel_response["items"][0]["snippet"]["title"],
                "Channel_ID": channel_id,
                "Subscription_Count": channel_response["items"][0]["statistics"].get("subscriberCount", "Not Available"),
                "Channel_Views": channel_response["items"][0]["statistics"].get("viewCount", "Not Available"),
                "Channel_Description": channel_response["items"][0]["snippet"].get("description", "Not Available"),
                "Playlist_ID": channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"],
            }
            return channel_information
        else:
            return None

    def get_video_ids(self, channel_id):
        api_function = self.youtube.channels().list(part="contentDetails", id=channel_id)
        channel_response = self.make_youtube_api_request(api_function)

        if channel_response:
            playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            api_function = self.youtube.playlistItems().list(
                part="contentDetails", playlistId=playlist_id, maxResults=50)
            response = self.make_youtube_api_request(api_function)

            if response:
                video_ids = [item["contentDetails"]["videoId"] for item in response.get("items", [])]
                next_page_token = response.get("nextPageToken")
                more_pages = True

                while next_page_token and more_pages:
                    api_function = self.youtube.playlistItems().list(
                        part="contentDetails",
                        playlistId=playlist_id,
                        maxResults=50,
                        pageToken=next_page_token,
                    )
                    response = self.make_youtube_api_request(api_function)

                    if response:
                        video_ids.extend(
                            [data["contentDetails"]["videoId"] for data in response.get("items", [])]
                        )
                        next_page_token = response.get("nextPageToken")
                    else:
                        more_pages = False

                return video_ids
        return []

    def get_videos_info(self, channel_id):
        channel_response = self.youtube.channels().list(part="snippet,statistics,contentDetails", id=channel_id).execute()
        playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        all_video_info = []

        for video_id in self.get_video_ids(channel_id):
            api_function = self.youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=video_id,
            )
            video_details = self.make_youtube_api_request(api_function)

            if video_details:
                try:
                    # Extract video details and handle missing fields
                    video_information = {
                        "Channel_ID": channel_id,
                        "Video_ID": video_id,
                        "Video_Name": video_details["items"][0]["snippet"]["title"],
                        "Video_Description": video_details["items"][0]["snippet"].get("description", "Not Available"),
                        "Tags": video_details["items"][0]["snippet"].get("tags", "Not Available"),
                        "Published_At": datetime.datetime.strptime(
                            video_details["items"][0]["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ"
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                        "View_Count": int(video_details["items"][0]["statistics"].get("viewCount", 0)),
                        "Like_Count": int(video_details["items"][0]["statistics"].get("likeCount", 0)),
                        "Dislike_Count": int(video_details["items"][0]["statistics"].get("dislikeCount", 0)),
                        "Favorite_Count": int(video_details["items"][0]["statistics"].get("favoriteCount", 0)),
                        "Comment_Count": int(video_details["items"][0]["statistics"].get("commentCount", 0)),
                        "Duration": isodate.parse_duration(video_details["items"][0]["contentDetails"]["duration"]).total_seconds(),
                        "Caption": bool(video_details["items"][0]["contentDetails"].get("caption", False)),
                        "Thumbnail": video_details["items"][0]["snippet"]["thumbnails"]["default"]["url"],
                        "Playlist_ID": playlist_id,
                    }
                    all_video_info.append(video_information)
                except KeyError as e:
                    print(f"Error processing video {video_id}: {e}")
                    continue

        return all_video_info

    def get_comments_info(self, channel_id):
        comment_info = []

        for video_id in self.get_video_ids(channel_id):
            api_function = self.youtube.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=50
            )
            comment_response = self.make_youtube_api_request(api_function)

            if comment_response:
                for item in comment_response.get("items", []):
                    comment_id = item["snippet"]["topLevelComment"]["id"]
                    comment_details = item["snippet"]["topLevelComment"]

                    comments_information = {
                        "Video_ID": video_id,
                        "Comment_ID": comment_id,
                        "Comment_Text": comment_details["snippet"]["textDisplay"],
                        "Comment_Author": comment_details["snippet"]["authorDisplayName"],
                        "Comment_Published_At": datetime.datetime.strptime(
                            comment_details["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ"
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    comment_info.append(comments_information)

        return comment_info


    def mongodb_channel_data(self, channel_id):

        # Define the criteria for filtering the documents
        criteria = {
            "Channel_ID": f"{channel_id}",
            "Playlist_ID": {"$ne": None},
            "Channel_Name": {"$ne": None},
        }

        try:
            # Retrieve channel data from MongoDB
            channel_data = self.mongodb_collection.find_one(criteria, {"_id": 0})

        except Exception as ex:
            print("An error occurred:", ex)

        return channel_data

    def mongodb_videos_data(self, channel_id):
        
        find_id = f"SELECT playlist_id FROM channels WHERE channel_id = '{channel_id}'"
        self.sqlite_cursor.execute(find_id)
        playlist_id = self.sqlite_cursor.fetchone()[0]

        # Define the criteria for filtering the documents
        criteria = {
            "Playlist_ID": f"{playlist_id}",
            "Video_ID": {"$ne": None},
            "Video_Name": {"$ne": None},
            "Video_Description": {"$ne": None},
        }

        try:
            # Retrieve video data from MongoDB
            video_data = list(self.mongodb_collection.find(criteria, {"_id": 0}))

        except Exception as ex:
            print("An error occurred:", ex)

        return video_data

    def mongodb_comments_data(self, channel_id):
        
        find_id = f"SELECT playlist_id FROM channels WHERE channel_id = '{channel_id}'"
        self.sqlite_cursor.execute(find_id)
        playlist_id = self.sqlite_cursor.fetchone()[0]
        
        find_id = f"SELECT video_id FROM videos WHERE playlist_id = '{playlist_id}'"
        self.sqlite_cursor.execute(find_id)
        video_ids = [video[0] for video in self.sqlite_cursor.fetchall()]

        # Define the criteria for filtering the documents
        criteria = {
            "Video_ID": {"$in": video_ids},
            "Comment_ID": {"$ne": None},
        }

        try:
            # Retrieve comment data from MongoDB
            comment_data = list(self.mongodb_collection.find(criteria, {"_id": 0}))

        except Exception as ex:
            print("An error occurred:", ex)

        return comment_data



    def insert_channel_data(self, document, sqlite_cursor):
        query = """
            INSERT INTO channels (
                channel_id, channel_name, subscription_count, channel_views,
                channel_description, playlist_id
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        values = (
            document["Channel_ID"],
            document["Channel_Name"],
            document["Subscription_Count"],
            document["Channel_Views"],
            document["Channel_Description"],
            document["Playlist_ID"],
        )
        sqlite_cursor.execute(query, values)

    def insert_video_data(self, document, table_name, sqlite_cursor):
        query = f"""
            INSERT INTO {table_name} (
                video_id, video_name, video_description, tags,
                published_at, view_count, like_count, favorite_count,
                comment_count, duration, caption, thumbnail, playlist_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            document["Video_ID"],
            document["Video_Name"],
            document["Video_Description"],
            ', '.join(document["Tags"]),
            document["Published_At"],
            document["View_Count"],
            document["Like_Count"],
            document["Favorite_Count"],
            document["Comment_Count"],
            document["Duration"],
            document["Caption"],
            document["Thumbnail"],
            document["Playlist_ID"],
        )
        sqlite_cursor.execute(query, values)

    def insert_comments_data(self, document, sqlite_cursor):
        query = """
            INSERT INTO comments (
                comment_Id, video_id, comment_text,
                comment_author, comment_published_date
            ) VALUES (?, ?, ?, ?, ?)
        """
        values = (
            document["Comment_ID"],
            document["Video_ID"],
            document["Comment_Text"],
            document["Comment_Author"],
            document["Comment_Published_At"],
        )
        sqlite_cursor.execute(query, values)

    def create_table_channels(self, sqlite_cursor):
        sqlite_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS channels (
                channel_id TEXT PRIMARY KEY,
                channel_name TEXT,
                subscription_count INT,
                channel_views TEXT,
                channel_description TEXT,
                playlist_id TEXT
            )
            """
        )

    def create_tables_videos(self, sqlite_cursor):
        sqlite_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                video_name TEXT,
                video_description TEXT,
                tags TEXT,
                published_at DATETIME,
                view_count INT,
                like_count INT,
                favorite_count INT,
                comment_count INT,
                duration TIME,
                caption BOOLEAN,
                thumbnail TEXT,
                playlist_id TEXT
            )
            """
        )

    def create_tables_comments(self, sqlite_cursor):
        sqlite_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                comment_Id TEXT PRIMARY KEY,
                video_id TEXT,
                comment_text TEXT,
                comment_author TEXT,
                comment_published_date DATETIME
            )
            """
        )

    def run_channel_pipeline(self, channel_id):
        try:
            # Fetch YouTube data
            youtube_channel_data = self.get_channel_info(channel_id)

            # Store data in MongoDB
            self.mongodb_collection.insert_one(youtube_channel_data)
            
             # Fetch YouTube channel data from MongoDB
            channel_data  = self.mongodb_channel_data(channel_id)

            #create tables
            self.create_table_channels(self.sqlite_cursor)

            # Load data from MongoDB to SQLite
            self.insert_channel_data(channel_data, self.sqlite_cursor)
            self.sqlite_connection.commit()

            st.success("Channel pipeline executed successfully.")
        except Exception as e:
            st.error(f"Error in channel pipeline: {e}")

    def run_videos_pipeline(self, channel_id):
        try:
            # Fetch YouTube data
            youtube_video_data = self.get_videos_info(channel_id)

            # Store data in MongoDB
            self.mongodb_collection.insert_many(youtube_video_data)

            #create tables
            self.create_tables_videos(self.sqlite_cursor)

            # Load data from MongoDB 
            video_data = self.mongodb_videos_data(channel_id)

            # Insert video data
            for document in video_data:
                self.insert_video_data(document, "videos", self.sqlite_cursor)
            self.sqlite_connection.commit()

            st.success("Videos pipeline executed successfully.")
        except Exception as e:
            st.error(f"Error in videos pipeline: {e}")

    def run_comments_pipeline(self, channel_id):
        try:
            # Fetch YouTube data
            youtube_comment_data = self.get_comments_info(channel_id)

            # Store data in MongoDB
            self.mongodb_collection.insert_many(youtube_comment_data)

            # Create tables
            self.create_tables_comments(self.sqlite_cursor)

            # Load data from MongoDB
            comment_data = self.mongodb_comments_data(channel_id)

            for document in comment_data:
                self.insert_comments_data(document, self.sqlite_cursor)
            self.sqlite_connection.commit()

            st.success("Comments pipeline executed successfully.")
        except Exception as e:
            st.error(f"Error in comments pipeline: {e}")

    def sql_query(self, query):
        try:
            result = pd.read_sql_query(query, self.sqlite_connection)
            return result
        except Exception as e:
            st.error(f"Error executing SQL query: {e}")
            return None

    def close_connections(self):
        self.sqlite_connection.close()
        self.mongodb_client.close()

