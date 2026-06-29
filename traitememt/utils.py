import math
import re 

def local_to_global(BasePoint : tuple, LocalPoint : tuple, BaseAngle : float) -> tuple:
    """
    Convert a point from local coordinates to global coordinates.

    Parameters:
    BasePoint (tuple): The global coordinates of the base point (x, y, z).
    LocalPoint (tuple): The local coordinates of the point to convert (x, y, z).
    BaseAngle (float): The angle of the local coordinate system relative to the global coordinate system (in radians).

    Returns:
    tuple: The global coordinates of the converted point (x, y, z).
    """
    BaseAngle = math.radians(BaseAngle)  # Convert angle from degrees to radians
    base_x, base_y, base_z = BasePoint
    local_x, local_y, local_z = LocalPoint

    # Apply rotation matrix
    global_x = base_x + local_x * math.cos(BaseAngle) - local_y * math.sin(BaseAngle)
    global_y = base_y + local_x * math.sin(BaseAngle) + local_y * math.cos(BaseAngle)
    global_z = base_z + local_z

    return [round(global_x, 4), round(global_y, 4), round(global_z, 4)]

DefaulteUnite = ["m","N","Pa","m2","m3","m4","m5","m6","m7","m8","m9"]

def To_SI(Unit : str = "MPa", value : float = 1.0) -> float:
    """
    Convert a unit prefix to its corresponding exponent value.
    """
    for i in DefaulteUnite:
        if i in Unit:
            Exposant = Unit.removesuffix(i)
            break

    if Exposant == "M":
        expo = 10**6
    elif Exposant == "k":
        expo = 10**3
    elif Exposant == "h":
        expo = 10**2
    elif Exposant == "da":
        expo = 10**1
    elif Exposant == "d":
        expo = 10**-1
    elif Exposant == "c":
        expo = 10**-2
    elif Exposant == "m":
        expo = 10**-3
    elif Exposant == "u":
        expo = 10**-6
    elif Exposant == "n":
        expo = 10**-9
    elif Exposant == "p":
        expo = 10**-12
    elif Exposant == "f":
        expo = 10**-15
    elif Exposant == "a":
        expo = 10**-18
    else:
        expo = 1  # Default to 1 if the prefix is not recognized
    
    return value * expo
    