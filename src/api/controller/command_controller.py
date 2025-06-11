import threading, time
from services.commands import CommandService

class CommandController:

    def __init__(self,socketio):
        self.service = CommandService(socketio)
        self.socketio = socketio

      # heartbeat - ack mechanism , WS-client triggers connect and server starts sending heartbeats, client responds on 'ack' event of server 
    def connect(self, data=None):
        print("client connected")
        threading.Thread(target=self._pingpong_thread).start()

    def _pingpong_thread(self):
        while True:
          self._handle_event(self.service.send_network_status, 'heartbeat')
          time.sleep(2)

    def ack(self,ack=None):
        # print(ack['message'])
        try:
            response = self.service.acknowledge(ack['message'])
            # print(response)  
        except Exception as e:
            print(e)  

    def disconnect(self, data=None):
        self.service.trigger_failsafe()
        print("disconnected, triggering failsafe") 


    # def input_data(self,data=None):
    #     try:
    #         # print(data)
    #         key, value = next(iter(data.items()))
    #         self.service.data[key] = data[value] 
    #         # self.socketio.emit("data_response", {'message': True})  
    #     except Exception as e:
    #         print(e)
    #         # self.socketio.emit('error', {'error': False})

    def connection_route(self, data=None):
        self._handle_event(self.service.start_connection, 'connection_response')   

    def disconnection_route(self, data=None):
        self._handle_event(self.service.stop_connection, 'disconnection_response')


    def arming_route(self, data=None):
        self._handle_event(self.service.start_to_arm, 'arm_response')

    def disarming_route(self, data=None):
        self._handle_event(self.service.start_to_disarm, 'disarm_response')



    def throttle_up_route(self, data=None):
        self._handle_event(self.service.start_motors, 'throttleup_response')

    def throttle_down_route(self, data=None):
        self._handle_event(self.service.stop_motors, 'throttledown_response')

    def roll_right_route(self, data=None):
        self._handle_event(self.service.start_roll, 'rollright_response')

    def roll_left_route(self, data=None):
        self._handle_event(self.service.stop_roll, 'rollleft_response')

    def pitch_forward_route(self, data=None):
        self._handle_event(self.service.start_pitch, 'pitchforward_response')

    def pitch_backward_route(self, data=None):
        self._handle_event(self.service.stop_pitch, 'pitchbackward_response')

    def yaw_clockwise_route(self, data=None):
        self._handle_event(self.service.start_yaw, 'yawclock_response')

    def yaw_anticlockwise_route(self, data=None):
        self._handle_event(self.service.stop_yaw, 'yawanticlock_response')


    def land_route(self, data=None):
        self._handle_event(self.service.return_to_land, 'land_response') 

    # def camera_route(self, data=None):
    #     self._handle_event(self.service.handle_camera, 'camera_response')

    def _handle_event(self, function, response_event):
        
        try:
            response = function()
            self.socketio.emit(response_event, {'message': response})  
        except Exception as e:
            self.socketio.emit('error', {'error': str(e)})  
    

    # methods below receives some data from client side

    def hold_alt_route(self, data=None):
        try:
            alt = data['height']
            response = self.service.hold_alt(alt)
            self.socketio.emit('setalt_response', {'message': response})  
        except Exception as e:
            self.socketio.emit('error', {'error': str(e)})

    # def get_wps(self,data=None):
    #     try:
    #         response = self.service.upload_wps(data)
    #         self.socketio.emit("upload_response", {'message': response})  
    #     except Exception as e:
    #         self.socketio.emit('error', {'error': str(e)})

    # gets waypoints list, [[lat,long,alt]] fromat, from interface and initiates the custom generated mission
    def start_scan_route(self,data=None):
        # print(data)
        waypoints = data["waypoints"]
        speed = data["speed"]
        print(waypoints)
        try:
            # Validate the input data format
            if not isinstance(waypoints, list) or not all(isinstance(wp, list) and len(wp) == 3 for wp in waypoints):
               raise ValueError("Invalid data format. Expected a list of [lat, lon, alt] lists.")

            # # If valid, proceed to scan
            response = self.service.scan(waypoints, speed)
            self.socketio.emit("start_scan_response", {'message': response})

        except Exception as e:
           self.socketio.emit('error', {'error': str(e)})
   

    def mode_switch_route(self, data=None):
        print(data["mode"])
        try:
            response = self.service.mode_switch(data["mode"]) 
            self.socketio.emit("mode_switch_response", {'message': response})  
        except Exception as e:
            self.socketio.emit('error', {'error': str(e)})

                              