import asyncio
import json
import websockets
import threading
import queue
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Configuration
WS_SERVER = 'ws://localhost:8765'
MAX_DATA_POINTS = 100  # Maximum number of data points for time-series charts

# Queue to hold data between websocket thread and Dash
data_queue = queue.Queue()

# Storage for historical data
class DataStore:
    def __init__(self, max_points=MAX_DATA_POINTS):
        self.max_points = max_points
        self.timestamps = []
        self.battery_voltage = []
        self.temperature = []
        self.altitude = []
        self.roll = []
        self.pitch = []
        self.yaw = []
        self.latitude = []
        self.longitude = []
        self.connection_strength = []
        self.latest_data = None
    
    def add_data(self, data):
        """Add new data point to the store"""
        self.latest_data = data
        timestamp = datetime.fromisoformat(data['timestamp'])
        
        # Add new data points
        self.timestamps.append(timestamp)
        self.battery_voltage.append(data['battery']['voltage'])
        self.temperature.append(data['sensors']['temperature'])
        self.altitude.append(data['sensors']['altitude'])
        self.roll.append(data['imu']['roll'])
        self.pitch.append(data['imu']['pitch'])
        self.yaw.append(data['imu']['yaw'])
        self.latitude.append(data['gps']['latitude'])
        self.longitude.append(data['gps']['longitude'])
        self.connection_strength.append(data['connection']['signal_strength'])
        
        # Trim lists if they exceed max_points
        if len(self.timestamps) > self.max_points:
            self.timestamps = self.timestamps[-self.max_points:]
            self.battery_voltage = self.battery_voltage[-self.max_points:]
            self.temperature = self.temperature[-self.max_points:]
            self.altitude = self.altitude[-self.max_points:]
            self.roll = self.roll[-self.max_points:]
            self.pitch = self.pitch[-self.max_points:]
            self.yaw = self.yaw[-self.max_points:]
            self.latitude = self.latitude[-self.max_points:]
            self.longitude = self.longitude[-self.max_points:]
            self.connection_strength = self.connection_strength[-self.max_points:]

data_store = DataStore()

