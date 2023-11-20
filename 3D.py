import pygame
from OpenGL.raw.GLU import gluPerspective
from OpenGL.GL import *
from geopy.geocoders import Nominatim
import ephem
import math
import paho.mqtt.client as mqtt
from pygame import DOUBLEBUF, OPENGL
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime
import numpy as np
from irradiance_calculator import calculate_irradiance

class SolarPositionVisualizer:
    def __init__(self):
        self.display = (600, 600)
        pygame.init()
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        gluPerspective(45, (self.display[0] / self.display[1]), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -5)
        glRotatef(315, 1, 0, 0)
        glRotatef(180, 1, 1, 0)
        self.mqtt_broker_address = "broker.hivemq.com"
        self.mqtt_port = 1883
        self.mqtt_username = ""
        self.mqtt_password = ""
        self.mqtt_topic = "solar_data" 
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
        self.mqtt_client.connect(self.mqtt_broker_address, self.mqtt_port)
        self.RED = pygame.Color(255, 0, 0)
        self.GREEN = pygame.Color(0, 255, 0)

        self.font = pygame.font.Font(None, 36)

        self.running = True
        self.print_sun_info = True
        self.last_update_time = 0 

    def update_sun_position(self, observer):
        sun = ephem.Sun()
        sun.compute(observer)
        azimuth = float(sun.az)
        altitude = float(sun.alt)

        sun_pos = np.array([
            math.cos(azimuth) * math.cos(altitude),
            math.sin(azimuth) * math.cos(altitude),
            math.sin(altitude)
        ])
        return sun_pos

    def run(self):
        #input
        city_name = input("Enter a city name: ")

        try:
            geolocator = Nominatim(user_agent="city_coordinates")
            location = geolocator.geocode(city_name)

            if location is not None:
                observer = ephem.Observer()
                observer.lat = str(location.latitude)
                observer.long = str(location.longitude)

                self.running = True
                self.print_sun_info = True

                while self.running:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False

                    observer.date = datetime.utcnow()
                    sun = ephem.Sun(observer)
                    
                    altitude_deg = math.degrees(sun.alt)
                    azimuth_deg = math.degrees(sun.az)
                    sun.compute(observer)
                    sun_pos = self.update_sun_position(observer)

                    tf = TimezoneFinder()
                    timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)

                    local_timezone = pytz.timezone(timezone_str)
                    local_time = datetime.now(local_timezone)
                    current_time = local_time.strftime("%Y-%m-%d %H:%M:%S")

                    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                    glColor3f(1.0, 0.0, 0.0)
                    glBegin(GL_LINES)
                    azimuth_line = sun_pos

                    glVertex2f(0, 0)
                    glVertex3fv(azimuth_line)

                    glColor3f(0.0, 1.0, 0.0)
                    glVertex3fv(azimuth_line)
                    glVertex3fv([sun_pos[0], sun_pos[1], -sun_pos[2]])

                    glColor3f(0.0, 0.0, 1.0)
                    glVertex3fv([sun_pos[0], sun_pos[1], -sun_pos[2]])
                    glVertex3f(0.0, 0.0, 0.0)

                    glEnd()

                    glColor3f(0.5, 0.5, 0.5)
                    glBegin(GL_LINES)
                    for x in range(-5, 6):
                        glVertex3f(x, -5, 0)
                        glVertex3f(x, 5, 0)
                        glVertex3f(-5, x, 0)
                        glVertex3f(5, x, 0)
                    glEnd()
                    city_text = f"City: {city_name}"
                    coords_text = f"Lat: {location.latitude:.2f}, Lon: {location.longitude:.2f}"
                    azimuth_text = f"Azimuth: {azimuth_deg:.2f} degrees"
                    altitude_text = f"Altitude: {altitude_deg:.2f} degrees"
                    float1 = location.latitude
                    float2 = location.longitude
                    float4 = altitude_deg
                    irradiance_data = calculate_irradiance(float1,float2,float4)
                    self.mqtt_client.publish(self.mqtt_topic, f"{azimuth_deg:.2f},{altitude_deg:.2f}")
                    print(f"{azimuth_deg:.2f},{altitude_deg:.2f},{current_time}")
                    print("Complete irradiance_data dictionary:")
                    print(irradiance_data)

                    local_time_text = f"Local Time: {current_time}"
                    timezone_text = f"Timezones: {timezone_str}"
                    text_surfaces = [
                        self.font.render(city_text, True, (255, 255, 255)),
                        self.font.render(coords_text, True, (255, 255, 255)),
                        self.font.render(azimuth_text, True, self.RED),
                        self.font.render(altitude_text, True, self.GREEN),
                        self.font.render(local_time_text, True, (255, 255, 255)),
                        self.font.render(timezone_text, True, (255, 255, 255))
                    ]
                    glMatrixMode(GL_PROJECTION)
                    glPushMatrix()
                    glLoadIdentity()
                    glOrtho(0, self.display[0], 0, self.display[1], -1, 1)
                    glMatrixMode(GL_MODELVIEW)
                    glPushMatrix()
                    glLoadIdentity()
                    glEnable(GL_BLEND)
                    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                    y_positions = [10, 50, 90, 130, 170, 210]
                    for i, text_surface in enumerate(text_surfaces):
                        y = y_positions[i]
                        glRasterPos(10, y)
                        glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE,
                                     pygame.image.tostring(text_surface, "RGBA", True))
                    glDisable(GL_BLEND)
                    glMatrixMode(GL_PROJECTION)
                    glPopMatrix()
                    glMatrixMode(GL_MODELVIEW)
                    glPopMatrix()
                    pygame.display.flip()
                    pygame.time.wait(1000)  
                pygame.quit()
            else:
                print(f"Could not find coordinates for {city_name}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    visualizer = SolarPositionVisualizer()
    visualizer.run()
