"""
Universal AI Agent Launcher & App Builder
Handles dependencies, shows 3D Welcome Screen, and starts the main loop.
"""

import os
import sys
import subprocess
import time

def check_dependencies():
    """Ensure all requirements are installed."""
    print("[LAUNCHER] Checking system environment...")
    try:
        import mediapipe
        import google.generativeai
        import cv2
    except ImportError:
        print("[LAUNCHER] Installing missing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def run_welcome():
    """Show the fütüristic intro before the main app."""
    try:
        import cv2
        import numpy as np
        from interaction_system import IntroManager
        
        intro = IntroManager(1280, 720)
        start_t = time.time()
        
        print("[LAUNCHER] Starting Neural Link...")
        
        while time.time() - start_t < intro.duration:
            intro.update()
            frame = intro.draw()
            
            cv2.imshow("Hand Control AI - INITIALIZING", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"[LAUNCHER] Intro skipped: {e}")

def start_main():
    """Launch the main AI Agent loop."""
    from main import GestureControlApp
    app = GestureControlApp()
    app.run()

if __name__ == "__main__":
    # 1. Self-Correction
    check_dependencies()
    
    # 2. Fütüristic Intro
    run_welcome()
    
    # 3. Main Engine
    start_main()
