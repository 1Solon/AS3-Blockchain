import logging
from flask import Flask, jsonify
from flask_cors import CORS
import threading
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
    # Start the Flask app
    app.run(port=5000)
