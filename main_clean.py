#!/usr/bin/env python3
"""
VisionX Control System - Main Application
Modular LED control system with GUI interface
"""

import sys
import os
import signal
from config import AppConfig
from communication import CommunicationHandler
from led import LEDController
from xilanh import XilanhController
from IR import IRController
from gui_clean import ModernGUI

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n⚡ Shutting down VisionX Control System...")
    sys.exit(0)

def main():
    """Main application entry point"""
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Initialize configuration
        print("🎯 Initializing VisionX Control System...")
        config = AppConfig()
        
        # Initialize communication
        print("📡 Setting up communication...")
        comm_handler = CommunicationHandler(config)
        
        # Initialize controllers
        print("🎮 Initializing controllers...")
        led_controller = LEDController(comm_handler)
        xilanh_controller = XilanhController(comm_handler)
        ir_controller = IRController(comm_handler, config)
        
        # Initialize and run GUI
        print("🚀 Starting GUI...")
        gui = ModernGUI(led_controller, xilanh_controller, ir_controller, comm_handler, config)
        gui.run()
        
    except KeyboardInterrupt:
        print("\n⚡ Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            if 'comm_handler' in locals():
                comm_handler.close()
        except:
            pass
        print("👋 VisionX Control System stopped")

if __name__ == "__main__":
    main()