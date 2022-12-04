import os
from tqdm import tqdm

def rom_from_file(path):
    """
    Attempt to read a file as a binary Chip-8 ROM.
    Returns a list of bytes read from the specified `path`.
    """

    if (not os.path.exists(path)):
        raise RuntimeError('ROM file could not be found')
    elif (not os.path.isfile(path)):
        raise RuntimeError('ROM path does not point to file')
    else:
        print(f"Loading ROM from {path}")
        rom = []

        with tqdm(total=os.path.getsize(path), bar_format='{desc:<5.5}{percentage:3.0f}%|{bar:10}{r_bar}') as pbar:
            with open(path, 'rb') as f:
                for opcode in f.read():
                    rom.append(opcode)
                    pbar.update(1)
        return rom