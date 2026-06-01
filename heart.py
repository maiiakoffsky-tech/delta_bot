import turtle

t = turtle.Turtle()
t.speed(3)
t.color("pink")
t.begin_fill()

t.left(140)
t.forward(224)
for _ in range(200):
    t.right(1)
    t.forward(2)
t.left(120)
for _ in range(200):
    t.right(1)
    t.forward(2)
t.forward(224)

t.end_fill()
turtle.done()