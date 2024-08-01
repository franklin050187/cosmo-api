"""tool to export ship data from a png or url to a json file"""

import json

import base64
import enum
import gzip
import struct
from io import BytesIO

import numpy as np
from PIL import Image
# from read_ship import get_ship_data
from center_of_mass import draw_ship_only
from png_upload import upload_image_to_imgbb

class OBNodeType(enum.Enum):
    Unset = 0
    Data = 1
    ChildList = 2
    ChildMap = 3
    Link = 4
    Null = 5


class Ship:
    def __init__(self, image_path, json_data) -> None: # take a base64 image and write data to it
        self.image_path = image_path
        self.image = Image.open(BytesIO(base64.b64decode(image_path)))  # read base64 string
        self.image_data = np.array(self.image.getdata())
        self.data = json_data # self.decode()

    def write(self, new_image: Image.Image = None) -> Image.Image:
        self.in_image = self.image_data.copy() # we will generate a new image
        data = self.encode(self.data)
        compressed = gzip.compress(data, 6)
        self.write_bytes(compressed)
        return Image.fromarray(self.in_image.reshape((*self.image.size, 4)).astype(np.uint8))

    def write_bytes(self, in_bytes) -> None:
        in_bytes = len(in_bytes).to_bytes(4, "big") + in_bytes
        for offset, byte in enumerate(in_bytes):
            self.set_byte(offset, byte)

    def set_byte(self, offset, byte) -> None:
        for bits_right in range(8):
            image_offset = offset * 8 + bits_right
            rgb = image_offset % 3
            pixel_offset = (offset * 8 + bits_right) // 3
            mask = (1 << 8) - 2
            bit = (byte >> bits_right) & 1
            self.in_image[pixel_offset][rgb] = (self.in_image[pixel_offset][rgb] & mask) | bit

    def write_varint(self, val, byte_data=None) -> bytearray:
        if byte_data is None:
            byte_data = bytearray()
        if val < 128:
            count = 1
        elif val < 16384:
            count = 2
        elif val < 2097152:
            count = 3
        else:
            count = 4
        val = val << min(count, 3)
        if count == 2:
            val |= 1
        elif count == 3:
            val |= 3
        elif count == 4:
            val |= 7
        for i in range(count):
            byte_data.append((val >> (i * 8)) % 256)
        return byte_data

    def write_string(self, text, byte_data=None) -> bytearray:
        if byte_data is None:
            byte_data = bytearray()
        num = len(text)
        while num >= 0x80:
            byte_data.append(num | 0x80)
            num = num >> 7
        byte_data.append(num)
        byte_data.extend(text.encode("latin1"))
        return byte_data

    def is_2int_list(self, data):
        return isinstance(data, list) and len(data) == 2 and all([isinstance(x, int) for x in data])

    def __str__(self):
        return str(self.data)

    def encode(self, data_node, byte_data: bytearray = None) -> bytearray:
        if byte_data is None:
            byte_data = bytearray()
        if data_node == "Unset":
            byte_data.append(OBNodeType.Unset.value)
            return byte_data
        elif isinstance(data_node, (str, int, float, bool, tuple, bytes)) or self.is_2int_list(
            data_node
        ):
            byte_data.append(OBNodeType.Data.value)
            if isinstance(data_node, str):
                string_data = self.write_string(data_node)
                byte_data = self.write_varint(len(string_data), byte_data)
                byte_data.extend(string_data)
                return byte_data
            elif isinstance(data_node, bool):
                data = bytearray([data_node])
            elif isinstance(data_node, int):
                if data_node < 0:
                    data = struct.pack("<i", data_node)
                else:
                    data = struct.pack("<I", data_node)
            elif isinstance(data_node, float):
                data = struct.pack("<f", data_node)
            elif isinstance(data_node, tuple):
                if len(data_node) == 2:
                    data = struct.pack("<ff", *data_node)
                else:
                    data = bytearray.fromhex("".join(data_node))
            elif isinstance(data_node, list):
                data = struct.pack("<ll", *data_node)
            else:
                data = data_node
            byte_data = self.write_varint(len(data), byte_data)
            byte_data.extend(data)
            return byte_data
        elif isinstance(data_node, list):
            byte_data.append(OBNodeType.ChildList.value)
            byte_data = self.write_varint(len(data_node), byte_data)
            for x in data_node:
                byte_data = self.encode(x, byte_data)
            return byte_data
        elif isinstance(data_node, dict):
            byte_data.append(OBNodeType.ChildMap.value)
            byte_data = self.write_varint(len(data_node), byte_data)
            for key in data_node.keys():
                byte_data = self.write_string(key, byte_data)
                byte_data = self.encode(data_node[key], byte_data)
            return byte_data
        elif data_node is None:
            byte_data.append(OBNodeType.Null.value)
            return byte_data
        else:
            raise TypeError(f"Unknown datatype: {type(data_node)}")

class JSONEncoderWithBytes(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return {"__bytes__": obj.decode("latin1")}
        return json.JSONEncoder.default(self, obj)


def write_ship_png(ship_data):
    """
    Generate a PNG image of a ship based on the given ship data.

    Parameters:
        ship_data (dict): A dictionary containing the ship data, including the 'Parts'
        key with a list of ship parts.

    Returns:
        str: The URL of the generated ship image uploaded to imgbb.
    """
    ship_parts = ship_data['Parts']
    base64_image = draw_ship_only(ship_parts)
    
    tuple_data = ["RoofBaseColor", "RoofDecalColor1", "RoofDecalColor2", "RoofDecalColor3"]
    for key, value in ship_data.items():
        if key in tuple_data:
            if isinstance(value, list):
                ship_data[key] = tuple(value)
    if "Roles" in ship_data:
        for role in ship_data["Roles"]:
            if "Color" in role and isinstance(role["Color"], list):
                role["Color"] = tuple(role["Color"])
    if "WeaponShipRelativeTargets" in ship_data:
        for WeaponShipRelativeTargets in ship_data["WeaponShipRelativeTargets"]:
            if "Value" in WeaponShipRelativeTargets and isinstance(
                WeaponShipRelativeTargets["Value"], list
            ):
                WeaponShipRelativeTargets["Value"] = tuple(WeaponShipRelativeTargets["Value"])
    
    new_image = Ship(base64_image, ship_data).write()
    buffered = BytesIO()
    new_image.save(buffered, format="PNG")
    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
    url_new_ship = upload_image_to_imgbb(base64_image)
    return url_new_ship
