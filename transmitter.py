import asyncio
import json
import random
import websockets
import time
import math
from datetime import datetime

# Configuration
UPDATE_INTERVAL = 0.1  # seconds

class DroneDataGenerator:
    def __init__(self):
        # Initial values
        self.battery_voltage = 12.0  # Starting with full battery
        self.temperature = 25.0      # Normal temperature in Celsius
        self.altitude = 100.0        # Starting altitude in meters
        
        # Position data (GPS)
        self.latitude = 37.7749      # Starting at San Francisco coordinates
        self.longitude = -122.4194
        
        # IMU data
        self.roll = 0.0              # Roll angle in degrees
        self.pitch = 0.0             # Pitch angle in degrees
        self.yaw = 0.0               # Yaw angle in degrees
        
        # Connection health status options
        self.connection_states = ["Excellent", "Good", "Fair", "Poor", "No Signal"]
        self.connection_health = "Excellent"
        
        # Movement patterns
        self.time_offset = 0
        
    def generate_data(self):
        """Generate simulated drone telemetry data with realistic patterns"""
        self.time_offset += UPDATE_INTERVAL
        
        # Battery simulation (slowly decreasing with random fluctuations)
        battery_drain_rate = 0.001  # Voltage drop per update
        self.battery_voltage -= battery_drain_rate
        self.battery_voltage += random.uniform(-0.01, 0.01)  # Small random fluctuations
        self.battery_voltage = max(8.0, min(12.0, self.battery_voltage))  # Keep within reasonable range
        
        # Temperature simulation (slight variations)
        self.temperature += random.uniform(-0.1, 0.1)
        
        # Movement simulation
        movement_factor = 2 * math.sin(self.time_offset / 10)  # Create cyclical movement
        
        # IMU data simulation
        self.roll = 15 * math.sin(self.time_offset / 5) + random.uniform(-2, 2)
        self.pitch = 10 * math.cos(self.time_offset / 7) + random.uniform(-2, 2)
        self.yaw = (self.yaw + 1 + random.uniform(-0.5, 0.5)) % 360  # Slowly rotating with jitter
        
        # Altitude simulation (gentle oscillation)
        self.altitude = 100 + 10 * math.sin(self.time_offset / 15) + random.uniform(-1, 1)
        
        # GPS simulation (drone moves in small circular pattern)
        circle_radius = 0.0001  # Small radius for GPS movement
        self.latitude += circle_radius * math.sin(self.time_offset / 20)
        self.longitude += circle_radius * math.cos(self.time_offset / 20)
        
        # Connection health (occasional changes)
        if random.random() < 0.01:  # 1% chance to change connection status each update
            weights = [0.5, 0.3, 0.1, 0.07, 0.03]  # Weighted probabilities
            self.connection_health = random.choices(self.connection_states, weights=weights)[0]
            
        # Format data as dictionary
        return {
            "timestamp": datetime.now().isoformat(),
            "battery": {
                "voltage": round(self.battery_voltage, 2),
                "percentage": round((self.battery_voltage - 8.0) / 4.0 * 100, 1)  # Calculate percentage (8V-12V range)
            },
            "sensors": {
                "temperature": round(self.temperature, 1),
                "altitude": round(self.altitude, 1)
            },
            "imu": {
                "roll": round(self.roll, 2),
                "pitch": round(self.pitch, 2),
                "yaw": round(self.yaw, 2)
            },
            "gps": {
                "latitude": round(self.latitude, 6),
                "longitude": round(self.longitude, 6),
                "altitude": round(self.altitude, 1)
            },
            "connection": {
                "status": self.connection_health,
                "signal_strength": self._get_signal_strength(self.connection_health)
            }
        }
    
    def _get_signal_strength(self, status):
        """Convert text status to numeric signal strength"""
        mapping = {
            "Excellent": 95,
            "Good": 75,
            "Fair": 50,
            "Poor": 25,
            "No Signal": 0
        }
        return mapping.get(status, 0)

async def transmit_data(websocket):
    """Handle WebSocket connection and send drone data"""
    drone = DroneDataGenerator()
    print(f"Client connected from {websocket.remote_address}")
    
    try:
        while True:
            data = drone.generate_data()
            await websocket.send(json.dumps(data))
            await asyncio.sleep(UPDATE_INTERVAL)
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected from {websocket.remote_address}")

async def main():
    server_host = 'localhost'
    server_port = 8765
    
    print(f"Starting drone telemetry transmitter server on ws://{server_host}:{server_port}")
    print("Press Ctrl+C to exit")
    
    async with websockets.serve(transmit_data, server_host, server_port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")