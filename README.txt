Baby Cry Monitoring System – README
Jaime Martin, Paula Arias

1. Project description
   This project is an IoT baby-cry monitor.
   The Raspberry Pi records 1-second audio frames with a USB microphone, runs an FFT to decide if the sound looks like crying, and publishes JSON messages over MQTT.
   A Windows laptop runs a “parent dashboard” GUI that subscribes to those messages, keeps a short history, and raises a loud alarm if most recent frames look like crying. The alarm keeps sounding until the parent presses “Acknowledge”.

2. How to run the code

Raspberry Pi (publisher – cry_detector_publisher.py)

1. Make sure Mosquitto broker is installed and running on the Pi:

   * `sudo apt update`
   * `sudo apt install -y mosquitto mosquitto-clients`
   * `sudo systemctl enable mosquitto`
   * `sudo systemctl start mosquitto`
2. Install Python packages:

   * `sudo apt install -y python3-pip python3-numpy python3-scipy`
   * `pip3 install paho-mqtt`
3. Plug in the USB microphone and test:
5. Run the cry detector:
   * `python3 cry_detector_publisher.py`

Laptop (subscriber / dashboard – parent_dashboard.py)

1. Install Python 3 (if not already installed).
2. Install required packages:
   * `pip install paho-mqtt`
   * `pip install numpy scipy` (only needed if you later extend processing on laptop)
4. Edit `BROKER_HOST` in `parent_dashboard.py` so it matches the Pi’s IP address (e.g. `172.20.10.3`).
5. Run the dashboard from that folder:
   * `python parent_dashboard.py`

3) External libraries and tools used

Python libraries

* `paho-mqtt` – MQTT client for publish/subscribe.
* `numpy` – numerical arrays and FFT.
* `scipy` (scipy.io.wavfile) – reading WAV files on the Pi.
* `tkinter` – built-in Python GUI toolkit for the parent dashboard.
* `winsound` – built-in Windows module used to play the alarm WAV file.

System tools / software

* `arecord` – ALSA command-line recorder on the Raspberry Pi.
* `aplay` – ALSA player used for quick audio tests on the Pi.
* `mosquitto` – MQTT broker running on the Raspberry Pi.
