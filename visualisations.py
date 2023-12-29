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

    def bar_chart(self, x, y, xlabel, ylabel, title, rotation=45, color='skyblue'):
        plt.figure(figsize=(10, 6))
        plt.bar(x, y, color=color)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.xticks(rotation=rotation, ha='right')
        plt.tight_layout()
        st.pyplot()

    def line_chart(self, x, y, xlabel, ylabel, title, rotation=45, marker='o', linestyle='-', color='orange'):
        plt.figure(figsize=(12, 6))
        plt.plot(x, y, marker=marker, linestyle=linestyle, color=color)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.xticks(rotation=rotation)
        plt.tight_layout()
        st.pyplot()
