import sys

def apply_line(target_file, from_address, to_address, line):
    if not line:
        print('warning: ignoring empty translation for range {:x}-{:x}'
                .format(from_address, to_address))
    # the game uses codepage 850 (DOS-Latin-1) for text
    enc_line = line.encode('cp850')
    orig_len = (to_address - from_address) + 1
    if len(enc_line) > orig_len:
        print('warning: new line for range {:x}-{:x} is longer than the original ({} > {})'
                .format(from_address, to_address, len(enc_line), orig_len))
    else:
        # fill the rest if too short
        enc_line = enc_line.ljust(orig_len, b' ')
    print('replacing line at range {:x}-{:x}'.format(from_address, to_address))
    target_file.seek(from_address)
    target_file.write(enc_line)

def apply_translations(translation_file_path, target_file_path):
    with open(translation_file_path, 'r') as tr:
        with open(target_file_path, 'r+b') as tgt:
            lines = tr.readlines()
            i = 0
            while i < len(lines):
                # the translation format is:
                # 1) address of the original text: "0xfrom 0xto"
                # 2) line with the original text
                # 3) line with the new text
                if lines[i].startswith('0x'):
                    addrline = lines[i]
                    fromline = lines[i + 1]
                    toline = lines[i + 2]
                    (fromaddr, toaddr) = (int(s, base=16) for s in addrline.split(' '))
                    apply_line(tgt, fromaddr, toaddr, toline)
                    i += 2
                i += 1

if __name__ == '__main__':
    apply_translations(sys.argv[1], sys.argv[2])