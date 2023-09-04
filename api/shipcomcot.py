## Full credit to https://github.com/lunastrod/cosmoteer-com LunastroD

import cv2
import numpy as np
import json
from png_upload import upload_image_to_imgbb
import base64

## variables ##
parts_data={
        "cosmoteer.corridor":{"mass":1, "size":(1,1)},
        "cosmoteer.structure":{"mass":1/3, "size":(1,1)},
        "cosmoteer.structure_wedge":{"mass":0.17, "size":(1,1)},
        "cosmoteer.structure_1x2_wedge":{"mass":0.33, "size":(1,2)},
        "cosmoteer.structure_1x3_wedge":{"mass":0.5, "size":(1,3)},
        "cosmoteer.structure_tri":{"mass":0.08, "size":(1,1)},
        "cosmoteer.laser_blaster_small":{"mass":2.5, "size":(1,2)},
        "cosmoteer.laser_blaster_large":{"mass":7.68, "size":(2,3)},
        "cosmoteer.disruptor":{"mass":3.48, "size":(1,3)},
        "cosmoteer.ion_beam_emitter":{"mass":8, "size":(2,4)},
        "cosmoteer.resource_collector":{"mass":4, "size":(2,2)},
        "cosmoteer.ion_beam_prism":{"mass":7.7, "size":(2,2)},
        "cosmoteer.tractor_beam_emitter":{"mass":32.07, "size":(5,5)},
        "cosmoteer.point_defense":{"mass":1, "size":(1,1)},
        "cosmoteer.mining_laser_small":{"mass":7.4, "size":(2,3)},
        "cosmoteer.cannon_med":{"mass":4.44, "size":(2,1)},
        "cosmoteer.sensor_array":{"mass":11.54, "size":(3,3)},
        "cosmoteer.cannon_large":{"mass":12.29, "size":(3,2)},
        "cosmoteer.hyperdrive_beacon":{"mass":17.13, "size":(4,4)},
        "cosmoteer.cannon_deck":{"mass":27.07, "size":(4,5)},
        "cosmoteer.explosive_charge":{"mass":1, "size":(1,1)},
        "cosmoteer.roof_light":{"mass":1, "size":(1,1)},
        "cosmoteer.missile_launcher":{"mass":6, "size":(2,3)},
        "cosmoteer.roof_headlight":{"mass":1, "size":(1,1)},
        "cosmoteer.railgun_loader":{"mass":24, "size":(2,3)},
        "cosmoteer.armor_structure_hybrid_1x1":{"mass":1.5, "size":(1,1)},
        "cosmoteer.armor_structure_hybrid_1x2":{"mass":3, "size":(1,2)},
        "cosmoteer.railgun_accelerator":{"mass":36, "size":(2,3)},
        "cosmoteer.armor_structure_hybrid_1x3":{"mass":4.5, "size":(1,3)},
        "cosmoteer.armor_structure_hybrid_tri":{"mass":1, "size":(1,1)},
        "cosmoteer.railgun_launcher":{"mass":36, "size":(2,3)},
        "cosmoteer.armor":{"mass":3, "size":(1,1)},
        "cosmoteer.armor_2x1":{"mass":6, "size":(2,1)},
        "cosmoteer.flak_cannon_large":{"mass":16.77, "size":(3,6)},
        "cosmoteer.armor_wedge":{"mass":1.5, "size":(1,1)},
        "cosmoteer.armor_1x2_wedge":{"mass":3, "size":(1,2)},
        "cosmoteer.shield_gen_small":{"mass":6, "size":(2,3)},
        "cosmoteer.armor_1x3_wedge":{"mass":4.5, "size":(1,3)},
        "cosmoteer.armor_tri":{"mass":0.75, "size":(1,1)},
        "cosmoteer.shield_gen_large":{"mass":12.65, "size":(3,6)},
        "cosmoteer.thruster_small":{"mass":1.3, "size":(1,1)},
        "cosmoteer.thruster_med":{"mass":2.45, "size":(1,2)},
        "cosmoteer.thruster_large":{"mass":4.99, "size":(2,2)},
        "cosmoteer.thruster_boost":{"mass":8.88, "size":(2,3)},
        "cosmoteer.fire_extinguisher":{"mass":1, "size":(1,1)},
        "cosmoteer.thruster_huge":{"mass":11, "size":(3,3)},
        "cosmoteer.control_room_small":{"mass":4, "size":(2,2)},
        "cosmoteer.control_room_med":{"mass":9, "size":(3,3)},
        "cosmoteer.thruster_small_2way":{"mass":1.61, "size":(1,1)},
        "cosmoteer.control_room_large":{"mass":16, "size":(4,4)},
        "cosmoteer.thruster_small_3way":{"mass":1.91, "size":(1,1)},
        "cosmoteer.hyperdrive_small":{"mass":4, "size":(2,2)},
        "cosmoteer.engine_room":{"mass":9, "size":(3,3)},
        "cosmoteer.crew_quarters_small":{"mass":2, "size":(1,2)},
        "cosmoteer.crew_quarters_med":{"mass":4, "size":(2,2)},
        "cosmoteer.airlock":{"mass":1, "size":(1,1)},
        "cosmoteer.conveyor":{"mass":1, "size":(1,1)},
        "cosmoteer.reactor_small":{"mass":4, "size":(2,2)},
        "cosmoteer.reactor_med":{"mass":9, "size":(3,3)},
        "cosmoteer.reactor_large":{"mass":16, "size":(4,4)},
        "cosmoteer.power_storage":{"mass":4, "size":(2,2)},
        "cosmoteer.factory_ammo":{"mass":4, "size":(2,2)},
        "cosmoteer.factory_he":{"mass":9, "size":(3,3)},
        "cosmoteer.factory_emp":{"mass":12, "size":(3,4)},
        "cosmoteer.factory_nuke":{"mass":16, "size":(4,4)},
        "cosmoteer.factory_mine":{"mass":12, "size":(4,3)},
        "cosmoteer.factory_steel":{"mass":16, "size":(4,4)},
        "cosmoteer.factory_coil":{"mass":9, "size":(3,3)},
        "cosmoteer.factory_coil2":{"mass":12, "size":(4,3)},
        "cosmoteer.factory_tristeel":{"mass":16, "size":(4,4)},
        "cosmoteer.factory_diamond":{"mass":6, "size":(2,3)},
        "cosmoteer.factory_processor":{"mass":9, "size":(3,3)},
        "cosmoteer.factory_uranium":{"mass":12, "size":(3,4)},
        "cosmoteer.storage_2x2":{"mass":4, "size":(2,2)},
        "cosmoteer.storage_3x2":{"mass":6, "size":(3,2)},
        "cosmoteer.storage_3x3":{"mass":9, "size":(3,3)},
        "cosmoteer.storage_4x3":{"mass":12, "size":(4,3)},
        "cosmoteer.storage_4x4":{"mass":16, "size":(4,4)},
}

