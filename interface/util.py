import os
import io

def swap32(x):
    return (((x << 24) & 0xFF000000) |
            ((x <<  8) & 0x00FF0000) |
            ((x >>  8) & 0x0000FF00) |
            ((x >> 24) & 0x000000FF))

def arbRead(a):
    result = 0
    for x in a:
        result = result | a
    return result

class List:
    def __init__(self, level):
        self.level = level
        self.start = level.readpointer()[1]
        self.end = level.readpointer()[1]
        self.count = level.lvlFile.read32()

    def forEach(self, callback):
        checkpoint = self.level.position()
        self.level.seek(self.start)

        for i in range(self.count - 1):
            next = self.level.readpointer()
            callback(self.level.position() - 4)
            self.level.seek(next[1])


class BinaryFile:
    h = None
    valid = True

    def seek(self, offset):
        self.h.seek(offset, os.SEEK_SET)

    def position(self):
        return self.h.tell()

    def read(self, sz):
        result = 0
        for x in self.h.read(sz):
            result = (result << 8) | x
        return result

    def read8(self):
        return self.read(1)

    def read16(self):
        return self.read(2)

    def read32(self):
        return self.read(4)

    def readchars(self, count):
        chars = []
        for i in range(count):
            chars.append(self.read8())
        return chars

    def readstring(self):
        chars = []
        while True:
            c = self.read8()
            if c == 0: break
            chars.append(c)
        return chars

    def size(self):
        if not self.h: return 0
        self.h.seek(0, os.SEEK_END)
        fileSize = self.h.tell()
        self.h.seek(0, os.SEEK_SET)
        return fileSize

    def __init__(self, path, mode = "rb"):
        try: self.h = open(path, mode)
        except FileNotFoundError:
            print(f"could not find {path}: no such file exists")
            exit()
