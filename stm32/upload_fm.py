#!/usr/bin/env python3
"""
STM32 Nucleo RDP (Read Protection) Demo Script
This script demonstrates setting RDP level 1 and verifying read protection.
"""

import subprocess
import sys
import time
import os
from pathlib import Path

# EEPROM/Data Flash addresses from your table
eeprom_bank1_start = "0x08080000"
eeprom_bank1_end = "0x08080BFF"   # 3KB
eeprom_bank2_start = "0x08080C00" 
eeprom_bank2_end = "0x080817FF"    # 3KB

# Total EEPROM size (both banks)
eeprom_size = "0x1800"  # 6KB total

# memo mode = 0, Boot0 = 0, UFB = 0
bank_1_start = "0x08000000"  # Flash start address
bank_1_end = "0x08017FFF"
bank_2_start = "0x08018000"
bank_2_end = "0x0802FFFF"

option_bytes_address = "0x1FF80000"

read_size = "0x18000"  #  96kbytes

verbose = False

test_data = bytearray()
test_data.extend(b"SIMON_SIMON_SIMO")  # 16 bytes


def run_command(cmd, description=""):
    """Execute a command and handle errors"""
    if verbose:
        print(f"\n{'='*50}")
        if description:
            print(f"Step: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*50}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if verbose:
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command {' '.join(cmd)} failed with return code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return None
    except FileNotFoundError:
        print(f"ERROR: Command not found. Make sure ST-Link tools are installed and in PATH.")
        return None


# def read_eeprom(description=""):
#     """Read EEPROM memory"""
#     output_file = f"eeprom_read_{int(time.time())}.bin"
#     cmd = ['st-flash', '--format', 'binary', 'read', output_file, eeprom_bank1_start, eeprom_size]
#     result = run_command(cmd, f"Reading EEPROM memory {description}")

#     if result and os.path.exists(output_file):
#         try:
#             with open(output_file, 'rb') as f:
#                 data = f.read()
            
#             # Check if all bytes are 0x00
#             all_zeros = all(b == 0 for b in data)
#             non_zero_count = sum(1 for b in data if b != 0)
            
#             if verbose:
#                 print(f"Read {len(data)} bytes")
#                 print(f"Non-zero bytes: {non_zero_count}/{len(data)}")
#                 print(f"All zeros: {all_zeros}")
            
#             # Show first 32 bytes
#             print("First 16 bytes:", ' '.join(f'{b:02X}' for b in data[:16]))
            
#             return data, all_zeros
#         except Exception as e:
#             print(f"Error reading flash data: {e}")
#     return result

# def write_eeprom(description=""):
#     """Write EEPROM memory"""
#     output_file = f"eeprom_write_{int(time.time())}.bin"
#     with open(output_file, 'wb') as f:
#         f.write(test_data)
#     cmd = ['st-flash', '--format', 'binary', 'write', output_file, eeprom_bank1_start, eeprom_size]
#     result = run_command(cmd, f"Writing EEPROM memory {description}")
#     return result

def read_flash(description=""):
    """Read flash memory"""
    output_file = f"flash_read_{int(time.time())}.bin"
    cmd = ['st-flash', '--format', 'binary', 'read', output_file, bank_1_start, '0x18000']
    result = run_command(cmd, f"Reading flash memory {description}")
    
    if result and os.path.exists(output_file):
        try:
            with open(output_file, 'rb') as f:
                data = f.read()
            
            # Check if all bytes are 0x00
            all_zeros = all(b == 0 for b in data)
            non_zero_count = sum(1 for b in data if b != 0)
            
            if verbose:
                print(f"Read {len(data)} bytes")
                print(f"Non-zero bytes: {non_zero_count}/{len(data)}")
                print(f"All zeros: {all_zeros}")
            
            # Show first 32 bytes
            print("First 32 bytes:", ' '.join(f'{b:02X}' for b in data[:32]))
            
            return data, all_zeros
        except Exception as e:
            print(f"Error reading flash data: {e}")
    
    return None, False

def write_flash(description=""):
    """Write EEPROM memory"""
    output_file = f"fflash_write_{int(time.time())}.bin"
    with open(output_file, 'wb') as f:
        f.write(test_data)
    cmd = ['st-flash', '--format', 'binary', 'write', output_file, bank_1_start]
    result = run_command(cmd, f"Writing flash memory {description}")
    return result

def check_tools():
    """Check if required tools are available"""
    tools = ['st-flash', 'st-info']
    missing_tools = []
    
    for tool in tools:
        result = subprocess.run(['which', tool], capture_output=True)
        if result.returncode != 0:
            missing_tools.append(tool)
    
    if missing_tools:
        print("ERROR: Missing required tools:")
        for tool in missing_tools:
            print(f"  - {tool}")
        print("\nPlease install ST-Link tools:")
        print("  Ubuntu/Debian: sudo apt install stlink-tools")
        print("  macOS: brew install stlink")
        print("  Or download from: https://github.com/stlink-org/stlink")
        return False
    
    return True

def get_device_info():
    """Get STM32 device information"""
    cmd = ['st-info', '--probe']
    return run_command(cmd, "Getting device information")

def read_option_bytes(print_result=False):
        """Read current option bytes to check RDP level"""
        cmd = ['st-flash', '--format', 'binary', 'read', 'option_bytes.bin', option_bytes_address, '0x10']
        result = run_command(cmd, "Reading option bytes")
        
        if result and os.path.exists('option_bytes.bin'):
            try:
                with open('option_bytes.bin', 'rb') as f:
                    data = f.read()
                rdp_byte = data[0] if len(data) > 0 else 0
                if rdp_byte == 0xAA:
                    if print_result:
                        print("RDP Level 0 (No protection)")
                elif rdp_byte == 0x33:
                    if print_result:
                        print("RDP Level 1 (Read protection enabled)")
                elif rdp_byte == 0xCC:
                    if print_result:
                        print("RDP Level 2 (Chip protection - IRREVERSIBLE!)")
                else:
                    if print_result:
                        print(f"Unknown RDP level: 0x{rdp_byte:02X}")
                return rdp_byte
            except Exception as e:
                print(f"Error reading option bytes file: {e}")
        return None

def upload_firmware():
    """Upload firmware to the device"""
    if not firmware_path:
        print("No firmware path specified. Creating a simple test firmware...")
        create_test_firmware()
    
    if not os.path.exists(firmware_path):
        print(f"ERROR: Firmware file {firmware_path} not found!")
        return False
        
    cmd = ['st-flash', 'write', firmware_path, '0x8000000']
    result = run_command(cmd, f"Uploading firmware: {firmware_path}")
    return result is not None

def create_test_firmware():
    """Create a simple test firmware binary"""
    firmware_path = "test_firmware.bin"
    
    # Create a simple test pattern
    test_data = bytearray()
    for i in range(1024):  # 1KB of test data
        test_data.append(i & 0xFF)
    
    with open(firmware_path, 'wb') as f:
        f.write(test_data)
    
    print(f"Created test firmware: {firmware_path}")


def set_rdp_level_1():
    """Set RDP to level 1"""
    if verbose:
        print("\n" + "!"*60)
        print("WARNING: Setting RDP Level 1 will enable read protection!")
        print("This will prevent reading flash memory via debug interface.")
        print("To disable, you'll need to perform a mass erase (which erases all flash).")
        print("!"*60)
    
    # Read current option bytes first
    current_rdp = read_option_bytes()
    if current_rdp is None:
        print("Failed to read current option bytes")
        return False
    
    if current_rdp == 0x33:
        print("RDP Level 1 is already set!")
        return True
    
    try:
        # Read current option bytes data
        with open('option_bytes.bin', 'rb') as f:
            current_data = f.read()
        
        # Create new option bytes with RDP Level 1
        new_data = bytearray(current_data)
        new_data[0] = 0x33  # RDP Level 1
        new_data[1] = 0xCC  # RDP complement
        
        if verbose:
            print(f"Current option bytes: {current_data.hex()}")
            print(f"New option bytes:     {new_data.hex()}")
        
        # Write to file first
        with open('new_option_bytes.bin', 'wb') as f:
            f.write(new_data)
        
        # Use file-based write
        cmd = ['st-flash', '--format', 'binary', 'write', 'new_option_bytes.bin', option_bytes_address]
        if verbose:
            print(f"SENDING command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if verbose:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("RDP Level 1 set successfully!")
            print("Device will reset...")
            time.sleep(2)
            return True
        else:
            print(f"Failed to set RDP Level 1. Return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"Error setting RDP: {e}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists('new_option_bytes.bin'):
            os.remove('new_option_bytes.bin')

def set_rdp_level_0():
    """Set RDP to level 0"""
    if verbose:
        print("\n" + "!"*60)
        print("WARNING: Setting RDP Level 0 will disable read protection!")
        print("This will allow reading flash memory via debug interface.")
        print("To enable, you'll need to perform a mass erase (which erases all flash).")
        print("!"*60)

    # Read current option bytes first
    current_rdp = read_option_bytes()
    if current_rdp is None:
        print("Failed to read current option bytes")
        return False

    if current_rdp == 0xAA:
        print("RDP Level 0 is already set!")
        return True

    try:
        # Read current option bytes data
        with open('option_bytes.bin', 'rb') as f:
            current_data = f.read()
        
        # Create new option bytes with RDP Level 0
        new_data = bytearray(current_data)
        new_data[0] = 0xAA  # RDP Level 0
        new_data[1] = 0x55  # RDP complement
        
        if verbose:
            print(f"Current option bytes: {current_data.hex()}")
            print(f"New option bytes:     {new_data.hex()}")
        
        # Write to file first
        with open('new_option_bytes.bin', 'wb') as f:
            f.write(new_data)
        
        # Use file-based write
        cmd = ['st-flash', '--format', 'binary', 'write', 'new_option_bytes.bin', option_bytes_address]
        if verbose:
            print(f"SENDING command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if verbose:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("RDP Level 0 set successfully!")
            print("Device will reset...")
            time.sleep(2)
            return True
        else:
            print(f"Failed to set RDP Level 0. Return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"Error setting RDP: {e}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists('new_option_bytes.bin'):
            os.remove('new_option_bytes.bin')

def reset_device():
    """Reset the device"""
    cmd = ['st-flash', 'reset']
    return run_command(cmd, "Resetting device")


def run_demo():
    print("STM32 Nucleo RDP (Read Protection) Demo")
    print("="*50)
    
    if not check_tools():
        return False
    get_device_info()

    print("STEP 1")
    current_rdp = read_option_bytes(print_result=True)

    set_rdp_level_0()
    reset_device()
    print("Waiting for device reset...")
    time.sleep(3)

    # Upload firmware
    # print("\n" + "="*50)
    # print("STEP 2: Upload firmware")
    # print("="*50)
    # if not upload_firmware():
    #     print("Failed to upload firmware!")
    #     return False
    
    # Read flash before RDP
    print("\n" + "="*50)
    print("STEP 2: Read flash BEFORE RDP protection")
    print("="*50)
    data_before, all_zeros_before = read_flash("initial flash state")
    
    if not data_before:
        print("Failed to read flash memory!")
        return False

    write_flash()
    reset_device()
    print("Waiting for device reset...")
    time.sleep(3)

    data_after, all_zeros_after = read_flash("after writing to flash")

    # Set RDP Level 1
    print("\n" + "="*50)
    print("STEP 4: Set RDP Level 1")
    print("="*50)

    if not set_rdp_level_1():
        print("Failed to set RDP Level 0!")
        print("Trying alternative method...")

    # wait for device to reset
    reset_device()
    print("Waiting for device reset...")
    time.sleep(3)

    # Verify RDP is set
    print("\n" + "="*50)
    print("STEP 5: Verify RDP level")
    print("="*50)
    new_rdp = read_option_bytes()
    
    # Try to read flash after RDP
    print("\n" + "="*50)
    print("STEP 6: Read flash AFTER RDP protection")
    print("="*50)
    data_after, all_zeros_after = read_flash("(after RDP)")
    
    # Summary
    print("\n" + "="*60)
    print("DEMO SUMMARY")
    print("="*60)
    print(f"RDP before: 0x{current_rdp:02X}" if current_rdp is not None else "RDP before: Unknown")
    print(f"RDP after:  0x{new_rdp:02X}" if new_rdp is not None else "RDP after: Unknown")
    print(f"Flash read before RDP: {'SUCCESS' if data_before else 'FAILED'}")
    print(f"Flash read after RDP:  {'SUCCESS' if data_after else 'FAILED'}")
    
    if data_before and data_after:
        print(f"Data before RDP all zeros: {all_zeros_before}")
        print(f"Data after RDP all zeros:  {all_zeros_after}")
        
        if not all_zeros_before and all_zeros_after:
            print("\n SUCCESS: RDP protection is working!")
            print("   - Before RDP: Could read actual flash data")
            print("   - After RDP:  Reading returns all zeros (protected)")
        elif all_zeros_before and all_zeros_after:
            print("\nWARNING: Both reads returned zeros")
            print("   This might indicate the flash was empty or RDP was already active")
        else:
            print("\nUNEXPECTED: RDP protection may not be working as expected")
    
    print("\nNOTE: To disable RDP Level 1, you'll need to perform a mass erase")
    print("      which will erase all flash memory content.")
    
    return True

if __name__ == "__main__":
    run_demo()