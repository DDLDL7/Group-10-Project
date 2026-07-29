import turtle
import random

class Racer:
    def __init__(self, name, color, y_position):
        self.name = name
        self.speed = random.randint(1, 10)
        self.turtle_object = turtle.Turtle()
        self.turtle_object.color(color)
        self.turtle_object.shape("turtle")
        self.turtle_object.penup()
        self.turtle_object.goto(-300, y_position)
        self.turtle_object.pendown()

    def move(self):
        self.turtle_object.forward(self.speed)

    def has_finished(self):
        return self.turtle_object.xcor() >= 300


# Set up the screen
screen = turtle.Screen()
screen.setup(width=700, height=400)
screen.title("Turtle Race")

# Create racers
racers = [
    Racer("Red", "red", 100),
    Racer("Blue", "blue", 50),
    Racer("Green", "green", 0),
    Racer("Orange", "orange", -50)
]

# Race loop
race_on = True
while race_on:
    for racer in racers:
        racer.move()
        if racer.has_finished():
            print(f"{racer.name} wins!")
            race_on = False
            break

screen.mainloop()


