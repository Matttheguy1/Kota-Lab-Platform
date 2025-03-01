import gpiozero as gpi
from time import sleep
#import keyboard

x_servo = gpi.Servo(17)
y_servo = gpi.Servo(18)


# Sets servo to minimum position
def initial_pos():
    x_servo.mid()
    y_servo.mid()


# pos can take any value from -90 to 90
pos = -1


# Increases the servo position by 1 degree
def increment_pos():
    global pos
    pos += 0.1


# Decreases the servo position by 1 degree
def decrease_pos():
    global pos
    pos -= 0.1


if __name__ == "__main__":
    x_servo.min()

#keyboard.on_press_key('w', increment_pos())
#keyboard.on_press_key('s', decrease_pos())
#keyboard.wait('esc')






