# Copyright 2023 GameDungeon

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use,  
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
# is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE 
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# modified by LunastroD (I made this a library and removed the dependency on json because I'm reading the data directly)


import base64
import enum
import gzip
import io
import re
import struct
from io import BytesIO

import numpy as np
import requests
from PIL import Image

SHIP="ships\Sion.ship.png"
JSON_ON=0
if(JSON_ON):
    import json

class OBNodeType(enum.Enum):
    Unset = 0
    Data = 1
    ChildList = 2
    ChildMap = 3
    Link = 4
    Null = 5

class Ship():
    def __init__(self, image_path) -> None:
        self.image_path = image_path
        
        # read image, base64 image or url
        input_type = check_input_type(image_path)
        # print(input_type)
        if input_type == "base64":
            self.image = Image.open(BytesIO(base64.b64decode(image_path))) # read base64 string
        elif input_type == "file_path":
            self.image = Image.open(image_path)
        elif input_type == "url":
            response = requests.get(image_path)
            self.image = Image.open(BytesIO(response.content))
        
        self.image_data = np.array(self.image.getdata())

        self.compressed_image_data = self.read_bytes()
        
        if self.compressed_image_data[:9] == b'COSMOSHIP':
            self.compressed_image_data = self.compressed_image_data[9:]
            self.version = 2
            
        self.raw_data=gzip.decompress(self.compressed_image_data)
        self.buffer = io.BytesIO(gzip.decompress(self.compressed_image_data))
        self.data = self.decode()

    def write(self, new_image: Image.Image = None) -> Image.Image:
        if new_image is None:
            self.in_image = self.image_data.copy()
        else:
            self.in_image = np.array(new_image.getdata())

        data = self.encode(self.data)
        compressed = gzip.compress(data, 6)

        if self.version == 2:
            b_compressed = bytearray(b'COSMOSHIP')
            b_compressed.extend(compressed)
            compressed = bytes(b_compressed)

        self.write_bytes(compressed)
        return Image.fromarray(self.in_image.reshape((*self.image.size, 4)).astype(np.uint8))


    def read_bytes(self) -> bytes:
        data = [byte for pixel in self.image_data for byte in pixel[:3]]
        length = int.from_bytes(bytes([self.get_byte(i, data) for i in range(4)]), "big")
        return bytes([self.get_byte(i + 4, data) for i in range(length)])

    def get_byte(self, offset, data) -> int:
        out_byte = 0
        for bits_right in range(8):
            out_byte |= (data[offset * 8 + bits_right] & 1) << bits_right
        return out_byte

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

        val = val << min(count, 3);
        
        if count == 2:
            val |= 1;
        elif count == 3:
            val |= 3;
        elif count ==  4:
            val |= 7;

        for i in range(count):
            byte_data.append((val >> (i * 8)) % 256)
        
        return byte_data

    def read_string(self, file: bytearray) -> str: 
        length = 0
        i = 0
        while True:
            byte = file.read(1)[0]
            length |= (byte & 0x7F) << (i * 7)
            if byte & 0x80 == 0:
                break
            if i>2:
                # print("Warning: string length is too long")
                break
            i += 1

        data = file.read(length)
        data = data.decode('latin1')

        return data

    def write_string(self, text, byte_data=None) -> bytearray:
        if byte_data is None:
            byte_data = bytearray()

        num = len(text)
        while (num >= 0x80):
            byte_data.append(num | 0x80)
            num = num >> 7
        
        byte_data.append(num)
        byte_data.extend(text.encode('latin1'))
        return byte_data       

    def is_2int_list(self, data):
        return isinstance(data, list) and len(data) == 2 and all([isinstance(x, int) for x in data])

    def decode(self):
        _type = self.buffer.read(1)[0]
        if _type == OBNodeType.Unset.value:
            return "Unset"

        elif _type == OBNodeType.Data.value:
            size = self.read_varint(self.buffer)
            return self.buffer.read(size)

        elif _type == OBNodeType.ChildList.value:
            count = self.read_varint(self.buffer)
            lst = []
            for _ in range(count):
                elem = self.decode()
                lst.append(elem)
            return lst

        elif _type == OBNodeType.ChildMap.value:
            count = self.read_varint(self.buffer)
            d = {}
            for _ in range(count):
                key = self.read_string(self.buffer)
                value = self.decode()
                if isinstance(value, bytes):
                    if (
                        key in ('Rotation', 'Orientation', 'Version', 'FlightDirection', 'FormationOrder', 'Key', 'Max', 'Min', "ID")
                        and len(value) == 4
                    ):
                        value = struct.unpack('<i', value)[0]
                    elif key == 'DefaultAttackRotation':
                        value = struct.unpack('<f', value)[0]
                        # print(self.image_path)
                        # print('DefaultAttackRotation: ', value)
                    elif key == 'DefaultAttackRadius':
                        value = struct.unpack('<I', value)[0]
                        # print('DefaultAttackRadius: ', value)
                    elif key == 'Value' and len(value) == 4:
                        value = struct.unpack('<I', value)[0]
                    elif key in ('Location', 'Cell', "Key") and len(value) == 8:
                        value = list(struct.unpack('<ll', value))
                    elif key in ('FlipX', 'FlipY', "Value") and len(value) == 1:
                        value = bool(value[0])
                    elif key in ('ID', 'Name', 'Author', 'RoofBaseTexture', 'ShipRulesID', 'Description', 'ComponentID', 'PartID', 'IDString', "Value"):
                        value = self.read_string(io.BytesIO(value))
                    elif key in ('Color', 'RoofBaseColor', 'RoofDecalColor1', 'RoofDecalColor2', 'RoofDecalColor3', 'CrewUniformColor') and len(value) == 16:
                        c1 = value[0:4].hex().upper()
                        c2 = value[4:8].hex().upper()
                        c3 = value[8:12].hex().upper()
                        c4 = value[12:16].hex().upper()
                        value = (c1, c2, c3, c4)
                    else:
                        # print('Unhandled key with binary value:', {key: value})
                        continue

                d[key] = value
            return d
        elif _type == OBNodeType.Link.value:
            subtype = self.buffer.read(1)[0]
            if subtype == 255:
                _id = self.read_varint(self.buffer)
                return {'_type': 'link', '_id': _id}
            elif subtype == 254:
                return None
        if _type == OBNodeType.Null.value:
            return None
        else:
            raise TypeError(f'Unexpected type {_type}')

    def encode(self, data_node, byte_data: bytearray=None) -> bytearray:
        if byte_data is None:
            byte_data = bytearray()

        if data_node == "Unset":
            byte_data.append(OBNodeType.Unset.value)
            return byte_data
        
        elif isinstance(data_node, (str, int, float, bool, tuple, bytes)) or self.is_2int_list(data_node):
            byte_data.append(OBNodeType.Data.value)
            
            if isinstance(data_node, str):
                string_data = self.write_string(data_node)
                byte_data = self.write_varint(len(string_data), byte_data)
                byte_data.extend(string_data)
                return byte_data
            elif isinstance(data_node, bool):
                data = bytearray([data_node])
            elif isinstance(data_node, int):
                data = struct.pack("<i", data_node)
            elif isinstance(data_node, float):
                data = struct.pack("<f", data_node)
            elif isinstance(data_node, tuple):
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

