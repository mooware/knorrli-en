# NOTES:
# main text: from 0x19618 to 0x1D5A2 (terminated by 0x2B 0x00)
# item names: from 0x1D5C7 to 0x1DBB7, starting every 0x20 bytes, max len at least 0x10
# TODO: 0x18F70 for save/load text?
#
# text in the game uses codepage 850 (DOS-Latin-1, "cp850" in python)
# and represents line breaks with '#'.

import sys

def apply_line(target_file, from_address, to_address, line, is_item=False):
    """Apply a line to the given range of a file.

    target_file -- seekable/writeable stream in which to make the change
    from_address -- start of the target range in the file
    to_address -- end of the target range (exclusive)
    line -- string to write into the target range
    is_item -- if true it is treated as an item string, which is terminated differently
    """
    if not line:
        print('warning: ignoring empty translation for range {:x}-{:x}'
                .format(from_address, to_address))
    # the game uses codepage 850 (DOS-Latin-1) for text
    enc_line = line.encode('cp850')
    orig_len = to_address - from_address
    if len(enc_line) > orig_len:
        print('warning: new line for range {:x}-{:x} is longer than the original ({} > {})'
                .format(from_address, to_address, len(enc_line), orig_len))
        return
    elif is_item:
        # pad the rest with null bytes
        enc_line = enc_line.ljust(orig_len, b'\0')
    else:
        # these texts end with 0x2B 0x00, pad the rest with null bytes
        enc_line = (enc_line + b'\x2B\0').ljust(orig_len, b'\0')
    target_file.seek(from_address)
    target_file.write(enc_line)

def apply_translations(translation_file_path, target_file_path):
    with open(translation_file_path, 'r') as tr:
        with open(target_file_path, 'r+b') as tgt:
            # avoid trailing newlines
            lines = [s.rstrip() for s in tr.readlines()]
            i = 0
            while i < len(lines):
                # the translation format is:
                # 1) address of the original text: "0xfrom 0xto" (or "item" instead of 2nd addr)
                # 2) line with the original text
                # 3) line with the new text
                if lines[i].startswith('0x'):
                    addrline = lines[i]
                    fromline = lines[i + 1]
                    toline = lines[i + 2]
                    is_item = addrline.endswith(' item')
                    if is_item:
                        fromaddr = int(addrline.split(' ')[0], base=16)
                        toaddr = fromaddr + 0x11
                    else:
                        (fromaddr, toaddr) = (int(s, base=16) for s in addrline.split(' '))
                    apply_line(tgt, fromaddr, toaddr, toline, is_item=is_item)
                    i += 2
                i += 1

if __name__ == '__main__':
    apply_translations(sys.argv[1], sys.argv[2])