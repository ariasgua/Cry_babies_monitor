<p align="center">
  <img src="assets/hero.svg" alt="Baby Cry Monitoring System: Raspberry Pi to MQTT to parent dashboard" width="100%">
</p>

<p align="center"><strong>Listen → analyze → publish → alert</strong></p>
<p align="center">
  <a href="#the-system">See the system</a> ·
  <a href="#how-a-cry-like-frame-is-detected">Explore the detector</a> ·
  <a href="#run-the-prototype">Run it</a> ·
  <a href="#project-materials">Project files</a>
</p>

> **Safety note:** This is an educational prototype, not a medical device or a substitute for direct adult supervision. Its rule-based detector can miss crying or mistake other sounds for crying.

## Why we built it

As our EE250 final project at USC, **Paula Arias and Jaime Martin** wanted to connect signal processing with a complete, working IoT system. Memories of growing up with younger siblings inspired a simple question: could a Raspberry Pi listen for cry-like sounds and notify someone on a separate computer?

The result connects a USB microphone, a Raspberry Pi 4, an MQTT broker, and a Windows dashboard. It demonstrates audio capture, FFT analysis, messages between devices, and a parent acknowledgement workflow.

| **1 second** | **16 kHz** | **2 frames** | **7 of 10** |
| :---: | :---: | :---: | :---: |
| Audio per sample | Mono capture rate | Positive frames before the Pi reports crying | Recent positive states before the dashboard alarms |

## The system

![System architecture: microphone and Raspberry Pi classify audio, Mosquitto routes status, and a Windows dashboard alerts the parent. The dashboard sends an acknowledgement to MQTT, but the current Pi script does not receive it.](assets/architecture.svg)

**Two physical nodes, one logical broker:** Mosquitto runs on the Pi. The dashboard subscribes to the Pi's JSON status messages over the local network and keeps the alarm active until a parent clicks **Acknowledge**. The dashboard publishes an acknowledgement event, but the current Pi script does not subscribe to that event; the button clears the alarm on the laptop.

## How a cry-like frame is detected

