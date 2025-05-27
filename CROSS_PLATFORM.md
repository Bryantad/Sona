# Cross-Platform Compatibility Guide

Sona is designed to work across different platforms. When moving Sona between operating systems (e.g., from macOS to Windows or vice versa), follow these simple steps to ensure smooth operation:

## Using Sona from a USB Drive

For the most convenient experience when using Sona from a USB drive:

1. Connect your USB drive to your computer (Windows or macOS)
2. Navigate to the `platform_compat` directory
3. Run the USB launcher script:

   ```
   # On Windows
   python usb_launcher.py

   # On macOS
   python3 usb_launcher.py
   ```

4. This will:
   - Automatically detect your operating system
   - Run the appropriate setup script for your platform
   - Configure path settings correctly for USB drives
   - Launch the Sona REPL directly

## Moving Sona to Windows

1. Copy all Sona files to your Windows PC
2. Navigate to the `platform_compat` directory
3. Run the Windows setup script:
   ```
   python win_setup.py
   ```
4. This will:
   - Configure the proper paths for Windows
   - Create a convenient batch file for launching Sona
   - Add Sona to your PYTHONPATH temporarily

## Moving Sona to macOS

1. Copy all Sona files to your macOS system
2. Navigate to the `platform_compat` directory
3. Run the macOS setup script:
   ```
   python3 mac_setup.py
   ```
4. This will:
   - Configure the proper paths for macOS
   - Create a launch script with proper permissions
   - Add Sona to your PYTHONPATH temporarily

## Automated Platform Detection

For automatic platform detection, simply run:

```
# On Windows
python platform_compat/setup.py

# On macOS
python3 platform_compat/setup.py
```

This script will automatically detect your operating system and run the appropriate setup script.

## Requirements

- Python 3.7+ installed on both platforms
- Standard Python libraries (`pathlib`, `os`, `sys`, etc.)
- All other dependencies will be handled by the setup scripts

## Troubleshooting Common Issues

**Module Import Errors:**

- Ensure the setup script was run and the Sona path was added to PYTHONPATH
- Check that all folders are accessible to the current user

**File Permission Issues:**

- On macOS, you may need to restore executable permissions: `chmod +x sona_repl.sh`
- On Windows, ensure your user has read/write access to the Sona directory

**Path Separator Issues:**

- The setup scripts handle path separator differences between platforms
- If you create custom paths in your Sona code, use `os.path.join()` or `pathlib.Path` for compatibility
