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

# memo mode = 0, Boot0 = 0, UFB = 0
bank_1_start = "0x08000000"  # Flash start address
bank_1_end = "0x08017FFF"

test_data = bytearray()
test_data.extend(b"SIMON_SIMON_SIMO")  # 16 bytes

verbose = True

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


def read_flash(description=""):
    """Read flash memory"""
    output_file = f"flash_read_{int(time.time())}.bin"
    cmd = ['st-flash', '--format', 'binary', 'read', output_file, bank_1_start, '0x18000']
    result = run_command(cmd, f"Reading flash memory {description}")
    
    if result and os.path.exists(output_file):
        with open(output_file, 'rb') as f:
            data = f.read()
        
        return data
    
    return None

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

def reset_device():
    """Reset the device"""
    cmd = ['st-flash', 'reset']
    return run_command(cmd, "Resetting device")


def check_data_0(data):
    # Check if all bytes are 0x00
    all_zeros = all(b == 0 for b in data)
    non_zero_count = sum(1 for b in data if b != 0)
    
    if verbose:
        print(f"Read {len(data)} bytes")
        print(f"Non-zero bytes: {non_zero_count}/{len(data)}")
        print(f"All zeros: {all_zeros}")
    
    return all_zeros

def check_data_write(data):
    # checking that data is same as test_data
    return data[:16] == test_data

def data_print_first_32_bytes(data):
    print("First 32 bytes:", ' '.join(f'{b:02X}' for b in data[:32]))

def data_to_ascii(data):
    return ''.join(chr(b) for b in data)

def check_data_protected(data):
    # checking that data is all 0x00
    # 8000550103000301000000000000ffff
    data_expected = bytearray(b"\x80\x00\x55\x01\x03\x00\x03\x01\x00\x00\x00\x00\x00\x00\xff\xff")
    if verbose:
        print("Expected data:", data_to_ascii(data_expected))
        print("Actual data:", data_to_ascii(data))
        print("data: ", data)
    return data[:16] == data_expected

def run_demo():
    print("STM32 Nucleo READ SRAM")
    print("="*50)
    
    if not check_tools():
        return False
    get_device_info()

    data_after = read_flash("read flash")

    print(data_to_ascii(data_after))

    # print first 32 bytes
    data_print_first_32_bytes(data_after)


    return True

if __name__ == "__main__":
    run_demo()