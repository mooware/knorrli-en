import sys, struct
from PIL import Image

# NOTE: these functions only work for some of the files,
# I assume only for normal static images and not e.g. animations

def rgb(b1, b2, b3):
    return b1 | (b2 << 8) | (b3 << 16)

def read_palette(stream):
    palette = []
    for i in range(256):
        b1, b2, b3 = stream.read(3)
        palette.append(rgb(b1, b2, b3))
    return palette

def has_palette(filename):
    """Try to determine if the given .gra file has a palette"""
    with open(filename, 'rb') as f:
        # not sure if this is reliable but the non-palette files start with width/height,
        # and the palette files start with the palette, which hopefully always starts with 0
        data = f.read(1)
        return data[0] == 0

def gra_to_png(filename, palette_file=None):
    """Convert a .gra file from Abenteuer Atlantis to PNG"""
    with open(filename, 'rb') as f:
        # some files don't have a palette, use another file to provide it
        if palette_file:
            with open(palette_file, 'rb') as pf:
                palette = read_palette(pf)
        else:
            # first the palette, with 256 x 3 bytes
            palette = read_palette(f)
        # after palette comes image size, width and height 2B LE each
        data = f.read(4)
        width, height = struct.unpack('<HH', data)
        img = Image.new('RGB', (width, height))
        # and then image data in a kind of runlength encoding
        pxpos = 0
        while True:
            data = f.read(1)
            if not data:
                break # apparently that's the best way to recognize eof
            # if len has high bit set it's run length encoded, otherwise it's the number of following bytes
            (plen,) = data
            if plen >= 128:
                length = (256 - plen) + 1
                (pcol,) = f.read(1)
                pixels = [pcol] * length
            else:
                length = plen + 1
                pixels = f.read(length)

            for px in pixels:
                color = palette[px]
                x = pxpos % width
                y = pxpos // width
                pxpos += 1
                img.putpixel((x, y), color)

        img.save(filename + '.png')

def png_to_gra(filename, old_filename=None):
    """Convert a PNG to a .gra file from Abenteuer Atlantis"""
    img = Image.open(filename).convert(mode='RGB')
    palette_map = {}
    with open(filename + '.gra', "wb") as f:
        # optionally, use and enforce an existing palette
        if old_filename:
            with open(old_filename, 'rb') as of:
                f.write(of.read(256 * 3))
                of.seek(0)
                old_palette = read_palette(of)
                for i in range(len(old_palette)):
                    palette_map[old_palette[i]] = i
        else:
            # put fixed colors on 0 and 255 because the other images seem to do that too
            palette_map[0x0] = 0
            palette_map[0xFFFFFF] = 255
            # write an empty palette first to reserve space, then fill it in later
            for i in range(256):
                f.write(b'\x00\x00\x00')
        # size in little endian
        f.write(struct.pack('<HH', img.width, img.height))
        # now for the hard part, run length encoding
        row = [-1] * img.width
        for y in range(img.height):
            # map colors to palette
            for x in range(img.width):
                color = rgb(*img.getpixel((x, y)))
                # look up color in palette, or add it (unless we have an existing palette)
                color_index = palette_map.get(color, -1)
                if color_index == -1:
                    if old_filename:
                        print(palette_map)
                        raise Exception('color {:X} not found in old palette'.format(color))
                    if len(palette_map) == 255:
                        raise Exception('too many colors for palette')
                    color_index = len(palette_map) - 1
                    palette_map[color] = color_index
                row[x] = color_index
            # prepare run length encoding, pass 1: find same color runs
            encoded = [(1, row[0])]
            for x in range(1, img.width):
                if row[x] == row[x - 1]:
                    count, color = encoded[-1]
                    if count < 127:
                        encoded[-1] = (count + 1, color)
                        continue
                encoded.append((1, row[x]))
            # pass 2: merge different colors and write
            i = 0
            while i < len(encoded):
                count, color = encoded[i]
                if count > 1:
                    # rle encoding is already done, just prepare the length
                    enc_len = 256 - (count - 1)
                    f.write(bytes([enc_len, color]))
                    i += 1
                else:
                    # non-rle parts still have to be merged
                    pixels = []
                    while i < len(encoded) and encoded[i][0] == 1:
                        pixels.append(encoded[i][1])
                        i += 1
                    enc_len = len(pixels) - 1
                    f.write(bytes([enc_len]))
                    f.write(bytes(pixels))
        # write the new palette if it wasn't just copied from the old file
        if not old_filename:
            f.seek(0)
            palette = [0] * 256
            for k in sorted(palette_map.keys()):
                palette[palette_map[k]] = k
            for color in palette:
                b1 = color & 0xFF
                b2 = (color >> 8) & 0xFF
                b3 = color >> 16
                f.write(bytes([b1, b2, b3]))

if __name__ == '__main__':
    if sys.argv[1] == 'decode_pal':
        print("decoding image with palette", sys.argv[2])
        gra_to_png(sys.argv[2])
    elif sys.argv[1] == 'decode':
        print("decoding image without palette", sys.argv[2])
        gra_to_png(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'decode_auto':
        print("decoding image with palette detection", sys.argv[2])
        has = has_palette(sys.argv[2])
        print('palette found?', has)
        gra_to_png(sys.argv[2], None if has else sys.argv[3])
    elif sys.argv[1] == 'encode_pal':
        template = sys.argv[3] if len(sys.argv) > 3 else None
        print("encoding image with palette", sys.argv[2])
        png_to_gra(sys.argv[2], template)