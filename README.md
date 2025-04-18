# Drone Telemetry Dashboard

A real-time telemetry visualization system for drone monitoring built with Python, WebSockets, and Plotly Dash.

![Dashboard Preview]()

## Overview

This project provides a complete solution for visualizing drone telemetry data in real-time through an interactive web dashboard. The system consists of two main components:

1. **Transmitter**: A Python script that simulates and transmits drone telemetry data over WebSockets
2. **Dashboard**: A Plotly Dash web application that receives, processes, and visualizes the telemetry data in real-time

The dashboard displays various metrics including:
- Drone 3D orientation (IMU data)
- GPS position with flight path tracking
- Battery voltage and percentage
- Altitude and temperature readings
- Connection status and signal strength
- Detailed telemetry data in real-time

## Features

- **Real-time Updates**: Data refreshes continuously with minimal latency
- **3D Orientation Visualization**: Interactive 3D model showing drone orientation based on IMU data
- **GPS Tracking**: Map display showing current position and flight path history
- **Time-Series Charts**: Track IMU, altitude, and temperature data over time
- **Connection Status Monitoring**: Visual indicators for connection quality
- **Battery Level Monitoring**: Real-time battery voltage and percentage display
- **Responsive Design**: Works on desktop and mobile devices

## Requirements

- Python 3.6+
- WebSockets
- Plotly Dash
- Pandas
- NumPy

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/drone-telemetry-dashboard.git
   cd drone-telemetry-dashboard
   ```

2. Install required packages using the requirements.txt file:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Step 1: Start the Transmitter

First, start the transmitter which generates simulated drone telemetry data:

```bash
python transmitter.py
```

You should see:
```
Starting drone telemetry transmitter server on ws://localhost:8765
Press Ctrl+C to exit
```

### Step 2: Launch the Dashboard

In a new terminal window, start the dashboard application:

```bash
python dashboard.py
```

You should see:
```
Starting Drone Telemetry Dashboard...
Make sure the transmitter is running on ws://localhost:8765
Access the dashboard at http://localhost:8050
```

### Step 3: Access the Dashboard

Open your web browser and navigate to:
```
http://localhost:8050
```

The dashboard should now be visible and displaying real-time telemetry data from the transmitter.

## Project Structure

```
drone-telemetry-dashboard/
├── dashboard.py       # Dash web application that displays telemetry data
├── transmitter.py     # WebSocket server that generates simulated telemetry data
├── README.md          # This file
├── requirements.txt   # List of required Python packages
└── assets
	└──styles.css      # CSS styles for the dashboard
```

## How It Works

### Transmitter (`transmitter.py`)

The transmitter simulates a drone sending telemetry data:

1. Generates realistic drone data (battery level, temperature, altitude, GPS coordinates, IMU readings)
2. Creates cyclic patterns to simulate drone movement and sensor readings
3. Serves this data via WebSockets on `ws://localhost:8765`
4. Updates at a configurable interval (default: 100ms)

You can modify the `UPDATE_INTERVAL` constant in the transmitter script to change the data transmission rate.

### Dashboard (`dashboard.py`)

The dashboard connects to the transmitter and visualizes the data:

1. Connects to the WebSocket server via a background thread
2. Processes incoming data and stores it in a time-series data store
3. Renders multiple interactive visualizations using Plotly
4. Updates the UI at a configurable interval (default: 100ms)

The dashboard uses a queue-based approach to safely transfer data between the WebSocket thread and the Dash application thread.

## Customization

### Styling

The dashboard uses a dark theme by default. You can modify the appearance by editing the `styles.css` file.

### Data Retention

By default, the dashboard keeps the last 100 data points for time-series charts. You can adjust this by changing the `MAX_DATA_POINTS` constant in `dashboard.py`.

### Custom Data Source

To use this dashboard with a real drone instead of simulated data:

1. Modify the transmitter script to connect to your drone's telemetry system
2. Ensure the data format matches the expected JSON structure
3. Adjust the WebSocket server address and port as needed

## Troubleshooting

**Issue**: Dashboard shows "No Data"  
**Solution**: Ensure the transmitter is running and accessible at ws://localhost:8765

**Issue**: Charts not updating  
**Solution**: Check if data is being received by monitoring the data values at the bottom of the dashboard

**Issue**: WebSocket connection error  
**Solution**: Verify that no firewall is blocking the WebSocket connection on port 8765

**Issue**: Missing packages after installation  
**Solution**: Ensure all packages are installed correctly with `pip install -r requirements.txt`

## Acknowledgements

- [Plotly Dash](https://dash.plotly.com/)
- [WebSockets](https://websockets.readthedocs.io/)
- [Plotly](https://plotly.com/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.