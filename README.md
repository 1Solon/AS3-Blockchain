# Secure Systems Development - AS3-Blockchain

This project is a simple blockchain viewer for the `seed.bitcoin.sipa.be` seed, when a new block is added, the application will display the bew block on the frontend.


## Project Structure

The project is divided into two main parts:

1. `backend`: This is where the blockchain logic resides. It's a Python application that handles block parsing, message handling, and node connections. It uses flask handling HTTP requests.

2. `frontend`: This is the user interface for the blockchain. It's a TypeScript application that uses Vite for building and serving the application. It also uses Tailwind CSS for styling.

## Example of the application running

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaHZqcWJobTV4ZmIwNncxemUyYmZ4MTUzOTFzZmFkOXRubDd4OXByNCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/nuEgC4PQAG3ueHDtkb/giphy.gif" width="250" height="250"/>

## Running the application

For this application to function, both the front and backend applications need to be running. The backend application should be running, this can be accomplished either by:

* running the application using docker-compose
* running each application separately

## Docker-Compose
If you have `docker` installed, you can run the application using the following commands:

```sh
docker-compose up
```

This will start the backend and frontend applications, and you can access the frontend at `http://localhost:5173`.

## Running each application separately

### Backend

To start the backend, navigate to the `src/backend` directory and run:

```sh
python src/app.py
```

### Frontend

To start the frontend, navigate to the `src/frontend` directory and run:

```sh
npm install
npm run dev
```
