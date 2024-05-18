import logging
import threading
import os
from flask import Flask, jsonify
from flask_cors import CORS
from node_connection import run_node_listener
from data import block_data

# Initialize the Flask app
app = Flask(__name__)
CORS(app)

# Set the logging level of the Werkzeug logger to WARNING
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)


# Define the route to get the blocks
@app.route('/blocks', methods=['GET'])
def get_blocks():
    return jsonify(block_data)


if __name__ == "__main__":
    # Start the node listener in a separate thread
    threading.Thread(target=run_node_listener, daemon=True).start()

    # Determine the host based on the environment
    if os.path.exists('/.dockerenv'):
        # If running in a Docker container, set the host to '0.0.0.0'
        host = '0.0.0.0'
        print("Running in Docker container")
    else:
        # If running locally, set the host to '127.0.0.1'
        host = '127.0.0.1'
        print("Running locally")
    
    # Start the Flask app
    app.run(host=host, port=5000)
