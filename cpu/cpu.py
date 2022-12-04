import pygame, sys, os, json, random, numpy as np
from utils.display import *
from utils.timer import *
from utils.input import InputHandler

# Type aliases
byte = np.uint8
short = np.uint16


# Constants
#MAX_FPS = 60

MEMORY_SIZE: short = 4096
N_REGS = 16

PC_INIT: short = 0
I_INIT: short = 0

FONT_START: byte = 0x50
FONT_END: byte = 0x9F + 0x01
FONT_SIZE = 5
FONT_DATA = np.array([
    0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
    0x20, 0x60, 0x20, 0x20, 0x70, # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
    0x90, 0x90, 0xF0, 0x10, 0x10, # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
    0xF0, 0x10, 0x20, 0x40, 0x40, # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90, # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
    0xF0, 0x80, 0x80, 0x80, 0xF0, # C
    0xE0, 0x90, 0x90, 0x90, 0xE0, # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
    0xF0, 0x80, 0xF0, 0x80, 0x80  # F
], dtype=byte)

ROM_START = 0x200

MASK_OP: short = 0xF000
MASK_X: short = 0x0F00
SHIFT_X: byte = 8
MASK_Y: short = 0x00F0
SHIFT_Y: short = 4
MASK_N: short = 0x000F
MASK_NN: short = 0x00FF
MASK_NNN: short = 0x0FFF
SHIFT_OVERFLOW: short = 0xF
MASK_SHORT: short = 0xFFFF
MASK_MSB: short = 0x80


