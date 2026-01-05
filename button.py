from build123d import (
    Axis,
    Bezier,
    BuildLine,
    BuildPart,
    BuildSketch,
    Line,
    Plane,
    VectorLike,
    make_face,
    revolve,
)
from yacv_server import show

button_diameter = 15
button_height = 3
button_hole_count = 4
button_hole_diameter = 1.8
button_hole_dist = 1.4


def get_curve_for_button_section() -> tuple[list[VectorLike], list[float]]:
    pts = [
        (0, button_height/2),  # center point
        (button_diameter/2, button_height/2),  # control point for center
        (button_diameter/2, button_height/2),  # control point for edge
        (button_diameter/2, 0),  # edge point
    ]
    weights = [0, 1, 1, 0]
    weights += weights[:-1][::-1]
    pts += [(x, -y) for (x, y) in pts[:-1][::-1]]  # mirroring points
    return pts, weights


def main():
    with BuildPart() as button:
        with BuildSketch(Plane.XZ) as section_sk:
            with BuildLine() as section_ln:
                l1 = Bezier(*get_curve_for_button_section())
                l2 = Line(l1 @ 1, l1 @ 0)
            make_face()
        revolve(axis=Axis.Z)
    show(section_sk, button)


if __name__ == '__main__':
    main()
