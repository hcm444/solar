import pvlib
from datetime import datetime
import math
import pandas as pd

def calculate_irradiance(latitude, longitude, altitude):
    try:

        location = pvlib.location.Location(latitude, longitude)

        times = pd.date_range(start=datetime.utcnow(), periods=1, freq='H', tz=location.tz)

        clearsky = location.get_clearsky(times, model='ineichen')

        ghi = clearsky['ghi'].values[0]
        dni = clearsky['dni'].values[0]
        dhi = clearsky['dhi'].values[0]

        poa_irradiance = dni * math.cos(math.radians(altitude)) + dhi

        return {
            "DNI": dni,
            "DHI": dhi,
            "GHI": ghi,
            "POA": poa_irradiance,
        }
    except Exception as e:
        return {"error": str(e)}

