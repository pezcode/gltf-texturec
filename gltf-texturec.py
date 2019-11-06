import argparse
from pathlib import Path, PurePath
from pygltflib import GLTF2
import subprocess
import sys
import shutil

class GLTFConverter:
    mimetypes = {
        '.dds':  'image/vnd-ms.dds',
        '.exr':  'image/x-exr', # not a registered mimetype
        '.hdr':  'image/vnd.radiance',
        '.ktx':  'image/ktx',
        '.png':  'image/png'
    }

    def __init__(self, file_format, texture_type, quality="default", generate_mips=True):
        if file_format not in GLTFConverter.mimetypes.keys():
            raise ValueError("file_format must be one of %s" % ", ".join(GLTFConverter.mimetypes.keys()))
        self.generate_mips = generate_mips
        self.file_format = file_format
        self.texture_type = texture_type
        self.quality = quality
        self.gltf = None
        self.directory = None
        self.outdirectory = None
        self.converted = []

    def load(self, file):
        self.file = file
        self.directory = Path(file).parent.resolve()
        self.gltf = GLTF2().load(file)
        return self.gltf is not None
    
    def convert(self, outfile):
        if self.gltf is None:
            raise RuntimeError("load must be called before convert")
        self.outdirectory = Path(outfile).parent.resolve()
        self.outdirectory.mkdir(parents=True, exist_ok=True)
        self.converted = []
        for mat in self.gltf.materials:
            self.convert_material(mat)
        self.gltf.save(outfile)
        # Copy binary blobs if needed
        # pygltflib doesn't seem to do this
        if self.outdirectory != self.directory:
            for buffer in self.gltf.buffers:
                srcbuffer = self.directory.joinpath(buffer.uri)
                dstbuffer = self.outdirectory.joinpath(buffer.uri)
                shutil.copy2(srcbuffer, dstbuffer)
    
    def convert_material(self, mat):
        pbr = mat.pbrMetallicRoughness
        if pbr is not None:
            if pbr.baseColorTexture is not None:
                self.convert_gltf_texture(pbr.baseColorTexture.index, is_linear = False)
            if pbr.metallicRoughnessTexture is not None:
                self.convert_gltf_texture(pbr.metallicRoughnessTexture.index, is_linear = True)
        if mat.normalTexture is not None:
            self.convert_gltf_texture(mat.normalTexture.index, is_linear = True, is_normal = True)
        if mat.occlusionTexture is not None:
            self.convert_gltf_texture(mat.occlusionTexture.index, is_linear = True)
        if mat.emissiveTexture is not None:
            self.convert_gltf_texture(mat.emissiveTexture.index, is_linear = False)

    def convert_gltf_texture(self, texture_index, is_linear, is_normal=False):
        texture = self.gltf.textures[texture_index]
        if texture.source not in self.converted:
            self.converted += [texture.source]
            image = self.gltf.images[texture.source]
            new_filename = self.convert_image_file(image.uri, is_linear, is_normal)
            image.uri = new_filename
            # is this necessary? should only apply to buffer views
            image.mimeType = GLTFConverter.mimetypes[self.file_format]

    def convert_image_file(self, filename, is_linear, is_normal=False):
        new_filename = str(PurePath(filename).with_suffix(self.file_format))
        inpath = str(self.directory.joinpath(filename))
        outpath = str(self.outdirectory.joinpath(new_filename))
        print("Converting %s" % inpath)
        arguments = ["-f", inpath, "-o", outpath, "-t", self.texture_type, "-q", self.quality]
        if self.generate_mips:
            arguments += ["--mips"]
        if is_linear:
            arguments += ["--linear"] # don't apply gamma correction
        if is_normal:
            arguments += ["--normalmap"]
        self.run_texturec(arguments)
        return new_filename

    def run_texturec(self, arguments):
        try:
            proc = subprocess.run(["texturec"] + arguments, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if proc.returncode != 0:
                print(proc.stdout, file=sys.stderr)
        except FileNotFoundError:
            sys.exit("texturec not found. Make sure its location is in the PATH environment variable.")

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # args like -f show up as optional arguments in the help, even if required
    # this is a workaround
    required = parser.add_argument_group('required arguments')
    required.add_argument("-i", type=str, help="Input file path", required=True)
    required.add_argument("-o", type=str, help="Output file path", required=True)
    parser.add_argument("-f", "--format", type=str, choices=GLTFConverter.mimetypes.keys(), default=".dds", help="File format")
    parser.add_argument("-t", "--type", type=str, default="BC3", help="Output format type (run texturec --formats for a list)")
    parser.add_argument("-q", "--quality", type=str, choices=["default", "fastest", "highest"], default="default", help="Encoding quality")
    parser.add_argument("-m", "--mips", action="store_true", help="Generate mip-maps")
    args = parser.parse_args()
    converter = GLTFConverter(args.format, args.type, args.quality, args.mips)
    if not converter.load(args.i):
        sys.exit("Input file not found")
    converter.convert(args.o)

if __name__ == "__main__":
    main()
