# gltf-texturec

A Python script to convert textures in a GLTF 2.0 model with bgfx's [texturec](https://bkaradzic.github.io/bgfx/tools.html#texture-compiler-texturec) tool. Converts the textures and updates the filenames inside the .gltf file. Both metallic/roughness and specular/glossiness (extension KHR_materials_pbrSpecularGlossiness) materials are supported.

## Prerequisites

- Python 3.6 or later
- pygltflib:
    ```sh
    pip install pygltflib
    ```
- texturec must be in the PATH environment variable

## Usage

```sh
python gltf-texturec.py -i /path/to/model.gltf -o /path/to/new_model.gltf --format .dds --type BC3 --mips
```

### Options

- **-i [file path]**: Input file path
- **-o [file path]**: Output file path
- **-f, --format [format]**: Output texture file format. Default is .dds.
    - **.dds**: Direct Draw Surface
    - **.exr**: OpenEXR
    - **.hdr**: Radiance RGBE
    - **.ktx**: Khronos Texture
    - **.png**: Portable Network Graphics
- **-t, --type [type]**: Output format type (BC1/2/3/4/5, ETC1, PVR14, etc.). Run `texturec --formats` for a complete list of  supported types. Default is BC3.
- **-q, --quality [quality]**: Encoding quality (default, fastest, highest)
- **-m, --mips**: Generate mip-maps

## Limitations

- No support for images embedded in buffers
- If you convert to .dds, a correct implementation should probably use the MSFT_texture_dds extension.
