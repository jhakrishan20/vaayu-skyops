from models.telemetry_model import TelemetryModel
from adapters import StatusMessageListener
from api.controller.event_controller import EventController
import datetime, time, threading

class EventService:
    def __init__(self, connection, socketio):
        self.connection = connection
        self.is_running = True
        self.vehicle = self.connection.vehicle
        self.telemetry = None
        self.mav_msg = StatusMessageListener(self.vehicle)
        self.event_controller = EventController(socketio)

        self.last_connected = None
        self.last_armed = None
        self.last_mavmsg_timestamp = None

        self._status_text_thread = None
        self._telem_thread = None
        self._hb_monitor_thread = None

    def trigger_events(self):

        # create instances
        self.telemetry = TelemetryModel(self.vehicle) # initallizing telemetry stream
        # self.mav_msg = StatusMessageListener(self.vehicle) # init the mav status text object
        self.mav_msg.start()  # start listening

        # invoke methods
        self._send_mavmsg()
        self._send_telemetry()
        self._send_vehicle_status()

    def stop_events(self):

        """ stop sendind events """
        self.is_running = False  
    
    
    # mav_msgs event
    def _send_mavmsg(self):
        self._status_text_thread = threading.Thread(target=self._mavmsg_thread).start()

    def _mavmsg_thread(self):
        while self.is_running:
            data = self._fetch_mavmsg()
            # print(data)
            # emit when any update from machine
            if data is not None:
               self.event_controller.emit_mavmsg(data)
            time.sleep(1)       

    def _fetch_mavmsg(self):
        """
        Retrieves the latest MAVLink status message (with timestamp),
        returns a payload only if the message is new compared to the last processed one.
        Format expected from get_all_messages(): {'WARNING': [(timestamp, message), ...]}
        """

        all_messages = self.mav_msg.get_all_messages()
        # print(all_messages)

        latest_entry = None
        latest_severity = None

        for severity in reversed(list(all_messages.keys())):
         messages = all_messages.get(severity, [])
         if messages:
            # Get the latest message in this severity group
            candidate = max(messages, key=lambda x: x[0])  # x = (timestamp, message)
            if self.last_mavmsg_timestamp is None or candidate[0] > self.last_mavmsg_timestamp:
                latest_entry = candidate
                latest_severity = severity
                self.last_mavmsg_timestamp = candidate[0]
                break

        if not latest_entry:
            return None  # No new message to send
        else:
            payload = {
            "severity": latest_severity,
            "timestamp": latest_entry[0],
            "message": latest_entry[1],
            "received_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            return payload



    # telemetry event
    def _send_telemetry(self):
        self._telem_thread = threading.Thread(target=self._telemetry_thread).start()

    def _safe_call(self, method_name, method, telemetry):
        """Calls a method safely and handles exceptions."""
        try:
            telemetry[method_name] = method()
        except Exception as e:
            telemetry[method_name] = f"⚠️ Error: {str(e)}"

    def _fetch_telemetry(self):

        telemetry = {}
        # Call each method safely
        self._safe_call("nav", self.telemetry.get_navigation_data, telemetry)
        self._safe_call("attitude", self.telemetry.get_attitude_data, telemetry)
        self._safe_call("gps", self.telemetry.get_gps_data, telemetry)
        self._safe_call("system", self.telemetry.get_system_status, telemetry)
        self._safe_call("battery", self.telemetry.get_battery_status, telemetry)
        self._safe_call("imu", self.telemetry.get_imu_data, telemetry)

        return telemetry
    
    def _telemetry_thread(self):
            while self.is_running:
              data = self._fetch_telemetry()
              if not data:
                break
              self.event_controller.emit_telemetry(data)
              time.sleep(1)


    # vehicle status event
    def _send_vehicle_status(self):
        self._hb_monitor_thread = threading.Thread(target=self._check_vehicle_status).start()

    def _check_vehicle_status(self):

        """loop to constantly check the connection"""   
        while self.is_running:
            connected = self.connection.is_connected
            armed = self.connection.is_arm
            # Check if there's any change
            if connected != self.last_connected or armed != self.last_armed:
               if not connected:
                   self.is_running = False
               payload = {
               "connected": connected,
               "armed": armed
               }
               self.event_controller.emit_vehicle_status(payload)

             # Update last known states
               self.last_connected = connected
               self.last_armed = armed
 
            time.sleep(1)

                

   
            