# WebSocket client function (runs in separate thread)
async def websocket_client():
    while True:
        try:
            async with websockets.connect(WS_SERVER) as websocket:
                print(f"Connected to transmitter at {WS_SERVER}")
                while True:
                    data = await websocket.recv()
                    data_json = json.loads(data)
                    data_queue.put(data_json)
        except Exception as e:
            print(f"Connection error: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

# Thread function to run the WebSocket client
def websocket_thread_function():
    asyncio.run(websocket_client())

# Initialize Dash app
app = dash.Dash(__name__, 
    title="Drone Telemetry Dashboard",
    update_title="Updating...",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# App layout
app.layout = html.Div([
    html.Div([
        html.H1("Drone Telemetry Dashboard", 
                style={'textAlign': 'center', 'color': '#FFFFFF', 'marginBottom': '20px'}),
        
        html.Div([
            # Connection status and battery level indicators
            html.Div([
                html.Div([
                    html.H4("Connection Status"),
                    html.Div(id='connection-status', className='status-indicator')
                ], className='status-card'),
                
                html.Div([
                    html.H4("Battery Level"),
                    html.Div(id='battery-indicator', className='status-indicator')
                ], className='status-card')
            ], className='status-row'),
            
            # Telemetry charts
            html.Div([
                html.Div([
                    html.H4("IMU Data"),
                    dcc.Graph(id='imu-chart', className='graph-display')
                ], className='chart-card'),
                
                html.Div([
                    html.H4("Altitude & Temperature"),
                    dcc.Graph(id='alt-temp-chart', className='graph-display')
                ], className='chart-card')
            ], className='chart-row'),
            
            # Real-time data values
            html.Div([
                html.Div(id='telemetry-data', className='data-values')
            ], className='data-row'),
            
            # 3D orientation display and GPS map
            html.Div([
                html.Div([
                    html.H4("Drone Orientation (IMU)"),
                    dcc.Graph(id='orientation-display', className='graph-display')
                ], className='viz-card'),
                
                html.Div([
                    html.H4("GPS Position"),
                    dcc.Graph(id='gps-map', className='graph-display')
                ], className='viz-card')
            ], className='viz-row'),
        ], className='dashboard-container')
    ], className='main-content'),
    
    # Interval component for updating the data
    dcc.Interval(
        id='interval-component',
        interval=100,  # in milliseconds
        n_intervals=0
    ),
    
    html.Div([], style={'display': 'none'}, id='css-container')
])

# Process queue data
@app.callback(
    Output('interval-component', 'n_intervals'),
    Input('interval-component', 'n_intervals')
)
def process_queue(n):
    # Process all available data in the queue
    while not data_queue.empty():
        try:
            data = data_queue.get_nowait()
            data_store.add_data(data)
        except queue.Empty:
            break
    return n

# Connection status callback
@app.callback(
    Output('connection-status', 'children'),
    Output('connection-status', 'style'),
    Input('interval-component', 'n_intervals')
)
def update_connection_status(n):
    if data_store.latest_data is None:
        return "No Data", {'backgroundColor': '#555555'}
    
    status = data_store.latest_data['connection']['status']
    
    colors = {
        "Excellent": "#4CAF50",  # Green
        "Good": "#8BC34A",       # Light Green
        "Fair": "#FFC107",       # Amber
        "Poor": "#FF9800",       # Orange
        "No Signal": "#F44336"   # Red
    }
    
    return status, {
        'backgroundColor': colors.get(status, '#555555'),
        'color': '#000000' if status in ["Excellent", "Good", "Fair"] else '#FFFFFF'
    }

# Battery indicator callback
@app.callback(
    Output('battery-indicator', 'children'),
    Output('battery-indicator', 'style'),
    Input('interval-component', 'n_intervals')
)
def update_battery_indicator(n):
    if data_store.latest_data is None:
        return "No Data", {'backgroundColor': '#555555'}
    
    voltage = data_store.latest_data['battery']['voltage']
    percentage = data_store.latest_data['battery']['percentage']
    
    # Color based on percentage
    if percentage > 75:
        color = "#4CAF50"  # Green
    elif percentage > 50:
        color = "#8BC34A"  # Light Green
    elif percentage > 25:
        color = "#FFC107"  # Amber
    elif percentage > 10:
        color = "#FF9800"  # Orange
    else:
        color = "#F44336"  # Red
    
    return f"{voltage}V ({percentage}%)", {
        'backgroundColor': color,
        'color': '#000000' if percentage > 25 else '#FFFFFF'
    }

# 3D orientation display callback
@app.callback(
    Output('orientation-display', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_orientation_display(n):
    if data_store.latest_data is None:
        # Create empty figure
        fig = go.Figure()
        fig.update_layout(
            scene=dict(aspectmode="cube"),
            margin=dict(l=0, r=0, b=0, t=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            scene_camera=dict(eye=dict(x=0.75, y=0.75, z=0.75))
        )
        return fig
    
    # Get IMU data
    roll = data_store.latest_data['imu']['roll'] * np.pi / 180  # Convert to radians
    pitch = data_store.latest_data['imu']['pitch'] * np.pi / 180
    yaw = data_store.latest_data['imu']['yaw'] * np.pi / 180
    
    # Create rotation matrices
    def rotation_matrix(axis, theta):
        """Return the rotation matrix for a counterclockwise rotation of theta radians around axis."""
        axis = np.asarray(axis)
        axis = axis / np.sqrt(np.dot(axis, axis))
        a = np.cos(theta / 2.0)
        b, c, d = -axis * np.sin(theta / 2.0)
        aa, bb, cc, dd = a * a, b * b, c * c, d * d
        bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
        return np.array([
            [aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
            [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
            [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]
        ])
    
    # Apply rotations in ZYX order (yaw, pitch, roll)
    R_z = rotation_matrix([0, 0, 0.75], yaw)
    R_y = rotation_matrix([0, 0.75, 0], pitch)
    R_x = rotation_matrix([0.75, 0, 0], roll)
    R = R_z.dot(R_y).dot(R_x)
    
    # Create drone model
    # Define the basic drone shape as a cross with 4 arms
    drone_size = 0.8
    center = np.array([0, 0, 0])
    
    # Main body points
    body_size = drone_size * 0.3
    body_points = np.array([
        [body_size, body_size, 0.05],
        [body_size, -body_size, 0.05],
        [-body_size, -body_size, 0.05],
        [-body_size, body_size, 0.05],
        [body_size, body_size, -0.05],
        [body_size, -body_size, -0.05],
        [-body_size, -body_size, -0.05],
        [-body_size, body_size, -0.05]
    ])
    
    # Arms points
    arm_length = drone_size
    thickness = 0.05
    
    # Define arms and rotors
    arm_front = np.array([
        [0, 0, thickness], [0, 0, -thickness], 
        [0, arm_length, thickness], [0, arm_length, -thickness]
    ])
    arm_back = np.array([
        [0, 0, thickness], [0, 0, -thickness], 
        [0, -arm_length, thickness], [0, -arm_length, -thickness]
    ])
    arm_right = np.array([
        [0, 0, thickness], [0, 0, -thickness], 
        [arm_length, 0, thickness], [arm_length, 0, -thickness]
    ])
    arm_left = np.array([
        [0, 0, thickness], [0, 0, -thickness], 
        [-arm_length, 0, thickness], [-arm_length, 0, -thickness]
    ])
    
    # Create reference ring (for orientation)
    ring_points = []
    ring_radius = arm_length * 1.2
    ring_segments = 36
    for i in range(ring_segments + 1):
        angle = 2 * np.pi * i / ring_segments
        ring_points.append([ring_radius * np.cos(angle), ring_radius * np.sin(angle), 0])
    ring_points = np.array(ring_points)
    
    # Apply rotation to all points
    body_rotated = np.dot(body_points, R.T)
    arm_front_rotated = np.dot(arm_front, R.T)
    arm_back_rotated = np.dot(arm_back, R.T)
    arm_right_rotated = np.dot(arm_right, R.T)
    arm_left_rotated = np.dot(arm_left, R.T)
    ring_rotated = ring_points  # Ring stays fixed as reference
    
    # Create figure
    fig = go.Figure()
    
    # Add reference ring (red)
    fig.add_trace(go.Scatter3d(
        x=ring_rotated[:, 0], y=ring_rotated[:, 1], z=ring_rotated[:, 2],
        mode='lines',
        line=dict(color='red', width=5),
        showlegend=False
    ))
    
    # Add reference axes
    axis_length = arm_length * 0.75
    
    # Forward reference (blue z-axis)
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, axis_length], z=[0, 0],
        mode='lines',
        line=dict(color='blue', width=5),
        showlegend=False
    ))
    
    # Right reference (green x-axis)
    fig.add_trace(go.Scatter3d(
        x=[0, axis_length], y=[0, 0], z=[0, 0],
        mode='lines',
        line=dict(color='green', width=5),
        showlegend=False
    ))
    
    # Add drone body
    i, j, k = np.array([7, 0, 0, 3, 4, 4, 6, 6, 1, 1, 7, 3, 0, 0, 5, 5, 2, 2, 7]), np.array([3, 7, 4, 0, 7, 0, 3, 0, 5, 0, 4, 4, 1, 5, 1, 6, 1, 6, 6]), np.array([0, 3, 7, 4, 4, 1, 1, 2, 2, 5, 5, 3, 2, 2, 6, 1, 5, 5, 2])
    
    fig.add_trace(go.Mesh3d(
        x=body_rotated[:, 0], y=body_rotated[:, 1], z=body_rotated[:, 2],
        i=i, j=j, k=k,
        color='grey',
        opacity=0.8,
        showlegend=False
    ))
    
    # Add arms
    # Front arm (red)
    fig.add_trace(go.Mesh3d(
        x=arm_front_rotated[:, 0], y=arm_front_rotated[:, 1], z=arm_front_rotated[:, 2],
        i=[0, 0, 2], j=[1, 2, 3], k=[3, 1, 1],
        color='red',
        opacity=0.8,
        showlegend=False
    ))
    
    # Back arm (green)
    fig.add_trace(go.Mesh3d(
        x=arm_back_rotated[:, 0], y=arm_back_rotated[:, 1], z=arm_back_rotated[:, 2],
        i=[0, 0, 2], j=[1, 2, 3], k=[3, 1, 1],
        color='green',
        opacity=0.8,
        showlegend=False
    ))
    
    # Right arm (blue)
    fig.add_trace(go.Mesh3d(
        x=arm_right_rotated[:, 0], y=arm_right_rotated[:, 1], z=arm_right_rotated[:, 2],
        i=[0, 0, 2], j=[1, 2, 3], k=[3, 1, 1],
        color='blue',
        opacity=0.8,
        showlegend=False
    ))
    
    # Left arm (yellow)
    fig.add_trace(go.Mesh3d(
        x=arm_left_rotated[:, 0], y=arm_left_rotated[:, 1], z=arm_left_rotated[:, 2],
        i=[0, 0, 2], j=[1, 2, 3], k=[3, 1, 1],
        color='yellow',
        opacity=0.8,
        showlegend=False
    ))
    
    # Set layout
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-1, 1], showbackground=False, visible=False),
            yaxis=dict(range=[-1, 1], showbackground=False, visible=False),
            zaxis=dict(range=[-1, 1], showbackground=False, visible=False),
            aspectmode="cube"
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        scene_camera=dict(eye=dict(x=1, y=1, z=1))
    )
    
    return fig

# GPS Map callback
@app.callback(
    Output('gps-map', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_gps_map(n):
    fig = go.Figure()
    
    if data_store.latest_data is not None and len(data_store.latitude) > 0:
        # Plot path
        fig.add_trace(go.Scattermap(
            lat=data_store.latitude,
            lon=data_store.longitude,
            mode='lines+markers',
            marker=dict(size=8, color='royalblue'),
            line=dict(width=2, color='royalblue'),
            name='Path'
        ))
        
        # Add current position marker
        fig.add_trace(go.Scattermap(
            lat=[data_store.latitude[-1]],
            lon=[data_store.longitude[-1]],
            mode='markers',
            marker=dict(
                size=13,
                color='red',
                symbol='circle'
            ),
            name='Current Position'
        ))
    
    fig.update_layout(
        mapbox=dict(
            style="dark",
            zoom=1000,
            center=dict(
                lat=data_store.latitude[-1] if data_store.latest_data else 11.064754,
                lon=data_store.longitude[-1] if data_store.latest_data else 77.093565
            )
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=300,
        paper_bgcolor='#1E1E1E',
        plot_bgcolor='#1E1E1E',
    )
    
    return fig

# IMU Chart callback
@app.callback(
    Output('imu-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_imu_chart(n):
    fig = make_subplots(specs=[[{"secondary_y": False}]])
    
    if data_store.latest_data is not None and len(data_store.timestamps) > 0:
        # Format timestamps for display
        time_strings = [ts.strftime('%H:%M:%S') for ts in data_store.timestamps]
        
        # Add Roll data
        fig.add_trace(
            go.Scatter(
                x=time_strings,
                y=data_store.roll,
                name="Roll",
                line=dict(color="#FF4136")
            )
        )
        
        # Add Pitch data
        fig.add_trace(
            go.Scatter(
                x=time_strings,
                y=data_store.pitch,
                name="Pitch",
                line=dict(color="#2ECC40")
            )
        )
        
        # Add Yaw data
        fig.add_trace(
            go.Scatter(
                x=time_strings,
                y=data_store.yaw,
                name="Yaw",
                line=dict(color="#0074D9")
            )
        )
    
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
        plot_bgcolor='#1E1E1E',
        paper_bgcolor='#1E1E1E',
        font=dict(color='white'),
        margin=dict(l=40, r=40, t=10, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=300
    )
    
    return fig

# Altitude & Temperature Chart callback
@app.callback(
    Output('alt-temp-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_alt_temp_chart(n):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    if data_store.latest_data is not None and len(data_store.timestamps) > 0:
        # Format timestamps for display
        time_strings = [ts.strftime('%H:%M:%S') for ts in data_store.timestamps]
        
        # Add Altitude data
        fig.add_trace(
            go.Scatter(
                x=time_strings,
                y=data_store.altitude,
                name="Altitude (m)",
                line=dict(color="#FF851B")
            )
        )
        
        # Add Temperature data (on secondary y-axis)
        fig.add_trace(
            go.Scatter(
                x=time_strings,
                y=data_store.temperature,
                name="Temperature (°C)",
                line=dict(color="#B10DC9")
            ),
            secondary_y=True
        )
    
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
        yaxis=dict(
            showgrid=True, 
            gridcolor='rgba(255,255,255,0.1)', 
            tickfont=dict(color='white'),
            title="Altitude (m)"
        ),
        yaxis2=dict(
            showgrid=False, 
            tickfont=dict(color='white'),
            title="Temperature (°C)",
            overlaying="y",
            side="right"
        ),
        plot_bgcolor='#1E1E1E',
        paper_bgcolor='#1E1E1E',
        font=dict(color='white'),
        margin=dict(l=40, r=40, t=10, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=300
    )
    
    return fig

# Telemetry data values callback
@app.callback(
    Output('telemetry-data', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_telemetry_data(n):
    if data_store.latest_data is None:
        return html.Div("No data received yet.")
    
    data = data_store.latest_data
    
    telemetry_values = [
        html.Div([
            html.Strong("Battery: "),
            html.Span(f"{data['battery']['voltage']}V ({data['battery']['percentage']}%)")
        ], className='data-value'),
        
        html.Div([
            html.Strong("Temperature: "),
            html.Span(f"{data['sensors']['temperature']}°C")
        ], className='data-value'),
        
        html.Div([
            html.Strong("Altitude: "),
            html.Span(f"{data['sensors']['altitude']}m")
        ], className='data-value'),
        
        html.Div([
            html.Strong("Roll: "),
            html.Span(f"{data['imu']['roll']}°")
        ], className='data-value'),
        
        html.Div([
            html.Strong("Pitch: "),
            html.Span(f"{data['imu']['pitch']}°")
        ], className='data-value'),
        
        html.Div([
            html.Strong("Yaw: "),
            html.Span(f"{data['imu']['yaw']}°")
        ], className='data-value'),
        
        html.Div([
            html.Strong("GPS: "),
            html.Span(f"Lat: {data['gps']['latitude']}, Lon: {data['gps']['longitude']}")
        ], className='data-value'),
        
        html.Div([
            html.Strong("Connection: "),
            html.Span(f"{data['connection']['status']} ({data['connection']['signal_strength']}%)")
        ], className='data-value'),
        
        html.Div([
            html.Strong("Last Updated: "),
            html.Span(datetime.fromisoformat(data['timestamp']).strftime('%H:%M:%S'))
        ], className='data-value')
    ]
    
    return telemetry_values

# Start WebSocket client in a separate thread
websocket_thread = threading.Thread(target=websocket_thread_function, daemon=True)
websocket_thread.start()

# Run the Dash app
if __name__ == '__main__':
    print("Starting Drone Telemetry Dashboard...")
    print("Make sure the transmitter is running on ws://localhost:8765")
    print("Access the dashboard at http://localhost:8050")
    app.run(debug=False, host='0.0.0.0', port=8050)