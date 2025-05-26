# systc - System Timecode Tool

A professional SMPTE timecode generator that converts system time to timecode at various frame rates, with support for custom starting timecodes and multiple display modes.

## Features

- **Multiple Frame Rates**: Support for all standard video frame rates (23.976, 24, 25, 29.97, 30, 50, 59.94, 60 fps)
- **Drop-Frame Support**: Automatic drop-frame correction for NTSC frame rates (29.97, 59.94)
- **Custom Start Times**: Begin timecode from any specified time instead of system time
- **Multiple Display Modes**:
  - Single timecode reading
  - Continuous updating display
  - Large ASCII art display
  - GUI window display
- **Professional Standards**: SMPTE-compliant timecode format (HH:MM:SS:FF)
- **Flexible Output**: Quiet mode for logging and scripting

## Installation

### Requirements
- Python 3.6 or higher
- tkinter (for GUI mode, usually included with Python)

### Setup
1. Clone this repository or download the script
2. Make the script executable:
   ```bash
   chmod +x systc.py
   ```
3. Optionally, create a symlink for global access:
   ```bash
   ln -s /path/to/systc.py /usr/local/bin/systc
   ```

## Usage

### Basic Syntax
```bash
systc <framerate> [options]
```

### Quick Examples
```bash
# Single timecode reading at 25fps (PAL)
systc 25

# Continuous display at 29.97fps (NTSC)
systc 29.97 -c

# Large ASCII art display at 24fps (Film)
systc 24 -d

# GUI window at 30fps
systc 30 -g

# Start from specific timecode
systc 25 --start 01:00:00:00

# Continuous display starting from custom time
systc 29.97 -s 10:30:15:12 -c
```

## Command Line Options

| Option | Long Form | Description |
|--------|-----------|-------------|
| `-s` | `--start HH:MM:SS:FF` | Starting timecode (e.g., 01:00:00:00) |
| `-c` | `--continuous` | Continuous updating display |
| `-d` | `--display` | Large ASCII art display mode |
| `-g` | `--gui` | GUI window display mode |
| `-r` | `--rate HZ` | Update rate in Hz for continuous display (default: 10) |
| `-l` | `--list` | List all supported frame rates |
| `-q` | `--quiet` | Quiet mode - output only timecode |

## Supported Frame Rates

| Frame Rate | Description | Drop Frame |
|------------|-------------|------------|
| 23.976 | Film transferred to video | No |
| 24 | Cinema/Film standard | No |
| 25 | PAL video standard | No |
| 29.97 | NTSC video standard | Yes |
| 30 | NTSC non-drop | No |
| 50 | PAL progressive | No |
| 59.94 | NTSC HD | Yes |
| 60 | High frame rate | No |

## Display Modes

### Single Reading (Default)
Displays a single timecode reading with system information:
```
System Time:  14:30:25.123
Timecode:     14:30:25:03
Frame Rate:   25 fps - PAL video standard
Drop Frame:   No
```

### Continuous Display (`-c`)
Real-time updating timecode display:
```
14:30:25:03 @ 25 fps
```

### Large ASCII Art Display (`-d`)
Impressive large-format timecode display:
```
  ███   █████         █████  █████         █████   ███           ███    ███   
 █   █  █   █    ██   █      █   █    ██       █  █   █    ██   █   █  █   █  
 █   █  █████         █████  █████         █████  █   █         █   █  █   █  
 █   █      █    ██       █      █    ██       █  █   █    ██   █   █  █   █  
  ███   █████         █████  █████         █████   ███           ███    ███   

                    @ 25 fps
```

### GUI Mode (`-g`)
Professional GUI window with large timecode display and frame rate information.
![image](https://github.com/user-attachments/assets/e8b12d2a-5c45-4963-9aee-649be302eeda)

## Starting Timecode Format

The starting timecode follows SMPTE format: **HH:MM:SS:FF**

- **HH**: Hours (00-23)
- **MM**: Minutes (00-59)
- **SS**: Seconds (00-59)
- **FF**: Frames (00 to framerate-1)

### Examples:
- `01:00:00:00` - Start at 1 hour
- `10:30:15:12` - Start at 10:30:15 and 12 frames
- `23:59:59:24` - Start near midnight (for 25fps)

## Use Cases

### Video Production
```bash
# Match camera timecode for editing
systc 24 --start 10:00:00:00 -c

# Monitor live production timecode
systc 25 -d -c
```

### Broadcasting
```bash
# NTSC broadcast timecode
systc 29.97 -c -q

# PAL broadcast timecode  
systc 25 -g
```

### Post-Production
```bash
# Film editing reference
systc 24 --start 01:00:00:00 -d

# Audio sync reference
systc 25 -c -r 30
```

### Scripting and Logging
```bash
# Log timecode to file
systc 25 -q >> timecode.log

# Use in scripts
CURRENT_TC=$(systc 29.97 -q)
echo "Current timecode: $CURRENT_TC"
```

## Technical Notes

### Drop-Frame Timecode
For NTSC frame rates (29.97 and 59.94 fps), the tool automatically applies drop-frame correction to maintain sync with real time. This skips specific frame numbers at the beginning of each minute (except multiples of 10).

### Accuracy
The tool uses system time with microsecond precision for frame calculations, ensuring broadcast-quality accuracy.

### Performance
- Continuous mode updates at 10Hz by default (configurable with `-r`)
- GUI mode updates at 20Hz for smooth display
- Minimal CPU usage in all modes

## Examples

### Film Production
```bash
# Start dailies timecode at 1 hour mark
systc 24 --start 01:00:00:00 -d -c
```

### Live Event Broadcasting
```bash
# Show timecode for live PAL broadcast
systc 25 -g
```

### Audio Post-Production
```bash
# High-precision timecode for audio sync
systc 25 -c -r 50
```

### Automation Scripts
```bash
#!/bin/bash
# Generate timecode log every second
while true; do
    echo "$(date): $(systc 25 -q)" >> production.log
    sleep 1
done
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:
- Additional frame rate support
- New display modes
- Bug fixes
- Documentation improvements

## License

Please specify your license terms.

## Version History

- **V3**: Added starting timecode support and improved display modes
- **V2**: Enhanced display options and GUI mode
- **V1**: Basic timecode conversion functionality
