# car_parts_picker
Part shop in works.
# FastAPI Website with PostgreSQL

This project is a simple website built using **FastAPI** and connected to a **PostgreSQL** database. The website allows for user interactions and data storage, making it a perfect starting point for a scalable web application.

## Features
- FastAPI for building high-performance APIs.
- PostgreSQL for persistent database storage.
- Basic user authentication (if applicable).
- CRUD operations (Create, Read, Update, Delete).

## Prerequisites

Before you begin, ensure you have met the following requirements:
- Docker and Docker Compose installed on your machine. [Install Docker](https://docs.docker.com/get-docker/)
- Python 3.12+ installed.
- PostgreSQL installed and running on your machine or a cloud instance.
- `pip` for installing dependencies.

## Setup

### 1. Clone the repository

  git clone https://github.com/yourusername/fastapi-postgresql-website.git
  
  cd fastapi-postgresql-website


###2. Create a Virtual Environment
#Create a virtual environment to manage dependencies:

	python3 -m venv venv


###3. Activate the virtual environment:

#On Linux/macOS:
	source venv/bin/activate

#On Windows:
	.\venv\Scripts\activate

###4. Docker Setup
To run the application in Docker, follow these steps.

#4.1 Dockerfile
Create a Dockerfile in the root directory of your project:

# Use official Python image as a base
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variable for FastAPI app
ENV UVICORN_CMD="uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the application
CMD ["sh", "-c", "$UVICORN_CMD"]

#4.2 Docker Compose
Create a docker-compose.yml file for managing the FastAPI app and PostgreSQL database containers:

version: '3.8'

services:
  web:
    build: .
    container_name: fastapi-website
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/website_db
    networks:
      - app-network

  db:
    image: postgres:13
    container_name: postgres-db
    environment:
      POSTGRES_DB: website_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
This setup defines two services:

web: The FastAPI application, built from the Dockerfile.
db: A PostgreSQL database container with an environment for user credentials and database name.

#4.3 Create a .env file (Optional)
For environment variables like DATABASE_URL, you can also use a .env file in your project directory to manage sensitive information:

DATABASE_URL=postgresql://postgres:password@db:5432/website_db
Make sure to adjust the database credentials according to your setup.

#5. Build and Run the Containers
Once the Dockerfile and docker-compose.yml are set up, you can easily build and run your containers with Docker Compose.

#5.1 Build the Containers
Run the following command to build the images:

docker-compose build

#5.2 Run the Application
Start the containers using:

docker-compose up
This will start both the FastAPI app and PostgreSQL database. The application will be accessible at http://localhost:8000.

#5.3 Stopping the Containers
To stop the running containers, use:

docker-compose down
This will stop and remove the containers but keep your data intact.


###6. Install Dependencies
#Install the required packages using pip:

pip install -r requirements.txt


###7. Setup PostgreSQL Database
#Make sure you have a PostgreSQL instance running.
#Create a database for the application, e.g., website_db.

CREATE DATABASE website_db;

#Update your database connection string in the application configuration, typically in config.py or .env:

DATABASE_URL=postgresql://username:password@localhost/website_db
(In database.py this is already is but check and if what copy code above and most importantly use your db info)


8. Run Database Migrations
#If you're using a migration tool like Alembic, you can run the migrations after starting the containers.

docker-compose exec web alembic upgrade head


###9. Run the Development Server
#Start the FastAPI server using uvicorn:

uvicorn main:app --reload

#This will start the server on http://127.0.0.1:8000. You can access the API documentation at http://127.0.0.1:8000/docs.



###Usage###
Visit http://127.0.0.1:8000 to interact with your website.
The API documentation is available at http://127.0.0.1:8000/docs (powered by FastAPI's auto-generated docs).

###Deployment###
Docker

###Testing###
Pytest -v <file name>




### Additional Notes:
1. **Dockerfile**: This file builds the application image by installing dependencies, copying the project files, and setting the command to run FastAPI using `uvicorn`.
2. **docker-compose.yml**: Manages the multi-container application setup. It starts the FastAPI container (`web`) and the PostgreSQL container (`db`).
3. **Volumes**: The database's data is persisted using Docker volumes to prevent data loss if the containers are stopped or removed.

This approach makes it easy to set up the development environment and ensures that your application can be quickly deployed in a containerized environment, making it portable and scalable.