thruster_data={
        "cosmoteer.thruster_small":{"cot":((0.5,1.5,0),),"thrust":400},
        "cosmoteer.thruster_med":{"cot":((0.5,2.5,0),),"thrust":1200},
        "cosmoteer.thruster_large":{"cot":((1,2.5,0),),"thrust":3200},
        "cosmoteer.thruster_boost":{"cot":((1,4.5,0),),"thrust":3200},
        "cosmoteer.thruster_huge":{"cot":((1.5,3.5,0),),"thrust":8000},
        "cosmoteer.thruster_small_2way":{"cot":((0.5,1.5,0),(1.5,0.5,3)),"thrust":400},
        "cosmoteer.thruster_small_3way":{"cot":((0.5,1.5,0),(1.5,0.5,3),(-0.5,0.5,1)),"thrust":400},
}

blue_parts = ["cosmoteer.shield_gen_small","cosmoteer.shield_gen_large","cosmoteer.control_room_small","cosmoteer.control_room_med","cosmoteer.control_room_large", "cosmoteer.armor", "cosmoteer.armor_2x1","cosmoteer.armor_wedge","cosmoteer.armor_1x2_wedge","cosmoteer.armor_1x3_wedge","cosmoteer.armor_tri","cosmoteer.armor_structure_hybrid_1x1","cosmoteer.armor_structure_hybrid_1x2","cosmoteer.armor_structure_hybrid_1x3","cosmoteer.armor_structure_hybrid_tri"]
gray_parts = ["cosmoteer.structure","cosmoteer.structure_wedge","cosmoteer.structure_1x2_wedge","cosmoteer.structure_1x3_wedge","cosmoteer.structure_tri","cosmoteer.corridor","cosmoteer.fire_extinguisher","cosmoteer.airlock","cosmoteer.crew_quarters_small","cosmoteer.crew_quarters_med","cosmoteer.conveyor","cosmoteer.storage_2x2","cosmoteer.storage_3x2","cosmoteer.storage_3x3","cosmoteer.storage_4x3","cosmoteer.storage_4x4"]
yellow_parts = ["cosmoteer.power_storage","cosmoteer.thruster_small","cosmoteer.thruster_med","cosmoteer.thruster_large","cosmoteer.thruster_small_2way","cosmoteer.thruster_small_3way","cosmoteer.thruster_huge","cosmoteer.thruster_boost","cosmoteer.engine_room","cosmoteer.reactor_small","cosmoteer.reactor_med","cosmoteer.reactor_large"]
red_parts = ["cosmoteer.laser_blaster_small","cosmoteer.laser_blaster_large","cosmoteer.disruptor","cosmoteer.ion_beam_emitter","cosmoteer.ion_beam_prism","cosmoteer.tractor_beam_emitter","cosmoteer.point_defense","cosmoteer.mining_laser_small","cosmoteer.cannon_med","cosmoteer.cannon_large","cosmoteer.cannon_deck","cosmoteer.explosive_charge","cosmoteer.missile_launcher","cosmoteer.railgun_loader","cosmoteer.railgun_accelerator","cosmoteer.railgun_launcher","cosmoteer.flak_cannon_large"]
## end of constants ##

