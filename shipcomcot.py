# Copyright 2023 LunastroD

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use,  
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
# is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE 
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# INSTRUCTIONS:
# move your ship.png to the ships folder
# change the SHIP variable to the name of your ship.png
#   the center of mass of your ship will be drawn as a green circle
#   the center of thrust will be drawn as a green arrow and yellow arrows for each direction
#   if you can't see the window, the image will be saved as out.png

import part_data
import cosmoteer_save_tools
import json
from png_upload import upload_image_to_imgbb
import base64
import cv2
import numpy as np
from tagextractor import PNGTagExtractor
from pricegen import calculate_price

GRAPHICS=1 #set to 1 to use opencv to draw ship
DRAW_ALL_COM=0
DRAW_COM=1
DRAW_COTS=1
DRAW_ALL_COT=1
WINDOWED=0 #set to 1 to show the opencv window




def parts_touching(part1, part2):
    #returns true if part1 and part2 are touching
    #part1 and part2 are touching if any of their tiles are touching
    part1_size = part_data.parts[part1["ID"]]["size"]
    part2_size = part_data.parts[part2["ID"]]["size"]
    part1_location = part1["Location"]#upper left corner
    part2_location = part2["Location"]#upper left corner
    part1_rotation = part1["Rotation"]#0,1,2,3
    part2_rotation = part2["Rotation"]#0,1,2,3

    if(part1_rotation==1 or part1_rotation==3):
        part1_size=(part1_size[1],part1_size[0])
    if(part2_rotation==1 or part2_rotation==3):
        part2_size=(part2_size[1],part2_size[0])

    #generate list of tiles for each part
    part1_tiles = []
    part2_tiles = []
    for i in range(part1_size[0]):
        for j in range(part1_size[1]):
            part1_tiles.append((part1_location[0]+i, part1_location[1]+j))
    for i in range(part2_size[0]):
        for j in range(part2_size[1]):
            part2_tiles.append((part2_location[0]+i, part2_location[1]+j))

    #expand tiles of part 1 to include adjacent tiles (except diagonals)
    for i in range(part1_size[0]):
        for j in range(part1_size[1]):
            part1_tiles.append((part1_location[0]+i+1, part1_location[1]+j))
            part1_tiles.append((part1_location[0]+i-1, part1_location[1]+j))
            part1_tiles.append((part1_location[0]+i, part1_location[1]+j+1))
            part1_tiles.append((part1_location[0]+i, part1_location[1]+j-1))
    
    #check if any of the tiles of part 1 are touching part 2
    for tile in part1_tiles:
        if(tile in part2_tiles):
            return True
    return False
    
def thruster_touching_engine_room(parts,thruster):
    for part in parts:
        if(part["ID"]=="cosmoteer.engine_room" and parts_touching(thruster,part)):
            return True
    return False

def calculate_total_thrust(parts):
    # Returns the total thrust of all the thrusters in the ship
    total_thrust = 0
    for part in parts:
        part_id = part["ID"]
        if part_id in part_data.thruster_data:
            if thruster_touching_engine_room(parts, part):
                thrust = part_data.thruster_data[part_id]["thrust"] * 1.5
            else:
                thrust = part_data.thruster_data[part_id]["thrust"]
            total_thrust += thrust
    return total_thrust

def calculate_top_speed(mass, thrust):
    speed = 0
    for _ in range(350):
        # Calculate drag based on current speed
        drag = (max(speed / 75, 1) ** 2 * speed * 0.4)
        
        # Calculate acceleration
        acceleration = thrust / mass - drag
        
        # Update speed
        speed += acceleration / 30
    
    return speed

def part_center_of_mass(part):
    part_size = part_data.parts[part["ID"]]["size"]
    part_rotation = part["Rotation"]
    
    if part_rotation == 0 or part_rotation == 2:
        center_of_mass_x = part["Location"][0] + part_size[0] / 2
        center_of_mass_y = part["Location"][1] + part_size[1] / 2
    elif part_rotation == 1 or part_rotation == 3:
        center_of_mass_x = part["Location"][0] + part_size[1] / 2
        center_of_mass_y = part["Location"][1] + part_size[0] / 2
    else:
        raise ValueError("Invalid part_rotation value: {}".format(part_rotation))
    
    return center_of_mass_x, center_of_mass_y

