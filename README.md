# Proxyshop Plugin: Caalyx

This is a plugin for Proxyshop that adds some custom frames that I like to use.

## Frames

### Borderless Ikoria Template
A Borderless frame based on the Godzilla themed box toppers from Ikoria.
#### Features
- All basic features of the base Borderless, including nicknames.
- No customizable text box size, only short allowed.

## Installation

1. Download the latest release, or all the files from this repository.
2. Drop the plugin code into a folder within your Proxyshop plugins folder.
3. Restart Proxyshop to load the plugin.

## Configuration

Since Proxyshop 1.13 does not support the settings GUI, you will need to manually configure the plugin using the `config_ini` file.

### Example `config_ini/BorderlessIkoriaTemplate.ini`

Below is an example configuration for the Borderless Ikoria template:

```ini
[TEXT]
Nickname = 1
Drop.Shadow = 1

[COLORS]
Max.Colors = 3
Hybrid.Colored = 1
Front.Face.Colors = 1
Land.Colorshift = 0
Multicolor.PT = 1
Multicolor.Pinlines = 1
```

### Instructions

1. Locate the `config_ini` folder within the plugin.
2. Copy and paste the example configuration a new file called BorderlessIkoriaTemplate.ini.
3. Adjust the settings as needed to fit your preferences.
4. Save the file and restart Proxyshop.

## Support

If you encounter any issues or have questions about the plugin, feel free to open an issue on the plugin's repository.
