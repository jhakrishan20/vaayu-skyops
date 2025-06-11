# customized scan mission, called in services with params as waypoints and planner object

from core.utils.math_tools import MathTools
import time, threading

class Scan:
    def __init__(self, planner, waypoints, g_speed):
        self.planner = planner 
        self.waypoints = waypoints
        self.ground_speed = g_speed
        self._alt_thread_active = False
        self._yaw_thread_active = False
        self._target_wp = None
        self._target_alt = None

    def start_mission(self):
     max_retries = 3
     print("🚀 Starting scan mission with waypoints...")

     try:
        if not self.waypoints or len(self.waypoints[0]) != 3:
            print("❌ Invalid waypoints data. Aborting mission.")
            return False

        """" Fetch altitude from the first waypoint """
        _, _, initial_alt = self.waypoints[0]

        """ Perform Takeoff and Hold at initial altitude """

        print(f"🛫 Taking off and holding at {initial_alt}m before starting mission...")
        takeoff_success = self.planner.takeoff_and_hold(initial_alt)
        self.planner.set_ground_speed(self.ground_speed)

        if not takeoff_success:
            print("❌ Takeoff failed. Aborting mission.")
            return False
        
        """ start yaw degree monitoring """
        self._yaw_thread_active = True
        yaw_thread = threading.Thread(target=self._maintain_yaw)
        yaw_thread.start()

        """ start current altitude monitoring """
        self._target_alt = initial_alt
        self._alt_thread_active = True
        alt_thread = threading.Thread(target=self._maintain_altitude)
        alt_thread.start()


        """ Start navigating through waypoints """
        for index, wp in enumerate(self.waypoints):
            self._target_wp = wp
            lat, lon, alt = wp
            print(f"📍 Navigating to Waypoint {index + 1}/{len(self.waypoints)}: ({lat}, {lon}, {alt}m)")

            attempt = 0
            success = False

            while attempt < max_retries:
                success = self.planner.goto_wp(lat, lon, alt, self.ground_speed)

                if success:
                    print(f"✅ Reached Waypoint {index + 1}")
                    break  # Go to next waypoint

                attempt += 1
                print(f"⚠️ Failed attempt {attempt}/{max_retries} for Waypoint {index + 1}. Retrying...")
                self.planner.stop()  # Stop and reset before retrying
                time.sleep(1)

            if not success:
                print(f"❌ Failed to reach Waypoint {index + 1} after {max_retries} retries. Returning home...")
                self.planner.emergency_land()
                return False

        """ hold alt after completion """    
        self.planner.hold_altitude()
        time.sleep(3)
        
        """ stop the alt monitor thread"""
        self._alt_thread_active = False
        alt_thread.join()

        """ stop the yaw monitor thread"""
        self._yaw_thread_active = False
        yaw_thread.join()

        print("✅ Scan mission complete. Returning to launch...")
        self.planner.emergency_land()
        # self.planner.safe_land()
        print("vehicle return to land")
        return True

     except Exception as e:
        print(f"❌ Unexpected Error during mission: {e}")
        print("⚠️ Triggering emergency landing!")
        self.planner.emergency_land()
        return False
    
    # method to maintain the alt of drone while mission
    def _maintain_altitude(self):
     while self._alt_thread_active:
        try:
            current_alt = self.planner.vehicle.location.global_relative_frame.alt
            diff = self._target_alt - current_alt

            if abs(diff) > 0.3:  # Threshold in meters
                direction = -0.5 if diff < 0 else 0.5 # NED vz: down is +, up is -
                print(f"↕️ Altitude off by {diff:.2f}m. Correcting with vz={direction}")
                self.planner.send_ned_velocity(0, 0, direction)
            else:
                pass  # Altitude is stable

            time.sleep(0.5)

        except Exception as e:
            print(f"⚠️ Altitude maintain error: {e}")   
    
    # method to keep the drone yaw facing towards the target wp
    def _maintain_yaw(self):
     while self._yaw_thread_active:
        try:
            if not self._target_wp:
                time.sleep(0.5)
                continue

            vehicle = self.planner.vehicle

            # Get current location
            current_location = vehicle.location.global_relative_frame
            current_lat = current_location.lat
            current_lon = current_location.lon

            # Target waypoint
            target_lat, target_lon, _ = self._target_wp

            # Calculate desired yaw (heading in degrees)
            target_heading = MathTools().calculate_bearing(current_lat, current_lon, target_lat, target_lon)

            # Get current heading from vehicle
            current_heading = vehicle.heading  # 0-360 degrees

            # Calculate yaw difference
            diff = target_heading - current_heading

            # Normalize difference to [-180, 180]
            diff = (diff + 180) % 360 - 180

            if abs(diff) > 3:  # Only adjust if difference is significant
                smooth_yaw = current_heading + (diff * 0.1)  # Gradually apply 10% of correction
                smooth_yaw = smooth_yaw % 360

                print(f"🧭 Yaw correction needed. Heading: {current_heading}, Target: {target_heading}, Adjusting to: {smooth_yaw:.2f}")
                self.planner.send_yaw_command(smooth_yaw)
            else:
                pass  # Heading is close enough

            time.sleep(0.5)

        except Exception as e:
            print(f"⚠️ Yaw maintain error: {e}")

    # mehtod for smooth yaw transitions     
    def _smooth_heading_interpolation():
       pass

   

            
    
    

        
