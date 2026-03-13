import pandas as pd
import time
from datetime import datetime, timedelta
import subprocess
import os
import glob
import board
import adafruit_dht

# ============== CONFIGURATION - EDIT THESE ==============
SAMPLE_INTERVAL = 10
STORAGE_DIR = "/home/rin/Documents/ht2/storage"
GDRIVE_FOLDER = "Pi_Data/HT2"
DEVICE_NAME = "HT2"
UPLOAD_DELAY_MINUTES = 5
CONSECUTIVE_FAIL_LIMIT = 10
TEMP_MIN = -10
TEMP_MAX = 60
HUMIDITY_MIN = 0
HUMIDITY_MAX = 90
# ========================================================

os.makedirs(STORAGE_DIR, exist_ok=True)
dht_device = adafruit_dht.DHT22(board.D4)


def reset_sensor():
    global dht_device
    print("Sensor reset triggered - reinitializing...")
    try:
        dht_device.exit()
    except Exception:
        pass
    time.sleep(3)
    dht_device = adafruit_dht.DHT22(board.D4)
    print("Sensor reinitialized successfully")


def get_sensor_data():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            temp     = dht_device.temperature
            humidity = dht_device.humidity

            if temp is not None and humidity is not None:
                if TEMP_MIN <= temp <= TEMP_MAX and HUMIDITY_MIN <= humidity <= HUMIDITY_MAX:
                    return round(temp, 2), round(humidity, 2)
                else:
                    print(f"  Rejected out-of-range: T={temp}C, H={humidity}%")
                    time.sleep(1)
                    continue
            else:
                time.sleep(1)

        except (RuntimeError, OverflowError):
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                return None, None

    return None, None


def get_current_hour_start():
    now = datetime.now()
    return now.replace(minute=0, second=0, microsecond=0)


def create_filename_for_hour(hour_start):
    return f"{DEVICE_NAME}_data_{hour_start.strftime('%Y-%m-%d')}_{hour_start.strftime('%H')}.csv"


def get_pending_files():
    pattern = os.path.join(STORAGE_DIR, f"{DEVICE_NAME}_data_*.csv")
    return sorted(glob.glob(pattern))


def extract_hour_from_filename(filename):
    try:
        parts = os.path.basename(filename).replace('.csv', '').split('_')
        if len(parts) >= 4:
            return datetime.strptime(f"{parts[2]} {parts[3]}", "%Y-%m-%d %H")
    except:
        pass
    return None


