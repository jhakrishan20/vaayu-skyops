# custom UAV's task planner for custom missions

from dronekit import LocationGlobalRelative
import time, math
from dronekit import VehicleMode
from pymavlink import mavutil
from core.utils.math_tools import MathTools

class Planner:
    def __init__(self, vehicle):
        self.vehicle = vehicle

    def set_mode(self, mode_name):
        """Set the flight mode and confirm the switch."""
        try:
            if not self.vehicle:
                print("❌ No vehicle connected!")
                return False

            print(f"🔄 Switching to {mode_name} mode...")
            self.vehicle.mode = VehicleMode(mode_name)
            time.sleep(2)  # Allow mode switch time

            if self.vehicle.mode.name == mode_name:
                print(f"✅ Successfully switched to {mode_name}.")
                return True
            else:
                print(f"❌ Failed to switch to {mode_name}.")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False


    def takeoff_and_hold(self, target_alt, hover_mode=None):
     try:
        if not self.vehicle:
            print("❌ No vehicle connected!")
            return False

        target_alt = float(target_alt)  # Ensure valid altitude input

        # Check GPS fix quality
        gps_fix = self.vehicle.gps_0.fix_type  # Fix type (higher is better)
        gps_okay = gps_fix >= 3  # Usually, 3+ means a valid 3D GPS fix

        # Decide the hover mode
        hover_mode = "LOITER" if gps_okay else "LAND"

        print(f"📡 GPS Fix Type: {gps_fix} - {'Good' if gps_okay else 'Poor'}")
        print(f"🔄 Selecting Hover Mode: {hover_mode}")

        # If already at or above target altitude, no need to climb
        if self.vehicle.location.global_relative_frame.alt >= target_alt:
            print(f"🚀 Already at {target_alt}m. No climb needed.")
            return True

        # Switch to GUIDED mode for takeoff
        if not self.set_mode("GUIDED"):
            print("⚠️ Failed to switch to GUIDED mode. Aborting takeoff.")
            return False

        print(f"🚀 Taking off to {target_alt}m...")
        self.vehicle.simple_takeoff(target_alt)

        # Monitor altitude until it reaches target
        while True:
            current_alt = self.vehicle.location.global_relative_frame.alt
            print(f"📡 Current Altitude: {current_alt:.2f} m")

            # If 95% of target altitude is reached, proceed
            if current_alt >= target_alt * 0.95:
                print(f"✅ Altitude {target_alt}m reached.")
                break

            time.sleep(0.5)  # Small delay to avoid excessive polling

        # Immediately check GPS fix before switching hover mode
        gps_fix = self.vehicle.gps_0.fix_type
        gps_okay = gps_fix >= 3
        hover_mode = "LOITER" if gps_okay else "LAND"

        print(f"🔄 Final GPS Check: {gps_fix} - {'Good' if gps_okay else 'Poor'}")
        print(f"🔄 Switching to {hover_mode} mode...")

        if not self.set_mode(hover_mode):
            print("⚠️ Failed to switch hover mode. Landing for safety.")
            self.set_mode("LAND")
            return False

        print(f"✅ Hovering at {target_alt}m in {hover_mode} mode.")
        return True

     except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️ Emergency Landing for Safety!")
        self.set_mode("LAND")
        return False
     
    # mid air hold alt mode (works when alt > 1m) 
    def hold_altitude(self):
     try:
        if not self.vehicle:
            print("❌ No vehicle connected!")
            return False

        current_alt = self.vehicle.location.global_relative_frame.alt
        if current_alt < 1.0:
            print(f"⚠️ Altitude too low ({current_alt:.2f}m). Consider taking off first.")
            return False

        # GPS fix check
        gps_fix = self.vehicle.gps_0.fix_type
        gps_okay = gps_fix >= 3
        hover_mode = "LOITER" if gps_okay else "ALT_HOLD"  # Fallback to non-GPS mode if needed

        print(f"📡 GPS Fix Type: {gps_fix} - {'Good' if gps_okay else 'Poor'}")
        print(f"📍 Current Altitude: {current_alt:.2f} m")
        print(f"🔄 Selecting Hover Mode: {hover_mode}")

        # Attempt to change mode
        if not self.set_mode(hover_mode):
            print("⚠️ Failed to switch to hover mode.")
            if gps_okay:
                print("⚠️ Attempting to land as backup.")
                self.set_mode("LAND")
            return False

        print(f"✅ Drone now holding altitude in {hover_mode} mode.")
        return True

     except Exception as e:
        print(f"❌ Error during hold_altitude: {str(e)}")
        print("⚠️ Emergency Landing for Safety!")
        self.set_mode("LAND")
        return False 
    
    # emergency onspot landing
    def emergency_land(self):
        """Safely land the drone in case of emergency."""
        try:
            if not self.vehicle:
                print("❌ No vehicle connected!")
                return False

            print("⚠️ Emergency detected! Initiating landing...")

            self.set_mode("LAND")
            return True

        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        
    # intelligent land according to gps fix, good-rtl bad-land    
    def safe_land(self):
        """Safely land the drone in case of emergency."""
        try:
            if not self.vehicle:
                print("❌ No vehicle connected!")
                return False

            print("⚠️ Emergency detected! Initiating landing...")

            # Check GPS fix before deciding to LAND or RTL
            if self.vehicle.gps_0.fix_type < 3:  # Weak GPS fix
                print("⚠️ Weak GPS! Performing immediate LAND.")
                self.set_mode("LAND")
            else:
                print("🏡 GPS fix strong. Returning to launch (RTL).")
                self.set_mode("RTL")

            return True

        except Exception as e:
            print(f"❌ Error: {e}")
            return False    

    def goto_wp(self, lat, lon, alt, groundspeed):
        """
        Smoothly navigate the drone to the given GPS waypoint.
        :param lat: Latitude of the target location
        :param lon: Longitude of the target location
        :param alt: Altitude in meters
        :param groundspeed: Groundspeed in m/s (default 5)
        :return: True if reached successfully, False otherwise
        """
        try:
            target_location = LocationGlobalRelative(lat, lon, alt)

            print(f"📍 Navigating to waypoint: ({lat}, {lon}, {alt}m)")

            # Ensure we're in GUIDED mode
            self.set_mode("GUIDED")

            self.vehicle.groundspeed = groundspeed
            self.vehicle.simple_goto(target_location)

            while True:
                distance = MathTools().distance_to_wp(target_location)
                print(f"📡 Distance to waypoint: {distance:.2f} m")

                if distance <= 1.0:  # Threshold for "arrived"
                    print("✅ Reached waypoint.")
                    break

                time.sleep(1)

            return True

        except Exception as e:
            print(f"❌ Navigation error: {e}")
            return False    
    

    def stop(self):
     try:
        # Determine appropriate hold mode
        gps_fix = self.vehicle.gps_0.fix_type
        gps_okay = gps_fix >= 3
        hold_mode = "LOITER" if gps_okay else "BRAKE"

        print(f"📡 GPS Fix Type: {gps_fix} - {'Good' if gps_okay else 'Poor'}")
        print(f"🔄 Switching to Hold Mode: {hold_mode}")

        if not self.set_mode(hold_mode):
            print("⚠️ Failed to switch to hold mode.")
            return False

        print("🛑 Drone is now holding position.")
        return True

     except Exception as e:
        print(f"❌ Error during hold: {e}")
        return False
    
    # set g_speed in guided mode
    def set_ground_speed(self, speed_mps):
     try:
        if not isinstance(speed_mps, (int, float)) or speed_mps <= 0:
            print("⚠️ Invalid ground speed value.")
            return False

        self.vehicle.groundspeed = speed_mps
        print(f"✅ Ground speed set to {speed_mps} m/s")
        return True
     except Exception as e:
        print(f"❌ Error in setting ground speed: {e}")
        return False
    

    def send_ned_velocity(self, vx, vy, vz):
        msg = self.vehicle.message_factory.set_position_target_local_ned_encode(
            0, 0, 0, mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            0b0000111111000111,  # Control only velocity
            0, 0, 0,
            vx, vy, vz,  # m/s
            0, 0, 0,
            0, 0)
        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()
        
    def send_yaw_command(self, heading, relative=False):
        """
        Sends a yaw command to the vehicle.
        heading: in degrees (0-360)
        relative: if True, yaw is relative to current yaw
        """
        is_relative = 1 if relative else 0
        msg = self.vehicle.message_factory.command_long_encode(
            0, 0,
            mavutil.mavlink.MAV_CMD_CONDITION_YAW,
            0,
            heading,     # target angle
            10,          # yaw speed deg/s
            1,           # direction (-1 ccw, 1 cw)
            is_relative,
            0, 0, 0
        )
        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()
    




  