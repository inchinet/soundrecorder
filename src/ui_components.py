import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import os

class RegionSelector(tk.Toplevel):
    def __init__(self, parent, on_update_coords):
        super().__init__(parent)
        self.on_update_coords = on_update_coords
        # Use standard window decoration for robust resizing (Top-Left, Bottom-Right, etc)
        self.title("Region Selector - Drag corners to resize")
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.5)  # Semi-transparent to see through
        self.configure(bg='green')
        
        # Initial geometry
        self.geometry("400x300+100+100")
        
        # Bind configure event to track moves/resizes provided by OS
        self.bind("<Configure>", self.on_configure)

    def on_configure(self, event):
        # Filter out events not meant for the window itself
        if event.widget == self:
            self.update_coords()

    def update_coords(self):
        # winfo_rootx/y gives the content area position (excluding title bar)
        x = self.winfo_rootx()
        y = self.winfo_rooty()
        w = self.winfo_width()
        h = self.winfo_height()
        self.on_update_coords(x, y, w, h)
        
    def show(self):
        self.deiconify()
        
    def hide(self):
        self.withdraw()

class MainUI:
    def __init__(self, root, recorder=None, app_cleanup_callback=None):
        self.root = root
        self.recorder = recorder
        self.cleanup = app_cleanup_callback
        self.root.title("Antigravity Recorder")
        self.root.geometry("300x250")
        self.root.attributes("-topmost", True)
        
        # Variables
        self.mode = tk.StringVar(value="region")
        self.coords_var = tk.StringVar(value="Select Region")
        self.status_var = tk.StringVar(value="Initializing..." if recorder is None else "Ready")
        self.region_coords = None

        # Style
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 10))
        style.configure("TLabel", font=("Helvetica", 10))
        
        # UI Elements
        frame = ttk.Frame(root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Mode Selection
        lbl_mode = ttk.Label(frame, text="Select Mode:")
        lbl_mode.pack(pady=5)
        
        rad_region = ttk.Radiobutton(frame, text="Region Mode", variable=self.mode, value="region", command=self.on_mode_change)
        rad_region.pack(anchor=tk.W)
        
        rad_full = ttk.Radiobutton(frame, text="Full Screen", variable=self.mode, value="fullscreen", command=self.on_mode_change)
        rad_full.pack(anchor=tk.W)
        
        # Coords Display
        self.lbl_coords = ttk.Label(frame, textvariable=self.coords_var, foreground="blue")
        self.lbl_coords.pack(pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        
        self.btn_start = ttk.Button(btn_frame, text="START Recording", command=self.start_recording)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        # Disable start if not ready
        if self.recorder is None:
            self.btn_start.config(state=tk.DISABLED, text="Loading backend...")
        
        self.btn_stop = ttk.Button(btn_frame, text="STOP", command=self.stop_recording, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        
        btn_exit = ttk.Button(frame, text="EXIT", command=self.on_exit)
        btn_exit.pack(pady=5)
        
        self.lbl_status = ttk.Label(frame, textvariable=self.status_var)
        self.lbl_status.pack(pady=5)
        
        # Region Picker
        self.region_window = RegionSelector(root, self.update_coords_display)
        self.on_mode_change() # Init state

    def set_recorder(self, recorder):
        self.recorder = recorder
        self.status_var.set("Ready")
        self.btn_start.config(state=tk.NORMAL, text="START Recording")

    def update_coords_display(self, x, y, w, h):
        self.region_coords = (x, y, w, h)
        self.coords_var.set(f"X:{x} Y:{y} W:{w} H:{h}")

    def on_mode_change(self):
        mode = self.mode.get()
        if mode == "region":
            self.region_window.show()
            self.lbl_coords.config(foreground="blue")
            if self.region_coords:
                 self.coords_var.set(f"X:{self.region_coords[0]} Y:{self.region_coords[1]} W:{self.region_coords[2]} H:{self.region_coords[3]}")
        else:
            self.region_window.hide()
            self.coords_var.set("Full Screen Mode")
            self.region_coords = None

    def start_recording(self):
        if self.mode.get() == "region" and not self.region_coords:
            messagebox.showerror("Error", "Please select a region first.")
            return

        # Hide windows
        # self.root.iconify()  # User requested UI remains visible
        self.region_window.hide()
        
        # Output file
        # We start generic, save dialog later
        # Output file
        # We start generic, save dialog later
        filename = "temp_recording_merged.mp4" # Intermediate
        

        try:
            # DPI SCALING LOGIC
            # App is now System DPI Aware (Level 1), so Tkinter coordinates match physical pixels (roughly).
            # We pass the coordinates directly.
            
            if self.region_coords:
                scaled_coords = self.region_coords
                logging.info(f"Recording Region: {scaled_coords}")
            else:
                scaled_coords = None

            self.recorder.start_recording(filename, scaled_coords)
            self.status_var.set("Recording...")
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start: {e}")
            self.root.deiconify()

    def stop_recording(self):
        self.status_var.set("Stopping...")
        self.root.update()
        
        try:
            self.recorder.stop_recording()
            
            # Save Dialog
            save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
            if save_path:
                # Move internal file to user location
                import shutil
                # The recorder already merged to "temp_recording_merged.mp4"
                if os.path.exists("temp_recording_merged.mp4"):
                    shutil.move("temp_recording_merged.mp4", save_path)
                    messagebox.showinfo("Success", f"Saved to {save_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
        finally:
            self.status_var.set("Ready")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.root.deiconify()
            if self.mode.get() == 'region':
                self.region_window.show()

    def on_exit(self):
        self.cleanup()
        self.root.destroy()
