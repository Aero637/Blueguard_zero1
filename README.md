BlueGuard Zero 🛡️:
BlueGuard Zero is an intelligent proximity-based security system that monitors Bluetooth devices in real-time. It leverages hardware detection and cloud synchronization to provide a seamless monitoring dashboard.
🚀 Features:
Hardware Integration: Uses Arduino for reliable electronic sensor management.
Device Discovery: Automated Bluetooth scanning via custom Python scripts.
Cloud Sync: Real-time data logging to MongoDB for history and alerts.
Live Dashboard: A clean, web-based interface to monitor status at a glance.
Tech Stack:
Component : Technology:    Role
Electronics:  Arduino:  It acts as Hardware controller & sensors
Backend:      Python:   It acts as Core logic and device discovery
Database:     MongoDB:  It acts as Persistent storage for security logs
Frontend:     HTML/CSS:  Real-time monitoring interface
📂 Project Structure
find_mac.py: Utility script used to identify and filter nearby Bluetooth MAC addresses.
Code:
import asyncio
from bleak import BleakScanner

async def main():
    print("Scanning for devices... please wait 10 seconds.")
    # This will list all BLE devices in range
    devices = await BleakScanner.discover()
    for d in devices:
        # Look for your headphone's name in this list
        print(f"Name: {d.name} | MAC Address: {d.address}")

asyncio.run(main())

security_system1.py: The core engine handling proximity logic and MongoDB communication.
Code:
import pymongo
import os
import asyncio
import threading
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from bleak import BleakScanner

# --- CONFIGURATION ---
# Using the Noise Pulse_9ECE address found in your find_mac.py scan
TARGET_ID = "D3:18:13:30:9E:CE" 
DATABASE_URI = "mongodb+srv://pandasrija_db_user:Aerovitb_db_user@cluster0.qljzylb.mongodb.net/"

# 1. DATABASE CONNECTION
try:
    client = pymongo.MongoClient(DATABASE_URI)
    db = client["Detection"]
    logs = db["Detection"]
    print("✅ Connected to MongoDB Cloud!")
except Exception as e:
    print(f"❌ Connection failed: {e}")

# 2. WEB SERVER SETUP
app = Flask(__name__)
CORS(app)

latest_event = {"status": "INITIALIZING", "rssi": "--", "device": "None", "proximity": "Unknown"}

@app.route('/data')
def get_live_data():
    """Endpoint for the dashboard to fetch real-time data"""
    return jsonify(latest_event)

# 3. REAL BLUETOOTH SCANNING LOGIC
async def run_bluetooth_monitor():
    global latest_event
    print(f"🚀 BlueGuard-Zero Active. Searching for: {TARGET_ID}")
    
    while True:
        target_rssi = None
        try:
            # FIX: Use return_adv=True to get RSSI from advertisement data
            devices = await BleakScanner.discover(timeout=2.0, return_adv=True)
            
            # The discover method now returns a dict where values are (device, advertisement_data)
            for d, adv in devices.values():
                if d.address.upper() == TARGET_ID.upper():
                    target_rssi = adv.rssi # Correctly accessing RSSI
                    break
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # --- PROXIMITY & SECURITY LOGIC ---
            if target_rssi is not None:
                # Human-readable proximity based on signal strength
                if target_rssi > -60:
                    proximity = "Immediate"
                elif target_rssi > -80:
                    proximity = "Near"
                else:
                    proximity = "Far"
                
                # Logic to trigger lock if device is too far away
                if target_rssi < -85:
                    status = "LOCK_TRIGGERED"
                    # To enable auto-lock, remove the '#' from the line below:
                    # os.system('rundll32.exe user32.dll, LockWorkStation')
                else:
                    status = "SAFE_PRESENT"
            else:
                status = "DEVICE_NOT_FOUND"
                target_rssi = "--"
                proximity = "Unknown"

            # Update Global Variable for the Website
            latest_event = {
                "timestamp": timestamp,
                "rssi": target_rssi,
                "status": status,
                "device": TARGET_ID,
                "proximity": proximity
            }

            # Sync to MongoDB (No schema definition required in Atlas)
            logs.insert_one(latest_event.copy())
            print(f"[{timestamp}] Signal: {target_rssi} | Status: {status} | Prox: {proximity}")

        except Exception as e:
            print(f"⚠️ Scan Error: {e}")

        await asyncio.sleep(1)

# 4. THREADING WRAPPER
def start_monitor_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bluetooth_monitor())

if __name__ == "__main__":
    # Start the Bluetooth monitor in its own thread
    monitor_thread = threading.Thread(target=start_monitor_loop, daemon=True)
    monitor_thread.start()

    # Start the Flask API - Ensure NO indentation before app.run
    print("🌐 Web API running at http://localhost:5000/data")
    app.run(port=5000, debug=False, use_reloader=False)