if(JSON_ON):
    class JSONEncoderWithBytes(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, bytes):
                # any bytes that could not be decoded, will be decoded using latin1 and then
                # wrapped in a special dictionary:
                return {'__bytes__': obj.decode('latin1')}
            return json.JSONEncoder.default(self, obj)
def check_input_type(input_value):
    # Check if it's a valid base64 string
    try:
        if base64.b64encode(base64.b64decode(input_value)) == input_value.encode():
            return "base64"
    except Exception:
        pass

    # Check if it's a valid file path (assuming it's on your server)
    if re.match(r'^[A-Za-z0-9_./-]*$', input_value):
        return "file_path"

    # Check if it's a valid URL
    # print(input_value)
    url_pattern = re.compile(r'^https?://\S+$')
    if url_pattern.match(input_value):
    # url_pattern = re.compile(r'^https?://\S+$')
    # if url_pattern.match(input_value):
        return "url"

    # If none of the above, return "unknown"
    return "unknown"


def test_ship(url1, url2):
    """ compare ship from url1 with ship from url2, print out the differences """
    # input_filename = "https://i.ibb.co/fMmCwKs/1b39bdff0418.png" # mod
    input_filename = url2
    test_data2 = Ship(input_filename)
    # input_filename2 = "https://i.ibb.co/vcttfZT/f9cfc51fd56f.png" # org
    input_filename2 = url1
    test_data = Ship(input_filename2)

    print(test_data.raw_data==test_data2.raw_data)
    #print the data around the first difference in hex
    for i in range(len(test_data.raw_data)):
        if test_data.raw_data[i]!=test_data2.raw_data[i]:
            #print(my_ship1.raw_data[i-100:i+100])
            #print the bytes separated by spaces but if the byte is a character, print the character
            print(" ".join([chr(x) if x>=32 and x<=126 else hex(x) for x in test_data.raw_data[i-100:i+50]]))
            #print(" ".join([hex(x) for x in my_ship1.raw_data[i-100:i+50]]))
            print("===================================")
            print(" ".join([chr(x) if x>=32 and x<=126 else hex(x) for x in test_data2.raw_data[i-100:i+50]]))
            #print(" ".join([hex(x) for x in my_ship2.raw_data[i-10:i+50]]))
            break

    print(test_data.data==test_data2.data)
    #print all of the differences
    for key in test_data.data.keys():
        if test_data.data[key]!=test_data2.data[key]:
            print(key)
            print(test_data.data[key])
            print("===================================")
            print(test_data2.data[key])
            print()