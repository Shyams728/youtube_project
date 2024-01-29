# Use an official base image with your desired version of Python
FROM python:3.10

# Set the working directory inside the container
WORKDIR /myapp

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port your app runs on
EXPOSE 8501

# Define the command to run your application
CMD ["streamlit", "run", "main_streamlit.py"]
