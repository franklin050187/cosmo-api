"""
Copyright 2023 LunastroD

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

INSTRUCTIONS:
move your ship.png to the ships folder
change the SHIP variable to the name of your ship.png
  the center of mass of your ship will be drawn as a green circle
  the center of thrust will be drawn as a green arrow and yellow arrows for each direction
  if you can't see the window, the image will be saved as out.png
"""

import base64
import json

import cv2
import numpy as np

from vector2d import Vector2D

import cosmoteer_save_tools
import part_data
from png_upload import upload_image_to_imgbb
from price_analysis_ocv import price_analysis
from pricegen import calculate_price
from tagextractor import PNGTagExtractor


def parts_touching(part1, part2):
    """
    Check if two parts are touching each other.

    Args:
        part1 (dict): Dictionary containing information about part 1.
        part2 (dict): Dictionary containing information about part 2.

    Returns:
        bool: True if part1 and part2 are touching, False otherwise.
    """
    part1_size = part_data.parts[part1["ID"]]["size"]
    part2_size = part_data.parts[part2["ID"]]["size"]
    part1_location = part1["Location"]  # upper left corner
    part2_location = part2["Location"]  # upper left corner
    part1_rotation = part1["Rotation"]  # 0, 1, 2, 3
    part2_rotation = part2["Rotation"]  # 0, 1, 2, 3

    if part1_rotation == 1 or part1_rotation == 3:
        part1_size = (part1_size[1], part1_size[0])
    if part2_rotation == 1 or part2_rotation == 3:
        part2_size = (part2_size[1], part2_size[0])

    # generate list of tiles for each part
    part1_tiles = []
    part2_tiles = []
    for i in range(part1_size[0]):
        for j in range(part1_size[1]):
            part1_tiles.append((part1_location[0] + i, part1_location[1] + j))
    for i in range(part2_size[0]):
        for j in range(part2_size[1]):
            part2_tiles.append((part2_location[0] + i, part2_location[1] + j))

    # expand tiles of part 1 to include adjacent tiles (except diagonals)
    for i in range(part1_size[0]):
        for j in range(part1_size[1]):
            part1_tiles.append((part1_location[0] + i + 1, part1_location[1] + j))
            part1_tiles.append((part1_location[0] + i - 1, part1_location[1] + j))
            part1_tiles.append((part1_location[0] + i, part1_location[1] + j + 1))
            part1_tiles.append((part1_location[0] + i, part1_location[1] + j - 1))

    # check if any of the tiles of part 1 are touching part 2
    for tile in part1_tiles:
        if tile in part2_tiles:
            return True
    return False


def thruster_touching_engine_room(parts, thruster):
    """
    Checks if the given thruster is touching the engine room part.

    Args:
        parts (list): List of parts to check.
        thruster (dict): The thruster part to check.

    Returns:
        bool: True if the thruster is touching the engine room, False otherwise.
    """
    for part in parts:
        if part["ID"] == "cosmoteer.engine_room" and parts_touching(thruster, part):
            return True
    return False


def center_of_thrust(parts, args):
    """
    Calculate the center of thrust for a given set of parts.

    Args:
        parts (list): List of parts.
        args (dict): Dictionary of arguments.

    Returns:
        tuple: A tuple containing the origin thrust, thrust vector, and thrust direction.
    """

    # Initialize origin thrust for each direction
    origin_thrust = [Vector2D(0, 0), Vector2D(0, 0), Vector2D(0, 0), Vector2D(0, 0)]

    # Initialize thrust direction for each direction
    thrust_direction = [0, 0, 0, 0]

    # Iterate over each part
    for part in parts:
        # Calculate the center of thrust for the part
        cots = part_center_of_thrust(part, args["boost"])

        # Skip if center of thrust is zero
        if cots == 0:
            continue

        # Iterate over each center of thrust
        for cot in cots:
            origin = cot[0]
            orientation = cot[1]
            thrust = cot[2]

            # Increase thrust if thruster is touching engine room
            if thruster_touching_engine_room(parts, part):
                thrust = thrust * 1.5

            # if part is thruster_rocket_extender then find thruster_rocket_nozzle in the same orientation and x or y and set origin to the origin of nozzle
            if part["ID"] == "cosmoteer.thruster_rocket_extender":
                for part2 in parts:
                    if part2["ID"] == "cosmoteer.thruster_rocket_nozzle":
                        if part2["Rotation"] == part["Rotation"]:
                            if part["Rotation"] == 0 or part["Rotation"] == 2:
                                if part2["Location"][0] == part["Location"][0]:
                                    cots2 = part_center_of_thrust(part2, args["boost"])
                                    for cot2 in cots2:
                                        origin = cot2[0]

                            if part["Rotation"] == 1 or part["Rotation"] == 3:
                                if part2["Location"][1] == part["Location"][1]:
                                    cots2 = part_center_of_thrust(part2, args["boost"])
                                    for cot2 in cots2:
                                        origin = cot2[0]
                            # if (
                            #     part2["Location"][0] == part["Location"][0]
                            #     or part2["Location"][1] == part["Location"]
                            # ):
                            #     cots2 = part_center_of_thrust(part2, args["boost"])
                            #     for cot2 in cots2:
                            #         origin = cot2[0]

            # Update thrust direction and origin thrust for the given orientation
            thrust_direction[orientation] += thrust
            origin_thrust[orientation] += origin * thrust

    # Calculate the average origin thrust for each direction
    for i, direction in enumerate(thrust_direction):
        if direction == 0:
            continue
        origin_thrust[i] = origin_thrust[i] / direction

    # Calculate the end of the thrust vector
    thrust_vector = [
        origin_thrust[0] + Vector2D(0, -thrust_direction[0]),
        origin_thrust[1] + Vector2D(thrust_direction[1], 0),
        origin_thrust[2] + Vector2D(0, thrust_direction[2]),
        origin_thrust[3] + Vector2D(-thrust_direction[3], 0),
    ]

    return origin_thrust, thrust_vector, thrust_direction