def part_center_of_thrust(part):
    part_cots = part_data.thruster_data.get(part["ID"], {"cot": 0})["cot"]
    if part_cots == 0:
        return 0

    part_rotation = part["Rotation"]
    part_size = part_data.parts[part["ID"]]["size"]
    absolute_cots = []
    
    for part_cot in part_cots:
        orientation = (part_rotation + part_cot[2]) % 4
        
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
            raise ValueError("part_rotation not 0, 1, 2, or 3")

        absolute_cots.append((center_of_thrust_x, center_of_thrust_y, orientation))
    
    return absolute_cots

def center_of_mass(parts):
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

def center_of_thrust_vector(parts, ship_direction):
    # Calculate the center of thrust vector of the ship in a given direction.
    # Each part has a center of thrust, calculated by part_center_of_thrust(part).
    # Returns a unit vector and the total thrust (originx, originy, endx, endy, thrust) representing the center of thrust vector.

    fthruster_lookup = {
        0: [0, 3],
        1: [0],
        2: [0, 1],
        3: [1],
        4: [1, 2],
        5: [2],
        6: [2, 3],
        7: [3]
    }

    total_thrust = 0
    total_thrust_direction = 0

    sum_x_cot = 0
    sum_y_cot = 0
    
    sum_x_thrust = 0
    sum_y_thrust = 0

    for part in parts:
        cots = part_center_of_thrust(part)
        if cots == 0:
            continue
        for cot in cots:
            thrust = part_data.thruster_data[part["ID"]]["thrust"]
            if thruster_touching_engine_room(parts, part):
                thrust = thrust * 1.5
            x_coord = cot[0]
            y_coord = cot[1]

            total_thrust += thrust
            if cot[2] in fthruster_lookup[ship_direction]:
                total_thrust_direction += thrust

                sum_x_cot += thrust * x_coord
                sum_y_cot += thrust * y_coord
                if cot[2] == 0:
                    sum_y_thrust -= thrust
                if cot[2] == 1:
                    sum_x_thrust += thrust
                if cot[2] == 2:
                    sum_y_thrust += thrust
                if cot[2] == 3:
                    sum_x_thrust -= thrust

    if total_thrust_direction == 0:
        return 0

    startx = sum_x_cot / total_thrust_direction
    starty = sum_y_cot / total_thrust_direction
    endx = startx + sum_x_thrust / total_thrust * 15
    endy = starty + sum_y_thrust / total_thrust * 15
    
    return startx, starty, endx, endy, total_thrust_direction / total_thrust
    


# Define a function to rotate an image by the specified angle
def rotate_image(image, angle, flipx):
    if(flipx):
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

# Define a function to insert a sprite onto the background image with a specified size and handle transparency
def insert_sprite(background, sprite, x, y, rotation, flipx, size):
    sprite_resized = cv2.resize(sprite, size)
    sprite_rotated = rotate_image(sprite_resized, rotation, flipx)

    sprite_height, sprite_width, _ = sprite_rotated.shape
    background_height, background_width, _ = background.shape

    if y + sprite_height <= background_height and x + sprite_width <= background_width:
        sprite_rgb = sprite_rotated[:, :, :3]
        alpha_channel = sprite_rotated[:, :, 3] / 255.0

        background_region = background[y:y+sprite_height, x:x+sprite_width]

        for c in range(3):
            background_region[:, :, c] = (
                (1.0 - alpha_channel) * background_region[:, :, c]
                + alpha_channel * sprite_rgb[:, :, c]
            )

    else:
        print(f"Warning: Sprite at ({x}, {y}) exceeds the background dimensions.")

