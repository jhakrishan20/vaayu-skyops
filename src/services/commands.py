# high level drone services module

from adapters import ConnectionHandler, FlightController, MotorController, Network, Planner, WaypointUploader

from .events import EventService

from core.utils.portmanager import PortManager
from core.config.config import config

from mission_factory import Scan

import os, time, datetime, threading

class CommandService:
    
   def __init__(self, socketio):
      self.socketio = socketio
      self.conn = ConnectionHandler()
      self.network = Network()
      self.manager = PortManager()

      self.event_service = None
      self.event_thread = None

      self.control = None
      self.motors = None
      self.plan = None
      self.upload = None

   def start_connection(self):
      self.manager.free_port(config["serial_port"])
      message = self.conn.connect(config["serial_port"],config["baud"])
      #   message = self.conn.connect_sitl(config["tcp_conn_string"],config["baud"])

      if message == True:
         self.control = FlightController(self.conn.vehicle, self.conn.is_connected)
         self.upload = WaypointUploader(self.conn.vehicle)  # initiallizing waypointuploader class with drone conn instance

         # trigger drone events
         self.event_service = EventService(self.conn, self.socketio)
         self.event_thread = threading.Thread(target=self.event_service.trigger_events)
         self.event_thread.start()

      else:
         print("vehicle not connected")    
      return message

   def stop_connection(self):
      """stop sending events"""
      self.event_service.stop_events()
      message = self.conn.disconnect()
      return message
        
   def send_network_status(self):
         # if self.network.network_monitoring:
            # self.network.network_monitoring = True
         return self.network.heartbeat()

   def acknowledge(self,ack):
           self.network.ack = ack
           return True 

   def trigger_failsafe(self):
        if self.control.is_arm and self.plan:
            self.plan.emergency_land()
                     
    # drone commands
   def start_to_arm(self):
        if self.conn.is_connected == True:
           message = self.control.arm_vehicle()
           self.motors = MotorController(self.conn.vehicle)
           if message == True:
            #   self.control.is_arm = True
              self.plan = Planner(self.conn.vehicle)   
           return message

   def start_to_disarm(self):
        if self.conn.is_connected:
            if self.control.is_arm == True:
               message = self.control.disarm_vehicle()
               if message == True:
                  # self.control.is_arm = False
                  self.plan = None   
            return message
            
   def start_motors(self):
        if self.conn.is_connected == True:
           if self.control.is_arm == True:
              message = self.motors.throttle_up()
        return message

   def stop_motors(self):
        if self.conn.is_connected == True:
           if self.control.is_arm == True:
              message = self.motors.throttle_down()
           return message

   def start_roll(self):
        if self.conn.is_connected == True:
           if self.control.is_arm == True:
              message = self.motors.roll_right()
           return message
        
   def stop_roll(self):
        if self.conn.is_connected == True:
           if self.control.is_arm == True:
              message = self.motors.roll_left()
           return message 

   def start_pitch(self):
        if self.conn.is_connected == True:
           if self.control.is_arm == True:
              message = self.motors.pitch_forward()
           return message

   def stop_pitch(self):
        if self.conn.is_connected == True:
           if self.control.is_arm == True:
              message = self.motors.pitch_backward()
           return message

   def start_yaw(self):
        if self.conn.is_connected == True:
           if self.control.is_arm == True:
              message = self.motors.yaw_clockwise()
           return message

   def stop_yaw(self):
        if self.conn.is_connected == True:
           if self.control.is_arm == True:
              message = self.motors.yaw_anticlockwise()
           return message               

   def hold_alt(self,alt):
      #  print(float(self.data["height"]),2)
       if self.conn.is_connected == True:
           if self.control.is_arm == True:
              message = self.plan.takeoff_and_hold(alt)
            #   self.data = {}  #empty the dict for reuse
           return message
       
   def return_to_land(self):
       if self.conn.is_connected == True:
           if self.control.is_arm == True:
              message = self.plan.emergency_land()
           return message

   def mode_switch(self,mode):
        message = self.plan.set_mode(mode)
        return message
                  
   #  def handle_file_upload(self, data):
    
   #   try:
   #      filename = data.get("filename")
   #      filedata = data.get("data")

   #      if not filename or not filedata:
   #          return {"status": "error", "message": "Invalid file data received."}

   #      # Ensure the directory exists
   #      wp_dir = config.get("wp_files", "wp_files")  # Default to 'wp_files' if not set
   #      os.makedirs(wp_dir, exist_ok=True)  # Create directory if it doesn't exist

   #      # Save the file
   #      file_path = os.path.join(wp_dir, filename)
   #      with open(file_path, "wb") as f:
   #          f.write(filedata)

   #      print(f"✅ File '{filename}' saved successfully at {file_path}")

   #      # Upload the waypoint file to Mission Planner
   #      self._file_upload_helper(file_path)

   #      return {"status": "success", "message": f"File '{filename}' uploaded and sent to Mission Planner successfully."}

   #   except Exception as e:
   #      print("❌ File upload failed:", e)
   #      return {"status": "error", "message": str(e)}

   #  def _file_upload_helper(self, wp_file):
   #   try:
   #      print(f"📡 Uploading waypoints from '{wp_file}' to Mission Planner...")
   #      self.upload.upload_mission(wp_file)
   #      print("✅ Waypoints uploaded successfully!")
   #   except Exception as e:
   #      print(f"❌ Failed to upload waypoints: {e}")



    # takes waypoints from gui, converts it into .wp format file and uploads the file to pixhawk 
   #  def upload_wps(self,data):
   #   try:
   #      waypoints = data
   #      self.upload.save_wp_file(waypoints)
   #    #   self.upload.upload_mission(mission)
   #      print("✅ Waypoints uploaded successfully!")
   #   except Exception as e:
   #      print(f"❌ Failed to upload waypoints: {e}")

   
   def scan(self, waypoints, g_speed):
         try:
            response = self.start_to_arm()
            print(response)
            if response:
               scan = Scan(self.plan, waypoints, g_speed)
               response = scan.start_mission()
               if response == False:
                  self.start_to_disarm() 
            else:
                print("failed to arm")
         except Exception as e:
            print(f"❌ Error occured, failed to start the mission: {e}")
                  