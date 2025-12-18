# Antigravity Recorder

A Python-based screen recorder application with audio support.

## Features

- Screen recording with audio
- Simple GUI interface
- Automatic audio device detection
- MP4 output format

## Installation

1.  **Clone the repository** (if applicable) or download the source.

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment**:
    - **Windows**:
        ```cmd
        venv\Scripts\activate
        ```
    - **macOS/Linux**:
        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Run from Source

To start the application:

```cmd
run.bat
```

Or manually:

```bash
python src/main.py
```

### Build Executable

To build a standalone executable:

```bash
python build.py
```

The executable will be located in the `dist` folder.
