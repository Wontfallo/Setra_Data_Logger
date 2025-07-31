import time
import serial
import threading
import csv
import math
import argparse
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO

# --- CONFIGURATION ---
# IMPORTANT: Change this to the serial port your microcontroller is connected to.
# - Windows: "COM3", "COM4", etc.

SERIAL_PORT = "COM3"
BAUD_RATE = 9600
# ---------------------

app = Flask(__name__)
# This is a secret key for the session management, not critical for this app
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

# --- Global flags & variables ---
is_simulation = False
# NEW: Global start time for the simulation to allow for resets
simulation_start_time = None
# --------------------------------

# --- Global variables for logging ---
is_logging = False
csv_writer = None
csv_file = None
csv_filename = None
# ------------------------------------

# Background thread for reading serial data
thread = None
thread_lock = threading.Lock()

def data_generator_thread():
    """
    A background thread that either reads from the serial port or generates
    simulated data, then emits it to the clients.
    """
    global simulation_start_time # NEW: Use the global start time
    if is_simulation:
        print("Starting data simulation thread.")
        # NEW: Initialize the simulation start time if it's not already set
        if simulation_start_time is None:
            simulation_start_time = time.time()
            
        while True:
            # The simulation can now be reset by changing `simulation_start_time`
            elapsed_time = time.time() - simulation_start_time
            # Logarithmic decay from 1 bar down to 1e-6 (microbar) over ~60 seconds
            pressure = max(1e-6, 1.1 * math.exp(-elapsed_time / 10))
            
            socketio.emit("new_data", {"pressure": pressure, "is_simulation": True})
            
            if is_logging and csv_writer:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                csv_writer.writerow([timestamp, pressure])

            socketio.sleep(0.2) # Update rate for simulation
    else:
        # This is the original serial reading logic
        print("Starting serial reader thread.")
        while True:
            try:
                with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
                    print(f"Connected to serial port {SERIAL_PORT}.")
                    while True:
                        if ser.in_waiting > 0:
                            try:
                                line = ser.readline().decode("utf-8").strip()
                                if line:
                                    pressure = float(line)
                                    socketio.emit("new_data", {"pressure": pressure, "is_simulation": False})
                                    
                                    if is_logging and csv_writer:
                                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                                        csv_writer.writerow([timestamp, pressure])
                            except (ValueError, UnicodeDecodeError) as e:
                                print(f"Could not parse data: {line}. Error: {e}")
                        socketio.sleep(0.1)
            except serial.SerialException:
                print(f"Error: Could not connect to {SERIAL_PORT}. Retrying in 5 seconds...")
                socketio.sleep(5)

@app.route("/")
def index():
    """Serve the main dashboard page."""
    return render_template("index.html")

@socketio.on("connect")
def connect():
    """Handle a new client connection."""
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=data_generator_thread)
    
    # Inform the new client about the current logging status
    socketio.emit("logging_status", {"active": is_logging, "filename": csv_filename})
    print("Client connected.")

# --- NEW: SocketIO handler for restarting the simulation ---
@socketio.on("restart_simulation")
def restart_simulation():
    """Resets the simulation start time."""
    global simulation_start_time
    with thread_lock:
        if is_simulation:
            simulation_start_time = time.time()
            # Notify all clients that the simulation has restarted so they can clear their charts
            socketio.emit("simulation_restarted")
            print("Simulation restarted by client.")
# -----------------------------------------------------------

@socketio.on("start_logging")
def start_logging():
    """Start writing data to a new CSV file."""
    global is_logging, csv_writer, csv_file, csv_filename
    if not is_logging:
        is_logging = True
        # Create a unique filename with a timestamp
        csv_filename = f"pressure_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_file = open(csv_filename, 'w', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Timestamp', 'Pressure (Bar)'])
        print(f"Started logging to {csv_filename}")
        socketio.emit("logging_status", {"active": True, "filename": csv_filename})

@socketio.on("stop_logging")
def stop_logging():
    """Stop writing data to the CSV file."""
    global is_logging, csv_writer, csv_file
    if is_logging:
        is_logging = False
        if csv_file:
            csv_file.close()
        csv_file = None
        csv_writer = None
        print(f"Stopped logging to {csv_filename}")
        socketio.emit("logging_status", {"active": False, "filename": None})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a Flask-SocketIO server for pressure sensor data.")
    parser.add_argument('--simulate', action='store_true', help='Run in simulation mode without a serial connection.')
    args = parser.parse_args()
    is_simulation = args.simulate

    if is_simulation:
        print("---- RUNNING IN SIMULATION MODE ----")
    else:
        print("---- RUNNING IN LIVE (SERIAL) MODE ----")

    print("Starting Flask-SocketIO server...")
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)