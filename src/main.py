import tkinter as tk
import logging
from utils import setup_logging, set_dpi_awareness, minimize_console
# from recorder import ScreenRecorder (Lazy loaded)
from ui_components import MainUI
import sys
import os
import pythoncom

import threading

def main():
    # Setup
    setup_logging()
    set_dpi_awareness()
    minimize_console()
    
    # Init UI immediately
    root = tk.Tk()
    
    # Recorder placeholder
    recorder_wrapper = {'instance': None}
    
    def on_app_cleanup():
        """Ensure threads stop on exit"""
        if recorder_wrapper['instance'] and recorder_wrapper['instance'].is_recording:
            try:
                recorder_wrapper['instance'].stop_recording()
            except:
                pass
        # Force kill if needed by system
        os._exit(0)
    
    app = MainUI(root, recorder=None, app_cleanup_callback=on_app_cleanup)
    
    def load_backend_thread():
        try:
            pythoncom.CoInitialize()
            logging.info("Loading backend thread started.")
            # Lazy import inside thread
            from recorder import ScreenRecorder
            logging.info("Recorder module imported.")
            
            rec = ScreenRecorder()
            logging.info("Recorder initialized.")
            
            recorder_wrapper['instance'] = rec
            
            # Callback to main thread to update UI
            logging.info("Scheduling UI update.")
            root.after(0, lambda: app.set_recorder(rec))
            logging.info("UI update scheduled.")
        except Exception as e:
            logging.error(f"Backend load failed: {e}")
            import traceback
            logging.error(traceback.format_exc())
            def show_error():
                from tkinter import messagebox
                messagebox.showerror("Fatal Error", f"Failed to initialize recorder: {e}")
                # root.destroy() # Don't destroy immediately so user can see error
            root.after(0, show_error)

    # Start loading in background thread
    threading.Thread(target=load_backend_thread, daemon=True).start()
    
    # Tkinter loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_app_cleanup()

if __name__ == "__main__":
    main()
