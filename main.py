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

t = None
use_drone = True

if use_drone:
    t = Tello()
    if t.connect():
        logging.info("Drone connected")
        logging.info(f"Battery remaining: {t.get_battery()}%")
        logging.info(f"Average temperature: {t.get_temperature()} Celcius")

is_drone_flying = False

flip_dict = {
    "x": {
        1: "r",
        -1: "l"
    },
    "y": {
        1: "f",
        -1: "b"
    }
}

done = False
prev_event_name = None
move_directions = ()
while not done:
    for event in pygame.event.get():
        event_name = pygame.event.event_name(event.type)
        if event_name != prev_event_name:
            prev_event_name = event_name
            logging.debug(event_name)

        if event.type == pygame.JOYAXISMOTION:
            event.value = int(round(event.value, 2) * 10)
            logging.info(f"Move intent detected: {event}")
            if t is not None and event.value != 0:
                t.go_xyz_speed(
                    event.value if event.axis == 1 else 0,
                    event.value if event.axis == 0 else 0,
                    0,
                    10
                )
                #if event.axis == 0:
                #    t.move("left" if event.value < 0 else "right", 20 + abs(event.value))
                #elif event.axis == 1:
                #    t.move("forward" if event.value < 0 else "back", 20 + abs(event.value))

        if event.type == pygame.JOYHATMOTION:
            logging.info(f"Flip intent detected: {event}")
            flip_directions = event.value
            x_flip = flip_directions[0]
            y_flip = flip_directions[1]
            if t is not None:
                logging.info(f"Flipping {flip_directions}")
                if x_flip in flip_dict["x"]:
                    t.flip(flip_dict["x"][x_flip])
                if y_flip in flip_dict["y"]:
                    t.flip(flip_dict["y"][y_flip])

        if event.type == pygame.JOYBUTTONUP:
            logging.info(f"Key pressed: {event}")
            if event.button == BTN_TRIANGLE and t is not None:
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



