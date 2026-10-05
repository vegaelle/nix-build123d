from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Annotated

import typer
from build123d import (
    Axis,
    Bezier,
    BuildLine,
    BuildPart,
    BuildSketch,
    CounterSinkHole,
    Cylinder,
    Line,
    Locations,
    Mode,
    Part,
    Plane,
    PolarLocations,
    Sphere,
    VectorLike,
    export_stl,
    extrude,
    import_svg,
    make_face,
    revolve,
)


@dataclass
class ButtonParams:
    button_diameter: float
    button_height: float
    button_hole_count: int
    button_hole_diameter: float
    button_hole_dist: float
    button_hole_fillet: float
    lift_height: float
    inner_sink_diameter: float
    inner_sink_depth: float
    shape_file: str | None = None

    def get_curve_for_button_section(self) -> tuple[list[VectorLike], list[float]]:
        pts = [
            (0, self.button_height / 2),  # center point
            (
                self.button_diameter / 2,
                self.button_height / 2,
            ),  # control point for center
            (
                self.button_diameter / 2,
                self.button_height / 6,
            ),  # control point for edge
            (self.button_diameter / 2, 0),  # edge point
        ]
        weights = [1, 1, 1, 1]
        weights += weights[:-1][::-1]
        pts += [(x, -y) for (x, y) in pts[:-1][::-1]]  # mirroring points
        return pts, weights


PRESETS: dict[str, ButtonParams] = {
    "sink": ButtonParams(
        button_diameter=15,
        button_height=3,
        button_hole_count=4,
        button_hole_diameter=1.8,
        button_hole_dist=2.5,
        button_hole_fillet=1.2,
        lift_height=3,
        inner_sink_diameter=35,
        inner_sink_depth=1.5,
    ),
    "sink_small": ButtonParams(
        button_diameter=11,
        button_height=2.5,
        button_hole_count=4,
        button_hole_diameter=1.6,
        button_hole_dist=2.3,
        button_hole_fillet=1.2,
        lift_height=2.5,
        inner_sink_diameter=30,
        inner_sink_depth=1.5,
    ),
    "sink_shape": ButtonParams(
        button_diameter=22.5,
        button_height=3,
        button_hole_count=4,
        button_hole_diameter=1.8,
        button_hole_dist=2.5,
        button_hole_fillet=1.2,
        lift_height=3,
        inner_sink_diameter=35,
        inner_sink_depth=1.5,
        shape_file="shape.svg",
    ),
}


class RenderMode(StrEnum):
    show = auto()
    write = auto()
    noop = auto()


class ButtonPreset(StrEnum):
    sink = auto()
    sink_small = auto()
    sink_shape = auto()


def build_part(params: ButtonParams) -> Part:
    with BuildPart() as button:
        with BuildSketch(Plane.XZ), Locations((0, params.lift_height)):
            with BuildLine():
                l1 = Bezier(params.get_curve_for_button_section()[0])
                Line(l1 @ 1, l1 @ 0)
            make_face()
        revolve(axis=Axis.Z)
        with Locations((0, 0, -params.button_height / 2)):
            # lift
            Cylinder(
                radius=params.button_hole_dist + params.button_hole_diameter / 4,
                height=params.lift_height,
            )
            # inner sink
            with Locations(
                (
                    0,
                    0,
                    params.button_height
                    + params.inner_sink_diameter / 2
                    - params.inner_sink_depth,
                )
            ):
                Sphere(radius=params.inner_sink_diameter / 2, mode=Mode.SUBTRACT)

        # holes
        with (
            PolarLocations(
                radius=params.button_hole_dist, count=params.button_hole_count
            ),
            Locations((0, 0, params.button_height / 2)),
        ):
            CounterSinkHole(
                radius=params.button_hole_diameter / 2,
                counter_sink_radius=2 * params.button_hole_fillet,
            )
    button = button.part

    if params.shape_file:
        with BuildPart() as shape, Locations((0, 0)):
            shape_face = import_svg(params.shape_file, align=None)[0]
            shape_face = shape_face.translate(-shape_face.center())
            with Locations((0, 0, -params.button_height)):
                extrude(shape_face, params.button_height / 2)
                extrude(shape_face, -params.button_height / 2)

            with Locations((0, 0, -params.button_height / 2)):
                # lift
                Cylinder(
                    radius=params.button_hole_dist + params.button_hole_diameter / 4,
                    height=params.lift_height,
                )
        button = button & shape.part

    return button


def main(
    preset: Annotated[ButtonPreset, typer.Argument()] = ButtonPreset.sink,
    mode: RenderMode = RenderMode.show,
    filename: str = "button.stl",
):
    params = PRESETS[preset]
    button = build_part(params)

    match mode:
        case RenderMode.show:
            from yacv_server import show

            show(button)
        case RenderMode.write:
            export_stl(button, filename)
            print(f'Model rendered in "{filename}"')
        case RenderMode.noop:
            print(f"mode = {mode}")


if __name__ == "__main__":
    typer.run(main)
