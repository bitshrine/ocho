# A timer
class Timer:
    def __init__(self):
        self.value = 0

    def countDown(self):
        if (self.value > 0):
            self.value -= 1

    def set(self, value):
        self.value = value

    def read(self):
        return self.value


class SoundTimer(Timer):

    def __init__(self):
        Timer.__init__(self)

    def beep(self):
        if (self.value > 0):
            print(end='\a')
            self.value = 0