#!/usr/bin/env python3

"""
flstweak.py 2.0 - Parse, replace, and extract data from Winner Micro .fls firmware files.

Run flstweak.py with the .fls firmware filename to view information about the
file. Run flstweak.py -h to view help and all options.

The .fls file can contain multiple images, each with a header specifying
image properties and a checksum for both the image and the header itself.

Image data replacement
---------------------------------------
The --replace option allows for image data replacement by specifying a reference
file (suffix: ref.bin) containing the image data to match or a directory containing
multiple reference files. Each reference file should have a corresponding modified
file (suffix: mod.bin) with the replacement data.

If the reference data is found, it will be replaced with the modified data and the
header will be updated with the new image checksum and header checksum.

By default, the modified firmware will be written as filename_mod and can be
customized with the --output option.

Note that data replacement is currently not supported for W60x-series firmware.

Image extraction
---------------------------------------
The images can also be extracted to individual files for analysis with the
--extract option. Each image will be written as filename_imageX, with X as
the image number.

References
---------------------------------------
https://doc.winnermicro.net/w800/en/latest/component_guides/firmware_format.html
http://www.winnermicro.com/en/upload/1/editor/1559640549130.pdf

"""

import struct
import binascii
import sys
import os
import argparse

MAGIC_WORD = 0xA0FFFF9F
HEADER_SIZE_W80X = 64
HEADER_SIZE_W60X = 56
W60X_HEADER_PADDING = 200
W60X_HEADER_PADDING_CRC = 0x947D8E12
VERSION = str(2.0)


def crc32(data):
    return (~binascii.crc32(data) & 0xFFFFFFFF)  # CRC-32/JAMCRC format


def detect_firmware_type(file):
    original_position = file.tell()
    file.seek(0)
    header_data = file.read(HEADER_SIZE_W80X)
    if len(header_data) < HEADER_SIZE_W60X:
        raise ValueError("[Error] Invalid header, wrong size")

    test_crc32 = struct.unpack("<I", header_data[52:56])[0]
    data_crc32 = crc32(header_data[:52])

    file.seek(original_position)
    if data_crc32 == test_crc32:
        return "W60x"
    elif len(header_data) >= HEADER_SIZE_W80X:
        return "W80x"
    else:
        raise ValueError("[Error] Unknown firmware type or corrupted header.")


def validate_header(header, header_size, hd_checksum):
    data_size = header_size - 4
    checksum = crc32(header[:data_size])
    if checksum != hd_checksum:
        raise ValueError(f"  [Error] Invalid header, checksum verification failed (expected 0x{hd_checksum:08X}, actual 0x{checksum:08X})")
    return True


def replace_data(body, ref_data, mod_data):
    ref_index = body.find(ref_data)
    if ref_index == -1:
        return body, False
    return body[:ref_index] + mod_data + body[ref_index + len(ref_data):], True


def parse_img_attr(img_attr, firmware_type):
    img_type = img_attr & 0xF                # Bits 0-3
    code_encrypt = (img_attr >> 4) & 0x1     # Bit 4
    prikey_sel = (img_attr >> 5) & 0x7       # Bits 5-7
    signature = (img_attr >> 8) & 0x1        # Bit 8
    reserved1 = (img_attr >> 9) & 0x7F       # Bits 9-15
    gzip_enable = (img_attr >> 16) & 0x1     # Bit 16
    erase_block_en = (img_attr >> 17) & 0x1  # Bit 17
    erase_always = (img_attr >> 18) & 0x1    # Bit 18
    compress_type = (img_attr >> 19) & 0x3   # Bits 19-20
    reserved2 = (img_attr >> 21) & 0x7FF     # Bits 21-31

    img_type_mapping = {
        0x0: "Bootloader",
        0x1: "User image",
        0x2: "Partition table",
        0xE: "Factory test program"
    }
    img_type_str = f"{img_type_mapping.get(img_type, 'Unknown')} (0x{img_type:X})"

    if firmware_type == "W60x":
        return {
            "Type": img_type_str,
            "GZIP compression": bool(gzip_enable),
            "Compression type": compress_type,
        }
    else:
        return {
            "Type": img_type_str,
            "Encryption": bool(code_encrypt),
            "Encryption private key #": prikey_sel,
            "Signature": bool(signature),
            #"Reserved 1": reserved1,
            "GZIP compression": bool(gzip_enable),
            "Block erase": bool(erase_block_en),
            "Always erase": bool(erase_always),
            "Compression type": compress_type,
            #"Reserved 2": reserved2,
        }


