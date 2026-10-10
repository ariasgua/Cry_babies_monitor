# Baby Cry Monitoring System

**Paula Arias** · Raspberry Pi · Python · FFT · MQTT · Tkinter

An IoT prototype that listens for cry-like sounds on a Raspberry Pi and alerts a parent through a Windows desktop dashboard. The Pi analyzes short audio recordings and publishes its results over MQTT; the dashboard uses recent results to decide when to sound an alarm.

> **Safety note:** This is an educational prototype, not a medical device or a substitute for direct adult supervision. Its threshold-based detector can miss crying or mistake other sounds for crying.

## How it works

| Part | What it does | Main tools |
| --- | --- | --- |
| Raspberry Pi | Records audio, measures frequency-band energy, and publishes a cry state | USB microphone, ALSA `arecord`, NumPy, SciPy, Paho MQTT |
| MQTT broker | Passes status messages from the Pi to the laptop | Mosquitto |
| Parent laptop | Displays the latest state and sounds an alarm until it is acknowledged | Python, Tkinter, `winsound`, Paho MQTT |

1. The Pi records a one-second, 16 kHz mono audio frame to `frame_fft.wav`.
2. It removes the frame's DC offset and uses a real-valued FFT to measure spectral energy.
3. It compares energy in the **300–3000 Hz voice band** with energy in the **900–1100 Hz narrow-tone band**. A frame counts as cry-like when it is sufficiently loud, voice-band dominant, and not dominated by the narrow tone.
4. The Pi publishes `crying: true` after **two consecutive** cry-like frames, along with a timestamp and energy ratios.
5. The dashboard considers the **last ten** received states. Once it has ten samples, it activates the alarm if **at least seven** are active. The alarm remains active until the parent presses **Acknowledge**.

These are adjustable heuristics in the two Python scripts, not a trained baby-cry classifier. Different microphones and rooms need calibration.

## Repository files

| File | Purpose |
| --- | --- |
| [`cry_detector_publisher.py`](cry_detector_publisher.py) | Raspberry Pi audio capture, FFT analysis, and MQTT publisher |
| [`parent_dashboard.py`](parent_dashboard.py) | Windows dashboard, rolling decision, alarm, and acknowledgement button |
| [Project report](Baby%20Cry%20Monitoring%20System%20%E2%80%93%20End-to-End%20IoT%20Project%20_%20Jaime%20Martin%26Paula%20Arias.docx) | Original design and implementation report |
| [Video link document](VIDEO%20LINK.docx) | Original video link document |

## Set up the Raspberry Pi

You need a Raspberry Pi with a USB microphone and network access to the Windows laptop. On the Pi, install the recording tools, broker, and Python libraries:

```bash
sudo apt update
sudo apt install -y alsa-utils mosquitto mosquitto-clients python3-venv python3-numpy python3-scipy
sudo systemctl enable --now mosquitto
```

Clone this repository and install the MQTT client in a virtual environment:

```bash
git clone https://github.com/ariasgua/Cry_babies_monitor.git
cd Cry_babies_monitor
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install paho-mqtt
```

Check that the microphone appears with `arecord -l`. The script uses ALSA's default input device; if that is not your USB microphone, select the correct device in `record_frame()` in `cry_detector_publisher.py`.

The publisher connects to `localhost:1883`, while the dashboard must connect to the Pi over the local network. **The scripts have no MQTT username or password.** For a lab demonstration on a trusted network, Mosquitto needs a listener that the laptop can reach. Open a configuration file with `sudo nano /etc/mosquitto/conf.d/baby-monitor.conf` and enter:

```conf
listener 1883
allow_anonymous true
```

Restart it with `sudo systemctl restart mosquitto`. Keep this broker on a trusted local network and do not expose port `1883` to the internet. Find the Pi's local address with `hostname -I`; you will enter that address in the dashboard script.

## Set up the Windows dashboard

Install Python 3 on the laptop, download or clone this repository there, and run these commands in its folder:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install paho-mqtt
```

In `parent_dashboard.py`, change `BROKER_HOST` to the Pi's current local IP address. The default address in the script is specific to the original setup and may not work on your network. The laptop must be able to reach the Pi on TCP port `1883`.

For a custom alarm sound, place a WAV file named `mixkit-warning-alarm-buzzer-991.wav` beside `parent_dashboard.py`. If the file is absent, the app uses the system bell.

## Run the system

Start the detector on the Pi:

```bash
.venv/bin/python cry_detector_publisher.py
```

Then start the dashboard on the Windows laptop:

```powershell
.venv\Scripts\python.exe parent_dashboard.py
```

The dashboard shows the incoming cry state, recent cry ratio, and alarm status. Press **Acknowledge** after checking on the baby to clear an active alarm. Stop either script with `Ctrl+C` or close the dashboard window.

### MQTT messages

| Topic | Sent by | Contents |
| --- | --- | --- |
| `jaimem57/baby/cry_status` | Pi | JSON with `crying`, frame number, timestamp, total energy, voice ratio, and beep ratio |
| `jaimem57/baby/parent_ack` | Dashboard | JSON acknowledgement flag and timestamp |

The dashboard publishes an acknowledgement message when its button is pressed. The current Pi script does **not** subscribe to that topic; the button clears the dashboard's alarm locally.

## Limitations and next steps

- The manually chosen audio thresholds can give false positives and false negatives; the project has no measured accuracy claim.
- The Pi writes the latest recorded audio frame to a local `frame_fft.wav` file. Do not commit or share recordings unintentionally.
- The example broker configuration uses unencrypted, unauthenticated MQTT on a trusted local network.
- Useful next steps are testing with a labeled audio set, reporting precision and recall, improving noise handling, and adding authenticated MQTT.

## Credits

Developed by **Paula Arias and Jaime Martin**. See the [original project report](Baby%20Cry%20Monitoring%20System%20%E2%80%93%20End-to-End%20IoT%20Project%20_%20Jaime%20Martin%26Paula%20Arias.docx) for the full project write-up.
