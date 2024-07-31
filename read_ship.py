"""tool to export ship data from a png or url to a json file"""

import json
import enum
import gzip
import io
import re
import struct
from io import BytesIO

import numpy as np
import requests
from PIL import Image

class OBNodeType(enum.Enum):
    Unset = 0
    Data = 1
    ChildList = 2
    ChildMap = 3
    Link = 4
    Null = 5


class Ship:
    def __init__(self, image_path) -> None:
        self.image_path = image_path
        input_type = check_input_type(image_path)
        if input_type == "url":
            response = requests.get(image_path, timeout=180)
            self.image = Image.open(BytesIO(response.content))
        else:
            raise ValueError("Invalid input type")
        # self.image = Image.open(image_path)
        self.image_data = np.array(self.image.getdata())
        self.compressed_image_data = self.read_bytes()
        if self.compressed_image_data[:9] == b"COSMOSHIP":
            self.compressed_image_data = self.compressed_image_data[9:]
            self.version = 2
        self.raw_data = gzip.decompress(self.compressed_image_data)
        self.buffer = io.BytesIO(self.raw_data)
        self.data = self.decode()

    def read_bytes(self) -> bytes:
        data = []
        for pixel in self.image_data:
            for byte in pixel[:3]:
                data.append(byte)
        length_bytes = []
        for i in range(4):
            byte = self.get_byte(i, data)
            length_bytes.append(byte)
        length_bytes_str = bytes(length_bytes)
        length = int.from_bytes(length_bytes_str, byteorder="big")
        result = bytearray()
        for i in range(length):
            byte = self.get_byte(i + 4, data)
            result.append(byte)
        return bytes(result)

    def get_byte(self, offset, data) -> int:
        out_byte = 0
        for bits_right in range(8):
            out_byte |= (data[offset * 8 + bits_right] & 1) << bits_right
        return out_byte

    def read_varint(self, file: io.BytesIO) -> int:
        byte = file.read(1)[0]
        count = 1
        if byte & 1 != 0:
            count += 1
            if byte & 2 != 0:
                count += 1
                if byte & 4 != 0:
                    count += 1
        for i in range(1, count):
            byte |= file.read(1)[0] << (i * 8)
        return byte >> min(count, 3)

    def read_string(self, file: bytearray) -> str:
        length = 0
        i = 0
        while True:
            byte = file.read(1)[0]
            length |= (byte & 0x7F) << (i * 7)
            if byte & 0x80 == 0:
                break
            if i > 2:
                print("Warning: string length is too long")
                break
            i += 1
        data = file.read(length)
        data = data.decode("latin1")
        return data

    def decode(self):
        _type = self.buffer.read(1)[0]
        if _type == OBNodeType.Unset.value:
            return "Unset"
        if _type == OBNodeType.Data.value:
            size = self.read_varint(self.buffer)
            return self.buffer.read(size)
        if _type == OBNodeType.ChildList.value:
            count = self.read_varint(self.buffer)
            lst = []
            for _ in range(count):
                elem = self.decode()
                if isinstance(elem, bytes):
                    elem = elem.decode("latin1")  # if byte decode it again
                try:
                    unicode_control_char_pattern = re.compile(r"[\x00-\x1F\x7F-\x9F]+")
                    elem = unicode_control_char_pattern.sub("", elem)
                except:
                    pass
                lst.append(elem)
            return lst
        if _type == OBNodeType.ChildMap.value:
            count = self.read_varint(self.buffer)
            d = {}
            for _ in range(count):
                key = self.read_string(self.buffer)
                value = self.decode()
                if isinstance(value, bytes):
                    if (
                        key
                        in (
                            "Rotation",
                            "Orientation",
                            "Version",
                            "FlightDirection",
                            "FormationOrder",
                            "Key",
                            "Max",
                            "Min",
                            "ID",
                            "BuildMirrorAxis",
                            "PaintMirrorAxis",
                            "AssignmentPriority",
                        )  # add AssignmentPriority
                        and len(value) == 4
                    ):
                        value = struct.unpack("<i", value)[0]
                    elif key == "DefaultAttackRotation":
                        value = struct.unpack("<f", value)[0]
                    elif key == "DefaultAttackRadius":
                        value = struct.unpack("<I", value)[0]
                    elif key == "Value" and len(value) == 4:
                        value = struct.unpack("<I", value)[0]
                    elif key in ("Location", "Cell", "Key") and len(value) == 8:
                        value = list(struct.unpack("<ll", value))
                    elif (
                        key
                        in (
                            "FlipX",
                            "FlipY",
                            "Value",
                            "BuildMirrorEnabled",
                            "PaintMirrorEnabled",
                            "AutoFillFromLower",
                        )
                        and len(value) == 1
                    ):  # add AutoFillFromLower
                        value = bool(value[0])
                    elif key == "Value" and len(value) == 8:  # ion aim data
                        x, y = struct.unpack("<ff", value)
                        value = (x, y)
                    elif key in (
                        "ID",
                        "Name",
                        "Author",
                        "RoofBaseTexture",
                        "ShipRulesID",
                        "Description",
                        "ComponentID",
                        "PartID",
                        "IDString",
                        "Value",
                    ):
                        value = self.read_string(io.BytesIO(value))
                    elif (
                        key
                        in (
                            "Color",
                            "RoofBaseColor",
                            "RoofDecalColor1",
                            "RoofDecalColor2",
                            "RoofDecalColor3",
                            "CrewUniformColor",
                        )
                        and len(value) == 16
                    ):
                        c1 = value[0:4].hex().upper()
                        c2 = value[4:8].hex().upper()
                        c3 = value[8:12].hex().upper()
                        c4 = value[12:16].hex().upper()
                        value = (c1, c2, c3, c4)
                    else:
                        print("Unhandled key with binary value:", {key: value})
                        continue
                d[key] = value
            return d
        if _type == OBNodeType.Link.value:
            subtype = self.buffer.read(1)[0]
            if subtype == 255:
                _id = self.read_varint(self.buffer)
                return {"_type": "link", "_id": _id}
            if subtype == 254:
                return None
        if _type == OBNodeType.Null.value:
            return None
        raise TypeError(f"Unexpected type {_type}")

def get_ship_data(url):
    ship_data = Ship(url).data
    return ship_data

class JSONEncoderWithBytes(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return {'__bytes__': obj.decode('latin1')}
        return json.JSONEncoder.default(self, obj)

def check_input_type(input_value):
    url_pattern = re.compile(r'^https?://\S+$')
    if url_pattern.match(input_value):
        return "url"
    return "unknown"

# test_data = get_ship_data("https://i.ibb.co/vcttfZT/f9cfc51fd56f.png")
# print(test_data)
# print(type(test_data))
