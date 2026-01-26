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


