# get price for a ship including storage, excluding preload gun 
# usage : calculate_price(png_url)

# from cosmoteer_save_tools import decode_ship_data
# import json

parts_resources = [
    {"ID": "cosmoteer.airlock", "Resources": [["steel", "8"], ["coil", "4"]]},
    {"ID": "cosmoteer.armor", "Resources": [["steel", "8"]]},
    {"ID": "cosmoteer.armor_1x2_wedge", "Resources": [["steel", "8"]]},
    {"ID": "cosmoteer.armor_1x3_wedge", "Resources": [["steel", "12"]]},
    {"ID": "cosmoteer.armor_2x1", "Resources": [["steel", "16"]]},
    {"ID": "cosmoteer.armor_structure_hybrid_1x1", "Resources": [["steel", "5"]]},
    {"ID": "cosmoteer.armor_structure_hybrid_1x2", "Resources": [["steel", "10"]]},
    {"ID": "cosmoteer.armor_structure_hybrid_1x3", "Resources": [["steel", "15"]]},
    {"ID": "cosmoteer.armor_structure_hybrid_tri", "Resources": [["steel", "3"]]},
    {"ID": "cosmoteer.armor_tri", "Resources": [["steel", "2"]]},
    {"ID": "cosmoteer.armor_wedge", "Resources": [["steel", "4"]]},
    {"ID": "cosmoteer.cannon_deck","Resources": [["steel", "200"], ["coil2", "30"], ["tristeel", "30"], ["bullet", "100"]]},
    {"ID": "cosmoteer.cannon_large", "Resources": [["steel", "84"], ["coil", "29"], ["bullet", "64"]]},
    {"ID": "cosmoteer.cannon_med", "Resources": [["steel", "48"], ["coil", "8"], ["bullet", "16"]]},
    {"ID": "cosmoteer.control_room_large","Resources": [["steel", "160"], ["coil2", "70"], ["processor", "10"]]},
    {"ID": "cosmoteer.control_room_med","Resources": [["steel", "80"], ["coil2", "35"], ["processor", "5"]]},
    {"ID": "cosmoteer.control_room_small","Resources": [["steel", "32"], ["coil2", "14"], ["processor", "2"]]},
    {"ID": "cosmoteer.conveyor", "Resources": [["steel", "4"], ["coil", "1"]]},
    {"ID": "cosmoteer.corridor", "Resources": [["steel", "4"]]},
    {"ID": "cosmoteer.crew_quarters_med", "Resources": [["steel", "48"]]},
    {"ID": "cosmoteer.crew_quarters_small", "Resources": [["steel", "24"]]},
    {"ID": "cosmoteer.disruptor", "Resources": [["steel", "40"], ["coil", "20"]]},
    {"ID": "cosmoteer.door", "Resources": [["coil", "1"]]},
    {"ID": "cosmoteer.engine_room","Resources": [["steel", "72"], ["coil2", "28"], ["tristeel", "9"]]},
    {"ID": "cosmoteer.explosive_charge","Resources": [["steel", "16"], ["coil", "4"], ["sulfur", "10"]]},
    {"ID": "cosmoteer.factory_ammo","Resources": [["steel", "32"], ["coil", "24"], ["tristeel", "4"], ["sulfur", "5"]]},
    {"ID": "cosmoteer.factory_coil","Resources": [["steel", "80"], ["coil", "80"], ["processor", "8"], ["copper", "10"]]},
    {"ID": "cosmoteer.factory_coil2","Resources": [["steel", "104"], ["coil2", "58"], ["processor", "12"], ["copper", "10"], ["coil", "40"] ]},
    {"ID": "cosmoteer.factory_diamond","Resources": [["steel", "48"], ["coil2", "118"], ["tristeel", "67"], ["carbon", "20"]]},
    {"ID": "cosmoteer.factory_emp","Resources": [["steel", "96"], ["coil2", "32"], ["diamond", "2"], ["iron", "5"], ["copper", "5"]]},
    {"ID": "cosmoteer.factory_he","Resources": [["steel", "76"], ["coil2", "27"], ["processor", "2"], ["iron", "5"], ["sulfur", "5"]]},
    {"ID": "cosmoteer.factory_mine","Resources": [["steel", "96"], ["coil2", "50"], ["tristeel", "13"], ["iron", "5"], ["bullet", "20"]]},
    {"ID": "cosmoteer.factory_nuke","Resources": [["steel", "136"], ["coil2", "62"], ["enriched_uranium", "4"], ["iron", "5"], ["uranium", "5"]]},
    {"ID": "cosmoteer.factory_processor","Resources": [["steel", "80"], ["coil2", "100"], ["diamond", "12"], ["coil", "40"], ["gold", "10"]]},
    {"ID": "cosmoteer.factory_steel","Resources": [["steel", "120"], ["coil", "90"], ["coil2", "60"], ["iron", "20"]]},
    {"ID": "cosmoteer.factory_tristeel","Resources": [["steel", "120"], ["coil2", "100"], ["diamond", "8"], ["tritanium", "20"]]},
    {"ID": "cosmoteer.factory_uranium","Resources": [["steel", "80"], ["coil2", "80"], ["enriched_uranium", "32"], ["uranium", "20"]]},
    {"ID": "cosmoteer.fire_extinguisher", "Resources": [["steel", "8"], ["coil", "1"]]},
    {"ID": "cosmoteer.flak_cannon_large","Resources": [["steel", "200"], ["coil2", "30"], ["bullet", "92"]]},
    {"ID": "cosmoteer.hyperdrive_beacon","Resources": [["steel", "160"], ["coil2", "40"], ["diamond", "6"]]},
    {"ID": "cosmoteer.hyperdrive_small","Resources": [["steel", "40"], ["coil2", "30"]]},
    {"ID": "cosmoteer.ion_beam_emitter","Resources": [["steel", "60"], ["coil2", "15"], ["diamond", "1"]]},
    {"ID": "cosmoteer.ion_beam_prism","Resources": [["steel", "16"], ["coil2", "2"], ["diamond", "1"]]},
    {"ID": "cosmoteer.laser_blaster_large","Resources": [["steel", "96"], ["coil", "36"]]},
    {"ID": "cosmoteer.laser_blaster_small","Resources": [["steel", "32"], ["coil", "12"]]},
    {"ID": "cosmoteer.mining_laser_small","Resources": [["steel", "96"], ["coil", "36"]]},
    {"ID": "cosmoteer.missile_launcher","Resources": [["steel", "60"], ["coil2", "20"], ["processor", "1"]]},
    {"ID": "cosmoteer.point_defense", "Resources": [["steel", "8"], ["coil", "8"]]},
    {"ID": "cosmoteer.power_storage", "Resources": [["steel", "32"], ["coil", "32"]]},
    {"ID": "cosmoteer.railgun_accelerator","Resources": [["steel", "76"], ["coil2", "12"], ["tristeel", "10"]]},
    {"ID": "cosmoteer.railgun_launcher","Resources": [["steel", "100"], ["coil2", "10"], ["tristeel", "10"]]},
    {"ID": "cosmoteer.railgun_loader","Resources": [["steel", "60"], ["coil2", "30"], ["tristeel", "10"], ["bullet", "46"]]},
    {"ID": "cosmoteer.reactor_large","Resources": [["steel", "120"], ["coil2", "80"], ["enriched_uranium", "24"]]},
    {"ID": "cosmoteer.reactor_med","Resources": [["steel", "72"], ["coil2", "54"], ["enriched_uranium", "16"]]},
    {"ID": "cosmoteer.reactor_small","Resources": [["steel", "32"], ["coil", "82"], ["enriched_uranium", "8"]]},
    {"ID": "cosmoteer.roof_headlight", "Resources": [["steel", "4"], ["coil", "2"]]},
    {"ID": "cosmoteer.roof_light", "Resources": [["steel", "4"], ["coil", "1"]]},
    {"ID": "cosmoteer.sensor_array","Resources": [["steel", "76"], ["coil2", "27"], ["processor", "4"]]},
    {"ID": "cosmoteer.shield_gen_large","Resources": [["steel", "120"], ["coil2", "30"], ["diamond", "2"]]},
    {"ID": "cosmoteer.shield_gen_small","Resources": [["steel", "40"], ["coil", "40"]]},
    {"ID": "cosmoteer.storage_2x2", "Resources": [["steel", "48"]]},
    {"ID": "cosmoteer.storage_3x2", "Resources": [["steel", "72"]]},
    {"ID": "cosmoteer.storage_3x3", "Resources": [["steel", "108"]]},
    {"ID": "cosmoteer.storage_4x3", "Resources": [["steel", "144"]]},
    {"ID": "cosmoteer.storage_4x4", "Resources": [["steel", "192"]]},
    {"ID": "cosmoteer.structure", "Resources": [["steel", "2"]]},
    {"ID": "cosmoteer.structure_1x2_wedge", "Resources": [["steel", "2"]]},
    {"ID": "cosmoteer.structure_1x3_wedge", "Resources": [["steel", "3"]]},
    {"ID": "cosmoteer.structure_tri", "Resources": [["steel", "1"]]},
    {"ID": "cosmoteer.structure_wedge", "Resources": [["steel", "1"]]},
    {"ID": "cosmoteer.thruster_boost","Resources": [["steel", "56"], ["coil2", "10"], ["tristeel", "8"]]},
    {"ID": "cosmoteer.thruster_huge","Resources": [["steel", "80"], ["coil2", "20"], ["tristeel", "10"]]},
    {"ID": "cosmoteer.thruster_large", "Resources": [["steel", "40"], ["coil2", "10"]]},
    {"ID": "cosmoteer.thruster_med", "Resources": [["steel", "24"], ["coil", "9"]]},
    {"ID": "cosmoteer.thruster_small", "Resources": [["steel", "8"], ["coil", "3"]]},
    {"ID": "cosmoteer.thruster_small_2way","Resources": [["steel", "12"], ["coil", "7"]]},
    {"ID": "cosmoteer.thruster_small_3way","Resources": [["steel", "16"], ["coil", "11"]]},
    {"ID": "cosmoteer.tractor_beam_emitter","Resources": [["steel", "200"], ["coil2", "50"], ["diamond", "5"]]},
    {"ID": "he_missiles","Resources": [["missile_part_he", "12"]]},
    {"ID": "nukes","Resources": [["missile_part_nuke", "12"]]},
    {"ID": "mines","Resources": [["mine_part", "24"]]},
    {"ID": "emp_missiles","Resources": [["missile_part_emp", "9"]]},
]