def diagonal_center_of_thrust(origin_thrust, thrust_vector, thrust_direction):
    """
    Calculates the center of thrust vectors for the diagonal directions.

    Args:
        origin_thrust (list[Vector2D]): List of origin thrust vectors for each direction (0,1,2,3).
        thrust_vector (list[Vector2D]): List of thrust vectors for each direction (0,1,2,3).
        thrust_direction (list[int]): List of thrust directions for each direction (0,1,2,3).

    Returns:
        tuple[list[Vector2D], list[Vector2D], list[int]]: A tuple containing
        the origin thrust vectors, thrust vectors, and thrust directions for all diagonal
        and non-diagonal directions.
    """

    # 0 is up_left, 1 is up_right, 2 is down_right, 3 is down_left
    diagonal_thrust_vector = [Vector2D(0, 0), Vector2D(0, 0), Vector2D(0, 0), Vector2D(0, 0)]
    diagonal_thrust_direction = [0, 0, 0, 0]
    diagonal_origin_thrust = [Vector2D(0, 0), Vector2D(0, 0), Vector2D(0, 0), Vector2D(0, 0)]

    for i in range(4):
        if thrust_direction[i] != 0 and thrust_direction[(i + 3) % 4] != 0:
            diagonal_thrust_direction[i] = (
                thrust_direction[i] ** 2 + thrust_direction[(i + 3) % 4] ** 2
            ) ** 0.5
            diagonal_origin_thrust[i] = Vector2D.Lerp(
                origin_thrust[i],
                origin_thrust[(i + 3) % 4],
                thrust_direction[(i + 3) % 4]
                / (thrust_direction[(i + 3) % 4] + thrust_direction[i]),
            )

    diagonal_thrust_vector[0] = diagonal_origin_thrust[0] + Vector2D(
        -thrust_direction[3], -thrust_direction[0]
    )
    diagonal_thrust_vector[1] = diagonal_origin_thrust[1] + Vector2D(
        thrust_direction[1], -thrust_direction[0]
    )
    diagonal_thrust_vector[2] = diagonal_origin_thrust[2] + Vector2D(
        thrust_direction[1], thrust_direction[2]
    )
    diagonal_thrust_vector[3] = diagonal_origin_thrust[3] + Vector2D(
        -thrust_direction[3], thrust_direction[2]
    )

    all_thrust_vector = []
    all_thrust_direction = []
    all_origin_thrust = []

    for i in range(4):
        all_thrust_vector.append(diagonal_thrust_vector[i])
        all_thrust_vector.append(thrust_vector[i])
        all_thrust_direction.append(diagonal_thrust_direction[i])
        all_thrust_direction.append(thrust_direction[i])
        all_origin_thrust.append(diagonal_origin_thrust[i])
        all_origin_thrust.append(origin_thrust[i])

    return all_origin_thrust, all_thrust_vector, all_thrust_direction


def top_speed(mass, thrust):
    """
    Calculate the top speed of a vehicle given its mass and thrust.

    Args:
        mass (float): The mass of the vehicle.
        thrust (float): The thrust of the vehicle.

    Returns:
        float: The top speed of the vehicle.
    """

    # Calculate speed below 75m/s
    x = thrust / mass
    speed = 2.5 * x

    # Calculate speed above 75m/s
    if speed > 75:
        # correction = 1
        speed = (14062.5 * x) ** (1 / 3)

    # Apply correction
    speed = 1.01518568052653 * speed - 0.000228187226585198 * speed**2

    return speed


def part_center_of_mass(part):
    """
    Calculate the center of mass for a given part.

    Args:
        part (dict): The part information.

    Returns:
        tuple: The x and y coordinates of the center of mass.
    """
    # Get part size
    part_size = part_data.parts[part["ID"]]["size"]
    part_rotation = part["Rotation"]  # 0, 1, 2, 3

    # Calculate center of mass
    if part_rotation == 0 or part_rotation == 2:
        center_of_mass_x = part["Location"][0] + part_size[0] / 2
        center_of_mass_y = part["Location"][1] + part_size[1] / 2
    elif part_rotation == 1 or part_rotation == 3:
        center_of_mass_x = part["Location"][0] + part_size[1] / 2
        center_of_mass_y = part["Location"][1] + part_size[0] / 2
    else:
        print("ERROR: part_rotation not 0, 1, 2, 3")

    return center_of_mass_x, center_of_mass_y


def part_center_of_thrust(part, boost):
    """
    Calculate the center of thrust for a given part.

    Args:
        part (dict): The part object.
        boost (bool): Whether the part is boosted or not.

    Returns:
        list: A list of tuples representing the multiple centers of thrust for the part.
    """
    # Get part center of thrust (cot) and thrust values
    part_cots = part_data.thruster_data.get(part["ID"], {"cot": 0})["cot"]
    thrust = part_data.thruster_data.get(part["ID"], {"thrust": 0})["thrust"]

    # Adjust thrust if part is not boosted and is a specific type
    if not boost and part["ID"] == "cosmoteer.thruster_boost":
        thrust = thrust / 3

    # Return 0 if part does not have a center of thrust
    if part_cots == 0:
        return 0

    # Calculate the absolute centers of thrust for the part
    part_rotation = part["Rotation"]
    part_size = part_data.parts[part["ID"]]["size"]
    absolute_cots = []

    for part_cot in part_cots:
        # Calculate orientation
        orientation = (part_rotation + part_cot[2]) % 4

        # Calculate center of thrust based on part rotation
        if part_rotation == 0:
            center_of_thrust_x = part["Location"][0] + part_cot[0]
            center_of_thrust_y = part["Location"][1] + part_cot[1]
        elif part_rotation == 1:
            center_of_thrust_x = part["Location"][0] - part_cot[1] + part_size[1]
            center_of_thrust_y = part["Location"][1] + part_cot[0]
        elif part_rotation == 2:
            center_of_thrust_x = part["Location"][0] - part_cot[0] + part_size[0]
            center_of_thrust_y = part["Location"][1] - part_cot[1] + part_size[1]
        elif part_rotation == 3:
            center_of_thrust_x = part["Location"][0] + part_cot[1]
            center_of_thrust_y = part["Location"][1] - part_cot[0] + part_size[0]
        else:
            print("ERROR: part_rotation not 0, 1, 2, 3")

        absolute_cots.append(
            (Vector2D(center_of_thrust_x, center_of_thrust_y), orientation, thrust)
        )

    return absolute_cots


