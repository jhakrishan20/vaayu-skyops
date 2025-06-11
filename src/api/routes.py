from api.controller import CommandController

class DroneControlRoute():
    def __init__(self, socketio):
        self.socketio = socketio
        self.controller = CommandController(socketio)  # instantiating controller object, so that, methods called from Controller class has valid  instance in it
        self.register_routes()

    def register_routes(self):  

        self.socketio.on_event('connect', self.controller.connect)
        self.socketio.on_event('disconnect', self.controller.disconnect)
        self.socketio.on_event('ack', self.controller.ack)
        # self.socketio.on_event('data', self.controller.input_data)

        self.socketio.on_event('connection', self.controller.connection_route)
        self.socketio.on_event('disconnection', self.controller.disconnection_route)
        self.socketio.on_event('arm', self.controller.arming_route)
        self.socketio.on_event('disarm', self.controller.disarming_route)

        # redesign these routes into one 'motors', receive req with a data specifing the action to be done, accordingly call the method
        self.socketio.on_event('throttleup', self.controller.throttle_up_route)
        self.socketio.on_event('throttledown', self.controller.throttle_down_route)
        self.socketio.on_event('rollright', self.controller.roll_right_route)
        self.socketio.on_event('rollleft', self.controller.roll_left_route)
        self.socketio.on_event('pitchforward', self.controller.pitch_forward_route)
        self.socketio.on_event('pitchbackward', self.controller.pitch_backward_route)
        self.socketio.on_event('yawclock', self.controller.yaw_clockwise_route)
        self.socketio.on_event('yawanticlock', self.controller.yaw_anticlockwise_route)


        self.socketio.on_event('setalt', self.controller.hold_alt_route)
        self.socketio.on_event('land', self.controller.land_route)
        # self.socketio.on_event('camera', self.controller.camera_route)
        self.socketio.on_event('mode_switch', self.controller.mode_switch_route)

        # upload .wp file route
        # get waypoints and generate .wp file route

        self.socketio.on_event('start_scan', self.controller.start_scan_route)
 