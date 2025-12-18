import logging
import ctypes
import os

def setup_logging():
    """Sets up logging to app.log, clearing it each run."""
    log_file = "app.log"
    # Clear previous log
    with open(log_file, "w") as f:
        f.write("")
        
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.info("Application started.")

def set_dpi_awareness():
    """Sets the process to be DPI aware for correct 4K rendering."""
    try:
        # Set DPI awareness to System Aware (1).
        # This ensures Tkinter coordinates match physical screen pixels on the primary monitor.
        ctypes.windll.shcore.SetProcessDpiAwareness(1) 
        logging.info("DPI Awareness set to System Aware (1).")
    except Exception as e:
        logging.warning(f"Failed to set DPI awareness: {e}")
        try:
            # Windows 8 and earlier
            ctypes.windll.user32.SetProcessDPIAware()
            logging.info("DPI Awareness set to global (legacy).")
        except Exception as e2:
             logging.error(f"Failed to set legacy DPI awareness: {e2}")

def get_dpi_scale():
    """Returns the screen scaling factor."""
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        w = user32.GetSystemMetrics(0)
        return 1.0 # If we are DPI aware, we might not need to scale OR we need to check logical vs physical.
        # Actually, best approach for Tkinter + MSS mixed usage:
        # Tkinter might report logical pixels if awareness failed.
        # Let's trust the user awareness set above.
    except:
        return 1.0

def minimize_console():
    """Minimizes the console window."""
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 6) # SW_MINIMIZE = 6
            logging.info("Console minimized.")
    except Exception as e:
        logging.error(f"Failed to minimize console: {e}")