resource_cost = [{'ID': 'bullet', 'BuyPrice': 4, 'MaxStackSize': 20}, {'ID': 'carbon', 'BuyPrice': 160, 'MaxStackSize': 5}, {'ID': 'coil', 'BuyPrice': 100, 'MaxStackSize': 20}, {'ID': 'coil2', 'BuyPrice': 300, 'MaxStackSize': 20}, {'ID': 'copper', 'BuyPrice': 80, 'MaxStackSize': 5}, {'ID': 'diamond', 'BuyPrice': 4000, 'MaxStackSize': 5}, {'ID': 'enriched_uranium', 'BuyPrice': 2000, 'MaxStackSize': 10}, {'ID': 'gold', 'BuyPrice': 500, 'MaxStackSize': 5}, {'ID': 'hyperium', 'BuyPrice': 50, 'MaxStackSize': 20}, {'ID': 'iron', 'BuyPrice': 20, 'MaxStackSize': 5}, {'ID': 'mine_part', 'BuyPrice': 52, 'MaxStackSize': 8}, {'ID': 'missile_part_emp', 'BuyPrice': 20, 'MaxStackSize': 10}, {'ID': 'missile_part_he', 'BuyPrice': 8, 'MaxStackSize': 10}, {'ID': 'missile_part_nuke', 'BuyPrice': 36, 'MaxStackSize': 10}, {'ID': 'processor', 'BuyPrice': 2500, 'MaxStackSize': 5}, {'ID': 'steel', 'BuyPrice': 25, 'MaxStackSize': 20}, {'ID': 'sulfur', 'BuyPrice': 20, 'MaxStackSize': 5}, {'ID': 'tristeel', 'BuyPrice': 200, 'MaxStackSize': 20}, {'ID': 'tritanium', 'BuyPrice': 160, 'MaxStackSize': 5}, {'ID': 'uranium', 'BuyPrice': 400, 'MaxStackSize': 5}]


