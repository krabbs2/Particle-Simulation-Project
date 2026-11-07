#!/usr/bin/env python3
import pyglet
import random
import math
from pyglet.window import key, mouse

# all constant variables

n = 300 # number of particles
dt = 0.02 # delta t, time step basically speed of simulationm
frictionHalfLife = 0.040 # in seconds
rMax = 0.1 # max radius
m = 6 # number of colors
forceFactor = 10   # overall strength of the forces tune to taste
beta = 0.3
particleRadius = 2

sidebar_width = 370
window_width = 1800
window_height = 1000


def make_random_matrix(m):
    rows = []
    for i in range(m):
        row = []
        for j in range(m):
            row.append(random.uniform(0, 1) * 2 - 1) # random between -1 and 1
        rows.append(row)
    return rows

matrix = make_random_matrix(m) # nxn attraction matrix

# using friction to prevent chaos and weird particles zapping around
frictionFactor = 0.5 ** (dt / frictionHalfLife) # velocity halves every frictionHalfLife regardless of frame rate

#######################################################

# SHOULD CHANGE: change to adapt to number of colors
COLORS = [
    (255, 0, 0), # r
    (255, 255, 0), # y
    (0, 255, 0), # g
    (0, 255, 255), # c
    (0, 0, 255),  # b
    (255, 0, 255) # m
]

window = pyglet.window.Window(width=window_width, height=window_height, caption="Particle Sim")

# using batch to optimize the use of opengl instead of repeating each drawing
batch = pyglet.graphics.Batch()
ui_batch = pyglet.graphics.Batch()

dots = []
colors = []
positions_x = []
positions_y = []
velocities_x = []
velocities_y = []


'''
force function:
combines the distance + attraction factor
calculates how hard a particle should be pulled or repelled
'''

def force_vec(r, a):
    if r < beta:
        return r / beta - 1
    else:
        if r < 1:
            return a * (1 - abs(2 * r - 1 - beta) / (1 - beta))
        else:
            return 0


def rebuild_dots():
    global dots
    for dot in dots:
        dot.delete()
    dots = []
    sim_width = window.width - sidebar_width
    for i in range(n):
        dot = pyglet.shapes.Circle(
            float(sidebar_width + positions_x[i] * sim_width),
            float(positions_y[i] * window.height),
            particleRadius,
            color=COLORS[colors[i]],
            batch=batch
        )
        dots.append(dot)


def initialize_particles():
    global colors, positions_x, positions_y, velocities_x, velocities_y
    # give random color for n number of particles
    colors = []
    for i in range(n):
        colors.append(random.randrange(m))    # 0 to m-1

    # random positions in between 0 and 1
    positions_x = [random.uniform(0, 1) for _ in range(n)]
    positions_y = [random.uniform(0, 1) for _ in range(n)]

    velocities_x = [0.] * n
    velocities_y = [0.] * n
    rebuild_dots()


def update_velocities():
    total_force_x = []
    total_force_y = []
    r_max_squared = rMax * rMax

    for i in range(n):
        sum_x = 0.0
        sum_y = 0.0
        xi = positions_x[i]
        yi = positions_y[i]
        matrix_row = matrix[colors[i]]

        for j in range(n):
            dx = positions_x[j] - xi
            dy = positions_y[j] - yi

            if dx > 0.5:
                dx -= 1
            elif dx < -0.5:
                dx += 1

            if dy > 0.5:
                dy -= 1
            elif dy < -0.5:
                dy += 1

            dist_squared = dx * dx + dy * dy
            if 0 < dist_squared < r_max_squared:
                dist = dist_squared ** 0.5
                f = force_vec(dist / rMax, matrix_row[colors[j]])
                sum_x += dx / dist * f
                sum_y += dy / dist * f

        total_force_x.append(sum_x)
        total_force_y.append(sum_y)

    return total_force_x, total_force_y


def update_positions():
    for i in range(n):
        positions_x[i] = (positions_x[i] + velocities_x[i] * dt) % 1
        positions_y[i] = (positions_y[i] + velocities_y[i] * dt) % 1


def apply_forces():
    total_force_x, total_force_y = update_velocities()
    for i in range(n):
        velocities_x[i] *= frictionFactor                # slow down
        velocities_y[i] *= frictionFactor
        velocities_x[i] += total_force_x[i] * rMax * forceFactor * dt   # speed up from forces
        velocities_y[i] += total_force_y[i] * rMax * forceFactor * dt


def format_value(value):
    if isinstance(value, float):
        return format(value, ".6g")
    return str(value)


def current_settings():
    return {
        "n": n,
        "dt": dt,
        "frictionHalfLife": frictionHalfLife,
        "rMax": rMax,
        "m": m,
        "forceFactor": forceFactor,
        "beta": beta,
        "particleRadius": particleRadius,
    }


