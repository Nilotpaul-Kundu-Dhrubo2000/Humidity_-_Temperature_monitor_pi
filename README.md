HTx Raspberry Pi Data Logger

Raspberry Pi based temperature and humidity data logger using DHT22, with:

Hourly CSV logging

Automatic Google Drive upload

Remote access via Tailscale

RTC time backup (DS3231)

systemd service for auto-start

1. Install Tailscale (Remote Access)
curl -fsSL https://tailscale.com/install.sh | sh

Example devices:

Laptop: laptop-8flnl6e0 → 100.119.9.96
Command Prompt → 100.111.243.63

Test connection:

ping 100.119.9.96 -c 4
2. Download Files via Tailscale (Linux)

Example:

scp rin@<ht1-tailscale-ip>:/home/rin/Documents/ht1/storage/HT1_data_2026-02-28_01.csv ~/Downloads/
3. Install System Packages

Update system:

sudo apt update
sudo apt upgrade

Install required packages (outside virtual environment):

sudo apt install python3-pip python3-dev python3-venv gpiod python3-libgpiod
4. Install Python Libraries
pip install adafruit-blinka adafruit-circuitpython-dht RPi.GPIO pandas
5. Install rclone (Google Drive Sync)
curl https://rclone.org/install.sh | sudo bash
6. Configure Google Drive

Run configuration:

rclone config

Follow these steps:

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

You will receive a URL.

Authorize from Laptop

On your laptop run:

rclone authorize "drive" "eyJzY29wZSI6ImRyaXZlIn0"

Open the provided URL

Login to Google

Copy the authorization code

Paste it into the Raspberry Pi terminal

Then paste the token provided by the laptop.

Finish configuration:

Configure as team drive: n
Confirm: y
Quit: q
7. Test Google Drive Connection
rclone lsd gdrive:

If successful, it will list your Google Drive folders.

8. Enable DS3231 RTC

Edit config:

sudo nano /boot/firmware/config.txt

Add at the bottom:

dtoverlay=i2c-rtc,ds3231

Reboot:

sudo reboot
9. Install Hardware Clock Tools
sudo apt install util-linux -y

Check time:

timedatectl

Expected output example:

Local time: Fri 2026-03-13 23:46:54 +06
Universal time: Fri 2026-03-13 17:46:54 UTC
RTC time: Fri 2026-03-13 17:46:54
Time zone: Asia/Dhaka
System clock synchronized: yes
NTP service: active
10. Create systemd Service

Create service file:

sudo nano /etc/systemd/system/datalogger.service

Example:

[Unit]
Description=HT Data Logger
After=network.target

[Service]
User=rin
WorkingDirectory=/home/rin/Documents/ht3
ExecStart=/home/rin/venv/bin/python /home/rin/Documents/ht3/datalogger.py
Restart=always

[Install]
WantedBy=multi-user.target
11. Enable and Start Logger

Reload systemd:

sudo systemctl daemon-reload

Enable service:

sudo systemctl enable datalogger.service

Start service:

sudo systemctl start datalogger.service
12. View Live Logger Output
journalctl -u datalogger.service -f
Directory Structure
Documents/
 ├── ht3/
 │   ├── datalogger.py
 │   ├── dht22_test.py
 │   └── storage/
 │       └── HT3_data_YYYY-MM-DD_HH.csv
Data Format

Example CSV:

device,timestamp,temperature_C,humidity_%
HT3,2026-03-14 00:05:08,29.7,65.9
Features

✔ Hourly CSV logging
✔ Automatic Google Drive upload
✔ Sensor auto-reset on failure
✔ Works offline and syncs later
✔ systemd auto-start
✔ Remote access via Tailscale
