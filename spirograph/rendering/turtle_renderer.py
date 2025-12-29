from .settings import RenderSettings
from .types import CurveRenderer, RenderPlan


class TurtleGraphicsRenderer(CurveRenderer):
    def render(self, plan: RenderPlan, settings: RenderSettings) -> None:
        import turtle

        screen = turtle.Screen()
        screen.clearscreen()
        screen.colormode(255)
        screen.tracer(0, 0)
        pen = turtle.Turtle()
        pen.hideturtle()
        pen.speed(0)
        pen.clear()

        batch = 2 ** max(0, settings.speed - 1)
        if batch < 1:
            batch = 1

        for path in plan.paths:
            if not path.points:
                continue
            pen.penup()
            start = path.points[0]
            pen.goto(start.x, start.y)
            pen.pendown()
            pen.color(path.color.as_rgb)
            pen.width(path.width)
            index = 1
            for point in path.points[1:]:
                pen.goto(point.x, point.y)
                if index % batch == 0:
                    screen.update()
                index += 1
            screen.update()
        screen.update()