def sprite_position(part, position):
    sprite_size = part_data.parts[part["ID"]].get("sprite_size")
    if sprite_size is None:
        return position

    part_size = part_data.parts[part["ID"]]["size"]
    part_rotation = part["Rotation"]

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
        "cosmoteer.shield_gen_small"
    ]

    down_turret_parts = [
        "cosmoteer.thruster_small",
        "cosmoteer.thruster_med",
        "cosmoteer.thruster_large",
        "cosmoteer.thruster_huge",
        "cosmoteer.thruster_boost"
    ]

    multiple_turrets = [
        "cosmoteer.thruster_small_2way",
        "cosmoteer.thruster_small_3way"
    ]

    if part_rotation == 0 and part["ID"] in up_turret_parts:
        position[1] = position[1] - (sprite_size[1] - part_size[1])
    elif part_rotation == 3 and part["ID"] in up_turret_parts:
        position[0] = position[0] - (sprite_size[1] - part_size[1])
    elif part_rotation == 1 and part["ID"] in down_turret_parts:
        position[0] = position[0] - (sprite_size[1] - part_size[1])
    elif part_rotation == 2 and part["ID"] in down_turret_parts:
        position[1] = position[1] - (sprite_size[1] - part_size[1])
    elif part["ID"] in multiple_turrets:
        if part["ID"] == "cosmoteer.thruster_small_2way":
            if part_rotation == 1:
                position[0] = position[0] - 1
            if part_rotation == 2:
                position[0] = position[0] - 1
                position[1] = position[1] - 1
            if part_rotation == 3:
                position[1] = position[1] - 1
        if part["ID"] == "cosmoteer.thruster_small_3way":
            if part_rotation == 0:
                position[0] = position[0] - 1
            if part_rotation == 1:
                position[0] = position[0] - 1
                position[1] = position[1] - 1
            if part_rotation == 2:
                position[0] = position[0] - 1
                position[1] = position[1] - 1
            if part_rotation == 3:
                position[1] = position[1] - 1

    return position

def crop(image, margin=10):
    # Find the non-zero indices
    y_nonzero, x_nonzero, _ = np.nonzero(image)
    
    # Find the min and max values
    xmin = np.min(x_nonzero) - margin
    xmax = np.max(x_nonzero) + margin
    ymin = np.min(y_nonzero) - margin
    ymax = np.max(y_nonzero) + margin
    
    # Make sure the values are within the image bounds
    xmin = max(xmin, 0)
    xmax = min(xmax, image.shape[1])
    ymin = max(ymin, 0)
    ymax = min(ymax, image.shape[0])
    
    # Crop the image
    return image[ymin:ymax, xmin:xmax]



