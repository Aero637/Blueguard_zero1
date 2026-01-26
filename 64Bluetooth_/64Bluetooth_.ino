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







