import PyInstaller.__main__
import os

def build_exe():
    work_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(work_dir, 'dist')
    build_dir = os.path.join(work_dir, 'build')
    
    # Ensure clean state
    # if os.path.exists(dist_dir): shutil.rmtree(dist_dir)
    # if os.path.exists(build_dir): shutil.rmtree(build_dir)
    
    PyInstaller.__main__.run([
        'src/main.py',
        '--name=AntigravityRecorder',
        '--onefile',
        '--windowed',
        '--icon=NONE', # Set icon if available later
        '--clean',
        # Moviepy and soundcard might have dynamic imports
        '--hidden-import=moviepy',
        '--hidden-import=soundcard',
        '--hidden-import=pkg_resources.py2_warn', 
        '--log-level=INFO',
    ])

if __name__ == '__main__':
    print("Starting build...")
    build_exe()
    print("Build complete.")