keys = ["n", "dt", "frictionHalfLife", "rMax", "m", "forceFactor", "beta", "particleRadius"]
labels = {
    "n": "n",
    "dt": "dt",
    "frictionHalfLife": "frictionHalfLife",
    "rMax": "rMax",
    "m": "m",
    "forceFactor": "forceFactor",
    "beta": "beta",
    "particleRadius": "particleRadius",
}
types = {
    "n": int,
    "dt": float,
    "frictionHalfLife": float,
    "rMax": float,
    "m": int,
    "forceFactor": float,
    "beta": float,
    "particleRadius": int,
}

field_texts = {}
dirty_fields = set()
selected_field = None
replace_on_next_text = False

startY = window_height - 115
row_step = 30
matrix_startY = window_height - 450
matrix_row_step = 30
matrixX = 30
matrix_cell_width = 45
matrix_cell_gap = 4

setting_boxes = {}
matrix_boxes = {}
matrix_row_labels = []
matrix_column_labels = []

for i, field in enumerate(keys):
    y = startY - i * row_step
    rect = pyglet.shapes.Rectangle(190, y, 155, 24, color=(45, 45, 45), batch=ui_batch)
    label = pyglet.text.Label(labels[field], x=12, y=y + 5, font_size=11, color=(255, 255, 255, 255))
    value_label = pyglet.text.Label("", x=196, y=y + 5, font_size=11, color=(255, 255, 255, 255))
    setting_boxes[field] = {"rect": rect, "label": label, "value_label": value_label}

matrix_title = pyglet.text.Label("Attraction matrix (-1 to 1)", x=12, y=window_height - 397, font_size=12, color=(255, 255, 255, 255))

for j in range(6):
    x = matrixX + j * (matrix_cell_width + matrix_cell_gap)
    matrix_column_labels.append(
        pyglet.text.Label(str(j + 1), x=x + 15, y=matrix_startY + 27, font_size=10, color=(255, 255, 255, 255))
    )

for i in range(6):
    y = matrix_startY - i * matrix_row_step
    matrix_row_labels.append(
        pyglet.text.Label(str(i + 1), x=12, y=y + 5, font_size=10, color=(255, 255, 255, 255))
    )
    for j in range(6):
        x = matrixX + j * (matrix_cell_width + matrix_cell_gap)
        rect = pyglet.shapes.Rectangle(x, y, matrix_cell_width, 23, color=(45, 45, 45), batch=ui_batch)
        value_label = pyglet.text.Label("", x=x + 2, y=y + 5, font_size=9, color=(255, 255, 255, 255))
        matrix_boxes[(i, j)] = {"rect": rect, "value_label": value_label}

apply_button = pyglet.shapes.Rectangle(12, 162, 112, 30, color=(55, 55, 55), batch=ui_batch)
apply_label = pyglet.text.Label("Apply values", x=21, y=171, font_size=11, color=(255, 255, 255, 255))
status_label = pyglet.text.Label("", x=12, y=133, font_size=10, color=(255, 100, 100, 255), width=sidebar_width - 24, multiline=True)
help_label = pyglet.text.Label("Click a box, type a value then Enter or Apply changes", x=12, y=95, font_size=10, color=(220, 220, 220, 255))


def refresh_input_texts():
    global field_texts
    settings = current_settings()
    field_texts = {}
    for field in keys:
        field_texts[field] = format_value(settings[field])
    for i in range(6):
        for j in range(6):
            key_name = f"matrix_{i}_{j}"
            if i < m and j < m:
                field_texts[key_name] = format(matrix[i][j], ".2f")
            else:
                field_texts[key_name] = ""


def apply_input_values():
    global n, dt, frictionHalfLife, rMax, m, forceFactor, beta, particleRadius
    global frictionFactor, matrix, selected_field, replace_on_next_text, dirty_fields

    if not dirty_fields:
        status_label.text = "No changes to apply."
        return

    settings = current_settings()
    new_settings = settings.copy()

    try:
        for field in keys:
            if field in dirty_fields:
                new_settings[field] = types[field](field_texts[field])

        for field in ("dt", "frictionHalfLife", "rMax", "forceFactor", "beta"):
            if not math.isfinite(new_settings[field]):
                raise ValueError(f"{field} must be a finite number.")
        if new_settings["n"] < 1 or new_settings["n"] > 5000:
            raise ValueError("n must be between 1 and 5000.")
        if new_settings["m"] < 1 or new_settings["m"] > len(COLORS):
            raise ValueError(f"m must be between 1 and {len(COLORS)}.")
        if new_settings["dt"] <= 0:
            raise ValueError("dt must be greater than 0.")
        if new_settings["frictionHalfLife"] <= 0:
            raise ValueError("frictionHalfLife must be greater than 0.")
        if new_settings["rMax"] <= 0:
            raise ValueError("rMax must be greater than 0.")
        if not 0 < new_settings["beta"] < 1:
            raise ValueError("beta must be between 0 and 1.")
        if new_settings["particleRadius"] < 1 or new_settings["particleRadius"] > 20:
            raise ValueError("particleRadius must be between 1 and 20.")

        new_matrix = [row[:] for row in matrix]
        if new_settings["m"] == m:
            for field in dirty_fields:
                if field.startswith("matrix_"):
                    _, row_index, column_index = field.split("_")
                    row_index = int(row_index)
                    column_index = int(column_index)
                    value = float(field_texts[field])
                    if not -1 <= value <= 1:
                        raise ValueError("Matrix values must be between -1 and 1.")
                    new_matrix[row_index][column_index] = value

    except (ValueError, OverflowError) as error:
        status_label.text = f"Error: {error}"
        return

    old_n = n
    old_m = m
    old_radius = particleRadius

    n = new_settings["n"]
    dt = new_settings["dt"]
    frictionHalfLife = new_settings["frictionHalfLife"]
    rMax = new_settings["rMax"]
    m = new_settings["m"]
    forceFactor = new_settings["forceFactor"]
    beta = new_settings["beta"]
    particleRadius = new_settings["particleRadius"]
    frictionFactor = 0.5 ** (dt / frictionHalfLife)

    if m != old_m:
        matrix = make_random_matrix(m)
        initialize_particles()
    elif n != old_n:
        matrix = new_matrix
        initialize_particles()
    else:
        matrix = new_matrix
        if particleRadius != old_radius:
            rebuild_dots()

    dirty_fields.clear()
    selected_field = None
    replace_on_next_text = False
    refresh_input_texts()
    status_label.text = "Applied."


