#!/usr/bin/env python3
"""
systc - System Timecode Tool V3 with Starting Timecode Support
Displays current system time as SMPTE timecode at specified frame rate
Can start from a specified timecode instead of system time

Usage:
    systc <framerate> [--start HH:MM:SS:FF]
    
Supported frame rates:
    23.976, 24, 25, 29.97, 30, 50, 59.94, 60
    
Examples:
    systc 25                           # PAL standard from system time
    systc 29.97                        # NTSC drop-frame from system time
    systc 24 --start 01:00:00:00       # Film starting at 1 hour
    systc 25 -s 10:30:15:12 -c         # Start at specific timecode, continuous
"""

import sys
import time
import argparse
import re
from datetime import datetime, timedelta

# ASCII Art Font for large display - MUST be defined first
LARGE_DIGITS = {
    '0': [
        "  ███  ",
        " █   █ ",
        " █   █ ",
        " █   █ ",
        "  ███  "
    ],
    '1': [
        "   █   ",
        "  ██   ",
        "   █   ",
        "   █   ",
        " █████ "
    ],
    '2': [
        " █████ ",
        "     █ ",
        " █████ ",
        " █     ",
        " █████ "
    ],
    '3': [
        " █████ ",
        "     █ ",
        " █████ ",
        "     █ ",
        " █████ "
    ],
    '4': [
        " █   █ ",
        " █   █ ",
        " █████ ",
        "     █ ",
        "     █ "
    ],
    '5': [
        " █████ ",
        " █     ",
        " █████ ",
        "     █ ",
        " █████ "
    ],
    '6': [
        " █████ ",
        " █     ",
        " █████ ",
        " █   █ ",
        " █████ "
    ],
    '7': [
        " █████ ",
        "     █ ",
        "    █  ",
        "   █   ",
        "  █    "
    ],
    '8': [
        " █████ ",
        " █   █ ",
        " █████ ",
        " █   █ ",
        " █████ "
    ],
    '9': [
        " █████ ",
        " █   █ ",
        " █████ ",
        "     █ ",
        " █████ "
    ],
    ':': [
        "       ",
        "   ██  ",
        "       ",
        "   ██  ",
        "       "
    ],
    ' ': [
        "       ",
        "       ",
        "       ",
        "       ",
        "       "
    ]
}

