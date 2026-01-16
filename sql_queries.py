
# SQL Queries for Visualisations and Analysis

# Dropdown options for the "Tables" tab
DROPDOWN_OPTIONS = {
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

# Queries for the "Visualisation" tab
QUERY_NUM_VIDEOS = """
SELECT c.channel_name, COUNT(*) AS num_videos
FROM channels c
INNER JOIN videos v ON v.playlist_id = c.playlist_id
GROUP BY c.channel_name
ORDER BY num_videos DESC
LIMIT 10;
"""

QUERY_TOP_VIEWED_VIDEOS = """
SELECT v.video_name, c.channel_name, v.view_count
FROM videos v
INNER JOIN channels c ON v.playlist_id = c.playlist_id
ORDER BY v.view_count DESC
LIMIT 10;
"""

QUERY_TOP_CHANNELS_SUBS = """
SELECT channel_name, subscription_count
FROM channels
ORDER BY subscription_count DESC
LIMIT 10
"""

QUERY_TIMELINE = """
SELECT c.channel_name, strftime('%Y-%m', v.published_at) as month_published
FROM channels c 
INNER JOIN videos v ON v.playlist_id = c.playlist_id 
WHERE v.published_at BETWEEN '2018-01-01 00:00:00' AND '2023-12-31 00:00:00';
"""

# KPI Dashboard Queries
QUERY_KPI_TOTAL_CHANNELS = "SELECT COUNT(*) FROM channels"
QUERY_KPI_TOTAL_VIDEOS = "SELECT COUNT(*) FROM videos"
QUERY_KPI_TOTAL_VIEWS = "SELECT SUM(view_count) FROM videos"
QUERY_KPI_TOTAL_LIKES = "SELECT SUM(like_count) FROM videos"
QUERY_KPI_TOTAL_COMMENTS = "SELECT SUM(comment_count) FROM videos"
QUERY_KPI_TOTAL_SUBS = "SELECT SUM(subscription_count) FROM channels"

QUERY_ENGAGEMENT_SCATTER = """
SELECT v.video_name, c.channel_name, v.view_count, v.like_count, v.comment_count
FROM videos v
INNER JOIN channels c ON v.playlist_id = c.playlist_id
WHERE v.view_count > 0
"""

QUERY_UPLOAD_SCHEDULE = """
SELECT strftime('%w', published_at) as day_of_week, COUNT(*) as num_videos
FROM videos
GROUP BY day_of_week
ORDER BY day_of_week
"""
