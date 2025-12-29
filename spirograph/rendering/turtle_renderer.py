from .settings import RenderSettings
from .types import CurveRenderer, RenderPlan


class TurtleGraphicsRenderer(CurveRenderer):
    def render(self, plan: RenderPlan, settings: RenderSettings) -> None:
        import turtle

        screen = turtle.Screen()
        screen.colormode(255)
        pen = turtle.Turtle()
        pen.speed(settings.speed)

        for path in plan.paths:
            if not path.points:
                continue
            pen.penup()
            start = path.points[0]
            pen.goto(start.x, start.y)
            pen.pendown()
            pen.color(path.color.as_rgb)
            pen.width(path.width)
            for point in path.points[1:]:
                pen.goto(point.x, point.y)

        screen.exitonclick()
