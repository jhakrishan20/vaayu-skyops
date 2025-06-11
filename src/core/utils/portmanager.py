import os
import signal
import platform
import subprocess
import re
import serial.tools.list_ports

class PortManager:
    @staticmethod
    def free_port(port):
        try:
            system = platform.system()

            if system == "Windows":
                result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
                for line in result.stdout.splitlines():
                    if f":{port}" in line:
                        parts = line.split()
                        pid = parts[-1]  # PID is the last column
                        if pid.isdigit():
                            os.system(f"taskkill /F /PID {pid}")
                            print(f"✅ Process {pid} using port {port} has been killed.")

            else:  # Linux / macOS
                result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)
                for line in result.stdout.splitlines()[1:]:  # Skip the header
                    parts = line.split()
                    pid = parts[1]  # PID is in the second column
                    os.kill(int(pid), signal.SIGKILL)
                    print(f"✅ Process {pid} using port {port} has been killed.")

            print(f"Port is now free.")
            return True
        
        except Exception as e:
            print(f"❌ Error freeing port {port}: {e}")
            return False

    @staticmethod
    def get_usb_port():
        """
        Detects USB serial device like ArduPilot across platforms.
        """
        try:
         ports = serial.tools.list_ports.comports()
        #  print(ports)

         for port in ports:
            #  print(port.description)
            #  print(f"🔍 Checking port: {port.device} | Desc: {port.description} | HWID: {port.hwid}")

             if any(keyword in port.description for keyword in ["USB", "FTDI", "CP210", "ArduPilot", "Cube Orange+ Mavlink"]):
                print(f"✅ Likely USB serial device found: {port.device}")
                return port.device

         print("❌ No matching USB serial device found.")
         return None

        except Exception as e:
         print(f"❌ Error detecting USB port: {e}")
         return None