def draw_ship(parts, com, sorient): ## added ship orientation
    #use opencv to draw ship
    #create blank image factor times of the ship
    sprite_square_size = 64
    size_factor = round(sprite_square_size/4)
    square_size = round(size_factor)
    img = np.zeros((120*size_factor,120*size_factor,3), np.uint8)


    #using sprites instead of rectangles
    for i in range(len(parts)):
        if(parts[i]["ID"] in ["cosmoteer.cannon_deck","cosmoteer.ion_beam_prism"]):
            parts.append(parts.pop(i))#move top turrets to the end of the list so they are drawn last
            
    for part in parts:
        x_coord = part["Location"][0] +60
        y_coord = part["Location"][1] +60
        size=part_data.parts[part["ID"]]["size"]
        rotation=part["Rotation"]
        flipx=part["FlipX"]

        x_coord,y_coord=sprite_position(part, [x_coord, y_coord])

        sprite_path="sprites/"+part["ID"].replace("cosmoteer.","")+".png"
        img_part = cv2.imread(sprite_path, cv2.IMREAD_UNCHANGED)
        #print(img_part.shape)
        #insert_sprite(img, img_part, round(x_coord*size_factor),round(y_coord*size_factor) , rotation,flipx, (round(size[0]*size_factor), round(size[1]*size_factor)))
        insert_sprite(img, img_part, round(x_coord*size_factor),round(y_coord*size_factor) , rotation,flipx, (round(img_part.shape[1]/4), round(img_part.shape[0]/4)))
    #the image should be a bit darker
    img=img*0.8

    #add center of mass (as a green circle)
    cv2.circle(img, (round((com[0]+60)*size_factor), round((com[1]+60)*size_factor)), square_size, [0,255,0], -1)
    
    #add center of thrust of each part (as a red circle)
    for part in parts:
        cots=part_center_of_thrust(part)
        if(cots==0):
            continue
        for cot in cots:
            #cv2.circle(img, (round((cot[0]+60)*size_factor), round((cot[1]+60)*size_factor)), 1, [0,0,255], -1)
            part_rotation = cot[2]
            end_point = (0,0)
            if(part_rotation==0):
                end_point = (cot[0], cot[1]-2)
            elif(part_rotation==1):
                end_point = (cot[0]+2, cot[1])
            elif(part_rotation==2):
                end_point = (cot[0], cot[1]+2)
            elif(part_rotation==3):
                end_point = (cot[0]-2, cot[1])
            
            
            cv2.arrowedLine(img, (round((cot[0]+60)*size_factor), round((cot[1]+60)*size_factor)), (round((end_point[0]+60)*size_factor), round((end_point[1]+60)*size_factor)), [0,0,255], 2, tipLength=0.3)
            #also draw a dot at the start of the arrow
            cv2.circle(img, (round((cot[0]+60)*size_factor), round((cot[1]+60)*size_factor)), 3, [0,0,255], -1)
    


    # ship_orientation = cosmoteer_save_tools.Ship(SHIP).data["FlightDirection"]
    ship_orientation = sorient
    arrow_draw_order=list(range(7,-1,-1))
    arrow_draw_order.remove(ship_orientation)
    arrow_draw_order.append(ship_orientation)
    for forient in arrow_draw_order:
        cot = center_of_thrust_vector(parts, forient) # include array of orientation
        if(cot!=0):
            #print('cot', cot)
            arrow_thickness=3
            if(forient==ship_orientation):
                arrow_color=[0,240,0]
            else:
                arrow_color=[0,255,255]
            cv2.arrowedLine(
                img, 
                (round((cot[0]+60)*size_factor), round((cot[1]+60)*size_factor)), # start must be center
                (round((cot[2]+60)*size_factor), round((cot[3]+60)*size_factor)), # end
                arrow_color,
                arrow_thickness, 
                tipLength=0.2
                )
            #also draw a dot at the start of the arrow
            cv2.circle(img, (round((cot[0]+60)*size_factor), round((cot[1]+60)*size_factor)), 5, arrow_color, -1)
                
    #crop image (remove the black border around the ship)
    img=crop(img)

    # Convert the OpenCV image to a NumPy array
    img_np = np.asarray(img)

    # Encode the NumPy array as a base64 string
    _, buffer = cv2.imencode('.png', img_np)
    base64_encoded = base64.b64encode(buffer).decode("utf-8")
    
    url_com = upload_image_to_imgbb(base64_encoded)
    
    return url_com
    

def com(url):
    # Decode the ship data from the URL
    json_data = cosmoteer_save_tools.decode_ship_data(url)
    json_data = json.loads(json_data) 
    
    ## get tags
    tags, author = PNGTagExtractor().extract_tags(json_data)
    print(tags)
    print(author)
    
    ## get crew and price
    price, crew = calculate_price(json_data)
 
    # Extract the necessary information from the JSON data
    parts = json_data["Parts"]
    sorient = json_data["FlightDirection"]

    # Calculate the center of mass and other data
    center_of_mass_data = center_of_mass(parts)
    center_of_mass_data = list(center_of_mass_data)
    center_of_mass_data.append(calculate_top_speed(center_of_mass_data[2], calculate_total_thrust(parts)))

    # Draw the ship and get the URL of the image
    url_com = draw_ship(parts, center_of_mass_data, sorient)

    # Format the data for output
    center_of_mass_x = "{:.2f}".format(center_of_mass_data[0])
    center_of_mass_y = "{:.2f}".format(center_of_mass_data[1])
    total_mass = "{:.2f}".format(center_of_mass_data[2])
    top_speed_x = "{:.2f}".format(center_of_mass_data[3])

    data = {
        "url_org": url,
        "url_com": url_com,
        "center_of_mass_x": center_of_mass_x,
        "center_of_mass_y": center_of_mass_y,
        "total_mass": total_mass,
        "top_speed": top_speed_x,
        "crew": crew,
        "price": price,
        "tags": tags,
        "author": author
    }

    # Convert the dictionary to a JSON string
    json_data = json.dumps(data)
    
    return json_data