def center_of_mass(parts):
    """
    Calculate the center of mass for a given list of parts.

    Args:
        parts (list): List of parts.

    Returns:
        tuple: Center of mass coordinates (x, y) and total mass.

    """

    total_mass = 0
    sum_x_mass = 0
    sum_y_mass = 0

    for part in parts:
        mass = part_data.parts[part["ID"]]["mass"]
        x_coord, y_coord = part_center_of_mass(part)

        total_mass += mass
        sum_x_mass += mass * x_coord
        sum_y_mass += mass * y_coord

    if total_mass == 0:
        center_of_mass_x = 0
        center_of_mass_y = 0
    else:
        center_of_mass_x = sum_x_mass / total_mass
        center_of_mass_y = sum_y_mass / total_mass

    return center_of_mass_x, center_of_mass_y, total_mass


# def center_of_thrust_vector(parts, ship_direction):
#     """
#     Calculate the center of thrust vector of the ship in a given direction.

#     Args:
#         parts (list): List of ship parts.
#         ship_direction (int): Direction of the ship.

#     Returns:
#         tuple: A tuple containing the start and end coordinates of the center of thrust vector,
#                along with the total thrust direction.
#     """

#     # Define the thrust vectors for each ship direction
#     thrust_vectors = {0: [0, 3], 1: [0], 2: [0, 1], 3: [1], 4: [1, 2], 5: [2], 6: [2, 3], 7: [3]}

#     total_thrust = 0
#     total_thrust_direction = 0

#     sum_x_cot = 0
#     sum_y_cot = 0

#     sum_x_thrust = 0
#     sum_y_thrust = 0

#     for part in parts:
#         cots = part_center_of_thrust(part, False)
#         if cots == 0:
#             continue
#         for cot in cots:
#             thrust = part_data.thruster_data[part["ID"]]["thrust"]
#             if thruster_touching_engine_room(parts, part):
#                 thrust *= 1.5
#             x_coord = cot[0]
#             y_coord = cot[1]

#             total_thrust += thrust
#             if cot[2] in thrust_vectors[ship_direction]:
#                 total_thrust_direction += thrust

#                 sum_x_cot += thrust * x_coord
#                 sum_y_cot += thrust * y_coord
#                 if cot[2] == 0:
#                     sum_y_thrust -= thrust
#                 if cot[2] == 1:
#                     sum_x_thrust += thrust
#                 if cot[2] == 2:
#                     sum_y_thrust += thrust
#                 if cot[2] == 3:
#                     sum_x_thrust -= thrust

#     if total_thrust_direction == 0:
#         return 0

#     startx = sum_x_cot / total_thrust_direction
#     starty = sum_y_cot / total_thrust_direction
#     endx = startx + sum_x_thrust / total_thrust * 15
#     endy = starty + sum_y_thrust / total_thrust * 15

#     return startx, starty, endx, endy, total_thrust_direction / total_thrust


def rotate_image(image, angle, flipx):
    """
    Rotate the given image by the specified angle and flip it horizontally if needed.

    Args:
        image (ndarray): The input image to rotate.
        angle (int): The angle to rotate the image by. Can be 0, 1, 2, or 3.
        flipx (bool): Whether to flip the image horizontally.

    Returns:
        ndarray: The rotated and flipped image.
    """
    if flipx:
        image = np.fliplr(image)

    if angle == 0:
        return image
    elif angle == 1:
        return np.rot90(image, 3)
    elif angle == 2:
        return np.rot90(image, 2)
    elif angle == 3:
        return np.rot90(image, 1)
    else:
        return image


def insert_sprite(background, sprite, x, y, rotation, flipx, size):
    """
    Inserts a sprite onto a background image at the specified position.

    Args:
        background (numpy.ndarray): The background image.
        sprite (numpy.ndarray): The sprite image.
        x (int): The x-coordinate of the top-left corner of the sprite.
        y (int): The y-coordinate of the top-left corner of the sprite.
        rotation (float): The rotation angle of the sprite.
        flipx (bool): Whether to flip the sprite horizontally.
        size (tuple): The desired size of the sprite after resizing.

    Returns:
        numpy.ndarray: The background image with the sprite inserted, or the original
        background image if the sprite doesn't fit.
    """
    sprite = cv2.resize(sprite, size)  # Resize the sprite

    sprite = rotate_image(sprite, rotation, flipx)  # Rotate the sprite
    try:
        y_end, x_end, _ = sprite.shape  # Get the dimensions of the sprite
    except:
        y_end, x_end = sprite.shape  # Get the dimensions of the sprite

    if y + y_end <= background.shape[0] and x + x_end <= background.shape[1]:
        # Check if sprite is 3D (height, width, channels) or 2D (height, width)
        if len(sprite.shape) == 3:  # Sprite has color channels
            sprite_rgb = sprite[:, :, :3]  # Extract RGB channels
            if sprite.shape[2] == 4:  # Check if the sprite has an alpha channel
                alpha_channel = sprite[:, :, 3] / 255.0  # Normalize to range [0, 1]
            else:
                alpha_channel = np.ones(
                    (sprite.shape[0], sprite.shape[1])
                )  # Create full opacity alpha channel
        elif len(sprite.shape) == 2:  # Sprite is 2D (grayscale)
            sprite_rgb = np.stack(
                (sprite,) * 3, axis=-1
            )  # Convert grayscale to RGB by duplicating the channel
            alpha_channel = np.ones(
                (sprite.shape[0], sprite.shape[1])
            )  # Create full opacity alpha channel
        else:
            raise ValueError("Unexpected sprite shape")

        # Extract the corresponding region from the background
        background_region = background[y : y + y_end, x : x + x_end]

        # Blend the sprite with the background using alpha compositing
        for c in range(3):  # Iterate over RGB channels
            background_region[:, :, c] = (1.0 - alpha_channel) * background_region[
                :, :, c
            ] + alpha_channel * sprite_rgb[:, :, c]

    else:
        # Handle cases where the sprite doesn't fit within the region
        print(f"Warning: Sprite at ({x}, {y}) exceeds the background dimensions.")

    return background


