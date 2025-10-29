"""
price generator

usage :

calculate_price(png_url)

"""
from part_data import parts_resources, resource_cost

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
            3: 'mines',
            4: 'thermal_missiles'
        }

    missile_types = []
    try :
        for entry in data.get("PartUIToggleStates", []):
            key = entry.get("Key", [])
            if (
                isinstance(key, list)
                and len(key) == 2
                and isinstance(key[0], dict)
                and key[0].get("ID") == "cosmoteer.missile_launcher"
                and key[1] == "missile_type"
            ):
                missile_types.append(entry.get("Value"))    
    except :
        pass


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
    crew_quarters_large_price = 0

    for item in parts:
        item_id = item['ID']
        if item_id == 'cosmoteer.crew_quarters_small':
            crew_quarters_small_price += 1000
        elif item_id == 'cosmoteer.crew_quarters_med':
            crew_quarters_med_price += 3000
        elif item_id == 'cosmoteer.crew_quarters_large':
            crew_quarters_large_price += 6000

# calculate crew number
    crew = 0
    # print('crew calculte before', crew)
    for item in parts:
        item_id = item['ID']
        if item_id == 'cosmoteer.crew_quarters_small':
            crew += 2
        elif item_id == 'cosmoteer.crew_quarters_med':
            crew += 6
        elif item_id == 'cosmoteer.crew_quarters_large':
            crew += 24
    # print('price crew', crew_quarters_small_price + crew_quarters_med_price)        
    total_price += crew_quarters_small_price + crew_quarters_med_price + crew_quarters_large_price

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