def print_image_info(firmware_type, header, body_len, body_checksum, replaced=False, new_hd_checksum=None, new_org_checksum=None):
    img_attr = header[1]
    img_attr_parsed = parse_img_attr(header[1], firmware_type)
    img_addr = header[2]
    img_len = header[3]
    if firmware_type == "W60x":
        org_checksum = header[4]
        upgrade_img_addr = header[5]
        upgrade_img_len = header[6]
        upgrade_img_checksum = header[7]
        upd_no = header[8]
        ver = header[9].decode('ascii').strip('\x00')
        hd_checksum = header[10]
    else:
        img_header_addr = header[4]
        upgrade_img_addr = header[5]
        org_checksum = header[6]
        upd_no = header[7]
        ver = header[8].decode('ascii').strip('\x00')
        reserved0 = header[9]
        reserved1 = header[10]
        next_img_addr = header[11]
        hd_checksum = header[12]

    # Parse header fields
    print("  Image attributes:")
    for key, value in img_attr_parsed.items():
        print(f"    {key}: {value}")
    print(f"  Image address: 0x{img_addr:08X}")
    if img_len != body_len:
        print(f"  Image size: expected {img_len}, actual {body_len} [INVALID]")
    else:
        print(f"  Image size: {img_len}")
    if firmware_type == "W60x":
        print(f"  OTA update address: 0x{upgrade_img_addr:08X}")
        print(f"  OTA update size: {upgrade_img_len}")
        print(f"  OTA update checksum: 0x{upgrade_img_checksum:08X}")
        print(f"  OTA update version: 0x{upd_no:08X}")
        print(f"  Version: {ver}")
    else:
        print(f"  Header address: 0x{img_header_addr:08X}")
        print(f"  OTA update address: 0x{upgrade_img_addr:08X}")
        print(f"  OTA update version: 0x{upd_no:08X}")
        print(f"  Version: {ver}")
        #print(f"  Reserved 0: 0x{reserved0:08X}")
        #print(f"  Reserved 1: 0x{reserved1:08X}")
        print(f"  Next image header address: 0x{next_img_addr:08X}")

    if replaced:
        print(f"  Image checksum: original 0x{org_checksum:08X}, new 0x{new_org_checksum:08X} (verified)")
        print(f"  Header checksum: original 0x{hd_checksum:08X}, new 0x{new_hd_checksum:08X} (verified)")
    else:
        if org_checksum != body_checksum:
            print(f"  Image checksum: expected 0x{org_checksum:08X}, actual 0x{body_checksum:08X} [INVALID]")
        else:
            print(f"  Image checksum: 0x{org_checksum:08X} (verified)")
        print(f"  Header checksum: 0x{hd_checksum:08X} (verified)")