def upload_file_to_gdrive(filepath):
    try:
        parts = os.path.basename(filepath).replace('.csv', '').split('_')
        if len(parts) >= 3:
            date_str = parts[2]
            year, month, date = date_str[0:4], date_str[5:7], date_str[8:10]
        else:
            now = datetime.now()
            year, month, date = now.strftime("%Y"), now.strftime("%m"), now.strftime("%d")

        folder_path = f"{GDRIVE_FOLDER}/{year}/{month}/{date}"

        subprocess.run(["rclone", "mkdir", f"gdrive:{folder_path}"],
                       check=False, capture_output=True)

        result = subprocess.run(["rclone", "copy", filepath, f"gdrive:{folder_path}"],
                                capture_output=True, text=True)

        if result.returncode == 0:
            return True
        else:
            print(f"  Upload failed: {result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"  Upload error: {e}")
        return False


def upload_pending_files(current_active_file=None):
    pending_files = get_pending_files()

    if current_active_file:
        pending_files = [f for f in pending_files if f != current_active_file]

    if not pending_files:
        print("  No pending files to upload")
        return True

    print(f"\n{'='*60}")
    print(f"  UPLOAD ATTEMPT - {len(pending_files)} file(s) pending")
    print(f"{'='*60}")

    uploaded_count = 0
    failed_count   = 0

    for filepath in pending_files:
        filename  = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        hour_dt   = extract_hour_from_filename(filepath)
        hour_range = (
            f"{hour_dt.strftime('%H:00')}-{(hour_dt + timedelta(hours=1)).strftime('%H:00')}"
            if hour_dt else "Unknown"
        )

        print(f"  Uploading: {filename} ({hour_range}, {file_size} bytes)...")

        if upload_file_to_gdrive(filepath):
            try:
                os.remove(filepath)
                print(f"  Uploaded & deleted: {filename}")
                uploaded_count += 1
            except Exception as e:
                print(f"  Uploaded but failed to delete: {e}")
                uploaded_count += 1
        else:
            print(f"  Failed: {filename}")
            failed_count += 1

    print(f"{'='*60}")
    print(f"  Summary: {uploaded_count} uploaded, {failed_count} failed")
    print(f"{'='*60}\n")

    return failed_count == 0


def should_upload_now():
    now = datetime.now()
    return now.minute == UPLOAD_DELAY_MINUTES and now.second < 60


def main():
    print("="*60)
    print(f"  DATA LOGGER STARTED - Device: {DEVICE_NAME}")
    print(f"  Sampling: Every {SAMPLE_INTERVAL}s | Upload: At :{UPLOAD_DELAY_MINUTES:02d} past each hour")
    print(f"  Storage: {STORAGE_DIR}")
    print(f"  Google Drive: {GDRIVE_FOLDER}")
    print(f"  Valid range: {TEMP_MIN}C to {TEMP_MAX}C | {HUMIDITY_MIN}% to {HUMIDITY_MAX}%")
    print("="*60)

    current_hour_start       = get_current_hour_start()
    current_filename         = create_filename_for_hour(current_hour_start)
    current_filepath         = os.path.join(STORAGE_DIR, current_filename)
    sample_count             = 0
    failed_reads             = 0
    consecutive_fails        = 0
    last_upload_check_minute = -1

    print(f"\n  Recording started: {current_filename}")
    print(f"  Period: {current_hour_start.strftime('%H:%M')} - "
          f"{(current_hour_start + timedelta(hours=1)).strftime('%H:%M')}")

    print("\n  Checking for pending files from previous run...")
    upload_pending_files(current_active_file=current_filepath)

    try:
        while True:
            current_time = datetime.now()
            hour_start   = get_current_hour_start()

            # New hour - roll over to new file
            if hour_start != current_hour_start:
                print(f"\n  Hour completed: {current_filename} ({sample_count} samples)")
                current_hour_start = hour_start
                current_filename   = create_filename_for_hour(current_hour_start)
                current_filepath   = os.path.join(STORAGE_DIR, current_filename)
                sample_count       = 0
                print(f"\n  New hour: {current_filename}")
                print(f"  Period: {current_hour_start.strftime('%H:%M')} - "
                      f"{(current_hour_start + timedelta(hours=1)).strftime('%H:%M')}")

            # ── UPLOAD TRIGGER (before sensor read so failures don't block it) ──
            current_minute = current_time.minute

            if should_upload_now() and last_upload_check_minute != current_minute:
                last_upload_check_minute = current_minute
                print(f"\n  Upload time! ({current_time.strftime('%H:%M')})")
                print(f"  Excluding current file: {os.path.basename(current_filepath)}")
                upload_pending_files(current_active_file=current_filepath)

            if current_minute != UPLOAD_DELAY_MINUTES:
                last_upload_check_minute = -1

            # ── SENSOR READ ──────────────────────────────────────────────
            temp, humidity = get_sensor_data()

            if temp is None or humidity is None:
                failed_reads      += 1
                consecutive_fails += 1
                print(f"  [{current_time.strftime('%H:%M:%S')}] Sensor failed "
                      f"(Consecutive: {consecutive_fails} | Total: {failed_reads})")

                if consecutive_fails >= CONSECUTIVE_FAIL_LIMIT:
                    print(f"  {consecutive_fails} consecutive failures - triggering auto-reset")
                    reset_sensor()
                    consecutive_fails = 0

                time.sleep(SAMPLE_INTERVAL)
                continue

            consecutive_fails = 0
            timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")

            # ── WRITE TO CSV ─────────────────────────────────────────────
            data = {
                "device":        DEVICE_NAME,
                "timestamp":     timestamp,
                "temperature_C": temp,
                "humidity_%":    humidity
            }

            df = pd.DataFrame([data])
            df.to_csv(current_filepath, mode='a',
                      header=not os.path.exists(current_filepath),
                      index=False)

            sample_count += 1
            print(f"[{timestamp}] T={temp}C, H={humidity}% | "
                  f"Samples: {sample_count} | Fails: {failed_reads}")

            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("  LOGGER STOPPED BY USER")
        print("="*60)
        print("\n  Attempting final upload of all pending files...")
        upload_pending_files(current_active_file=None)
        dht_device.exit()

        remaining = get_pending_files()
        if remaining:
            print(f"\n  {len(remaining)} file(s) still pending upload:")
            for f in remaining:
                print(f"    - {os.path.basename(f)}")
        else:
            print("\n  All files uploaded successfully!")

        print("\n  Goodbye!\n")


if __name__ == "__main__":
    main()