class CPU:
    """
    ### Chip-8 CPU
    """
    def __init__(self, cpu_mode = None, shift_mode = 1, jump_mode = 1, io_mode = 1, max_fps = 60, DEBUG_MODE = 0):
        """
        Initialize a CPU and its internal components.
        ### Arguments
        - `cpu_mode`: Used for all instructions
            - 0 is for the original COSMAC VIP
            - 1 is for CHIP-48 and later
        - `shift_mode`: Used for the 8XYE/8XY6 instructions
            - 0 is for the original COSMAC VIP
            - 1 is for CHIP-48 and later
        - `jump_mode`: Used for the BNNN/BXNN instructions
            - 0 is for the original COSMAC VIP
            - 1 is for the CHIP-48 and later
        - `io_mode`: Used for the FX55/FX65 instructions
            - 0 is for the original COSMAC VIP
            - 1 is for the CHIP-48 and later
        - `DEBUG_MODE`: Set to `1` to use instruction stepping
        """
        self.mem = np.zeros(shape=(MEMORY_SIZE, ), dtype=byte)
        self.display = PyGameDisplay()
        self.delay = Timer()
        self.sound = SoundTimer()
        self.regs = np.zeros(shape=(N_REGS, ), dtype=byte)

        self.ihandler = InputHandler()
        pygame.time.set_timer(pygame.USEREVENT+1, int(1000/60))

        if cpu_mode != None:
            self.shift_mode = cpu_mode
            self.jump_mode = cpu_mode
            self.io_mode = cpu_mode
        else:
            self.shift_mode = shift_mode
            self.jump_mode = jump_mode
            self.io_mode = io_mode

        self.max_fps = max_fps

        self.DEBUG_MODE = DEBUG_MODE

        self.interrupt = False

        self.reset()

    def reset(self):
        """
        Reset the display and CPU memory, registers, stack, and timers
        """
        self.mem.fill(0)
        self.display.clear()

        self.ir = I_INIT
        self.pc = ROM_START

        self.stack = []

        self.delay.set(0)
        self.sound.set(0)

        self.regs.fill(0)

        # load font data
        self.mem[FONT_START:FONT_END] = FONT_DATA


    def start(self):
        """
        Start the CPU (begins the fetch-decode-execute loop)
        """
        clock = pygame.time.Clock()

        while (not self.interrupt):

            clock.tick(self.max_fps)
            self.sound.beep()

            self.handle_events()
            
            self.decode_ex(self.fetch())

            self.display.draw()

    def handle_events(self):
        """
        Handles pygame events
        """

        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                sys.exit()

            elif (event.type == pygame.USEREVENT + 1):
                self.delay.countDown()

            elif (event.type == pygame.KEYDOWN):
                self.ihandler.set(event.key, True)

            elif (event.type == pygame.KEYUP):
                if (self.DEBUG_MODE):
                    if (event.key == pygame.K_TAB):
                        self.interrupt = not self.interrupt
                    elif (event.key == pygame.K_p):
                        print(self)
                else:
                    self.ihandler.set(event.key, False)

            # Drag-n-drop theme support 
            elif (event.type == pygame.DROPFILE):
                extension = os.path.splitext(event.file)[1]
                if (extension == '.c8t'):
                    with open(event.file) as f:
                        new_colors_str = json.load(f)
                        for k, v in new_colors_str.items():
                            self.display.COLORS.update({int(k): v})


    def load_rom(self, rom: list[byte]):
        """
        Load a list of bytes into the CPU's memory
        """
        self.mem[ROM_START:ROM_START + len(rom)] = rom

    # Stack functions
    def stack_push(self, val: byte):
        """
        Push a value to the stack
        """
        self.stack.append(val)

    def stack_pop(self) -> byte:
        """
        Pop the first value on the stack
        """
        return self.stack.pop()


    # Main loop functions
    def fetch(self) -> short:
        """
        Fetch the next instruction from memory
        """
        opcode: short = (self.mem[self.pc] << 8) | self.mem[self.pc + 1]
        self.pc += 2
        return opcode

    def decode_ex(self, opcode: short):
        """
        Decodes the instruction (and executes it)
        """
        op: short = opcode & MASK_OP

        if (op == 0x0000):
            if (opcode == 0x00E0):
                self.display.clear()
            elif (opcode == 0x00EE):
                self.pc = self.stack.pop()

        elif (op == 0x1000):
            self.pc = opcode & MASK_NNN

        elif (op == 0x2000):
            self.stack.append(self.pc)
            self.pc = opcode & MASK_NNN

        elif (op == 0x3000):
            x = (opcode & MASK_X) >> SHIFT_X
            nn = opcode & MASK_NN
            if (self.regs[x] == nn):
                self.pc += 2
            
        elif (op == 0x4000):
            x = (opcode & MASK_X) >> SHIFT_X
            nn = opcode & MASK_NN
            if (self.regs[x] != nn):
                self.pc += 2

        elif (op == 0x5000):
            x = (opcode & MASK_X) >> SHIFT_X
            y = (opcode & MASK_Y) >> SHIFT_Y
            if (self.regs[x] == self.regs[y]):
                self.pc += 2
            
        elif (op == 0x6000):
            x = (opcode & MASK_X) >> SHIFT_X
            self.regs[x] = opcode & MASK_NN

        elif (op == 0x7000):
            x = (opcode & MASK_X) >> SHIFT_X
            self.regs[x] += opcode & MASK_NN

        elif (op == 0x8000):
            subop = opcode & MASK_N
            x = (opcode & MASK_X) >> SHIFT_X
            y = (opcode & MASK_Y) >> SHIFT_Y
            if (subop == 0):
                self.regs[x] = self.regs[y]
            # AND, OR and XOR reset vF register
            elif (subop == 1):
                self.regs[x] |= self.regs[y]
                self.regs[0xF] = 0
            elif (subop == 2):
                self.regs[x] &= self.regs[y]
                self.regs[0xF] = 0
            elif (subop == 3):
                self.regs[x] ^= self.regs[y]
                self.regs[0xF] = 0
            elif (subop == 4):
                res: np.uint32 = np.uint32(self.regs[x]) + np.uint32(self.regs[y])
                self.regs[0xF] = 1 if (res & ~MASK_NN) != 0x0 else 0
                self.regs[x] = res & MASK_NN

            # Subtractions
            elif (subop == 5):
                carry: byte = 0x1 if self.regs[x] > self.regs[y] else 0x0
                res: np.uint32 = np.int32(self.regs[x]) - np.int32(self.regs[y])
                self.regs[x] = res & MASK_NN
                self.regs[0xF] = carry
                    

            elif (subop == 7):
                carry: byte = 0x1 if self.regs[y] > self.regs[x] else 0x0
                res: np.uint32 = np.int32(self.regs[y]) - np.int32(self.regs[x])
                self.regs[x] = res & MASK_NN
                self.regs[0xF] = carry

            # Shifts
            elif (subop == 6):
                if (self.shift_mode == 0):
                    self.regs[x] = self.regs[y]
                carry: byte = self.regs[x] & 0x1
                self.regs[x] >>= 0x1
                self.regs[0xF] = carry
            elif (subop == 0xE):
                if (self.shift_mode == 0):
                    self.regs[x] = self.regs[y]
                carry: byte = 1 if (self.regs[x] & MASK_MSB) != 0 else 0x0
                self.regs[x] <<= 0x1
                self.regs[0xF] = carry


        elif (op == 0x9000):
            x = (opcode & MASK_X) >> SHIFT_X
            y = (opcode & MASK_Y) >> SHIFT_Y
            if (self.regs[x] != self.regs[y]):
                self.pc += 2

        elif (op == 0xA000):
            self.ir = opcode & MASK_NNN

        elif (op == 0xB000):
            val: byte = opcode & MASK_NNN
            reg: byte = 0x0 if self.jump_mode == 0 else ((opcode & MASK_X) >> SHIFT_X)
            self.pc = self.regs[reg] = val

        elif (op == 0xC000):
            x = (opcode & MASK_X) >> SHIFT_X
            self.regs[x] = random.getrandbits(8) & (opcode & MASK_NN)

        elif (op == 0xD000):
            
            x_start = self.regs[(opcode & MASK_X) >> SHIFT_X] % self.display.width
            y = self.regs[(opcode & MASK_Y) >> SHIFT_Y] % self.display.height
            self.regs[0xF] = 0
            b: byte = 0

            for n in range(opcode & MASK_N):
                x = x_start
                sprite_data = self.mem[self.ir + n]

                for i_pixel in range(8):
                    screen_pixel = self.display.get(x, y)
                    sprite_pixel = (sprite_data >> (7 - i_pixel)) & 0x1
                    if (screen_pixel == 1 and sprite_pixel == 1):
                        self.display.set(x, y, 0)
                        self.regs[0xF] = 1
                    elif (screen_pixel == 0 and sprite_pixel == 1):
                        self.display.set(x, y, 1)

                    if (x == self.display.width - 1):
                        break
                    x += 1

                if (y == self.display.height - 1):
                    break
                y += 1
            

        elif (op == 0xE000):
            subop: short = opcode & MASK_NN
            x = (opcode & MASK_X) >> SHIFT_X
            if (subop == 0x9E):
                if (self.ihandler.get(self.regs[x]) == 1):
                    self.pc += 2
            elif (subop == 0xA1):
                if (self.ihandler.get(self.regs[x]) == 0):
                    self.pc += 2

        elif (op == 0xF000):
            subop: short = opcode & MASK_NN
            x = (opcode & MASK_X) >> SHIFT_X

            # Timers
            if (subop == 0x07):
                self.regs[x] = self.delay.read()
            elif (subop == 0x15):
                self.delay.set(self.regs[x])
            elif (subop == 0x18):
                self.sound.set(self.regs[x])

            # Add to index
            elif (subop == 0x1E):
                self.ir += self.regs[x]
                self.regs[0xF] = 1 if (self.ir & MASK_NNN) != 0 else 0
                self.ir &= MASK_NNN

            # Get key
            elif (subop == 0x0A):
                key = self.ihandler.get_any()
                if (key == -1):
                    self.pc -= 2
                else:
                    self.regs[x] = key

            # Font character
            elif (subop == 0x29):
                self.ir = FONT_START + (self.regs[x] * FONT_SIZE)

            # Binary decimal conversion
            elif (subop == 0x33):
                val: byte = self.regs[x]
                units: byte = val % 10
                tens: byte = np.floor((val % 100) / 10)
                hundreds: byte = np.floor(val / 100)
                self.mem[self.ir : self.ir + 3] = [hundreds, tens, units]

            # Store registers
            elif (subop == 0x55):
                for i in range(x + 1):
                    self.mem[self.ir + i] = self.regs[i]

                if(self.io_mode == 0):
                    self.ir += 1 + x
                
            # Load registers
            elif(subop == 0x65):
                for i in range(x + 1):
                    self.regs[i] = self.mem[self.ir + i]

                if (self.io_mode == 0):
                    self.ir += 1 + x



    def __str__(self):
        return f"\
        [CPU]\n\
        Registers:\t{list(map(hex, self.regs))}\n\
        PC:\t{hex(self.pc)}\n\
        IR:\t{hex(self.ir)}\n\
        Timer:\t{self.delay.read()}\n\
        "