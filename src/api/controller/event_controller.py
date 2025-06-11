class EventController:
    def __init__(self, socketio):
        self.socketio = socketio
        # self.event_room = "event_room"

    def emit_telemetry(self, response):
        self._emit_event(response, "telemetry_response")

    def emit_mavmsg(self, response):
        self._emit_event(response, "mavmsg_response")

    def emit_vehicle_status(self, response):
        print(response)
        self._emit_event(response, "monitoring_response")

    def _emit_event(self, response, response_event):
        try:
            self.socketio.emit(response_event, {'message': response})
            # print("okkay")
        except Exception as e:
            self.socketio.emit('error', {'error': str(e)})

    # def join_event_room(self):
    #  try:
    #     sid = request.sid
    #     join_room(self.event_room, sid = sid)
    #     print(f"Client {sid} joined event_room")
    #  except Exception as e:
    #     print(f"⚠️ Failed to join event_room: {str(e)}")

    # def leave_event_room(self):
    #  try:
    #     sid = request.sid
    #     leave_room(self.event_room, sid = sid)
    #     print(f"Client {sid} left event_room")
    #  except Exception as e:
    #     print(f"⚠️ Failed to leave event_room: {str(e)}")

