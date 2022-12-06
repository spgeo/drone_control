#!/usr/env  python3

import logging
import time
from djitellopy import Tello
import pygame

#logger = logging.Logger(__name__)
class Logger():

    def info(self, msg):
        print(f"[INFO] {msg}")

    def error(self, msg):
        print(f"[ERROR] {msg}")


logger = Logger()

logger.info("Connecting the controller...")
pygame.init()
clock = pygame.time.Clock()

joystick = {}

done = False
while not done:
    for event in pygame.event.get():
        logger.info(event.type)

exit()

t = Tello()

t.connect()
logger.info("Drone successfully connected")
logger.info(f"Battery remaining: {t.get_battery()}%")
logger.info(f"Average temperature: {t.get_temperature()} Celcius")

logger.info("Trying liftoff...")
try:
    t.takeoff()
except Exception as err:
    logger.error(f"Takeoff failed: {err}")
logger.info("Drone is flying")

time.sleep(5)
logger.info("Landing...")
t.land()
