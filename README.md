# FLSTweak
This tool parses .fls firmware files for Winner Micro microcontrollers, including the W60x series (W600, W601) and W80x series (W800, W801, W806). This includes decoding and presenting header information, verifying data integrity, replacing data (including updating header checksums), and extracting images to individual files for analysis.

These firmware file can contain multiple images, including the bootloader image (Secboot) and the runtime user image, each with a header specifying image properties and checksums for the image and the header itself.

## Quick start
Run flstweak.py with the -h option to display help with all options:
```
$python3 flstweak.py -h
usage: flstweak.py [-h] [--replace] [--ref REF] [--mod MOD] [--output OUTPUT] [--extract] filename

flstweak 0.1 - Parse, replace, and extract data from Winner Micro .fls firmware files.

positional arguments:
  filename         .fls firmware file to process

options:
  -h, --help       show this help message and exit
  --replace        replace data, requires --ref and --mod
  --ref REF        file containing reference data
  --mod MOD        file containing modified data
  --output OUTPUT  output file for modified firmware (default: filename_mod)
  --extract        extracts images to individual files

```
Run flstweak.py with the firmware file to parse and display image info:
```
$python3 flstweak.py hello_world.fls
Detected firmware type: W80x

Image 0:
  Image attributes:
    Type: Bootloader (0x0)
    Encryption: False
    Encryption private key #: 0
    Signature: False
    GZIP compression: False
    Block erase: False
    Always erase: False
    Compression type: 0
  Image address: 0x08002400
  Image size: 25984
  Header address: 0x08002000
  OTA update address: 0x00000000
  OTA update version: 0x00000000
  Version: G03.00.00
  Next image header address: 0x0800F000
  Image checksum: 0x65C3A078 (verified)
  Header checksum: 0x3F0A6E0A (verified)

Image 1:
  Image attributes:
(...)
```

## Image data replacement
The `--replace` option allows for image data replacement and requires a reference data file (with `--ref`) containing the image data to match and a modified data file (with `--mod`) of the same size. If the reference data is found, it will be replaced with the modified data and the header will be updated with the new image checksum and header checksum.

By default, the modified firmware will be written as `filename_mod` and can be customized with the `--output` option.

* Note that data replacement is currently not supported for W60x-series firmware.

## Image extraction
The images can also be extracted to individual files for analysis with the `--extract` option. Each image will be written as `filename_imageX`, with `X` as the image number.

## Release notes
* 0.1
  - Initial release

## References
https://doc.winnermicro.net/w800/en/latest/component_guides/firmware_format.html
http://www.winnermicro.com/en/upload/1/editor/1559640549130.pdf