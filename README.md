# FLSTweak
This tool parses .fls firmware files for [Winner Micro](http://www.winnermicro.com/en/) microcontrollers, including the W60x series (W600, W601) and W80x series (W800, W801, W806). This includes decoding and presenting header information, verifying data integrity, replacing data (including updating header checksums), and extracting images to individual files for analysis.

For example, the [Zeeweii DSO3D12 oscilloscope](http://www.zeeweii.com/productinfo/dso3d12.html) uses the W806 chip and can be modified to improve the font quality and other UI elements. See the [ZeeTweak](https://github.com/taligentx/ZeeTweak) repo for firmware modifications that can be applied using FLSTweak.

## Quick start
The .fls firmware file can contain multiple images, including the bootloader image (Secboot) and the runtime user image, each with a header specifying image properties and checksums for the image and the header itself. See the References section below for details.

Run flstweak.py with the -h option to display help with all options:
```
$ python3 flstweak.py -h
usage: flstweak.py [-h] [--replace REPLACE] [--output OUTPUT] [--extract] filename

flstweak 2.0 - Parse, replace, and extract data from Winner Micro .fls firmware files.

positional arguments:
  filename           .fls firmware file to process

options:
  -h, --help         show this help message and exit
  --replace REPLACE  reference file (suffix: ref.bin) for replacement or directory for multiple replacements
  --output OUTPUT    output file for modified firmware (default: filename_mod)
  --extract          extracts images to individual files

```
Run flstweak.py with the firmware file to parse and display image info:
```
$ python3 flstweak.py hello_world.fls
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
On Linux and macOS, the following will make the script directly executable:
```
$ chmod +x flstweak.py
$ ./flstweak.py hello_world.fls
```

## Image data replacement
The `--replace` option allows for image data replacement by specifying a reference file (suffix: `ref.bin`) containing the image data to match or a directory containing multiple reference files. Each reference file should have a corresponding modified file (suffix: `mod.bin`) of the same size with the replacement data.

If the reference data is found, it will be replaced with the modified data and the header will be updated with the new image checksum and header checksum.
```
$ python3 flstweak.py hello_world.fls --replace data_ref.bin
Detected firmware type: W80x

Image 0:
  (...)
  Image checksum: original 0x7C67C28A, new 0x187EC376 (verified)
  Header checksum: original 0x2857E698, new 0x9F17B19D (verified)
  [Replace] Matched and replaced: data_ref
```

By default, the modified firmware will be written as `filename_mod` and can be customized with the `--output` option.
```
[Output] Saved processed firmware as hello_world_mod.fls
```

* Notes
  - The reference and mod files must contain a single block of contiguous data. The first matching data in the image will be replaced - for multiple occurances, run the same command on the produced `_mod.fls` file.
  - Data replacement is currently not supported for W60x-series firmware.

## Image extraction
The images can also be extracted to individual files for analysis with the `--extract` option, including stripping the header to only include the image data. Each image is written as `filename_imageX.img`, with `X` as the image number. If combined with `--replace`, both the original image and the modified image will be extracted to separate files.
```
Image 0:
  (...)
  [Extract] Saved image as hello_world_image0.img

Image 1:
  (...)
  [Replace] Matched and replaced: data_ref
  [Extract] Saved original image as hello_world_image1.img, modified image as hello_world_image1_mod.img
```

## Release notes
* 2.0
  - Support multiple replacements: `--replace` now directly accepts a reference filename or directory containing multiple reference files (removed `--ref` and `--mod` arguments)
  - Zeeweii DSO3D12: updated example `mod.fls` file with measurement label changes, fixed `Normal` label
* 1.1
  - Zeeweii DSO3D12: Rendered new small font with all characters shifted down 1 pixel
* 1.0
  - Release after successful testing on the Zeeweii DSO3D12
* 0.1
  - Initial release

## References
  * [W80x series firmware format](https://doc.winnermicro.net/w800/en/latest/component_guides/firmware_format.html)
  * [W60x series firmware format](http://www.winnermicro.com/en/upload/1/editor/1559640549130.pdf)