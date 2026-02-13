import pigpio, time, math

pi = pigpio.pi()
if not pi.connected: exit("pigpiod not running")

SERVO_PINX = 18
SERVO_PINY = 17

CENTER_X = 1500
CENTER_Y = 1500


AMPLITUDE_X = 260  # ±22.5 degrees
AMPLITUDE_Y = 260  # ±22.5 degrees

FREQUENCY = 0.5  # One cycle every 2 seconds

DURATION = 10

UPDATE_RATE = 50
dt = 1.0 / UPDATE_RATE

pi.set_servo_pulsewidth(SERVO_PINX, CENTER_X)
pi.set_servo_pulsewidth(SERVO_PINY, CENTER_Y)
time.sleep(1)

# Execute harmonic trajectory
start_time = time.time()
elapsed = 0

while elapsed < DURATION:
    elapsed = time.time() - start_time
    

    angle = 2 * math.pi * FREQUENCY * elapsed
    
    # X follows sine wave
    pos_x = CENTER_X + AMPLITUDE_X * math.sin(angle)
    
    # Y follows cosine wave (90 degrees out of phase for circular motion)
    pos_y = CENTER_Y + AMPLITUDE_Y * math.cos(angle)
    
    # Set servo positions
    pi.set_servo_pulsewidth(SERVO_PINX, int(pos_x))
    pi.set_servo_pulsewidth(SERVO_PINY, int(pos_y))
    
    time.sleep(dt)

# Return to center
pi.set_servo_pulsewidth(SERVO_PINX, CENTER_X)
pi.set_servo_pulsewidth(SERVO_PINY, CENTER_Y)
time.sleep(0.5)

# Stop servos
pi.set_servo_pulsewidth(SERVO_PINX, 0)
pi.set_servo_pulsewidth(SERVO_PINY, 0)
pi.stop()
