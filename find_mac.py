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