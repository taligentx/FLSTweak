# FLSTweak
This tool parses .fls firmware files for [Winner Micro](http://www.winnermicro.com/en/) microcontrollers, including the W60x series (W600, W601) and W80x series (W800, W801, W806). This includes decoding and presenting header information, verifying data integrity, replacing data (including updating header checksums), and extracting images to individual files for analysis.

For example, the [Zeeweii DSO3D12 oscilloscope](http://www.zeeweii.com/productinfo/dso3d12.html) uses the W806 chip and can be modified to improve the font quality and other UI issues. See Examples below.

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

## Examples
* Zeeweii DSO3D12 - this directory contains mod files for new fonts and fixing UI typos/display bugs. These can be used with the [firmware available from Zeeweii](http://www.zeeweii.com/support.html). Thanks to [@timschuerewegen](https://www.eevblog.com/forum/testgear/new-2ch-pocket-dsosg-sigpeak-dso2512g/msg5124096/#msg5124096) for developing the fonts for the DSO2512G and permitting their addition to this repo!

  `dso3d12_v3.0.6_III_mod_v2.0.fls` is an example of modifying the original 3.0.6-III firmware:
    - Replaced small (8x13) and large (16x16) fonts - as of v1.1, I've re-rendered the small font for a better fit to the DSO3D12.
    - Updated measurement labels (removes divider `:`, changed capitalization, replace `Mea` with `Avg`)
    - Fixed DMM calibration label typos
    - Fixed label "Normal"

![Zeeweii_DSO3D12_mod_v2.0](https://github.com/user-attachments/assets/f21b143d-f933-4e98-aac6-cfb2dd442958)

## Flashing - DSO3D12
Linux/macOS:
  1. Download and extract the [WM IoT SDK](https://doc.winnermicro.net/download/version/).
  2. Install required packages - from the `wm_iot_sdk` directory:
     ```
     python -m pip install --user -r tools/wm/requirements.txt
     ```
  3. With the DSO3D12 turned off, press and hold the power button - the scope will enter a boot loop and enable the scope's serial port to allow for flashing. Keep the power button pressed until flashing is complete.
  4. Check the name of the serial port - on macOS, use the tty.wchusbserial device:
     ```
     % ls /dev/tty*
     /dev/tty.Bluetooth-Incoming-Port
     /dev/tty.usbserial-1410  
     /dev/tty.wchusbserial1410
     ```
  5. From the `wm_iot_sdk/tools/wm/` directory, run `flash.py` with the serial port and firmware:
     ```
     % python3 flash.py --port /dev/tty.wchusbserial1410 --image dso3d12_v3.0.6_III_mod.fls 
     connecting serial...
     serial connected
     trying reset device...
     wait serial sync...
     serial sync success
     trying baudrate 2000000...
     start download image...
     download dso3d12_v3.0.6_III_mod.fls...
     0% [##############################] 100%
     flash device complete
     ```
  6. Done! Release the power button.

Windows:
  1. Download [Upgrade Tools](http://www.isme.fun/?log=blog&id=34).
  2. Change the language to English from the top left menu (third option).
  3. Set "Chip" to `W80X` and set the image to the firmware .fls file.
  4. Press and hold the scope power button to enable the serial port until flashing is complete.
  5. Select the new COM port, click "Open Serial", and then "Download" to flash.
  6. Done! Release the power button.
  ![Flashing_DSO3D12_Upgrade_Tools](https://github.com/user-attachments/assets/0cf60add-3fdf-4c25-b316-f78c7475e515)

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