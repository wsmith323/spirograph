from .data_types import CurveRenderer, RenderPlan, RenderSettings


class TurtleGraphicsRenderer(CurveRenderer):
    def __init__(self) -> None:
        import turtle

        self._screen = turtle.Screen()
        self._screen.setup(width=1000, height=1000)
        self._screen.colormode(255)
        self._screen.tracer(0, 0)
        self._pen = turtle.Turtle()
        self._pen.hideturtle()
        self._pen.speed(0)

    def render(self, plan: RenderPlan, settings: RenderSettings) -> None:
        self._pen.clear()

        batch = 2 ** max(0, settings.speed - 1)
        if batch < 1:
            batch = 1

        for path in plan.paths:
            if not path.points:
                continue
            self._pen.penup()
            start = path.points[0]
            self._pen.goto(start.x, start.y)
            self._pen.pendown()
            self._pen.color(path.color.as_rgb)
            self._pen.width(path.width)
            index = 1
            for point in path.points[1:]:
                self._pen.goto(point.x, point.y)
                if index % batch == 0:
                    self._screen.update()
                index += 1
            self._screen.update()
        self._screen.update()
