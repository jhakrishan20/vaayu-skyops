import math

class MathTools:
    def __init__(self, alpha=0.3, initial_value=0):
        self.alpha = alpha
        self.smoothed_value = initial_value
    
    def ewma_smooth_alt(self, new_value):
        self.smoothed_value = self.alpha * new_value + (1 - self.alpha) * self.smoothed_value
        return self.smoothed_value
    
    def distance_to_wp(self, target_location):
        """Calculate the ground distance in meters between two LocationGlobalRelative points."""
        dlat = target_location.lat - self.vehicle.location.global_relative_frame.lat
        dlong = target_location.lon - self.vehicle.location.global_relative_frame.lon
        return math.sqrt((dlat * 1.113195e5) ** 2 + (dlong * 1.113195e5) ** 2)
    
    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """
        Calculates the bearing between two GPS coordinates.
        """
        dLon = math.radians(lon2 - lon1)
        y = math.sin(dLon) * math.cos(math.radians(lat2))
        x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
            math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dLon)
        bearing = math.atan2(y, x)
        return (math.degrees(bearing) + 360) % 360