def sprite_position(part, position):
    """
    Calculate the offset needed to draw a sprite at a given position.

    Args:
        part (dict): The part object containing information about the sprite.
        position (list): The current position of the sprite.

    Returns:
        list: The updated position of the sprite.
    """
    # Get the sprite size from the part data
    sprite_size = part_data.parts[part["ID"]].get("sprite_size")

    if sprite_size is None:
        return position

    # Get the part size and rotation
    part_size = part_data.parts[part["ID"]]["size"]
    part_rotation = part["Rotation"]

    # Define problematic parts for each rotation
    up_turret_parts = [
        "cosmoteer.laser_blaster_small",
        "cosmoteer.laser_blaster_large",
        "cosmoteer.disruptor",
        "cosmoteer.ion_beam_emitter",
        "cosmoteer.ion_beam_prism",
        "cosmoteer.point_defense",
        "cosmoteer.cannon_med",
        "cosmoteer.cannon_large",
        "cosmoteer.cannon_deck",
        "cosmoteer.missile_launcher",
        "cosmoteer.railgun_launcher",
        "cosmoteer.flak_cannon_large",
        "cosmoteer.shield_gen_small",
        "cosmoteer.chaingun",  # added chaingun
    ]

    down_turret_parts = [
        "cosmoteer.thruster_small",
        "cosmoteer.thruster_med",
        "cosmoteer.thruster_large",
        "cosmoteer.thruster_huge",
        "cosmoteer.thruster_boost",
    ]

    multiple_turrets = ["cosmoteer.thruster_small_2way", "cosmoteer.thruster_small_3way"]

    # Update position based on part rotation and type
    if part_rotation == 0 and part["ID"] in up_turret_parts:
        position[1] -= sprite_size[1] - part_size[1]
    elif part_rotation == 3 and part["ID"] in up_turret_parts:
        position[0] -= sprite_size[1] - part_size[1]
    elif part_rotation == 1 and part["ID"] in down_turret_parts:
        position[0] -= sprite_size[1] - part_size[1]
    elif part_rotation == 2 and part["ID"] in down_turret_parts:
        position[1] -= sprite_size[1] - part_size[1]
    elif part["ID"] in multiple_turrets:
        if part["ID"] == "cosmoteer.thruster_small_2way":
            if part_rotation == 1:
                position[0] -= 1
            if part_rotation == 2:
                position[0] -= 1
                position[1] -= 1
            if part_rotation == 3:
                position[1] -= 1
        if part["ID"] == "cosmoteer.thruster_small_3way":
            if part_rotation == 0:
                position[0] -= 1
            if part_rotation == 1:
                position[0] -= 1
                position[1] -= 1
            if part_rotation == 2:
                position[0] -= 1
                position[1] -= 1
            if part_rotation == 3:
                position[1] -= 1

    return position


def crop(image, margin=10):
    """
    Crop the given image based on the non-zero pixel values.
    The image is a square with the ship in the center.

    Args:
        image (numpy.ndarray): The input image.
        margin (int): The margin to add or subtract from the min/max values.

    Returns:
        numpy.ndarray: The cropped image.
    """
    # Find the non-zero pixels and get their indices
    coords = np.transpose(np.nonzero(image))

    # Calculate the min/max values for x and y
    xmin = np.min(coords[:, 1]) - margin
    xmax = np.max(coords[:, 1]) + margin
    ymin = np.min(coords[:, 0]) - margin
    ymax = np.max(coords[:, 0]) + margin

    # Ensure the image is a square
    dx = xmax - xmin
    dy = ymax - ymin
    if dx > dy:
        margin = (dx - dy) // 2
        ymax += margin
        ymin -= margin
    elif dy > dx:
        margin = (dy - dx) // 2
        xmax += margin
        xmin -= margin

    # Clamp the min/max values to fit within image boundaries
    xmin = max(0, xmin)
    xmax = min(image.shape[1], xmax)
    ymin = max(0, ymin)
    ymax = min(image.shape[0], ymax)

    # Crop the image
    return image[ymin:ymax, xmin:xmax]


