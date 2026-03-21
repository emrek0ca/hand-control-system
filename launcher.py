#!/usr/bin/env python3
"""
Launcher for Hand Gesture Control System
"""
import os
import sys
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Hand Gesture Control Launcher")
    parser.add_argument("--mode", "-m", choices=["debug", "pro"], default="pro",
                      help="Mode to run: 'debug' (windowed) or 'pro' (headless/magic wand)")
    args = parser.parse_args()

    # Base command
    cmd = [sys.executable, "main.py"]

    if args.mode == "pro":
        print("\n🚀 Starting Professional 'Magic Wand' Mode...")
        print("   - No camera window")
        print("   - Advance smoothing active")
        print("   - System control active")
        print("💡 Commands:")
        print("   - Point index finger to move cursor")
        print("   - Pinch (OK sign) to click")
        print("   - Fist (Grab) to drag")
        print("   - Peace sign to right click")
        print("\n❌ Press Ctrl+C to stop.\n")
        
        cmd.append("--headless")
        
    else:
        print("\n🐞 Starting Debug Mode...")
        print("   - Camera window visible")
        print("   - Visual feedback on")
        
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopping...")

if __name__ == "__main__":
    main()
