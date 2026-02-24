#!/usr/bin/env python3
import subprocess
import time
import json

import numpy as np
from scipy.io import wavfile
import paho.mqtt.client as mqtt

# settings
BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "jaimem57/baby/cry_status"

SAMPLE_RATE = 16000
FRAME_DURATION = 1.0
MIN_TOTAL_ENERGY = 1e7
ALERT_FRAMES = 2




FRAME_WAV = "frame_fft.wav"

# thresholds
VOICE_RATIO_THRESHOLD = 0.70
BEEP_RATIO_MAX = 0.60







def record_frame(filename=FRAME_WAV):
    cmd = [
        "arecord",
        "-q",
        "-d", str(int(FRAME_DURATION)),
        "-f", "S16_LE",
        "-r", str(SAMPLE_RATE),
        "-c", "1",
        filename,
    ]
    subprocess.run(cmd, check=True)






def band_energy(mag, fs, n, f_low, f_high):
    # energy in band
    k_low = int(f_low * n / fs)
    k_high = min(int(f_high * n / fs), len(mag) - 1)
    if k_high <= k_low:
        return 0.0
    return float(np.sum(mag[k_low:k_high] ** 2))









def analyze_frame(filename=FRAME_WAV):
    # fft and ratios
    fs, data = wavfile.read(filename)

    if fs != SAMPLE_RATE:
        print(f"warning: expected fs={SAMPLE_RATE}, got {fs}")

    data = data.astype(np.float32)
    n = len(data)
    if n == 0:
        return False, 0.0, 0.0, 0.0

    data = data - np.mean(data)

    spectrum = np.fft.rfft(data)
    mag = np.abs(spectrum)

    total_energy = float(np.sum(mag ** 2)) + 1e-9

    voice_energy = band_energy(mag, fs, n, 300.0, 3000.0)
    beep_energy = band_energy(mag, fs, n, 900.0, 1100.0)

    voice_ratio = voice_energy / total_energy
    beep_ratio = beep_energy / total_energy

    is_loud = total_energy > MIN_TOTAL_ENERGY
    looks_like_voice = voice_ratio > VOICE_RATIO_THRESHOLD
    looks_like_beep = beep_ratio > BEEP_RATIO_MAX

    is_cry_frame = is_loud and looks_like_voice and (not looks_like_beep)

    return is_cry_frame, total_energy, voice_ratio, beep_ratio







def main():
    client = mqtt.Client()
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()

    consecutive_cry_frames = 0
    frame_counter = 0

    try:
        while True:
            frame_counter += 1
            print(f"\nrecording frame {frame_counter} ...")
            record_frame(FRAME_WAV)

            is_cry_frame, total_energy, voice_ratio, beep_ratio = analyze_frame(
                FRAME_WAV
            )

            if is_cry_frame:
                consecutive_cry_frames += 1
            else:
                consecutive_cry_frames = 0

            crying_state = consecutive_cry_frames >= ALERT_FRAMES

            payload = {
                "crying": crying_state,
                "frame": frame_counter,
                "timestamp": time.time(),
                "total_energy": total_energy,
                "voice_ratio": voice_ratio,
                "beep_ratio": beep_ratio,
            }

            client.publish(TOPIC, json.dumps(payload))

            print(
                f"frame {frame_counter}: "
                f"is_cry_frame={is_cry_frame}, "
                f"crying_state={crying_state}, "
                f"voice_ratio={voice_ratio:.3f}, "
                f"beep_ratio={beep_ratio:.3f}, "
                f"total_energy={total_energy:.1e}"
            )

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\nstopping cry detector")

    finally:
        client.loop_stop()
        client.disconnect()






if __name__ == "__main__":
    main()
