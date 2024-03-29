#!/usr/env  python3

import logging
import time
from djitellopy import Tello
import pygame
import threading
import os
import subprocess

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
Tello.LOGGER.setLevel(logging.WARNING)

DRONE_SPEED = 20
BTN_CIRCLE_INDEX = 1
BTN_TRIANGLE_INDEX = 2
JOYSTICK_INDEX_TO_AXIS = {
    4: "y",     # forward / backward
    3: "x",     # left / right
    1: "z",     # up / down
    0: "w"      # clockwise / counter-clockwise
}
JOYHAT_AXIS_TO_INDEX = {
    "x": 0,
    "y": 1
}

AIRBORNE_STATE = False

MOVE_STATES = {"x": 0, "y": 0, "z": 0, "w": 0}
AIRBORNE_ACTIONS = {"land": False, "takeoff": False, "return": False}
FLIP_ACTIONS = {"x": 0, "y": 0}


class DroneStateThread(threading.Thread):

    def __init__(self, threadID, name, counter, tello):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.t = tello

    def run(self):
        while True:
            time.sleep(3)
            if self.t:
                logging.info(f"{self.t.get_current_state()}")



class DroneActionThread(threading.Thread):
    
    def __init__(self, threadID, name, counter, tello):
        global MOVE_STATES
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.move_states = MOVE_STATES.copy()

        self.t = tello
        try:
            retry_cnt = 5
            while retry_cnt > 0:
                try:
                    subprocess.run(
                        ["nmcli", "d", "wifi", "connect", "TELLO-CFB4A2", "password", "''", "ifname", "wlp0s20f3"],
                        check = True
                    )
                    break
                except subprocess.CalledProcessError as err:
                    logging.warning(f"Error trying to connect to network: {err}. Trying {retry_cnt} more time(s)")
                    time.sleep(5)
                    retry_cnt -= 1

            self.t.connect()
            #self.t.streamoff()
            #self.t.streamon()
        except Exception as err:
            logging.error(f"Drone detection error: {err}")
            self.t = None

    def run(self):
        global MOVE_STATES, AIRBORNE_ACTIONS, AIRBORNE_STATE, FLIP_ACTIONS
        
        while True:
            time.sleep(0.1)
            if self.t:
                if self.move_states != MOVE_STATES:
                    self.move_states = MOVE_STATES.copy()
                    #logging.debug(f"New move states: {self.move_states}")
                    try:
                        self.t.send_rc_control(
                            MOVE_STATES["x"],
                            MOVE_STATES["y"] * (-1),
                            MOVE_STATES["z"],
                            MOVE_STATES["w"]
                        )

                    except Exception as err:
                        logging.error(f"Move state update failed: {err}")
                    logging.info(f"{self.t.get_current_state()}")


            if any(FLIP_ACTIONS.values()):
                logging.debug(f"Flip actions detected: {FLIP_ACTIONS}")
                if self.t:
                    try:
                        if FLIP_ACTIONS["y"]:
                            self.t.flip("f" if FLIP_ACTIONS["y"] == 1 else "b")
                        if FLIP_ACTIONS["x"]:
                            self.t.flip("r" if FLIP_ACTIONS["x"] == 1 else "l")
                    except Exception as err:
                        logging.error(f"Flip failed: {err}")
                FLIP_ACTIONS = dict.fromkeys(FLIP_ACTIONS, 0)

            if any(AIRBORNE_ACTIONS.values()):
                logging.debug(f"Airborne actions detected: {AIRBORNE_ACTIONS}")
                if self.t:
                    try:
                        if AIRBORNE_ACTIONS["land"]:
                            self.t.land()
                            AIRBORNE_STATE = False
                            logging.info("Drone has landed")
                        elif AIRBORNE_ACTIONS["takeoff"]:
                            self.t.takeoff()
                            AIRBORNE_STATE = True
                            logging.info("Drone has taken off")
                        elif AIRBORNE_ACTIONS["return"]:
                            logging.info("Drone is returning")
                            acc = 30
                            closer_distance = 90
                            distance_diff_thres = 5
                            count_time = 2

                            # try the x-axis
                            last_measured_distance = self.t.get_distance_tof()
                            self.t.send_rc_control(acc, 0, 0, 0)
                            # change direction if moving away
                            time.sleep(count_time)
                            while self.t.get_distance_tof() > last_measured_distance:
                                acc = acc * (-1)
                                self.t.send_rc_control(acc, 0, 0, 0)
                                time.sleep(count_time)
                                last_measured_distance = self.t.get_distance_tof()
                            logging.info("x-axis direction established.")
                            time.sleep(count_time)
                            # minimize distance while there's a significant change
                            distance_diff = abs(self.t.get_distance_tof() - last_measured_distance)
                            while self.t.get_distance_tof() > closer_distance and distance_diff > distance_diff_thres:                                    
                                time.sleep(count_time)
                                distance_diff = abs(self.t.get_distance_tof() - last_measured_distance)
                                last_measured_distance = self.t.get_distance_tof()
                            self.t.send_rc_control(0, 0, 0, 0)
                            logging.info("Drone got as close as it could on the x-axis.")

                            # try the y-axis
                            last_measured_distance = self.t.get_distance_tof()
                            self.t.send_rc_control(0, acc, 0, 0)
                            # change direction if moving away
                            while self.t.get_distance_tof() > last_measured_distance:
                                acc = acc * (-1)
                                self.t.send_rc_control(0, acc, 0, 0)
                                time.sleep(count_time)
                                last_measured_distance = self.t.get_distance_tof()
                            logging.info("y-axis direction established.")
                            # minimize distance while there's a significant change
                            distance_diff = abs(self.t.get_distance_tof() - last_measured_distance)
                            while self.t.get_distance_tof() > closer_distance and distance_diff > distance_diff_thres:                                    
                                time.sleep(count_time)
                                distance_diff = abs(self.t.get_distance_tof() - last_measured_distance)
                                last_measured_distance = self.t.get_distance_tof()
                            self.t.send_rc_control(0, 0, 0, 0)
                            logging.info("Drone got as close as it could on the y-axis. Rest is manual :)")


                    except Exception as err:
                        logging.error(f"Airborne state change failed: {err}")
                AIRBORNE_ACTIONS = dict.fromkeys(AIRBORNE_ACTIONS, False)


