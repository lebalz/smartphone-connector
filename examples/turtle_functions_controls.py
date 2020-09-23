import turtle
import random
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector
from smartphone_connector.api_types import KeyMsg

phone = Connector("https://io.lebalz.ch", "FooBar")

turtle.home()


def on_f1():
    for _ in range(4):
        turtle.forward(100)
        turtle.left(90)


def on_f2():
    for _ in range(9):
        turtle.forward(30)
        turtle.left(360 / 9)


def on_f3():
    for _ in range(5):
        turtle.forward(100)
        turtle.left(144)


def on_f4():
    turtle.penup()
    turtle.goto(random.randint(-250, 250), random.randint(-250, 250))
    turtle.pendown()


def on_key(key: KeyMsg):
    if key.key == 'up':
        turtle.setheading(90)
        turtle.forward(10)
    if key.key == 'right':
        turtle.setheading(0)
        turtle.forward(10)
    if key.key == 'left':
        turtle.setheading(180)
        turtle.forward(10)
    if key.key == 'down':
        turtle.setheading(-90)
        turtle.forward(10)
    if key.key == 'home':
        if turtle.isdown():
            turtle.penup()
        else:
            turtle.pendown()


phone.on_f1 = on_f1
phone.on_f2 = on_f2
phone.on_f3 = on_f3
phone.on_f4 = on_f4
phone.on_key = on_key

turtle.Screen().mainloop()