![Analysis bands: 300 to 3000 Hz voice band and 900 to 1100 Hz narrow-tone band, plus the detector's three thresholds.](assets/frequency-bands.svg)

The Pi records one-second audio frames with `arecord`, reads the WAV file with SciPy, removes the DC offset, and computes an FFT with NumPy. It checks the broad voice band while rejecting frames dominated by a narrow beep-like tone. It then requires **two consecutive positive frames** before publishing an active cry state. The dashboard waits for **ten received states** and sounds an alarm when **at least seven** are active. These numbers come from the current Python scripts.

<details>
<summary><strong>Click to see the exact signal checks</strong></summary>

The publisher calculates:

- `total_energy`: sum of squared FFT magnitudes.
- `voice_ratio`: energy from **300–3000 Hz** divided by total energy.
- `beep_ratio`: energy from **900–1100 Hz** divided by total energy.

A frame is marked cry-like only when **all three** checks pass:

```text
total_energy > 10,000,000
voice_ratio > 0.70
beep_ratio <= 0.60
```

The narrow band lies inside the broader voice band; rejecting a large narrow-band ratio helps avoid labeling a pure tone as a cry. These are hand-tuned heuristics, not an audio machine-learning model.

</details>

## Run the prototype

You need a **Raspberry Pi 4 with a USB microphone**, a **Windows laptop**, and a trusted local network. The team used a SunFounder USB 2.0 Mini Microphone Model B and a mobile hotspot for the original demonstration. Other microphones may need threshold or device adjustments.

### 1. Prepare the Raspberry Pi

Install the audio tools, Mosquitto, and Python dependencies:

```bash
sudo apt update
sudo apt install -y alsa-utils mosquitto mosquitto-clients python3-venv python3-numpy python3-scipy
sudo systemctl enable --now mosquitto
```

Clone this repository, make a virtual environment, and install the MQTT client:

```bash
git clone https://github.com/ariasgua/Cry_babies_monitor.git
cd Cry_babies_monitor
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install paho-mqtt
```

Check the microphone with `arecord -l`. The script records from ALSA's default input device; if necessary, select your USB microphone in `record_frame()` in `cry_detector_publisher.py`.

<details>
<summary><strong>Click to configure the MQTT broker for a local demo</strong></summary>

The Pi script connects to `localhost:1883`. The laptop needs to reach that same broker at the Pi's local IP address. The current scripts do not supply MQTT credentials. On a **trusted, isolated local network**, open a Mosquitto configuration file:

```bash
sudo nano /etc/mosquitto/conf.d/baby-monitor.conf
```

Enter the following lab configuration, save it, and restart Mosquitto:

```conf
listener 1883
allow_anonymous true
```

```bash
sudo systemctl restart mosquitto
hostname -I
```

Use the displayed Pi IP address in the next step. This listener accepts unauthenticated connections, so keep port `1883` off the public internet. For deployment outside a lab, add authentication and encryption to both broker and clients.

</details>

### 2. Prepare the Windows laptop

Download or clone this repository on the laptop. In its folder, run:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install paho-mqtt
```

Open `parent_dashboard.py` and set `BROKER_HOST` to the Pi's **current local IP address**. The value in the file comes from the original lab setup and may not work on your network. The laptop must be able to reach port `1883` on the Pi.

The dashboard looks for `mixkit-warning-alarm-buzzer-991.wav` beside its script. If that file is absent, it uses the system bell.

### 3. Start both programs

On the Pi:

```bash
.venv/bin/python cry_detector_publisher.py
```

On the Windows laptop:

```powershell
.venv\Scripts\python.exe parent_dashboard.py
```

Watch the dashboard's current state and recent cry ratio. If an alarm sounds, check on the baby and press **Acknowledge** to clear the laptop alarm. Stop the Pi script with `Ctrl+C` and close the dashboard window when finished.

## Explore the messages

| MQTT topic | Publisher | Purpose |
| --- | --- | --- |
| `jaimem57/baby/cry_status` | Raspberry Pi | Frame index, timestamp, energy measurements, and smoothed `crying` state |
| `jaimem57/baby/parent_ack` | Laptop | Acknowledgement flag and timestamp |

<details>
<summary><strong>Click to see an example status message</strong></summary>

The values below are illustrative; the keys match the publisher's JSON payload.

```json
{
  "crying": true,
  "frame": 12,
  "timestamp": 1710000000.0,
  "total_energy": 16000000.0,
  "voice_ratio": 0.82,
  "beep_ratio": 0.08
}
```

The dashboard bases its alarm on recent `crying` values. The acknowledgement button publishes `{"ack": true, "timestamp": ...}` and clears the dashboard's local history and alarm.

</details>

## What we learned and what comes next

Working with real microphone data made FFT analysis concrete. MQTT separated sensing from the dashboard, and a rolling window helped prevent single-frame events from immediately becoming alarms. The original [project report](Baby%20Cry%20Monitoring%20System%20%E2%80%93%20End-to-End%20IoT%20Project%20_%20Jaime%20Martin%26Paula%20Arias.docx) discusses the design decisions and lessons learned.

The detector still relies on manually tuned thresholds. Microphone sensitivity, background voices, and room acoustics can change its behavior; we have not established a measured detection accuracy. The Pi writes each recorded frame to a local `frame_fft.wav` file, and the lab MQTT configuration has no authentication or encryption. Future work includes a labeled evaluation set, precision and recall measurements, adaptive noise handling, and authenticated MQTT.

## Project materials

| File | What's inside |
| --- | --- |
| [`cry_detector_publisher.py`](cry_detector_publisher.py) | Pi audio capture, FFT analysis, and MQTT publisher |
| [`parent_dashboard.py`](parent_dashboard.py) | Windows Tkinter dashboard, rolling alarm, and acknowledgement |
| [End-to-end project report](Baby%20Cry%20Monitoring%20System%20%E2%80%93%20End-to-End%20IoT%20Project%20_%20Jaime%20Martin%26Paula%20Arias.docx) | Full team write-up, including design and limitations |
| [Video link document](VIDEO%20LINK.docx) | Original demo link document |

**Built by Paula Arias and Jaime Martin for USC EE250.**
