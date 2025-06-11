import threading
import time
from pymavlink import mavutil
from collections import defaultdict
import datetime

class StatusMessageListener:
    def __init__(self, vehicle, log_file_path="mavlink_status.log"):
        self.vehicle = vehicle
        self.messages = defaultdict(list)
        self.log_file_path = log_file_path
        self.running = False
        self.thread = None

        self.severity_map = {
            mavutil.mavlink.MAV_SEVERITY_EMERGENCY: "EMERGENCY",
            mavutil.mavlink.MAV_SEVERITY_ALERT: "ALERT",
            mavutil.mavlink.MAV_SEVERITY_CRITICAL: "CRITICAL",
            mavutil.mavlink.MAV_SEVERITY_ERROR: "ERROR",
            mavutil.mavlink.MAV_SEVERITY_WARNING: "WARNING",
            mavutil.mavlink.MAV_SEVERITY_NOTICE: "NOTICE",
            mavutil.mavlink.MAV_SEVERITY_INFO: "INFO",
            mavutil.mavlink.MAV_SEVERITY_DEBUG: "DEBUG"
        }

        with open(self.log_file_path, "a") as f:
            f.write(f"\n--- MAVLink Status Log Started at {datetime.datetime.now()} ---\n")

    def _listen_loop(self):
        self.vehicle.add_message_listener('STATUSTEXT', self._handle_status_text)
        print("[StatusMessageListener] Listening for STATUSTEXT messages...")
        while self.running:
            time.sleep(0.2)  # keep thread alive

        self.vehicle.remove_message_listener('STATUSTEXT', self._handle_status_text)
        print("[StatusMessageListener] Listener stopped.")

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._listen_loop)
            self.thread.daemon = True
            self.thread.start()
            print("[StatusMessageListener] Background thread started.")

    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()
            print("[StatusMessageListener] Background thread stopped.")

    def _handle_status_text(self, vehicle, name, msg):
        severity = msg.severity
        text = msg.text.strip()
        severity_name = self.severity_map.get(severity, f"UNKNOWN({severity})")
        timestamp = int(time.time())
        self.messages[severity_name].append((timestamp,text))

        print(f"[{severity_name}] {text}")
        self._log_message(severity_name, text)

    def _log_message(self, severity_name, text):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{severity_name}] {text}\n"
        with open(self.log_file_path, "a") as f:
            f.write(log_line)

    def get_all_messages(self):
        return dict(self.messages)

    def get_messages_by_severity(self, severity_name):
        return self.messages.get(severity_name.upper(), [])
