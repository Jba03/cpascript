from interface import *
from .util import *

class SuperObject:
    def __init__(self, level, offset):
        self.offset = offset
        checkpoint = level.position()
        level.seek(offset)

        level.seek(checkpoint)

class StdGame:
    def __init__(self, level, offset):
        self.offset = offset
        checkpoint = level.position()
        level.seek(offset)
        self.familyType = level.read32()
        self.modelType = level.read32()
        self.instanceType = level.read32()
        self.superObject = level.readpointer()

        #print(self.superObject)

        # if self.superObject[1] != 0:
        #     if self.superObject[0] == 0:
        #         self.superObject = SuperObject(level, self.superObject[1])
        #     elif self.superObject[0] == 1:
        #         self.superObject = SuperObject(level.otherFile, self.superObject[1])
        #if self.superObject[0] == 1: # Read from level
        level.seek(checkpoint)

class Macro:
    def __init__(self, level):
        self.offset = level.position()
        self.name = level.readchars(0x100)
        self.initialScript = level.readpointer()
        self.currentScript = level.readpointer()
        self.fullname = "".join(map(chr, self.name))
        self.name = self.fullname.split(':')[1]
        self.name = self.name.split('\0')[0]

class MacroList:
    macroList = None
    def __init__(self, level, offset):
        self.offset = offset
        checkpoint = level.position()
        level.seek(offset)
        self.macros = level.readpointer()
        #print(level.position())
        self.numMacros = swap32(level.read32())

        # Seek to list beginning
        level.seek(self.macros[1])
        if self.numMacros > 0:
            self.macroList = []
        # Read macros
        for i in range(self.numMacros):
            macro = Macro(level)
            self.macroList.append(macro)

        level.seek(checkpoint)

class AIModel:
    macroList = None
    def __init__(self, level, offset):
        self.offset = offset
        checkpoint = level.position()
        level.seek(offset)
        self.intelligenceList = level.readpointer()
        self.reflexList = level.readpointer()
        self.dsgVar = level.readpointer()
        self.macroList = level.readpointer()
        if self.macroList[1] != 0x00:
            self.macroList = MacroList(level, self.macroList[1])
        else:
            self.macroList = None
        level.seek(checkpoint)

class Mind:
    AIModel = None
    def __init__(self, level, offset):
        self.offset = offset
        checkpoint = level.position()
        level.seek(offset)
        aiModel = level.readpointer()
        if aiModel[1] != 0x00:
            self.AIModel = AIModel(level, aiModel[1])
        level.seek(checkpoint)

class Brain:
    mind = None
    def __init__(self, level, offset):
        self.offset = offset
        checkpoint = level.position()
        level.seek(offset)
        mind = level.readpointer()
        if mind[1] != 0x00:
            self.mind = Mind(level, mind[1])
        level.seek(checkpoint)

class Actor:
    def __init__(self, level, offset):
        self.offset = offset
        checkpoint = level.position()
        level.seek(offset)
        #print(hex(level.position()))
        self.p3Ddata = level.readpointer()
        self.stdGame = level.readpointer()
        self.dynam = level.readpointer()
        self.brain = level.readpointer()

        #print(self.brain)

        #if self.stdGame[0] == 0: # Read from fix
        self.stdGameStruct = StdGame(level, self.stdGame[1])
        self.brain = Brain(level, self.brain[1])

        self.instanceNameIndex = self.stdGameStruct.instanceType
        self.superObject = self.stdGameStruct.superObject

        self.macros = []
        if self.brain:
            if self.brain.mind:
                if self.brain.mind.AIModel:
                    if self.brain.mind.AIModel.macroList:
                        if len(self.brain.mind.AIModel.macroList.macroList) > 0:
                            for macro in self.brain.mind.AIModel.macroList.macroList:
                                self.macros.append(macro)

        # for a in self.macroList:
        #     print("\t" + a.name)


        level.seek(checkpoint)

    def name(self, namelist):
        #print(len(namelist))
        #print(self.stdGameStruct.instanceType)
        return namelist[self.stdGameStruct.instanceType]

    def findMacro(self, macroName):
        for macro in self.macros:
            if macroName == macro.name:
                return macro
        return None