if __name__ == '__main__':

    pygame.init()
    clock = pygame.time.Clock()

    pygame.display.set_caption("Tello video stream")
    screen = pygame.display.set_mode([960, 720])

    FPS = 120 # frames per second
    pygame.time.set_timer(pygame.USEREVENT + 1, 1000 // FPS)

    c = None
    retry_cnt = 5
    while retry_cnt > 0:
        if pygame.joystick.get_count() == 0:
            logging.warning(f"No controllers detected. Retrying in 5 seconds {retry_cnt} more time(s)...")
            time.sleep(5)
            retry_cnt -= 1
            continue
        else:
            logging.info(f"{pygame.joystick.get_count()} controller(s) detected. Connecting the first...")
            try:
                c = pygame.joystick.Joystick(0)
                c.init()
                logging.info("Controller connected")
                break
            except pygame.error as err:
                logging.error(f"Controller detection error: {err}")
                exit()
    if c is None:
        logging.error(f"No controller found. Exiting...")
        exit()

    t = Tello()
    is_drone_flying = False
    if t:
        logging.info("Connecting the drone...")
        droneActionThread = DroneActionThread(1, "DroneActionThread", 1, t)
        droneActionThread.start()
        #droneStateThread = DroneStateThread(2, "DroneStateThread", 2, t)
        #droneStateThread.start()

    logging.info("Listening for controller events...")
    done = False
    prev_event_name = None
    move_directions = ()
    while not done:
        for event in pygame.event.get():
            event_name = pygame.event.event_name(event.type)
            if event_name != prev_event_name:
                prev_event_name = event_name
                #logging.debug(event_name)

            if event.type == pygame.JOYAXISMOTION:
                event.value = int(round(event.value, 2) * 10)
                # Calculate direction and volume from event.axis and event.value
                if event.axis in JOYSTICK_INDEX_TO_AXIS:
                    #logging.debug(f"Move intent detected: {event}")
                    MOVE_STATES[JOYSTICK_INDEX_TO_AXIS[event.axis]] = event.value * 10

            if event.type == pygame.JOYHATMOTION:
                logging.info(f"Flip intent detected: {event}")
                FLIP_ACTIONS = {
                    "x": event.value[JOYHAT_AXIS_TO_INDEX["x"]],
                    "y": event.value[JOYHAT_AXIS_TO_INDEX["y"]]
                }

            if event.type == pygame.JOYBUTTONUP:
                logging.info(f"Key pressed: {event}")
                if event.button == BTN_CIRCLE_INDEX:
                    AIRBORNE_ACTIONS["return"] = True
                elif event.button == BTN_TRIANGLE_INDEX:
                    if not AIRBORNE_STATE:
                        logging.info("Trying liftoff...")
                        AIRBORNE_ACTIONS["takeoff"] = True
                        c.rumble(0, 1, 0)
                        while AIRBORNE_ACTIONS["takeoff"]:
                            time.sleep(0.25)
                        c.stop_rumble()
                    else:
                        logging.info("Landing...")
                        AIRBORNE_ACTIONS["land"] = True
                        c.rumble(0, 1, 0)
                        while AIRBORNE_ACTIONS["land"]:  
                            time.sleep(0.25)
                        c.stop_rumble()
        time.sleep(0.1)

    droneActionThread.join()