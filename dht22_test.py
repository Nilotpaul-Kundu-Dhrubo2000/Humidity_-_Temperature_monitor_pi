import adafruit_dht
import board
import time

# Initialize DHT22 sensor on GPIO4 (Physical Pin 7)
dht_device = adafruit_dht.DHT22(board.D4)

print("DHT22 Sensor Test")
print("=" * 50)
print("Sensor: DHT22")
print("Pin: GPIO4 (Physical Pin 7)")
print("Reading temperature and humidity...")
print("Press CTRL+C to exit")

try:
    while True:
        try:
            temperature = dht_device.temperature
            humidity    = dht_device.humidity

            if temperature is not None and humidity is not None:
                print(f"✅ Temp: {temperature:.1f}°C  |  Humidity: {humidity:.1f}%")
            else:
                print("⚠️  No reading — sensor returned None")

        except (RuntimeError, OverflowError) as error:
            # RuntimeError: common DHT22 timing glitch
            # OverflowError: adafruit_dht bug with Python 3.13
            print(f"⚠️  Reading error (will retry): {error}")

        time.sleep(2)

except KeyboardInterrupt:
    dht_device.exit()
    print("\nTest stopped.")
