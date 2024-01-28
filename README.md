# YouTube Data Dashboard

## Overview

This project, the **YouTube Data Dashboard**, is a comprehensive system designed to extract valuable insights from YouTube. The project employs a multi-step process that begins with extracting pertinent information from YouTube using a designated API key. The extracted data is then stored in both a MongoDB cloud server, functioning as a data lake for efficient and secure data management, and a SQLite database, facilitating structured querying and retrieval of specific information.

## Features

- **Data Collection:** The project incorporates various functionalities, including the ability to input a YouTube channel ID, triggering the execution of a comprehensive data pipeline. This pipeline collects channel-related data, video details, and comments, offering a holistic view of the YouTube presence.

- **User-Friendly Interface:** The project features a user-friendly interface with tabs for distinct functionalities, such as displaying tables, charts, visualizations, and conducting NLP (Natural Language Processing) analysis on comments.

## Project Structure

The project is structured as follows:

- **Main Script (`main_streamlit.py`):** This script serves as the entry point for running the YouTube Data Dashboard. It utilizes Streamlit for creating an interactive web application.

- **Data Pipeline (`youtube_data.py`):** The `YouTubeDataPipeline` class handles the extraction and processing of data from YouTube. It interfaces with the YouTube API, MongoDB, and SQLite.

- **Visualizations Module (`visualisations.py`):** The `YouTubeDataVisualisation` class contains functions for generating various visualizations based on the stored data.

- **Additional Modules:**
  - `dockerfile.txt`: Configuration file for building a Docker image.
  - `requirements.txt`: List of Python dependencies required for the project.

## Setup and Configuration

To use the YouTube Data Dashboard, you need to provide the following credentials and configuration:

- **YouTube API Key:** Input your YouTube API key in the provided text field on the sidebar.

- **MongoDB Configuration:**
  - Connection String: Enter the connection string for your MongoDB instance.
  - Database Name: Specify the name of the MongoDB database.
  - Collection Name: Set the name of the MongoDB collection to store YouTube data.

- **SQLite Configuration:**
  - The SQLite database file is named `youtube_data.sqlite` and is located in the project directory.

## Usage

1. Run the main script (`main_streamlit.py`) using Streamlit:
   ```bash
   streamlit run main_streamlit.py
   ```

2. Access the interactive web application at the provided URL.

3. On the sidebar, input the required credentials and configurations.

4. Use the tabs to explore tables, visualizations, and perform NLP analysis.

## Dockerization

To run the `shyamsd/youtube_streamlit_app` Docker container:

1. Pull the Docker image:
   ```
   docker pull shyamsd/youtube_streamlit_app
   ```

2. Run the Docker container:
   ```
   docker run -p 8501:8501 shyamsd/youtube_streamlit_app
   ```

3. Access the application at [http://localhost:8501](http://localhost:8501) in your web browser.

## Dependencies

The project relies on the following Python libraries and packages:

- `streamlit`
- `sqlite3`
- `pandas`
- `pymongo`
- `plotly`
- `googleapiclient`
- `transformers`
- `matplotlib`
- `os`

## Contributing

Contributions to enhance the YouTube Data Dashboard are welcome! Feel free to fork the repository, make changes, and submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