def process_image(file, firmware_type, image_number, replace_target, output_file, extract):
    image_increment = 1
    if firmware_type == "W60x":
        header_size = HEADER_SIZE_W60X
        header_data = file.read(header_size)
        if crc32(header_data) == 0x27445404: #W60X data can be padded with 0xFF
            while True:
                padding_test = file.read(4)
                if len(padding_test) < 4:
                    break
                if padding_test != b'\xFF\xFF\xFF\xFF':
                    file.seek(-4,1)
                    break
            header_data = file.read(header_size)
    else:
        header_size = HEADER_SIZE_W80X
        header_data = file.read(header_size)

    image_prefix = ""

    if firmware_type == "W60x" and image_number == 1: # Checks if the image is a wrapper around additional images
        if not header_data or len(header_data) == 0:
            file.seek(56)
            header_data = file.read(header_size)
            image_number = 0.0
            image_increment = 0.1

    else:
        if not header_data or len(header_data) == 0:
            return None

    print(f"\nImage {image_prefix}{image_number}:")

    magic_data = struct.unpack("<I", header_data[:4])[0]
    if magic_data != MAGIC_WORD:
        raise ValueError(f"  [Error] Invalid header, incorrect magic word (expected 0x{MAGIC_WORD:08X}, actual 0x{magic_data:08X})")

    if len(header_data) != header_size:
        raise ValueError(f"  [Error] Invalid header, incorrect size (expected {header_size} bytes, actual {len(header_data)})")

    if firmware_type == "W60x":
        header = struct.unpack("<IIIIIIIII16sI", header_data)
        img_len, org_checksum, hd_checksum = header[3], header[4], header[10]
        validate_header(struct.pack("<IIIIIIIII16sI", *header), header_size, hd_checksum)
    else:
        header = struct.unpack("<IIIIIIII16sIIII", header_data)
        img_len, org_checksum, hd_checksum = header[3], header[6], header[12]
        validate_header(struct.pack("<IIIIIIII16sIIII", *header), header_size, hd_checksum)

    if firmware_type == "W60x":
        file_position = file.tell()
        filler_test = file.read(W60X_HEADER_PADDING) # W60x firmware can have images padded with 0xFF
        if crc32(filler_test) == W60X_HEADER_PADDING_CRC:
            file.seek(file_position + W60X_HEADER_PADDING)
        else:
            file.seek(file_position)
        body = file.read(img_len)
    else:
        body = file.read(img_len)

    body_checksum = crc32(body)
    body_len = len(body)
    if body_len != img_len or body_checksum != org_checksum:
        valid_body = False
    else:
        valid_body = True

    replaced = False
    if replace_target and valid_body:
        if os.path.isdir(replace_target):
            ref_files = [f for f in os.listdir(replace_target) if f.endswith('ref.bin')]
            if not ref_files:
                raise ValueError("No reference files found in specified directory.")

            replaced_files = {}
            for ref_file in ref_files:
                mod_file = ref_file.replace("ref.bin", "mod.bin")
                ref_path = os.path.join(replace_target, ref_file)
                mod_path = os.path.join(replace_target, mod_file)

                if not os.path.exists(mod_path):
                    print(f"[Warning] No matching mod file for {ref_file}, skipping.")
                    continue

                with open(ref_path, "rb") as ref_input, open(mod_path, "rb") as mod_input:
                    ref_data, mod_data = ref_input.read(), mod_input.read()
                    if len(ref_data) != len(mod_data):
                        print(f"[Error] Reference and modification files must be the same size: {ref_file}")
                        continue

                if replaced:
                    new_body, replaced = replace_data(new_body, ref_data, mod_data)
                    replaced_files[ref_file] = replaced
                    replaced = True
                else:
                    new_body, replaced = replace_data(body, ref_data, mod_data)
                    replaced_files[ref_file] = replaced

        elif os.path.isfile(replace_target) and replace_target.endswith('ref.bin'):
            ref_filename = replace_target
            mod_filename = replace_target.replace("ref.bin", "mod.bin")
            if not os.path.exists(mod_filename):
                raise ValueError(f"Matching modification file not found for {ref_filename}")

            with open(ref_filename, "rb") as ref_file, open(mod_filename, "rb") as mod_file:
                ref_data, mod_data = ref_file.read(), mod_file.read()

                if len(ref_data) != len(mod_data):
                    raise ValueError("Reference and modification files must be the same size.")

            ref_name, _ = os.path.splitext(ref_filename)
            new_body, replaced = replace_data(body, ref_data, mod_data)

        else:
            raise ValueError("Invalid replacement reference file or directory.")

        if replaced:
            new_org_checksum = crc32(new_body)
            new_header = list(header)
            new_header[6] = new_org_checksum
            new_header[12] = crc32(struct.pack("<IIIIIIII16sIII", *new_header[:12]))
            output_file.write(struct.pack("<IIIIIIII16sIIII", *new_header))
            output_file.write(new_body)
            print_image_info(firmware_type, header, body_len, body_checksum, True, new_header[12], new_org_checksum)
        else:
            output_file.write(struct.pack("<IIIIIIII16sIIII", *header))
            output_file.write(body)
            print_image_info(firmware_type, header, body_len, body_checksum, False)

        if os.path.isdir(replace_target):
            for replaced_item, matched in replaced_files.items():
                ref_name, _ = os.path.splitext(replaced_item)
                print(f"  [Replace] {'Matched and replaced' if matched else 'Not matched'}: {ref_name}")
        else:
            print(f"  [Replace] {'Matched and replaced' if replaced else 'Not matched'}: {ref_name}")

    else:
        print_image_info(firmware_type, header, body_len, body_checksum, False)

    if extract:
        base_name, _ = os.path.splitext(args.filename)
        output = f"{base_name}_image{image_number}.img"
        with open(output, "wb") as image_file:
            image_file.write(body)
        if replaced:
            mod_output = f"{base_name}_image{image_number}_mod.img"
            with open(mod_output, "wb") as image_file:
                image_file.write(new_body)
            print(f"  [Extract] Saved original image as {output}, modified image as {mod_output}")
        else:
            print(f"  [Extract] Saved image as {output}")

    return image_number + image_increment


def parse_firmware(args):
    try:
        with open(args.filename, "rb") as file:
            firmware_type = detect_firmware_type(file)
            print(f"Detected firmware type: {firmware_type}")

            image_number = 0
            if args.replace and firmware_type != "W60x":
                output_filename = args.output or f"{os.path.splitext(args.filename)[0]}_mod.fls"
                with open(output_filename, "wb") as output_file:
                    while True:
                        try:
                            image_number = process_image(file, firmware_type, image_number, args.replace, output_file, args.extract)
                            if not image_number:
                                break
                        except ValueError as e:
                            print(e)
                            break
                    print(f"\n[Output] Saved processed firmware as {output_filename}")
            else:
                while True:
                    try:
                        image_number = process_image(file, firmware_type, image_number, None, None, args.extract)
                        if not image_number:
                            break
                    except ValueError as e:
                        print(e)
                        break

    except FileNotFoundError as e:
        print(e)
    except ValueError as e:
        print(f"[Error] {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='flstweak ' + VERSION + ' - Parse, replace, and extract data from Winner Micro .fls firmware files.')
    parser.add_argument('filename', help='.fls firmware file to process')
    parser.add_argument('--replace', help='reference file (suffix: ref.bin) for replacement or directory for multiple replacements')
    parser.add_argument('--output', help='output file for modified firmware (default: filename_mod)')
    parser.add_argument('--extract', action='store_true', help='extracts images to individual files')
    args = parser.parse_args()

    parse_firmware(args)