def update_sidebar():
    for field in keys:
        box_info = setting_boxes[field]
        box_info["rect"].color = (90, 90, 90) if selected_field == field else (45, 45, 45)
        box_info["value_label"].text = field_texts.get(field, "")
        box_info["label"].draw()
        box_info["value_label"].draw()

    for i in range(6):
        matrix_row_labels[i].text = str(i + 1) if i < m else ""
        if i < m:
            matrix_row_labels[i].draw()
        for j in range(6):
            box_info = matrix_boxes[(i, j)]
            visible = i < m and j < m
            box_info["rect"].color = (90, 90, 90) if selected_field == f"matrix_{i}_{j}" else ((45, 45, 45) if visible else (0, 0, 0))
            box_info["value_label"].text = field_texts.get(f"matrix_{i}_{j}", "") if visible else ""
            if visible:
                box_info["value_label"].draw()

    for j in range(6):
        matrix_column_labels[j].text = str(j + 1) if j < m else ""
        if j < m:
            matrix_column_labels[j].draw()

    matrix_title.draw()
    apply_label.draw()
    status_label.draw()
    help_label.draw()


@window.event
def on_draw():
    window.clear()
    batch.draw()
    ui_batch.draw()
    update_sidebar()


@window.event
def on_mouse_press(x, y, button, modifiers):
    global selected_field, replace_on_next_text
    if button != mouse.LEFT:
        return

    if apply_button.x <= x <= apply_button.x + apply_button.width and apply_button.y <= y <= apply_button.y + apply_button.height:
        apply_input_values()
        return

    for field, box_info in setting_boxes.items():
        rect = box_info["rect"]
        if rect.x <= x <= rect.x + rect.width and rect.y <= y <= rect.y + rect.height:
            selected_field = field
            replace_on_next_text = True
            status_label.text = ""
            return

    for (i, j), box_info in matrix_boxes.items():
        rect = box_info["rect"]
        if i < m and j < m and rect.x <= x <= rect.x + rect.width and rect.y <= y <= rect.y + rect.height:
            selected_field = f"matrix_{i}_{j}"
            replace_on_next_text = True
            status_label.text = ""
            return

    selected_field = None
    replace_on_next_text = False


@window.event
def on_text(text):
    global replace_on_next_text
    if selected_field is None:
        return
    if not all(character in "0123456789.-+eE" for character in text):
        return
    if replace_on_next_text:
        field_texts[selected_field] = text
        replace_on_next_text = False
    else:
        field_texts[selected_field] += text
    dirty_fields.add(selected_field)
    status_label.text = ""


@window.event
def on_key_press(symbol, modifiers):
    global selected_field, replace_on_next_text
    if symbol in (key.ENTER, key.NUM_ENTER):
        apply_input_values()
        return
    if symbol == key.ESCAPE:
        selected_field = None
        replace_on_next_text = False
        return
    if selected_field is None:
        return
    if symbol == key.BACKSPACE:
        if replace_on_next_text:
            field_texts[selected_field] = ""
        else:
            field_texts[selected_field] = field_texts[selected_field][:-1]
        replace_on_next_text = False
        dirty_fields.add(selected_field)
        status_label.text = ""
    elif symbol == key.A and modifiers & key.MOD_CTRL:
        field_texts[selected_field] = ""
        replace_on_next_text = False
        dirty_fields.add(selected_field)
        status_label.text = ""


def update(_):                       # https://pyglet.readthedocs.io/en/latest/programming_guide/time.html pyglet passes its own dt, just ignore it and use the fixed one
    apply_forces()
    update_positions()
    sim_width = window.width - sidebar_width
    for i in range(n):
        dots[i].x = sidebar_width + positions_x[i] * sim_width
        dots[i].y = positions_y[i] * window.height


initialize_particles()
refresh_input_texts()
pyglet.clock.schedule_interval(update, 1 / 60)
pyglet.app.run()
