# Secure Systems Development - AS3-Blockchain

This project is a simple implementation of a blockchain system, developed as part of the Secure Systems Development course.

## Project Structure

The project is divided into two main parts:

1. `backend`: This is where the blockchain logic resides. It's a Python application that handles block parsing, message handling, and node connections. It uses flask handling HTTP requests.

2. `frontend`: This is the user interface for the blockchain. It's a TypeScript application that uses Vite for building and serving the application. It also uses Tailwind CSS for styling.

## Running the application

If you have `docker` installed, you can run the application using the following commands:

```sh
docker-compose up
```

This will start the backend and frontend applications, and you can access the frontend at `http://localhost:5173`.

### Backend

To start the backend, navigate to the `src/backend` directory and run:

```sh
docker build -t backend .
docker run -p 5000:5000 backend
````

Frontend
To start the frontend, navigate to the src/frontend directory and run:

```sh
docker build -t frontend .
docker run -p 3000:3000 frontend
````