def analyze_ship(json_data):
    dataclean = json.loads(json_data)
    parts = dataclean['Parts']
    fdir = dataclean['FlightDirection']


    size_factor = 8
    square_size = round(size_factor)
    img = np.zeros((120*size_factor,120*size_factor,3), np.uint8)

    # Define the center of the image
    center_x = img.shape[0] // 2 // size_factor
    center_y = img.shape[1] // 2 // size_factor

    # init center of mass
    total_mass = 0
    sum_x_mass = 0
    sum_y_mass = 0

    #add parts to image
    for part_data in parts:
        x = part_data["Location"][0] + center_x
        
        y = part_data["Location"][1] + center_y
        part_id = part_data['ID']
        # print(part_id)
        if part_id in red_parts:
            color = [0, 0, 125]
        elif part_id in yellow_parts:
            color = [0, 125, 125]
        elif part_id in gray_parts:
            color = [125, 125, 125]
        elif part_id in blue_parts:
            color = [125, 0, 0]
        else:
            color = [125, 0, 125]

        part_size = parts_data[part_id]["size"]

        if part_data["Rotation"] in (1, 3):
            part_size = (part_size[1], part_size[0])

        # Precompute values
        x_start = int(x * size_factor)
        y_start = int(y * size_factor)
        x_end = int((x + part_size[0]) * size_factor)
        y_end = int((y + part_size[1]) * size_factor)
        
        for i in range(part_size[0]):
            for j in range(part_size[1]):
                cv2.rectangle(img, 
                                (x_start + 1, y_start + 1),
                                (x_end - 1, y_end - 1),
                                color, -1)
        # center of mass calculations
        if(part_data["Rotation"]==0 or part_data["Rotation"]==2):
            center_of_mass_x = part_data["Location"][0] + part_size[0]/2
            center_of_mass_y = part_data["Location"][1] + part_size[1]/2
        elif(part_data["Rotation"]==1 or part_data["Rotation"]==3):
            center_of_mass_x = part_data["Location"][0] + part_size[1]/2
            center_of_mass_y = part_data["Location"][1] + part_size[0]/2
        else:
            print("ERROR: part_rotation not 0,1,2,3")
            
        mass = parts_data[part_id]["mass"]
        x_coord = center_of_mass_x
        y_coord = center_of_mass_y

        total_mass += mass
        sum_x_mass += mass * x_coord
        sum_y_mass += mass * y_coord

    # COM init 
    if total_mass == 0:
            center_of_mass_x = 0
            center_of_mass_y = 0
    else:
            center_of_mass_x = sum_x_mass / total_mass
            center_of_mass_y = sum_y_mass / total_mass

    # Precompute values for COM
    center_of_mass_x_start = int((center_of_mass_x+center_x) * size_factor)
    center_of_mass_y_start = int((center_of_mass_y+center_y) * size_factor)

    # print data COM
    # print('center_of_mass_x: ', center_of_mass_x)
    # print('center_of_mass_y: ', center_of_mass_y)
    # print('total_mass: ', total_mass)

    #add center of mass (as a green circle)
    cv2.circle(
        img, 
        (center_of_mass_x_start, center_of_mass_y_start), 
        square_size, [0,255,0],
        -1
        )
    
    #add center of thrust of each part (as a red circle)
    for part in parts:
        cots=part_center_of_thrust(part)
        if(cots==0):
            continue
        for cot in cots:
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


            # Precompute values for red COT
            redcot_x_start = int((cot[0]+center_x) * size_factor)
            redcot_x_end = int((cot[1]+center_y) * size_factor)
            redcot_y_start = int((end_point[0]+center_x) * size_factor)
            redcot_y_end = int((end_point[1]+center_y) * size_factor)
            
            #instead of drawing a line, draw an arrow
            cv2.arrowedLine(
                img, 
                (redcot_x_start, redcot_x_end), 
                (redcot_y_start, redcot_y_end), 
                [0,0,255], 
                1, 
                tipLength=0.3)

    
    #draw center of thrust of the ship
    ship_orientation = fdir


    for forient in range(7,-1,-1):
        cot = center_of_thrust_vector(parts, forient) # include array of orientation
        
        if(cot!=0):
            # print('cot', cot)
            arrow_thickness=2
            if(forient==ship_orientation):
                arrow_color=[0,240,0]
                # print(cot[5]) ## here thrust power in ship direction
                forward_power = cot[5]
            else:
                arrow_color=[0,255,255]
            
            
        # Precompute values for COT
        cot_x_start = int((cot[0]+center_x) * size_factor)
        cot_x_end = int((cot[1]+center_y) * size_factor)
        cot_y_start = int((cot[2]+center_x) * size_factor)
        cot_y_end = int((cot[3]+center_y) * size_factor)
        cv2.arrowedLine(
            img, 
            (cot_x_start, cot_x_end), # start must be center
            (cot_y_start, cot_y_end), # end
            arrow_color,
            arrow_thickness, 
            tipLength=0.2
            )


    
       
    # Display or save the rotated image as needed
    # cv2.imshow("Image", img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    
    # Convert the OpenCV image to a NumPy array
    img_np = np.asarray(img)

    # Encode the NumPy array as a base64 string
    _, buffer = cv2.imencode('.png', img_np)
    base64_encoded = base64.b64encode(buffer).decode("utf-8")
    
    url_com = upload_image_to_imgbb(base64_encoded)
    # url_com = 'testing'
    
    # print(url_com)
    # return url_com, center_of_mass_x, center_of_mass_y, total_mass
    
    # calculate top speed
    top_speed = calculate_top_speed(forward_power, total_mass)
    
    
    # Create a dictionary with your values
    data = {
        "url_com": url_com,
        "center_of_mass_x": center_of_mass_x,
        "center_of_mass_y": center_of_mass_y,
        "total_mass": total_mass,
        "top_speed": top_speed
    }

    # Convert the dictionary to a JSON string
    json_data = json.dumps(data)

    # Return the JSON string
    return json_data