# def calculate_price(png_url): ## take json instead of png
def calculate_price(data_json): ## take json instead of png
    # json_data = decode_ship_data(png_url)
    # data = json.loads(json_data)
    data = data_json
    parts = data["Parts"]
    doors = data["Doors"]
    # toggle = data["PartUIToggleStates"]
    
    # need missile type to calculate cost of the ammo
    missile_mapping = {
            0: 'he_missiles',
            1: 'emp_missiles',
            2: 'nukes',
            3: 'mines'
        }
    # list of missile types "__bytes__": "\fmissile_type"
    missile_types = []
    # for item in toggle:
    #     try:
    #         if '__bytes__' in item['Key'][1] and item['Key'][1]['__bytes__'] == '\x0cmissile_type':
    #             missile_types.append(item['Value'])
    #     except:
    #         continue
    try :
        missile_types = [entry["Value"] for entry in data["PartUIToggleStates"] if entry["Key"][0]["ID"] == "cosmoteer.missile_launcher" and entry["Key"][1] == "DG1pc3NpbGVfdHlwZQ=="]
    except :
        pass
    # print(missile_types)
    # # Print the values
    # for value in values:
    # init the data
    mapped_output = [] # missile type and number
    for item in missile_types:
        if item in missile_mapping:
            mapped_output.append(missile_mapping[item])

    try:
        storage = data["NewFlexResourceGridTypes"]
    except KeyError:
        storage = None
    
    # calculate price for parts
    total_price = 0

    for item in parts:
        item_id = item['ID']
        resources = None

        for part in parts_resources:
            if part['ID'] == item_id:
                resources = part['Resources']
                break

        if resources:
            item_price = 0
            for resource in resources:
                resource_id = resource[0]
                resource_quantity = int(resource[1])

                for cost in resource_cost:
                    if cost['ID'] == resource_id:
                        resource_price = cost['BuyPrice']
                        item_price += resource_price * resource_quantity
                        break

            # print(f"Price for {item_id}: {item_price}")
            total_price += item_price
            # print('price parts', item_price)
    # add missile prices
    for item in mapped_output:
        item_id = item
        resources = None
        for part in parts_resources:
            if part['ID'] == item_id:
                resources = part['Resources']
                break
        if resources:
            item_price = 0
            for resource in resources:
                resource_id = resource[0]
                resource_quantity = int(resource[1])
                for cost in resource_cost:
                    if cost['ID'] == resource_id:
                        resource_price = cost['BuyPrice']
                        item_price += resource_price * resource_quantity
                        break
            total_price += item_price
            # print('price missiles', item_price)
    # Calculate the price for doors
    door_price = 0
    if doors is not None and isinstance(doors, list):
        for door in doors:
            door_id = door['ID']
            for part in parts_resources:
                if part['ID'] == door_id:
                    resources = part['Resources']
                    break

            if resources:
                for resource in resources:
                    resource_id = resource[0]
                    resource_quantity = int(resource[1])

                    for cost in resource_cost:
                        if cost['ID'] == resource_id:
                            resource_price = cost['BuyPrice']
                            door_price += resource_price * resource_quantity
                            break

    # print(f"Price for doors: {door_price}")
    total_price += door_price
    
        # Calculate the price for crew quarters
    crew_quarters_small_price = 0
    crew_quarters_med_price = 0

    for item in parts:
        item_id = item['ID']
        if item_id == 'cosmoteer.crew_quarters_small':
            crew_quarters_small_price += 1000
        elif item_id == 'cosmoteer.crew_quarters_med':
            crew_quarters_med_price += 3000

# calculate crew number
    crew = 0
    # print('crew calculte before', crew)
    for item in parts:
        item_id = item['ID']
        if item_id == 'cosmoteer.crew_quarters_small':
            crew += 2
        elif item_id == 'cosmoteer.crew_quarters_med':
            crew += 6
    # print('price crew', crew_quarters_small_price + crew_quarters_med_price)        
    total_price += crew_quarters_small_price + crew_quarters_med_price

    # Calculate the price for storage
    storage_price = 0
    if storage is not None:
        for item in storage:
            if 'Value' in item:
                resource_id = item['Value']
                for cost in resource_cost:
                    if cost['ID'] == resource_id:
                        resource_price = cost['BuyPrice']
                        max_stack = cost['MaxStackSize']
                        storage_price += resource_price * max_stack
    # print('price storage', storage_price)
    total_price += storage_price

    return total_price, crew