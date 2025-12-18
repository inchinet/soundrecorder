
import cv2
import mss
import numpy as np
import soundcard as sc
from scipy.io.wavfile import write
import threading
import time
import os
import logging
import pythoncom

import subprocess
import logging
# MoviePy removed in favor of direct ffmpeg


class ScreenRecorder:
    def __init__(self):
        self.is_recording = False
        self.output_filename = "output.mp4"
        self.monitor = None
        self.video_thread = None
        self.audio_thread = None
        
        # Audio settings
        self.samplerate = 44100
        self.channels = 2 # Stereo
        self.audio_data = [] # List to hold audio chunks

    def start_recording(self, filename, region=None):
        """
        Starts recording.
        region: tuple (x, y, w, h) or None for full screen.
        """
        self.output_filename = filename
        self.is_recording = True
        self.audio_data = [] # Reset
        
        # Setup Monitor
        with mss.mss() as sct:
            if region:
                self.monitor = {"top": int(region[1]), "left": int(region[0]), "width": int(region[2]), "height": int(region[3])}
            else:
                self.monitor = sct.monitors[1] # Primary monitor

        # Start threads
        self.video_thread = threading.Thread(target=self._record_video)
        self.audio_thread = threading.Thread(target=self._record_audio)
        
        self.video_thread.start()
        self.audio_thread.start()
        logging.info(f"Recording started. Region: {self.monitor}")

    def stop_recording(self):
        """Stops recording and merges files."""
        if not self.is_recording:
            return

        self.is_recording = False
        
        # Wait for threads with timeout to prevent hang
        if self.video_thread:
            self.video_thread.join(timeout=2.0)
        if self.audio_thread:
            self.audio_thread.join(timeout=2.0)
            
        logging.info("Recording threads stopped. Merging files...")
        self._merge_files()
        logging.info("Merge complete.")

    def _record_video(self):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v") # Better compat than XVID for some players
        fps = 20.0
        # Wait for monitor to be set
        timeout = 0
        while not self.monitor and timeout < 20: 
            time.sleep(0.1)
            timeout += 1
        
        if not self.monitor:
            logging.error("Monitor not set, stopping video thread.")
            return
            
        width = self.monitor["width"]
        height = self.monitor["height"]
        
        # Temp video file
        temp_video = "temp_video_silent.mp4" # Changed to mp4 directly
        out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
        
        with mss.mss() as sct:
            while self.is_recording:
                last_time = time.time()
                try:
                    img = sct.grab(self.monitor)
                    frame = np.array(img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    out.write(frame)
                except Exception as e:
                    logging.error(f"Error capturing screen: {e}")
                    break
                
                # FPS Control
                delay = 1.0 / fps - (time.time() - last_time)
                if delay > 0:
                    time.sleep(delay)
                    
        out.release()
        logging.info("Video recording finished.")

    def _record_audio(self):
        try:
            # Clear previous data
            self.audio_data = []

            # Initialize COM for this thread
            # Initialize COM for this thread - Must be MTA for Media Foundation/SoundCard
            pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
            
            # soundcard setup
            fs = self.samplerate = 44100
            
            try:
                # Get default speaker
                default_speaker = sc.default_speaker()
                logging.info(f"Default Speaker: {default_speaker.name} (ID: {default_speaker.id})")
                
                # Try to find matching loopback
                mic = None
                loopbacks = sc.all_microphones(include_loopback=True)
                
                # 1. Try to find loopback with same name/ID as speaker
                for m in loopbacks:
                    if m.isloopback and (m.name == default_speaker.name or m.id == default_speaker.id):
                        mic = m
                        logging.info(f"Found matching loopback: {mic.name}")
                        break
                
                # 2. If not found, look for any loopback (common fallback)
                if not mic:
                    # Filter only loopbacks
                    loopback_mics = [m for m in loopbacks if m.isloopback]
                    if loopback_mics:
                        mic = loopback_mics[0]
                        logging.info(f"Fallback: Using first available loopback: {mic.name}")
                    else:
                        logging.error("No loopback microphones found in system.")
                        # List all mics for debug
                        for i, m in enumerate(loopbacks):
                             logging.info(f"Device {i}: {m.name} (Loopback: {m.isloopback})")
                        # Write silent wav
                        write("temp_audio.wav", 44100, np.zeros((44100, 2), dtype=np.int16))
                        return

                self.channels = mic.channels
            except Exception as e:
                logging.error(f"Error finding loopback device: {e}")
                return
            
            logging.info(f"Audio Recording started on {mic.name}. Rate={fs}, Channels={self.channels}")
            
            # Record in chunks
            # Record in chunks - larger buffer (0.5s) to prevent discontinuity warnings and drops
            block_size = int(fs * 0.5)
            
            with mic.recorder(samplerate=fs) as recorder:
                while self.is_recording:
                    # Record chunk
                    data = recorder.record(numframes=block_size)
                    self.audio_data.append(data)
                    
            # Save temp audio
            if self.audio_data:
                full_audio = np.concatenate(self.audio_data, axis=0)
                
                # Check for silence (debug)
                max_vol = np.max(np.abs(full_audio))
                mean_vol = np.mean(np.abs(full_audio))
                logging.info(f"Audio recorded. Max amplitude: {max_vol:.4f}, Mean: {mean_vol:.4f}")
                
                if max_vol == 0:
                    logging.warning("Recorded audio is completely silent (0.0). Check microphone volume.")
                
                # soundcard returns float32 -1.0 to 1.0, convert to int16 for WAV
                full_audio_int16 = (full_audio * 32767).astype(np.int16)
                write("temp_audio.wav", fs, full_audio_int16)
                logging.info(f"Audio recording finished. Frames: {len(full_audio)}")
            else:
                logging.warning("No audio data recorded.")
                # Create silent file
                write("temp_audio.wav", fs, np.zeros((100, self.channels), dtype=np.int16))

        except Exception as e:
            logging.error(f"Audio recording internal error: {e}")
            import traceback
            logging.error(traceback.format_exc())
            write("temp_audio.wav", 44100, np.zeros((44100, 2), dtype=np.int16))

    def _merge_files(self):
        temp_video = "temp_video_silent.mp4"
        audio_path = "temp_audio.wav"
        
        try:
            if not os.path.exists(temp_video):
                logging.error("No temp video found to merge.")
                return

            if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
                logging.warning(f"Audio file invalid or too small. Saving video only.")
                # Just rename/copy video
                try:
                    if os.path.exists(self.output_filename):
                        os.remove(self.output_filename)
                    os.rename(temp_video, self.output_filename)
                except Exception as e:
                    logging.error(f"Failed to save video only: {e}")
                return

            logging.info(f"Merging video {temp_video} and audio {audio_path}...")
            
            # FFmpeg command
            # -y: overwrite
            # -i: inputs
            # -c:v copy: copy video stream (fast)
            # -c:a aac: encode audio to aac
            # -shortest: finish when shortest input ends
            cmd = [
                "ffmpeg", "-y",
                "-i", temp_video,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                self.output_filename
            ]
            
            logging.info(f"Running command: {' '.join(cmd)}")
            
            # Run ffmpeg
            # Capture output to log
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info(f"Merge successful! Saved to {self.output_filename}")
            else:
                logging.error(f"FFmpeg merge failed with code {result.returncode}")
                logging.error(f"FFmpeg stderr: {result.stderr}")
                # Fallback: keep silent video
                logging.info("Saving silent video as fallback.")
                if os.path.exists(self.output_filename):
                    os.remove(self.output_filename)
                import shutil
                shutil.copy(temp_video, self.output_filename)

        except Exception as e:
            logging.error(f"Error merging files: {e}")
            import traceback
            logging.error(traceback.format_exc())

        # Cleanup
        if os.path.exists(temp_video):
            try: os.remove(temp_video) 
            except: pass
        if os.path.exists(audio_path):
            try: os.remove(audio_path)
            except: pass
                
    def cleanup(self):
        """Destructor-like cleanup"""
        self.is_recording = False
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=1)
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1)

    def __del__(self):
        pass

