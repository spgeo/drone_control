#!/usr/env  python3

import logging
import time
from djitellopy import Tello
import pygame

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logging.info("Connecting the controller...")
pygame.init()
#clock = pygame.time.Clock()

BTN_TRIANGLE = 2
MOVE_STEP = 40

c = pygame.joystick.Joystick(0)
c.init()
logging.info("Controller connected")

t = Tello()

t.connect()
logging.info("Drone connected")
logging.info(f"Battery remaining: {t.get_battery()}%")
logging.info(f"Average temperature: {t.get_temperature()} Celcius")

is_drone_flying = False

done = False
prev_event_name = None
move_directions = ()
while not done:
    for event in pygame.event.get():
        event_name = pygame.event.event_name(event.type)
        if event_name != prev_event_name:
            prev_event_name = event_name
            logging.debug(event_name)

        if event.type == pygame.JOYHATMOTION:
            logging.info(f"Motion intent detected: {event}")
            move_directions = event.value
            x_axis = move_directions[0]
            y_axis = move_directions[1]
            logging.info(f"Moving {move_directions}")
            if x_axis > 0:
                t.move_right(MOVE_STEP)
            elif x_axis < 0:
                t.move_left(MOVE_STEP)
            if y_axis > 0:
                t.move_forward(MOVE_STEP)
            elif y_axis < 0:
                t.move_back(MOVE_STEP)

        if event.type == pygame.JOYBUTTONUP:
            logging.info(f"Key pressed: {event}")
            if event.button == BTN_TRIANGLE:
                if not is_drone_flying:
                    logging.info("Trying liftoff...")
                    try:
                        c.rumble(0, 1, 0)
                        t.takeoff()
                        logging.info("Drone is flying")
                        is_drone_flying = True
                    except Exception as err:
                        logging.error(f"Takeoff failed: {err}")
                    c.stop_rumble()
                else:
                    logging.info("Landing...")
                    try:
                        c.rumble(0, 1, 0)
                        t.land()
                        logging.info("Drone has landed")
                        is_drone_flying = False
                    except Exception as err:
                        logging.error(f"Landing failed: {err}")
                    c.stop_rumble()



