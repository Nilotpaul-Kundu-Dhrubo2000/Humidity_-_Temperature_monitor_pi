# HTx Raspberry Pi Data Logger

Raspberry Pi based **temperature and humidity data logger** using **DHT22**.

## Features

- Hourly CSV logging
- Automatic Google Drive upload
- Remote access via Tailscale
- RTC time backup (DS3231)
- systemd service for auto-start

---
# 1. Log in to Pi (Connected via local network)

```bash
ssh rin@device_name.local
- then enter password which was saved via installtion
Remember, while installtion, hostname must be ht_device_number and username rin, then you will get write ssh rin@ht1.local like that. 
```

# 2. Install Tailscale (Remote Access)

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

Example devices:

Laptop: laptop-8flnl6e0 → 100.119.9.96  
Command Prompt → 100.111.243.63  


# 3. Install System Packages

Update system:

```bash
sudo apt update
sudo apt upgrade
```

Install required packages (outside virtual environment):

```bash
sudo apt install python3-pip python3-dev python3-venv gpiod python3-libgpiod
```

---

# 4. Create Virtual Environment 
```bash
python3 -m venv venv
```
Activate it in the home directory by 
```bash
source venv/bin/activate
```

# 5. Install Python Libraries
These libraries will be needed to run both codes. 
```bash
pip install adafruit-blinka adafruit-circuitpython-dht RPi.GPIO pandas
```

---

# 6. Install rclone (Google Drive Sync)

```bash
curl https://rclone.org/install.sh | sudo bash
```

---

# 7. Configure Google Drive

Run configuration:

```bash
rclone config
```

Follow these steps:

```
n (new remote)
Name: gdrive
Storage: drive
Client ID: Enter
Client Secret: Enter
Scope: 1
Root folder ID: Enter
Service account: Enter
Advanced config: n
Auto config: n
```

You will receive a **URL**.

---

## Authorize from Laptop

Run on laptop:

```bash
rclone authorize "drive" "eyJzY29wZSI6ImRyaXZlIn0"
```

Steps:

1. Open the URL in a browser
2. Login to your Google account
3. Copy the authorization code
4. Paste it in the Raspberry Pi terminal
5. Paste the returned token

Finish configuration:

```
Configure as team drive: n
Confirm: y
Quit: q
```

---

# 8. Test Google Drive Connection

```bash
rclone lsd gdrive:
```

If successful, it will list your Google Drive folders.

---

# 9. Enable DS3231 RTC

Edit config:

```bash
sudo nano /boot/firmware/config.txt
```

Add the following at the bottom:

```
dtoverlay=i2c-rtc,ds3231
```

Reboot:

```bash
sudo reboot
```

---

# 10. Install Hardware Clock Tools

```bash
sudo apt install util-linux -y
```

Check time:

```bash
timedatectl
```

Example expected output:

```
Local time: Fri 2026-03-13 23:46:54 +06
Universal time: Fri 2026-03-13 17:46:54 UTC
RTC time: Fri 2026-03-13 17:46:54
Time zone: Asia/Dhaka
System clock synchronized: yes
NTP service: active
```

---

# 11. Create systemd Service

Create service file:

```bash
sudo nano /etc/systemd/system/datalogger.service
```

Example service configuration:

```ini
[Unit]
Description=HT Data Logger
After=network.target

[Service]
User=rin
WorkingDirectory=/home/rin/Documents/ht_device_number
ExecStart=/home/rin/venv/bin/python /home/rin/Documents/ht_device_number/datalogger.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

# 12. Enable and Start Logger

Reload systemd:

```bash
sudo systemctl daemon-reload
```

Enable service:

```bash
sudo systemctl enable datalogger.service
```

Start service:

```bash
sudo systemctl start datalogger.service
```
Restart service:

```bash
sudo systemctl restart datalogger.service
```
Stop service:

```bash
sudo systemctl stop datalogger.service
```
---

# 13. View Live Logger Output

```bash
journalctl -u datalogger.service -f
```

---

# 14. Download Files via Tailscale (Linux)

Example:

```bash
scp rin@<ht1-tailscale-ip>:/home/rin/Documents/ht1/storage/HT1_data_2026-02-28_01.csv ~/Downloads/
```

---

# Directory Structure

```
Documents/
 ├── ht3/
 │   ├── datalogger.py
 │   ├── dht22_test.py
 │   └── storage/
 │       └── HT3_data_YYYY-MM-DD_HH.csv
```

---

# Example CSV Output

```
device,timestamp,temperature_C,humidity_%
HT3,2026-03-14 00:05:08,29.7,65.9
```

---

# Features

✔ Hourly CSV logging  
✔ Automatic Google Drive upload  
✔ Sensor auto-reset on failure  
✔ Works offline and syncs later  
✔ systemd auto-start  
✔ Remote access via Tailscale  

---