index.html: The frontend dashboard for visual alerts.
Code:
<html>
<head>
    <title>BlueGuard-Zero | Live Dashboard</title>
    <style>
        body { background: #0f172a; color: #38bdf8; font-family: 'Segoe UI', sans-serif; text-align: center; }
        .status-card { border: 2px solid #38bdf8; padding: 20px; display: inline-block; border-radius: 15px; margin-top: 50px; min-width: 320px; }
        .live-dot { height: 10px; width: 10px; background-color: #4ade80; border-radius: 50%; display: inline-block; animation: blink 1s infinite; }
        @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
        #status { transition: color 0.5s ease; font-size: 24px; margin: 10px 0; }
        .info { font-size: 18px; color: #94a3b8; margin: 5px 0; }
        #proximity { font-weight: bold; color: #fbbf24; } /* Amber color for Proximity */
    </style>
</head>
<body>
    <h1>BLUEGUARD-ZERO MONITORING</h1>
    <div class="status-card">
        <div class="live-dot"></div> LIVE SYSTEM FEED
        <h2 id="status">CONNECTING TO PYTHON...</h2>
        <p class="info" id="rssi">RSSI: -- dBm</p>
        <p class="info">Proximity: <span id="proximity">Unknown</span></p>
    </div>

    <script>
        async function refreshData() {
            try {
                const response = await fetch('http://localhost:5000/data');
                const data = await response.json();

                const statusElement = document.getElementById('status');
                const proxElement = document.getElementById('proximity');
                const rssiElement = document.getElementById('rssi');

                // 1. Update the Status
                statusElement.innerText = data.status;
                if (data.status === "SAFE_PRESENT") {
                    statusElement.style.color = "#4ade80"; // Green
                } else if (data.status === "LOCK_TRIGGERED") {
                    statusElement.style.color = "#ff4444"; // Red
                } else {
                    statusElement.style.color = "#38bdf8"; // Blue (Connecting)
                }

                // 2. Update the RSSI and Proximity (New Fields)
                rssiElement.innerText = `RSSI: ${data.rssi} dBm`;
                proxElement.innerText = data.proximity;

            } catch (error) {
                document.getElementById('status').innerText = "OFFLINE (RUN PYTHON)";
                document.getElementById('status').style.color = "#64748b";
                document.getElementById('rssi').innerText = "RSSI: -- dBm";
                document.getElementById('proximity').innerText = "Unknown";
            }
        }

        setInterval(refreshData, 2000);
        refreshData();
    </script>
</body>
</html>

64Bluetooth_/: Configuration and support files for the Bluetooth module:
Code:
void setup() {
  Serial.begin(9600); // Must match Python BAUD_RATE
}

void loop() {
  // If you have a sensor, read actual RSSI here.
  // For now, we simulate a "Strong" signal (-60)
  int simulatedRSSI = -60; 
  
  Serial.print("RSSI:");
  Serial.println(simulatedRSSI);
  
  delay(1000); // Send data every second
}

⚙️ Setup & Installation

Hardware: Connect your Arduino and Bluetooth module according to the schematics.
Arduino :<img width="1522" height="788" alt="image" src="https://github.com/user-attachments/assets/9081ae97-6963-4f5a-81eb-c5b560115870" />

Environment: ```bash pip install pymongo pybluez

Database: Ensure your MongoDB instance is running and update the connection string in security_system1.py.

Run: Execute the core script:

Bash
python security_system1.py

picture of the frontend portion:
<img width="1017" height="700" alt="image" src="https://github.com/user-attachments/assets/4ac5fcfd-5837-4105-b576-ae0114352aab" />
This gives the resullt when the headphones get connected using bluetooth, so it detects the headphones connected via bluetooth.
When not connected, it will show:
<img width="1033" height="782" alt="image" src="https://github.com/user-attachments/assets/0ad5309a-e95d-4cf0-b0fa-94b751c62a8c" />


The backend database triggers logs in the following way:
<img width="526" height="174" alt="image" src="https://github.com/user-attachments/assets/66fa96ff-b112-4d9f-b801-4d8ad528ffb9" />
It is like it detects the bluetooth headphone and triggers log

The circuit diagram: Demonstration via LTSpice softaware, the architecture drawing:
🔌 Hardware Architecture
To bridge the 5V Arduino logic with the 3.3V Bluetooth module, we use a voltage divider (1kΩ and 2kΩ resistors). This prevents overvoltage damage to the Bluetooth module.
<img width="1908" height="924" alt="image" src="https://github.com/user-attachments/assets/b55c2295-cf07-4f77-89b0-04a4d0fcf3ba" />

Component:  Arduino Pin:  Bluetooth Pin:
Power:       5:             VCC
Ground:     GND:            GND
Logic(TX):  Pin 11,RX : (via 1k/2k Divider)
Logic (RX),Pin 10,TX
