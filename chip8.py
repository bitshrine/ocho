NAME = "CHIP8 EMULATOR"
VERSION = 0.3

import sys, getopt

import pygame
import tkinter as tk
from tkinter import filedialog

from cpu.cpu import CPU
from utils.fileio import rom_from_file

class Chip8:
    """
    Top-level class for the Chip8 emulator
    """
    def __init__(self, debug=False, cpu_mode=None, max_fps=60):
        pygame.init()
        self.cpu = CPU(DEBUG_MODE = debug, cpu_mode = cpu_mode, max_fps = max_fps)

    def run(self, rom):
        """
        Load a ROM into the Chip8 CPU and start
        execution. The ROM must be a list of bytes.
        """
        self.cpu.load_rom(rom)
        self.cpu.start()


if (__name__ == "__main__"):
    root = tk.Tk()
    root.withdraw()

    print(f"\n=========== {NAME} v{VERSION} ===========")

    opts = 'r:dc:'
    longopts = ['rom=', 'debug', 'cpu_mode=']

    path = None
    debug = False
    cpu_mode = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], opts, longopts)
    except getopt.GetoptError as err:
        print(err) 
        sys.exit(2)

    for o, a in opts:
        if o in ("-r", "--rom"):
            path = a
        elif o in ("-d", "--debug"):
            debug = True
        elif (o in ("-c", "--cpu_mode")):
            cpu_mode = a
        else:
            assert False, "unhandled option"

    if (path == None):

        rom_file_extensions = ['*.ch8', '*.Ch8', '*.cH8', '*.CH8', '*.c8', '*.C8']
        ftypes = [
            ('CHIP-8 ROM', rom_file_extensions),
            ('All files', '*'),
        ]

        path = filedialog.askopenfilename(title="Select file",
                                           filetypes=ftypes)

    if (path == '' or path == None):
        print('No ROM file chosen. Exiting.\n')
        exit(0)

    chip8 = Chip8(debug, cpu_mode=cpu_mode, max_fps=60)
    rom = rom_from_file(path)
    chip8.run(rom)


