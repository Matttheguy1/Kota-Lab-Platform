#!/usr/bin/env python3
import pigpio
import time


MIN_PULSE = 500
MAX_PULSE = 2500

def set_angle(pi, angle, SERVO_PIN = 17):
    pulse = int(MIN_PULSE + (angle / 180.0) * (MAX_PULSE - MIN_PULSE))
    pi.set_servo_pulsewidth(SERVO_PIN, pulse)

pi = pigpio.pi()
#set_angle(pi, 80)
#time.sleep(1)

#time.sleep(5)
#set_angle(pi, 70)
set_angle(pi, 90, 18)
set_angle(pi,90)
time.sleep(1)
pi.set_servo_pulsewidth(17, 0)
pi.stop()