def calculate_top_speed(power, mass):
    # Game settings
    pups = 30  # Physics updates per second (Hz)
    speedLimit = 600  # Hard coded speed limit (ms⁻¹)
    # Derived constants
    dampingPercent = 40
    # Linear damping per physics update
    dampingPerPU = (1 - (dampingPercent / 100)) ** (1 / pups)
    maxacceleration = power / mass
    maxspeed = min(speedLimit, maxacceleration * dampingPerPU / ((1 - dampingPerPU) * pups))
    
    return maxspeed



def center_of_thrust_vector(parts, ship_direction):
    #calculate the center of thrust vector of the ship in a given direction
    #each part has a center of thrust, calculated by part_center_of_thrust(part)
    #returns a unit vector and the total thrust(originx, originy, endx, endy, thrust) representing the center of thrust vector

    if ship_direction == 0:
        fthruster = [0,3]
    elif ship_direction == 1:
        fthruster = [0]
    elif ship_direction == 2:
        fthruster = [0,1]
    elif ship_direction == 3:
        fthruster = [1]
    elif ship_direction == 4:
        fthruster = [1,2]
    elif ship_direction == 5:
        fthruster = [2]
    elif ship_direction == 6:
        fthruster = [2,3]
    elif ship_direction == 7:
        fthruster = [3]
    
    total_thrust = 0
    total_thrust_direction = 0

    sum_x_cot = 0
    sum_y_cot = 0
    
    sum_x_thrust = 0
    sum_y_thrust = 0

    for part in parts:
        cots=part_center_of_thrust(part)
        if(cots==0):
            continue
        for cot in cots:
            #print("cot", cot)
            # thrust=part_data.thruster_data[part["ID"]]["thrust"]
            thrust = thruster_data[part["ID"]]["thrust"]
            x_coord=cot[0]
            y_coord=cot[1]

            total_thrust += thrust
            if(cot[2] in fthruster):
                total_thrust_direction += thrust

                sum_x_cot += thrust * x_coord
                sum_y_cot += thrust * y_coord
                if(cot[2] == 0):
                    sum_y_thrust -= thrust
                if(cot[2] == 1):
                    sum_x_thrust += thrust
                if(cot[2] == 2):
                    sum_y_thrust += thrust
                if(cot[2] == 3):
                    sum_x_thrust -= thrust

    if(total_thrust_direction==0):
        return 0

    startx = sum_x_cot / total_thrust_direction
    starty = sum_y_cot / total_thrust_direction
    endx = startx+sum_x_thrust / total_thrust *15
    endy = starty+sum_y_thrust / total_thrust *15
    
    # print('total_thrust', total_thrust)
    # print('total_thrust_direction', total_thrust_direction)
    
    return startx, starty, endx, endy, total_thrust_direction/total_thrust, total_thrust_direction

