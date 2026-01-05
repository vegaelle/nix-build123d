from enum import StrEnum, auto
from typing import Annotated

import typer
from build123d import (
    Axis,
    Bezier,
    BuildLine,
    BuildPart,
    BuildSketch,
    Cylinder,
    CounterSinkHole,
    Line,
    Locations,
    Mode,
    Part,
    Plane,
    PolarLocations,
    Sphere,
    VectorLike,
    export_stl,
    make_face,
    revolve,
)

button_diameter = 18
button_height = 3
button_hole_count = 4
button_hole_diameter = 1.8
button_hole_dist = 2.5
button_hole_fillet = 1.2
lift_height = 2.5
inner_sink_diameter = 40
inner_sink_depth = 1.5


class RenderMode(StrEnum):
    show = auto()
    write = auto()
    noop = auto()


def get_curve_for_button_section() -> tuple[list[VectorLike], list[float]]:
    pts = [
        (0, button_height/2),  # center point
        (button_diameter/2, button_height/2),  # control point for center
        (button_diameter/2, button_height/6),  # control point for edge
        (button_diameter/2, 0),  # edge point
    ]
    weights = [1, 1, 1, 1]
    weights += weights[:-1][::-1]
    pts += [(x, -y) for (x, y) in pts[:-1][::-1]]  # mirroring points
    return pts, weights


def build_part() -> Part:
    with BuildPart() as button:
        with BuildSketch(Plane.XZ):
            with Locations((0, lift_height)):
                with BuildLine():
                    l1 = Bezier(get_curve_for_button_section()[0])
                    Line(l1 @ 1, l1 @ 0)
                make_face()
        revolve(axis=Axis.Z)
        with Locations((0, 0, -button_height/2)):
            Cylinder(radius=button_hole_dist,
                     height=lift_height)
            # inner sink
            with Locations((0, 0,
                            button_height
                            + inner_sink_diameter/2
                            - inner_sink_depth)):
                Sphere(radius=inner_sink_diameter/2, mode=Mode.SUBTRACT)
        # holes
        with PolarLocations(radius=button_hole_dist, count=button_hole_count):
            with Locations((0, 0, button_height/2)):
                CounterSinkHole(radius=button_hole_diameter/2,
                                counter_sink_radius=2 * button_hole_fillet)
    return button


def main(mode: Annotated[RenderMode, typer.Argument()] = RenderMode.show,
         filename: str = 'button.stl'):
    button = build_part()

    match mode:
        case RenderMode.show:
            from yacv_server import show
            show(button)
        case RenderMode.write:
            export_stl(button.part, filename)
            print(f'Model rendered in "{filename}"')
        case RenderMode.noop:
            print(f'mode = {mode}')


if __name__ == '__main__':
    typer.run(main)
