
import soundcard as sc
import numpy as np
import threading
import time
import sys

# Global flag for thread control
running = True

def monitor_device(mic):
    fs = 44100
    try:
        with mic.recorder(samplerate=fs) as recorder:
            while running:
                data = recorder.record(numframes=int(fs*0.2))
                vol = np.max(np.abs(data))
                if vol > 0.01: # Threshold for activity
                    print(f"\n[Sound Detected] Device: {mic.name} | Level: {vol:.4f}")
    except Exception as e:
        # Ignore errors from unused devices
        pass

def main():
    global running
    print("Scanning all available loopback devices...")
    try:
        mics = sc.all_microphones(include_loopback=True)
        # Filter for actual loopback devices
        loopbacks = [m for m in mics if m.isloopback]
    except Exception as e:
        print(f"Error listing microphones: {e}")
        return

    if not loopbacks:
        print("No loopback devices found!")
        return

    print(f"Found {len(loopbacks)} loopback candidates:")
    for m in loopbacks:
        print(f" - {m.name}")

    print("\nStarting Multi-Device Monitor...")
    print("Play your local video. If sound is detected on ANY device, it will show below.")
    print("Press Ctrl+C to stop.\n")

    threads = []
    for mic in loopbacks:
        t = threading.Thread(target=monitor_device, args=(mic,))
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        running = False
        print("\nStopped.")

if __name__ == "__main__":
    main()