class SystemTimecode:
    """Generate SMPTE timecode from system time V2 with starting timecode support"""
    
    FRAME_RATES = {
        23.976: 23.976,
        24: 24.0,
        25: 25.0,
        29.97: 29.97,  # Drop-frame NTSC
        30: 30.0,
        50: 50.0,
        59.94: 59.94,  # Drop-frame HD
        60: 60.0
    }
    
    def __init__(self, frame_rate, start_timecode=None):
        if frame_rate not in self.FRAME_RATES:
            raise ValueError(f"Unsupported frame rate: {frame_rate}")
        
        self.frame_rate = self.FRAME_RATES[frame_rate]
        self.is_drop_frame = frame_rate in [29.97, 59.94]
        
        # Initialize starting timecode offset
        self.start_time = datetime.now()
        self.start_timecode = start_timecode
        self.timecode_offset = None
        
        if start_timecode:
            self._calculate_timecode_offset(start_timecode)
    
    def _parse_timecode(self, timecode_str):
        """Parse timecode string (HH:MM:SS:FF) into components"""
        pattern = r'^(\d{1,2}):(\d{2}):(\d{2}):(\d{2})$'
        match = re.match(pattern, timecode_str)
        
        if not match:
            raise ValueError(f"Invalid timecode format: {timecode_str}. Expected HH:MM:SS:FF")
        
        hours, minutes, seconds, frames = map(int, match.groups())
        
        # Validate ranges
        if hours > 23:
            raise ValueError(f"Hours must be 0-23, got {hours}")
        if minutes > 59:
            raise ValueError(f"Minutes must be 0-59, got {minutes}")
        if seconds > 59:
            raise ValueError(f"Seconds must be 0-59, got {seconds}")
        if frames >= int(self.frame_rate):
            raise ValueError(f"Frames must be 0-{int(self.frame_rate)-1} for {self.frame_rate} fps, got {frames}")
        
        return hours, minutes, seconds, frames
    
    def _timecode_to_seconds(self, hours, minutes, seconds, frames):
        """Convert timecode components to total seconds"""
        total_seconds = hours * 3600 + minutes * 60 + seconds
        frame_seconds = frames / self.frame_rate
        return total_seconds + frame_seconds
    
    def _calculate_timecode_offset(self, start_timecode_str):
        """Calculate the offset between start timecode and current system time"""
        hours, minutes, seconds, frames = self._parse_timecode(start_timecode_str)
        
        # Convert start timecode to seconds
        start_tc_seconds = self._timecode_to_seconds(hours, minutes, seconds, frames)
        
        # Get current system time in seconds since midnight
        now = self.start_time
        current_seconds = (now.hour * 3600 + 
                          now.minute * 60 + 
                          now.second + 
                          now.microsecond / 1000000.0)
        
        # Calculate offset
        self.timecode_offset = start_tc_seconds - current_seconds
    
    def get_current_timecode(self):
        """Get current timecode (either from system time or with offset)"""
        now = datetime.now()
        
        if self.start_timecode and self.timecode_offset is not None:
            # Calculate elapsed time since start
            elapsed = (now - self.start_time).total_seconds()
            
            # Parse the starting timecode
            start_h, start_m, start_s, start_f = self._parse_timecode(self.start_timecode)
            start_total_seconds = self._timecode_to_seconds(start_h, start_m, start_s, start_f)
            
            # Add elapsed time
            current_total_seconds = start_total_seconds + elapsed
            
            # Handle day rollover
            current_total_seconds = current_total_seconds % (24 * 3600)
            
            # Convert back to timecode components
            hours = int(current_total_seconds // 3600)
            remaining = current_total_seconds % 3600
            minutes = int(remaining // 60)
            seconds_with_frames = remaining % 60
            seconds = int(seconds_with_frames)
            frame_fraction = seconds_with_frames - seconds
            frames = int(frame_fraction * self.frame_rate)
            
        else:
            # Use system time (original behavior)
            hours = now.hour
            minutes = now.minute
            seconds = now.second
            microseconds = now.microsecond
            
            # Calculate frames from microseconds
            frame_fraction = microseconds / 1000000.0
            frames = int(frame_fraction * self.frame_rate)
        
        # Apply drop-frame correction if needed
        if self.is_drop_frame:
            frames = self._apply_drop_frame_correction(hours, minutes, seconds, frames)
        
        # Ensure frames don't exceed frame rate
        max_frames = int(self.frame_rate) - 1
        if frames > max_frames:
            frames = max_frames
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
    
    def _apply_drop_frame_correction(self, hours, minutes, seconds, frames):
        """Apply drop-frame timecode correction for NTSC rates"""
        # Simplified drop-frame: skip frames 0 and 1 at the start of each minute
        # except for minutes that are multiples of 10
        if self.frame_rate == 29.97:
            if seconds == 0 and frames < 2 and (minutes % 10) != 0:
                frames += 2
        elif self.frame_rate == 59.94:
            if seconds == 0 and frames < 4 and (minutes % 10) != 0:
                frames += 4
        
        return frames
    
    def get_frame_rate_info(self):
        """Get information about the current frame rate"""
        rate_info = {
            23.976: "23.976 fps - Film transferred to video",
            24: "24 fps - Cinema/Film standard",
            25: "25 fps - PAL video standard",
            29.97: "29.97 fps - NTSC video (drop-frame)",
            30: "30 fps - NTSC non-drop",
            50: "50 fps - PAL progressive",
            59.94: "59.94 fps - NTSC HD (drop-frame)",
            60: "60 fps - High frame rate"
        }
        
        return rate_info.get(self.frame_rate, f"{self.frame_rate} fps")

def render_large_timecode(timecode_str):
    """Render timecode in large ASCII art format"""
    lines = ["", "", "", "", ""]
    
    for char in timecode_str:
        if char in LARGE_DIGITS:
            char_lines = LARGE_DIGITS[char]
            for i in range(5):
                lines[i] += char_lines[i] + " "
        else:
            # Handle unknown characters as spaces
            for i in range(5):
                lines[i] += "       "
    
    return lines

def display_large_timecode(frame_rate, start_timecode=None, update_rate=10, continuous=True):
    """Display large ASCII art timecode"""
    tc = SystemTimecode(frame_rate, start_timecode)
    
    # Clear screen for continuous mode
    if continuous:
        print("\033[2J\033[H", end="")
        print("System Timecode V2 - Large Display Mode")
        print(f"Frame Rate: {tc.get_frame_rate_info()}")
        print(f"Drop Frame: {'Yes' if tc.is_drop_frame else 'No'}")
        if start_timecode:
            print(f"Start Time: {start_timecode}")
        print("Press Ctrl+C to stop")
        print("=" * 80)
        print()
    
    try:
        last_timecode = ""
        while True:
            current_timecode = tc.get_current_timecode()
            
            # Only update display if timecode changed or single mode
            if current_timecode != last_timecode or not continuous:
                if continuous:
                    # Move cursor to timecode position
                    print("\033[8;1H" if start_timecode else "\033[7;1H", end="")
                
                # Render large timecode
                large_lines = render_large_timecode(current_timecode)
                
                # Print each line of the large timecode
                for line in large_lines:
                    print(line)
                
                # Add frame rate info below
                print(f"\n                    @ {frame_rate} fps")
                
                if tc.is_drop_frame:
                    print("                   (Drop Frame)")
                else:
                    print()  # Empty line for consistent spacing
                
                last_timecode = current_timecode
            
            if not continuous:
                break
                
            time.sleep(1.0 / update_rate)
            
    except KeyboardInterrupt:
        if continuous:
            print("\n\nLarge timecode display stopped.")

def display_continuous_timecode(frame_rate, start_timecode=None, update_rate=10, quiet=False):
    """Display continuously updating timecode"""
    tc = SystemTimecode(frame_rate, start_timecode)
    
    if not quiet:
        print(f"System Timecode Display V2")
        print(f"Frame Rate: {tc.get_frame_rate_info()}")
        print(f"Drop Frame: {'Yes' if tc.is_drop_frame else 'No'}")
        if start_timecode:
            print(f"Start Time: {start_timecode}")
        print(f"Update Rate: {update_rate} Hz")
        print("-" * 40)
        print("Press Ctrl+C to stop\n")
    
    try:
        last_timecode = ""
        while True:
            current_timecode = tc.get_current_timecode()
            
            # Only update display if timecode changed
            if current_timecode != last_timecode:
                if quiet:
                    # Just print the timecode (good for logging/piping)
                    print(current_timecode)
                else:
                    # Clear line and print new timecode
                    display_text = f"{current_timecode} @ {frame_rate} fps"
                    if start_timecode:
                        display_text += f" (started at {start_timecode})"
                    print(f"\r{display_text}", end="", flush=True)
                last_timecode = current_timecode
            
            time.sleep(1.0 / update_rate)
            
    except KeyboardInterrupt:
        if not quiet:
            print("\n\nTimecode display stopped.")

def display_gui_timecode(frame_rate, start_timecode=None):
    """Display timecode in a GUI window using tkinter"""
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        print("Error: tkinter not available. GUI mode requires tkinter.")
        print("Use regular display mode instead.")
        return
    
    tc = SystemTimecode(frame_rate, start_timecode)
    
    class TimecodeGUI:
        def __init__(self, root, timecode_gen):
            self.root = root
            self.tc = timecode_gen
            title = f"System Timecode V2 - {frame_rate} fps"
            if start_timecode:
                title += f" (Start: {start_timecode})"
            self.root.title(title)
            self.root.geometry("830x260")
            self.root.configure(bg='#000000')
            
            # Configure style
            style = ttk.Style()
            style.configure('Timecode.TLabel', 
                          font=("Bebas Neue",192, 'bold'),  # Use Orbitron
                          foreground='#ff0000',
                          background='#000000')
            

            style.configure('Info.TLabel',
                          font=('Arial', 14),
                          foreground='#000000',
                          background='#000000')
            
            # Main frame
            main_frame = ttk.Frame(root)
            main_frame.pack(expand=True, fill='both', padx=20, pady=20)
            
            # Timecode display
            self.timecode_var = tk.StringVar()
            timecode_label = ttk.Label(main_frame, 
                                     textvariable=self.timecode_var,
                                     style='Timecode.TLabel')
            timecode_label.pack(expand=True)
            
            # Info frame
            info_frame = ttk.Frame(main_frame)
            info_frame.pack(fill='x', pady=(20, 0))
            
            # Frame rate info
            rate_info = f"{tc.get_frame_rate_info()}"
            if tc.is_drop_frame:
                rate_info += " (Drop Frame)"
            if start_timecode:
                rate_info += f" | Started at: {start_timecode}"
            
            info_label = ttk.Label(info_frame, text=rate_info, style='Info.TLabel')
            info_label.pack()
            
            # Start update loop
            self.update_timecode()
        
        def update_timecode(self):
            """Update timecode display"""
            current_timecode = self.tc.get_current_timecode()
            self.timecode_var.set(current_timecode)
            
            # Schedule next update
            self.root.after(50, self.update_timecode)  # 20 FPS update
    
    # Create and run GUI
    root = tk.Tk()
    gui = TimecodeGUI(root, tc)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nGUI timecode display stopped.")

def get_single_timecode(frame_rate, start_timecode=None):
    """Get single timecode reading"""
    tc = SystemTimecode(frame_rate, start_timecode)
    timecode = tc.get_current_timecode()
    
    # Get current system time for reference
    now = datetime.now()
    system_time = now.strftime("%H:%M:%S.%f")[:-3]  # milliseconds
    
    print(f"System Time:  {system_time}")
    print(f"Timecode:     {timecode}")
    if start_timecode:
        print(f"Start Time:   {start_timecode}")
    print(f"Frame Rate:   {tc.get_frame_rate_info()}")
    print(f"Drop Frame:   {'Yes' if tc.is_drop_frame else 'No'}")

def list_frame_rates():
    """List all supported frame rates"""
    print("Supported Frame Rates:")
    print("-" * 50)
    
    for rate in sorted(SystemTimecode.FRAME_RATES.keys()):
        tc = SystemTimecode(rate)
        drop_frame = " (Drop Frame)" if tc.is_drop_frame else ""
        print(f"  {rate:>6} fps - {tc.get_frame_rate_info()}{drop_frame}")
    
    print("\nUsage Examples:")
    print("  systc 25                           # Single reading at 25fps")
    print("  systc 29.97 -c                    # Continuous display at 29.97fps")
    print("  systc 24 --start 01:00:00:00      # Start at 1 hour mark")
    print("  systc 25 -s 10:30:15:12 -c        # Continuous from custom start")
    print("  systc --list                      # Show this help")

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description='System Timecode Tool - Convert system time to SMPTE timecode with starting timecode support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  systc 25                           # Single timecode reading at 25fps
  systc 29.97 -c                     # Continuous timecode display at 29.97fps  
  systc 24 -d                        # Large ASCII art display at 24fps
  systc 25 -c -d                     # Continuous large display at 25fps
  systc 30 -g                        # GUI window display at 30fps
  systc 24 -r 30                     # Continuous at 24fps, 30Hz update rate
  systc 25 --start 01:00:00:00       # Start counting from 1 hour
  systc 29.97 -s 10:30:15:12 -c      # Continuous from 10:30:15:12
  systc --list                       # List all supported frame rates

Starting Timecode Format:
  HH:MM:SS:FF (e.g., 01:30:45:12)
  - HH: Hours (00-23)
  - MM: Minutes (00-59) 
  - SS: Seconds (00-59)
  - FF: Frames (00 to framerate-1)

Display Modes:
  Default: Single line timecode output
  -c: Continuous updating display
  -d: Large ASCII art display
  -g: GUI window display

Supported frame rates:
  23.976, 24, 25, 29.97, 30, 50, 59.94, 60
        """
    )
    
    parser.add_argument('framerate', nargs='?', type=float,
                       help='Frame rate (23.976, 24, 25, 29.97, 30, 50, 59.94, 60)')
    
    parser.add_argument('-s', '--start', dest='start_timecode', metavar='HH:MM:SS:FF',
                       help='Starting timecode (e.g., 01:00:00:00)')
    
    parser.add_argument('-c', '--continuous', action='store_true',
                       help='Display continuously updating timecode')
    
    parser.add_argument('-d', '--display', action='store_true',
                       help='Large ASCII art display mode')
    
    parser.add_argument('-g', '--gui', action='store_true',
                       help='GUI window display mode')
    
    parser.add_argument('-r', '--rate', type=int, default=10, metavar='HZ',
                       help='Update rate in Hz for continuous display (default: 10)')
    
    parser.add_argument('-l', '--list', action='store_true',
                       help='List all supported frame rates and exit')
    
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Quiet mode - output only timecode')
    
    args = parser.parse_args()
    
    # Handle list option
    if args.list:
        list_frame_rates()
        return
    
    # Validate frame rate argument
    if args.framerate is None:
        parser.error("Frame rate is required (use --list to see supported rates)")
    
    try:
        # Validate frame rate
        if args.framerate not in SystemTimecode.FRAME_RATES:
            print(f"Error: Unsupported frame rate {args.framerate}")
            print("Use 'systc --list' to see supported frame rates")
            sys.exit(1)
        
        # Validate starting timecode if provided
        if args.start_timecode:
            try:
                # Test parsing the timecode
                temp_tc = SystemTimecode(args.framerate, args.start_timecode)
            except ValueError as e:
                print(f"Error: {e}")
                sys.exit(1)
        
        # Handle display modes
        if args.gui:
            # GUI mode
            display_gui_timecode(args.framerate, args.start_timecode)
        elif args.display:
            # Large ASCII display mode
            if args.continuous:
                display_large_timecode(args.framerate, args.start_timecode, args.rate, continuous=True)
            else:
                display_large_timecode(args.framerate, args.start_timecode, args.rate, continuous=False)
        elif args.continuous:
            # Regular continuous mode (with quiet option)
            display_continuous_timecode(args.framerate, args.start_timecode, args.rate, quiet=args.quiet)
        else:
            # Single reading mode
            if args.quiet:
                tc = SystemTimecode(args.framerate, args.start_timecode)
                print(tc.get_current_timecode())
            else:
                get_single_timecode(args.framerate, args.start_timecode)
                
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
