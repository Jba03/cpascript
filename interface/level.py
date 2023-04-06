import io
import os

from .util import *
from array import array
from .structure import *

class LVL:
    directory = ""
    filename = ""

    ptrFile = None
    lvlFile = None
    fix = None
    pointers = {}

    numTextures = 0
    instanceNames = []
    actors = []

    # If the file is *.lvl, this references fix.lvl.
    # If the file is fix.lvl, this references *.lvl.
    otherFile = None

    def baseFilePath(self):
        return self.directory + self.filename

    def readPTR(self):
        numPointers = self.ptrFile.read32()
        # Read pointers.
        for i in range(numPointers):
            fileID = self.ptrFile.read32()
            doublePointer = self.ptrFile.read32()
            #print("seek " + hex(doublePointer + 4))
            self.lvlFile.seek(doublePointer + 4) # +4: skip pointer count
            self.pointers[doublePointer + 4] = [fileID, self.lvlFile.read32() + 4]


        # for keys,values in self.pointers.items():
        #     print(hex(keys) + ":  " + hex(values))

        # R3
        # numFillInPointers = int((total - self.ptrFile.position()) / 16)
        # print("num fill: " + str(total) + "  " + str(self.ptrFile.position()))
        # for i in range(numFillInPointers):
        #     doublePointer = self.ptrFile.read32()
        #     sourceFileID = self.ptrFile.read32()
        #     pointer = self.ptrFile.read32()
        #     targetFileID = self.ptrFile.read32()

    def readpointer(self):
        value = self.lvlFile.read32()
        offset = self.lvlFile.position() - 4
        #print("location: " + hex(offset))
        #print(self.pointers[offset])
        #data = self.pointers[offset]
        return self.pointers.get(offset, [0, 0])

    def loadAsFix(self):
        read = self.lvlFile.read
        seek = self.lvlFile.seek
        read8 = self.lvlFile.read8
        read16 = self.lvlFile.read16
        read32 = self.lvlFile.read32

        # Base + ? + matrix + localization
        seek(4 * 6)
        # Text
        read(20)

        levelNameCount = read32()
        demoNameCount = read32()

        # Demo save names
        read(12 * demoNameCount)
        # Demo level names
        read(12 * demoNameCount)
        # Level names
        read(30 * (levelNameCount + 1))
        # Language
        read(10)
        # Texture count
        self.numTextures = read32()
        # Skip textures
        read(4 * self.numTextures)
        # Skip menu textures
        read(4 * read32())
        # Skip file textures
        #read(4 * self.numTextures)
        # Skip memory channels
        read(4 * self.numTextures)
        # Skip input structure (for now)
        read(0x12E0 + 0x8 + 0x418 + 0xE8)

        numActors = read32()
        for i in range(numActors):
            offset = self.readpointer()[1]
            actor = Actor(self, offset)
            self.actors.append(actor)

    def loadAsLevel(self, fix):
        read = self.lvlFile.read
        seek = self.lvlFile.seek
        read8 = self.lvlFile.read8
        read16 = self.lvlFile.read16
        read32 = self.lvlFile.read32
        readchars = self.lvlFile.readchars
        self.fix = fix

        seek(4)
        read(4 * 4 + 24 + 4 * 60)

        # Compute the texture count
        self.numTextures = read32() - fix.numTextures
        # Skip all textures
        read(self.numTextures * 4 * 2)

        #print(self.position())
        #actualWorld = self.readpointer()
        #dynamicWorld = self.readpointer()
        #inactiveDynamicWorld = self.readpointer()
        #fatherSector = self.readpointer()

        # Skip until object types
        read(12 * 4)

        self.familyList = List(self)
        self.modelList = List(self)
        self.instanceList = List(self)

    def readInstanceNames(self, array):
        def addInstanceName(s, h=self.lvlFile):
            # Skip next, prev and father
            h.seek(s + 4 * 3)
            name, data, pointer = "NULL", [], self.readpointer()

            if pointer[0] == 0:
                # Read name from fix
                self.fix.lvlFile.seek(pointer[1])
                data = self.fix.lvlFile.readstring()

            elif pointer[0] == 1:
                # Read name from level
                h.seek(pointer[1])
                data = h.readstring()

            name = "".join(map(chr, data))
            array.append(name)

        self.instanceList.forEach(addInstanceName)

    def __init__(self, path):
        self.filename = os.path.basename(path)
        self.directory = path.replace(self.filename, "")
        self.filename = self.filename.replace(".lvl", "")

        self.lvlFile = BinaryFile(self.baseFilePath() + ".lvl", "rb")
        self.ptrFile = BinaryFile(self.baseFilePath() + ".ptr", "rb")

        self.seek = self.lvlFile.seek
        self.read8 = self.lvlFile.read8
        self.read16 = self.lvlFile.read16
        self.read32 = self.lvlFile.read32
        self.position = self.lvlFile.position
        self.readchars = self.lvlFile.readchars

        self.readPTR()
