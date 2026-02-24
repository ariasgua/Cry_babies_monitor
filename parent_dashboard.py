#!/usr/bin/env python3
import json
import time
import tkinter as tk
import os

import paho.mqtt.client as mqtt

# sound on windows
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# settings
BROKER_HOST = "172.20.10.3"
BROKER_PORT = 1883

TOPIC_STATUS = "jaimem57/baby/cry_status"
TOPIC_ACK = "jaimem57/baby/parent_ack"

HISTORY_LENGTH = 10
ALARM_RATIO_THRESHOLD = 0.7
MIN_SAMPLES_FOR_ALARM = 10

ALARM_WAV = os.path.join(
    os.path.dirname(__file__),
    "mixkit-warning-alarm-buzzer-991.wav",
)

state = {
    "crying_instant": False,
    "last_update": None,
    "history": [],
    "alarm_active": False,
    "cry_ratio": 0.0,
}

client = mqtt.Client()

# ui
root = tk.Tk()
root.title("Baby Cry Monitor - Parent Dashboard")
root.geometry("900x550")
root.configure(bg="#111111")

status_label = tk.Label(
    root,
    text="status: unknown",
    font=("Helvetica", 40, "bold"),
    bg="#111111",
    fg="white",
    width=25,
    height=2,
)
status_label.pack(padx=20, pady=25)

alarm_label = tk.Label(
    root,
    text="no active alarm.",
    font=("Helvetica", 20),
    bg="#111111",
    fg="white",
    justify="center",
)
alarm_label.pack(padx=20, pady=10)

ratio_label = tk.Label(
    root,
    text="cry ratio: 0.00",
    font=("Helvetica", 16),
    bg="#111111",
    fg="white",
)
ratio_label.pack(padx=20, pady=5)

time_label = tk.Label(
    root,
    text="last update: (none)",
    font=("Helvetica", 14),
    bg="#111111",
    fg="white",
)
time_label.pack(padx=20, pady=5)

instant_label = tk.Label(
    root,
    text="instant cry flag: false",
    font=("Helvetica", 14),
    bg="#111111",
    fg="white",
)
instant_label.pack(padx=20, pady=5)


def on_ack_button():
    # reset alarm
    state["alarm_active"] = False
    state["history"].clear()
    state["cry_ratio"] = 0.0
    update_ui()

    if HAS_WINSOUND:
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass

    payload = json.dumps({"ack": True, "timestamp": time.time()})
    try:
        client.publish(TOPIC_ACK, payload)
    except Exception as e:
        print("failed to publish ack:", e)


ack_button = tk.Button(
    root,
    text="acknowledge alarm",
    font=("Helvetica", 18, "bold"),
    command=on_ack_button,
)
ack_button.pack(padx=20, pady=25)







def update_ui():
    # main banner
    if state["alarm_active"]:
        status_text = "BABY CRYING – ALARM"
        status_color = "#ff3333"
    else:
        status_text = "quiet"
        status_color = "#44dd44"

    status_label.config(text=status_text, fg=status_color)

    hist = state["history"]
    if hist:
        ratio = sum(hist) / len(hist)
    else:
        ratio = 0.0
    state["cry_ratio"] = ratio

    ratio_label.config(text=f"cry ratio (last {len(hist)}): {ratio:.2f}")

    instant_label.config(
        text=f"instant cry flag: {state['crying_instant']}"
    )

    if state["last_update"] is None:
        time_text = "last update: (none)"
    else:
        time_text = "last update: " + time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(state["last_update"]),
        )
    time_label.config(text=time_text)

    if state["alarm_active"]:
        alarm_label.config(
            text=(
                "alarm: baby has been crying in most recent frames\n"
                "go check the baby then press acknowledge"
            ),
            fg="#ff3333",
        )
    else:
        alarm_label.config(text="no active alarm.", fg="white")









def alarm_beeper():
    # sound loop
    if state["alarm_active"]:
        if HAS_WINSOUND and os.path.exists(ALARM_WAV):
            try:
                winsound.PlaySound(
                    ALARM_WAV,
                    winsound.SND_FILENAME | winsound.SND_ASYNC,
                )
            except Exception as e:
                print("error playing alarm sound:", e)
                root.bell()
        else:
            root.bell()
    else:
        if HAS_WINSOUND:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass

    root.after(1000, alarm_beeper)


# mqtt callbacks
def on_connect(client, userdata, flags, rc):
    print("connected to broker with result code", rc)
    client.subscribe(TOPIC_STATUS)



def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception as e:
        print("bad payload:", e)
        return

    now = time.time()

    crying_flag = bool(payload.get("crying"))
    state["crying_instant"] = crying_flag
    state["last_update"] = now

    hist = state["history"]
    hist.append(1 if crying_flag else 0)
    if len(hist) > HISTORY_LENGTH:
        hist.pop(0)

    if hist:
        ratio = sum(hist) / len(hist)
    else:
        ratio = 0.0
    state["cry_ratio"] = ratio

    if (
        not state["alarm_active"]
        and len(hist) >= MIN_SAMPLES_FOR_ALARM
        and ratio >= ALARM_RATIO_THRESHOLD
    ):
        state["alarm_active"] = True

    print(
        f"received frame={payload.get('frame')}, "
        f"instant_cry={crying_flag}, "
        f"ratio={ratio:.2f}, "
        f"hist_len={len(hist)}, "
        f"alarm_active={state['alarm_active']}"
    )

    update_ui()



client.on_connect = on_connect
client.on_message = on_message


def start_mqtt():
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()


start_mqtt()
update_ui()
root.after(1000, alarm_beeper)

try:
    root.mainloop()
finally:
    client.loop_stop()
    client.disconnect()
