# Use an official Python runtime as a parent image
FROM python:3.12-slim


# Create and set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt requirements.txt

# Install the Python dependencies
RUN pip install -r requirements.txt


# Copy the rest of the application source code to the container
COPY . .

# Expose the port your application will run on (replace 3000 with your app's port)
EXPOSE 8080

# Define the command to run your application
CMD ["gunicorn", "-b", "0.0.0.0:8080", "run:app"]