def part_center_of_thrust(part):
    #each part has a center of thrust, relative to its own origin
    #use part_data.thruster_data[part["ID"]][cot] to get the center of thrust relative to the origin
    #the origin is the top left corner
    #some parts don't have a center of thrust, we return 0 for those

    #get part cot
    # part_cots = part_data.thruster_data.get(part["ID"], {"cot":0})["cot"]
    part_cots = thruster_data.get(part["ID"], {"cot":0})["cot"]
    if(part_cots==0):
        return 0

    #some parts have multiple cots, we return a list of all of them

    part_rotation = part["Rotation"]#0,1,2,3
    # part_size = part_data.parts[part["ID"]]["size"]
    part_size = parts_data[part["ID"]]["size"]
    absolute_cots = []
    for part_cot in part_cots:
        #calculate orientation
        orientation = (part_rotation+part_cot[2])%4
        #calculate center of thrust
        if(part_rotation==0):
            center_of_thrust_x = part["Location"][0] + part_cot[0]
            center_of_thrust_y = part["Location"][1] + part_cot[1]
        elif(part_rotation==1):
            center_of_thrust_x = part["Location"][0] - part_cot[1] + part_size[1]
            center_of_thrust_y = part["Location"][1] + part_cot[0]
        elif(part_rotation==2):
            center_of_thrust_x = part["Location"][0] - part_cot[0] + part_size[0]
            center_of_thrust_y = part["Location"][1] - part_cot[1] + part_size[1]
        elif(part_rotation==3):
            center_of_thrust_x = part["Location"][0] + part_cot[1]
            center_of_thrust_y = part["Location"][1] - part_cot[0] + part_size[0]
        else:
            print("ERROR: part_rotation not 0,1,2,3")
        absolute_cots.append((center_of_thrust_x, center_of_thrust_y, orientation))
    return absolute_cots

# test = analyze_ship('https://cdn.discordapp.com/attachments/1142102499273224372/1142222754775564359/discord_botship.ship.png')
# print(test)
