import pygame
import curses
import numpy as np

byte = np.byte

class Display:
    """
    A superclass to handle CHIP-8 displays
    """

    COLORS = {
        0: [212, 252, 217],
        1: [71, 115, 77]
    }

    TERM_COLORS = {
        0: 'black',
        1: 'white'
    }

    size = 10
    width = 64
    height = 32

    def __init__(self, name: str ='Chip-8 Emulator'):
        self.grid = np.zeros(shape=(self.height, self.width), dtype=byte)


    def get(self, x: byte, y: byte) -> byte:
        """
        Get the value of a pixel at coordinates (x, y)
        """
        return self.grid[y, x]

    def set(self, x: byte, y: byte, value: byte):
        """
        Set the value of the pixel at coordinates (x, y)
        """
        self.grid[y, x] = value


    def clear(self):
        """
        Clear the display, i.e. set all grid elements to 0
        """
        self.grid.fill(0)
        self.draw()

    def draw(self):
        """
        Draw the display according to the grid
        """
        pass


class PyGameDisplay(Display):
    """
    PyGame display for CHIP-8
    """
    
    def __init__(self, name: str = "Chip-8 Emulator"):
        super().__init__(name)
        self.disp = pygame.display.set_mode([self.width * self.size, self.height * self.size])
        pygame.display.set_caption(name)
        self.disp.fill(self.COLORS[0])
        pygame.display.flip()

    def draw(self):
        for i in range(self.height):
            for j in range(self.width):
                cell = self.COLORS[self.grid[i, j]]
                pygame.draw.rect(self.disp, cell, [j * self.size, i * self.size, self.size, self.size], 0)

        pygame.display.flip()


class TermDisplay(Display):

    def __init__(self, name: str = "Chip-8 Emulator"):
        super().__init__(name)

    def draw(self):
        pass

    