def draw_legend(output_filename):
    """
    Draw a legend image with arrows, circles, and text.

    Args:
        output_filename (str): The filename to save the legend image.
    """

    # Set up parameters
    line_sep = 40
    left_margin = 300

    # Create an empty image
    img = np.zeros((line_sep * 5, 600, 3), np.uint8)

    # Draw arrows and circles
    cv2.arrowedLine(
        img,
        (left_margin, line_sep * 1),
        (left_margin + 100, line_sep * 1),
        [0, 255, 0],
        3,
        tipLength=0.3,
    )
    cv2.arrowedLine(
        img,
        (left_margin, line_sep * 2),
        (left_margin + 100, line_sep * 2),
        [0, 255, 255],
        3,
        tipLength=0.3,
    )
    cv2.arrowedLine(
        img,
        (left_margin, line_sep * 3),
        (left_margin + 100, line_sep * 3),
        [0, 0, 255],
        3,
        tipLength=0.3,
    )
    cv2.circle(img, (left_margin, line_sep * 4), 10, [0, 255, 0], -1)

    # Draw dots at the start of the arrows
    cv2.circle(img, (left_margin, line_sep * 1), 6, [0, 255, 0], -1)
    cv2.circle(img, (left_margin, line_sep * 2), 6, [0, 255, 255], -1)
    cv2.circle(img, (left_margin, line_sep * 3), 6, [0, 0, 255], -1)

    # Add text
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Center of mass next to green circle
    cv2.putText(
        img,
        "Center of Mass",
        (left_margin + 20, line_sep * 4 + 5),
        font,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    # Add white thin arrow from text to circle
    cv2.arrowedLine(
        img,
        (left_margin + 20, line_sep * 4),
        (left_margin, line_sep * 4),
        [255, 255, 255],
        2,
        tipLength=0.2,
    )

    # Center of thrust to the left of green arrow
    cv2.putText(
        img,
        "Center of Thrust",
        (left_margin - 200, line_sep * 1 + 5),
        font,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    # Add white thin arrow from text to start of green arrow
    cv2.arrowedLine(
        img,
        (left_margin - 50, line_sep * 1),
        (left_margin, line_sep * 1),
        [255, 255, 255],
        2,
        tipLength=0.2,
    )

    # Strafe center of thrust to the left of yellow arrow
    cv2.putText(
        img,
        "Strafe Center of Thrust",
        (left_margin - 250, line_sep * 2 + 5),
        font,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    # Add white thin arrow from text to start of yellow arrow
    cv2.arrowedLine(
        img,
        (left_margin - 50, line_sep * 2),
        (left_margin, line_sep * 2),
        [255, 255, 255],
        2,
        tipLength=0.2,
    )

    # Draw the text for the engine center of thrust to the left of the red arrow
    cv2.putText(
        img,
        "Engine Center of Thrust",
        (left_margin - 250, line_sep * 3 + 5),
        font,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    # Add a white thin arrow from the text to the start of the red arrow
    cv2.arrowedLine(
        img,
        (left_margin - 50, line_sep * 3),
        (left_margin, line_sep * 3),
        [255, 255, 255],
        2,
        tipLength=0.2,
    )
    # Add the text "length of vector" on three lines to the right of the arrows
    cv2.putText(
        img,
        "length of vector",
        (left_margin + 120, line_sep * 1 + 5),
        font,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        img,
        "depends on thrust",
        (left_margin + 120, line_sep * 2 + 5),
        font,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        img,
        "on that direction",
        (left_margin + 120, line_sep * 3 + 5),
        font,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    # Save the image
    cv2.imwrite(output_filename, img)


def draw_ship(parts, data_com, data_cot, ship_orientation, output_filename, args):
    """
    Draw a ship using OpenCV.
    Args:
    - parts: a list of ship parts
    - data_com: the center of mass data
    - data_cot: the center of thrust data
    - ship_orientation: the orientation of the ship
    - output_filename: the filename to save the image
    - args: additional arguments
    Returns:
    - an empty string if the image was successfully saved
    """
    # init min and max values for x and y
    min_x = parts[0]["Location"][0]
    max_x = parts[0]["Location"][0]
    min_y = parts[0]["Location"][1]
    max_y = parts[0]["Location"][1]
    # size should be auto, min max abs
    for part in parts:
        x = part["Location"][0]
        y = part["Location"][1]
        # Update min and max values for x and y
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)
    # now the canvas must be at least min x to max x and min y to max y
    canva_size = max((abs(max_x) + abs(min_x)), (abs(max_y) + abs(min_y))) + 250  # add 50 margin
    canva_offset = canva_size // 2
    sprite_square_size = 64
    size_factor = round(sprite_square_size / 4)
    square_size = round(size_factor)
    img = np.zeros((canva_size * size_factor, canva_size * size_factor, 3), np.uint8)
    sprite_directory = "sprites/"
    loaded_sprites = {}
    for i, part in enumerate(parts):
        if part["ID"] in [
            "cosmoteer.cannon_deck",
            "cosmoteer.ion_beam_prism",
        ]:
            parts.append(parts.pop(i))
    for part in parts:
        sprite_id = part["ID"].replace("cosmoteer.", "")
        sprite_path = sprite_directory + sprite_id + ".png"
        if sprite_path in loaded_sprites:
            part_image = loaded_sprites[sprite_path]
        else:
            part_image = cv2.imread(sprite_path, cv2.IMREAD_UNCHANGED)
            loaded_sprites[sprite_path] = part_image
        x_coord = part["Location"][0] + canva_offset
        y_coord = part["Location"][1] + canva_offset
        if x_coord < 0 or x_coord > canva_size or y_coord < 0 or y_coord > canva_size:
            return "error drawing ship: out of bounds\n"
        size = part_data.parts[part["ID"]]["size"]
        rotation = part["Rotation"]
        flipx = part.get("FlipX", 0)
        x_coord, y_coord = sprite_position(part, [x_coord, y_coord])
        scaled_x_coord = round(x_coord * size_factor)
        scaled_y_coord = round(y_coord * size_factor)
        sprite_dimensions = (round(part_image.shape[1] / 4), round(part_image.shape[0] / 4))
        insert_sprite(
            img, part_image, scaled_x_coord, scaled_y_coord, rotation, flipx, sprite_dimensions
        )
    img = img * 0.8
    if args["draw_com"]:
        cv2.circle(
            img,
            (
                round((data_com[0] + canva_offset) * size_factor),
                round((data_com[1] + canva_offset) * size_factor),
            ),
            square_size,
            [0, 255, 0],
            -1,
        )
        parts_tb = []
        for part in parts:
            if part["ID"] == "cosmoteer.tractor_beam_emitter":
                parts_tb.append(part)
        if parts_tb:
            comxtb, comytb, masstb = list(center_of_mass(parts_tb)) or [0, 0, 0]
            data_comtb = [comxtb, comytb, masstb]
            square_size_mod = 12
            cv2.circle(
                img,
                (
                    round((data_comtb[0] + canva_offset) * size_factor),
                    round((data_comtb[1] + canva_offset) * size_factor),
                ),
                square_size_mod,
                [0, 0, 255],
                -1,
            )
        if args["draw_all_com"]:
            for part in parts:
                x_coord, y_coord = part_center_of_mass(part)
                cv2.circle(
                    img,
                    (
                        round((x_coord + canva_offset) * size_factor),
                        round((y_coord + canva_offset) * size_factor),
                    ),
                    1,
                    [0, 255, 0],
                    -1,
                )
    if args["draw_all_cot"]:
        # prepare storing vector of thruster_rocket_extender for each thruster_rocket_nozzle
        # create a variable for each thruster_rocket_nozzle found
        nozzle_vectors = {}
        # List to temporarily hold the parts to be moved to the end
        thruster_nozzles = []

        for part in parts:
            if part["ID"] == "cosmoteer.thruster_rocket_nozzle":
                location = str(part["Location"])
                nozzle_vectors[location] = 0
                thruster_nozzles.append(part)
        # Remove the parts to be moved from the original list
        parts = [part for part in parts if part["ID"] != "cosmoteer.thruster_rocket_nozzle"]

        # Append the thruster nozzles to the end of the list
        parts.extend(thruster_nozzles)

        for part in parts:
            cots = part_center_of_thrust(part, args["boost"])
            if cots == 0:
                continue
            for cot in cots:
                part_rotation = cot[1]
                vector = cot[0]
                end_point = (0, 0)
                size = cot[2] / 2000
                # if part is extender check the nozzle on the same x or y axis
                if part["ID"] == "cosmoteer.thruster_rocket_extender":
                    for part2 in parts:
                        if part2["ID"] == "cosmoteer.thruster_rocket_nozzle":
                            # same rotation and same x or y
                            if part2["Rotation"] == part["Rotation"]:
                                # check for rotation the correct axis
                                if part["Rotation"] == 0 or part["Rotation"] == 2:
                                    if part2["Location"][0] == part["Location"][0]:
                                        location = str(part2["Location"])  # location of the nozzle
                                        # add size of thruster_rocket_extender to thruster_rocket_nozzle
                                        nozzle_vectors[location] += size
                                        # then set size to 0
                                        size = 0
                                if part["Rotation"] == 1 or part["Rotation"] == 3:
                                    if part2["Location"][1] == part["Location"][1]:
                                        location = str(part2["Location"])  # location of the nozzle
                                        # add size of thruster_rocket_extender to thruster_rocket_nozzle
                                        nozzle_vectors[location] += size
                                        # then set size to 0
                                        size = 0
                # then dont draw the extender
                if part["ID"] == "cosmoteer.thruster_rocket_extender":
                    continue
                if part["ID"] == "cosmoteer.thruster_rocket_nozzle":
                    location = str(part["Location"])
                    # find the location matching and get size value
                    size = nozzle_vectors[location]
                    size = size / 2
                rotation_mapping = {
                    0: (vector.x, vector.y - size),
                    1: (vector.x + size, vector.y),
                    2: (vector.x, vector.y + size),
                    3: (vector.x - size, vector.y),
                }
                end_point = rotation_mapping[part_rotation]
                if args["flip_vectors"]:
                    end_point = (vector.x * 2 - end_point[0], vector.y * 2 - end_point[1])
                scaled_vector = (
                    round((vector.x + canva_offset) * size_factor),
                    round((vector.y + canva_offset) * size_factor),
                )  ##MOD##
                scaled_end_point = (
                    round((end_point[0] + canva_offset) * size_factor),
                    round((end_point[1] + canva_offset) * size_factor),
                )  ##MOD##
                cv2.arrowedLine(
                    img, scaled_vector, scaled_end_point, [0, 0, 255], 2, tipLength=0.3
                )  ##MOD##
                cv2.circle(img, scaled_vector, 3, [0, 0, 255], -1)  ##MOD##
    if args["draw_cot"]:
        origin_thrust, thrust_vector, thrust_direction = data_cot
        total_thrust = sum(thrust_direction)
        origin_thrust.append(origin_thrust.pop(ship_orientation))
        thrust_vector.append(thrust_vector.pop(ship_orientation))
        thrust_direction.append(thrust_direction.pop(ship_orientation))
        size_of_arrow = 35
        for i in range(8):
            if not args["draw_all_cot"] and i != 7:
                continue
            start = (origin_thrust[i] + canva_offset) * size_factor
            start = (round(start.x), round(start.y))
            if thrust_direction[i] == 0:
                continue
            thrust = (thrust_vector[i] - origin_thrust[i]) / total_thrust
            if args["flip_vectors"]:
                thrust = thrust * -1
            end = thrust * size_of_arrow + origin_thrust[i]
            end = (end + canva_offset) * size_factor
            end = (round(end.x), round(end.y))
            if i == 7:
                arrow_color = [0, 200, 0]
            else:
                arrow_color = [0, 255, 255]
            cv2.arrowedLine(img, start, end, arrow_color, 2, tipLength=0.2)
            cv2.circle(img, start, 3, arrow_color, -1)
        origin_thrust.insert(ship_orientation, origin_thrust.pop())
        thrust_vector.insert(ship_orientation, thrust_vector.pop())
        thrust_direction.insert(ship_orientation, thrust_direction.pop())
    img = crop(img)
    if output_filename != "":
        cv2.imwrite(output_filename, img)
        return output_filename
    else:
        img_np = np.asarray(img)
        _, buffer = cv2.imencode(".png", img_np)
        base64_encoded = base64.b64encode(buffer).decode("utf-8")
        return base64_encoded


def draw_ship_only(parts):
    """
    Draw a ship using OpenCV.
    Args:
    - parts: a list of ship parts
    Returns:
    - an empty string if the image was successfully saved
    """
    min_x = parts[0]["Location"][0]
    max_x = parts[0]["Location"][0]
    min_y = parts[0]["Location"][1]
    max_y = parts[0]["Location"][1]
    for part in parts:
        x = part["Location"][0]
        y = part["Location"][1]
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)
    canva_size = max((abs(max_x) + abs(min_x)), (abs(max_y) + abs(min_y))) + 250  # add 50 margin
    canva_offset = canva_size // 2
    sprite_square_size = 64
    size_factor = round(sprite_square_size / 4)
    img = np.zeros((canva_size * size_factor, canva_size * size_factor, 3), np.uint8)
    sprite_directory = "sprites/"
    loaded_sprites = {}
    for i, part in enumerate(parts):
        if part["ID"] in [
            "cosmoteer.cannon_deck",
            "cosmoteer.ion_beam_prism",
        ]:
            parts.append(parts.pop(i))
    for part in parts:
        sprite_id = part["ID"].replace("cosmoteer.", "")
        sprite_path = sprite_directory + sprite_id + ".png"
        if sprite_path in loaded_sprites:
            part_image = loaded_sprites[sprite_path]
        else:
            part_image = cv2.imread(sprite_path, cv2.IMREAD_UNCHANGED)
            loaded_sprites[sprite_path] = part_image
        x_coord = part["Location"][0] + canva_offset
        y_coord = part["Location"][1] + canva_offset
        if x_coord < 0 or x_coord > canva_size or y_coord < 0 or y_coord > canva_size:
            return "error drawing ship: out of bounds\n"
        rotation = part["Rotation"]
        flipx = part.get("FlipX", 0)
        x_coord, y_coord = sprite_position(part, [x_coord, y_coord])
        scaled_x_coord = round(x_coord * size_factor)
        scaled_y_coord = round(y_coord * size_factor)
        sprite_dimensions = (round(part_image.shape[1] / 4), round(part_image.shape[0] / 4))
        insert_sprite(
            img, part_image, scaled_x_coord, scaled_y_coord, rotation, flipx, sprite_dimensions
        )

    img = img * 0.8
    img = crop(img)
    # put text on the image
    font = cv2.FONT_HERSHEY_SIMPLEX
    line_sep = 40
    left_margin = 0
    # Center of mass next to green circle
    cv2.putText(
        img,
        "Made with CosmoShipBuilder",
        (left_margin + 20, line_sep * 4 + 5),
        font,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    img = cv2.resize(img, (512, 512), interpolation=cv2.INTER_AREA)
    # read the image and add alpha bit plane to it
    b_channel, g_channel, r_channel = cv2.split(img)
    alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * 200 #creating a dummy alpha channel image.
    img_BGRA = cv2.merge((b_channel, g_channel, r_channel, alpha_channel))
    img_np = np.asarray(img_BGRA)
    
    # img_np = np.asarray(img)
    _, buffer = cv2.imencode(".png", img_np)
    base64_encoded = base64.b64encode(buffer).decode("utf-8")
    return base64_encoded


def remove_weird_parts(parts):
    """
    Removes parts from the given list that are not present in the part_data.
    Replaces certain old part IDs with their corresponding new part IDs.
    Returns the updated list of parts and any error messages encountered.
    """
    # Set to store unknown part IDs
    unknown_parts = set()

    # Boolean flag to indicate if classic ships are present
    classic = False

    # List to store the updated parts
    new_parts = []

    # Iterate over each part in the given list
    for part in parts:
        # Check if the part ID is present in part_data
        if part["ID"] in part_data.parts:
            new_parts.append(part)
        else:
            # List of old factory IDs and their corresponding new factory IDs
            old_part_ids = [
                "cosmoteer.ammo_factory",
                "cosmoteer.missile_factory_nuke",
                "cosmoteer.missile_factory_he",
                "cosmoteer.electro_bolter",
            ]
            new_part_ids = [
                "cosmoteer.factory_ammo",
                "cosmoteer.factory_nuke",
                "cosmoteer.factory_he",
                "cosmoteer.disruptor",
            ]

            if part["ID"] in old_part_ids:
                # Replace the part ID with its corresponding new ID
                part["ID"] = new_part_ids[old_part_ids.index(part["ID"])]
                # print(part)
                new_parts.append(part)
                classic = True
                continue

            # List of old mirror L IDs and their corresponding updated IDs
            old_mirror_left = [
                "cosmoteer.structure_1x2_wedge_L",
                "cosmoteer.structure_1x3_wedge_L",
                "cosmoteer.armor_1x2_wedge_L",
                "cosmoteer.armor_1x3_wedge_L",
            ]

            # List of old mirror R IDs and their corresponding updated IDs
            old_mirror_right = [
                "cosmoteer.structure_1x2_wedge_R",
                "cosmoteer.structure_1x3_wedge_R",
                "cosmoteer.armor_1x2_wedge_R",
                "cosmoteer.armor_1x3_wedge_R",
            ]

            # Check if the part ID is in the old_mirror_L list
            if part["ID"] in old_mirror_left:
                # Update the part ID and FlipX value
                part["ID"] = part["ID"][:-2]
                part["FlipX"] = 0
                new_parts.append(part)
                classic = True
                continue

            # Check if the part ID is in the old_mirror_R list
            if part["ID"] in old_mirror_right:
                # Update the part ID and FlipX value
                part["ID"] = part["ID"][:-2]
                part["FlipX"] = 1
                new_parts.append(part)
                classic = True
                continue

            # Add the unknown part ID to the set
            unknown_parts.add(part["ID"])

            # Update the part ID to "cosmoteer.UNKNOWN"
            part["ID"] = "cosmoteer.UNKNOWN"
            new_parts.append(part)

    # Generate the error message for unknown parts
    error_msg = ""
    for part in unknown_parts:
        error_msg += "unknown part: " + part + "\n"

    # Check if classic ships are present and add error message accordingly
    if classic:
        error_msg += "classic ships are not supported, com and cot may be wrong\n"

    return new_parts, error_msg


def com(input_filename, output_filename, args={}):
    """
    Calculate the center of mass, center of thrust, and speed of a ship.

    Args:
        input_filename (str): The filename of the ship data.
        output_filename (str): The filename of the output image.
        args (dict, optional): Additional arguments. Defaults to {"boost":True,"draw_all_cot":True,"draw_all_coms":False}.

    Returns:
        tuple: A tuple containing the center of mass, center of thrust, speed, and error message.

    """
    # define default arguments
    defaults = {
        "draw": True,
        "flip_vectors": False,
        "draw_all_com": False,
        "draw_all_cot": True,
        "draw_cot": True,
        "draw_com": True,
        "boost": True,
        "analyze": False,
    }

    args = {**defaults, **args}

    # preprocessing
    # Read ship data and extract part data
    try:
        decoded_data = cosmoteer_save_tools.Ship(input_filename).data
    except Exception as e:
        error_text = f"Could not read input file (save tool) {e}"
        return json.dumps({"Error": error_text})
    # Convert bytes to base64-encoded strings in the decoded_data dictionary
    try:
        decoded_data = convert_bytes_to_base64(decoded_data)
    except Exception as e:
        error_text = "Could not convert_bytes_to_base64 (json cleaner)"
        return json.dumps({"Error": error_text})
    # decoded data processing
    try:
        parts = decoded_data["Parts"]
    except Exception as e:
        error_text = "Could not read Parts"
        return json.dumps({"Error": error_text})
    try:
        ship_orientation = decoded_data["FlightDirection"]
    except Exception as e:
        error_text = "Could not read FlightDirection"
        return json.dumps({"Error": error_text})
    ## get tags
    try:
        tags, author = PNGTagExtractor().extract_tags(decoded_data)
    except Exception as e:
        error_text = "Could not execute extract_tags (PNGTagExtractor)"
        return json.dumps({"Error": error_text})
    ## get crew and price
    try:
        price, crew = calculate_price(decoded_data)
    except Exception as e:
        error_text = "Could not execute calculate_price (pricegen)"
        return json.dumps({"Error": error_text})
    # parts processing
    # Remove weird parts
    try:
        parts, error_message = remove_weird_parts(parts)
    except Exception as e:
        error_text = "Could not remove_weird_parts (classic ships)"
        return json.dumps({"Error": error_text})
    # Calculate center of mass
    try:
        comx, comy, mass = list(center_of_mass(parts))
    except Exception as e:
        error_text = "Could not execute center_of_mass"
        return json.dumps({"Error": error_text})
    data_com = [comx, comy, mass]

    # Calculate center of thrust
    try:
        origin_thrust, thrust_vector, thrust_direction = center_of_thrust(parts, args)
    except Exception as e:
        error_text = "Could not execute center_of_thrust"
        return json.dumps({"Error": error_text})
    try:
        origin_thrust, thrust_vector, thrust_direction = diagonal_center_of_thrust(
            origin_thrust, thrust_vector, thrust_direction
        )
    except Exception as e:
        error_text = "Could not execute diagonal_center_of_thrust"
        return json.dumps({"Error": error_text})
    data_cot = [origin_thrust, thrust_vector, thrust_direction]

    # direction mapping
    direction_mapping = {0: "NW", 1: "N", 2: "NE", 3: "E", 4: "SE", 5: "S", 6: "SW", 7: "W"}

    # Calculate speed in all directions
    speeds = {}
    try:
        for ship_orient, direction_ori in direction_mapping.items():
            speeds[direction_ori] = top_speed(mass, thrust_direction[ship_orient])
    except Exception as e:
        error_text = "Could not execute top_speed"
        return json.dumps({"Error": error_text})

    # actual return function
    if args["analyze"]:
        try:
            analysis = json.loads(price_analysis(decoded_data))
        except Exception as e:
            error_text = f"Could not execute price_analysis (price_analysis_ocv) {e}"
            return json.dumps({"Error": error_text})
    else:
        analysis = False

    if args["draw"]:
        # API override
        output_filename = ""  # we dont store file on the server instead we upload it
        # Draw ship and write to output image
        try:
            base64_output = draw_ship(
                parts, data_com, data_cot, ship_orientation, output_filename, args
            )
        except Exception as e:
            error_text = "Could not execute draw_ship"
            return json.dumps({"Error": error_text})
        url_com = "error url upload_image"
        try:
            url_com = upload_image_to_imgbb(base64_output)
        except Exception as e:
            error_text = "Could not execute upload_image_to_imgbb (png_upload)"
            return json.dumps({"Error": error_text})
        # print(url_com)
        data = {
            # "url_org": url,
            "url_com": url_com,
            "center_of_mass_x": comx,
            "center_of_mass_y": comy,
            "total_mass": mass,
            "top_speed": speeds[direction_mapping[decoded_data["FlightDirection"]]],
            "crew": crew,
            "price": price,
            "tags": tags,
            "author": author,
            "all_direction_speeds": speeds,
            "analysis": analysis,
        }
        # Convert the dictionary to a JSON string
        try:
            json_data = json.dumps(data)
        except Exception as e:
            error_text = "Could not convert output data to json"
            return json.dumps({"Error": error_text})

        return json_data

    url_com = "draw is false"
    data = {
        # "url_org": url,
        "url_com": url_com,
        "center_of_mass_x": comx,
        "center_of_mass_y": comy,
        "total_mass": mass,
        "top_speed": speeds[direction_mapping[decoded_data["FlightDirection"]]],
        "crew": crew,
        "price": price,
        "tags": tags,
        "author": author,
        "all_direction_speeds": speeds,
        "analysis": analysis,
    }
    # Convert the dictionary to a JSON string
    try:
        json_data = json.dumps(data)
    except Exception as e:
        error_text = "Could not convert output data to json"
        return json.dumps({"Error": error_text})

    return json_data


# Function to recursively convert bytes to base64-encoded strings in the dictionary
def convert_bytes_to_base64(data):
    """
    A function that recursively converts bytes to base64-encoded strings in the dictionary.

    Parameters:
    - data: The input data that can be bytes, a list, a dictionary, or any other type.

    Returns:
    - The converted data with bytes converted to base64-encoded strings.
    """
    if isinstance(data, bytes):
        return base64.b64encode(data).decode("utf-8")
    if isinstance(data, list):
        return [convert_bytes_to_base64(item) for item in data]
    if isinstance(data, dict):
        return {key: convert_bytes_to_base64(value) for key, value in data.items()}
    return data
