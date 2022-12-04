import pygame
import numpy as np

byte = np.uint8
short = np.uint16

K_KEYS = [
        '1', '2', '3', '4',
        'q', 'w', 'e', 'r',
        'a', 's', 'd', 'f', 
        'y', 'x', 'c', 'v'
    ]

C8_KEYS = [
    0x1, 0x2, 0x3, 0xC,
    0x4, 0x5, 0x6, 0xD,
    0x7, 0x8, 0x9, 0xE, 
    0xA, 0x0, 0xB, 0xF
]

class InputHandler():

    def __init__(self):
        # Create a key map, i.e. a dict from the keyboard
        # key pygame keycodes to the Chip8 keys
        self.KEY_MAP = {}
        self.KEY_STATE = {}
        for idx, k_key in enumerate(K_KEYS):
            self.KEY_MAP.update(
                {pygame.key.key_code(k_key): C8_KEYS[idx]}
            )
            self.KEY_STATE.update(
                {C8_KEYS[idx]: False}
            )

    
    def set(self, key: byte, value: byte):
        """
        Set a value of the keymap
        """
        c8_key = self.KEY_MAP.get(key, None)
        if (c8_key != None):
            self.KEY_STATE[c8_key] = value

    def get(self, c8_key: byte) -> byte:
        """
        Retrieves a value of the keymap
        """
        return self.KEY_STATE[c8_key]

    def get_any(self) -> int:
        """
        Returns a key if it is pressed, or -1
        if none are pressed.
        """
        for k, v in self.KEY_STATE.items():
            if (v):
                return k
        return -1

    def reset(self):
        """
        Clears all values in the keymap
        """
        for k in self.KEY_STATE.keys():
            self.KEY_STATE[k] = False