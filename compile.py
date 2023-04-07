import sys
import types
import ctypes
import io

from antlr4 import *
from parser.GenericLexer import GenericLexer
from parser.GenericListener import GenericListener
from parser.GenericParser import GenericParser

from table.r3types import *
from interface.level import *

nodes = []
depth = 1
targetActor = None

instanceNames = [
    # List fix actors
    # "StdCamer",
    # "global",
    # "ODA_Director",
    # "GenCamera",
    # "YAM_GenGratificator_I1",
    # "Rayman"
]

fix = None
level = None

def fail(ctx, reason):
    sys.exit(f"line {ctx.start.line}: " + reason)

def makeNode(type, param):
    global depth
    nodes.append([param, type, depth])

def d(i): # Change node depth
    global depth
    depth += i

def findCallable(fn):
    if fn in Conditions: return ["condition", Conditions.index(fn)]
    if fn in Functions: return ["function", Functions.index(fn)]
    if fn in Procedures: return ["procedure", Procedures.index(fn)]
    return None

def findActor(name):
    for a in level.actors:
        if name == a.name(instanceNames):
            return a
    return None

# Listener
class Listener(GenericListener):

    # Access actor or dsgVar?
    dotAccess = False

    # Current actor in dot access
    currentActor = None

    def enterSource(self, ctx):
        pass

    def enterIfStatement(self, ctx):
        condition = ctx.ifCondition()
        if not condition: fail(ctx, "missing condition in if statement")
        makeNode(NodeType.KeyWord, 0) # If `X`
        d(+1)

    def exitIfStatement(self, ctx):
        d(-1)

    def enterElseStatement(self, ctx):
        d(-1)
        makeNode(NodeType.KeyWord, 17) # Else
        d(+1)

    def exitElseStatement(self, ctx):
        pass

    def enterIfCondition(self, ctx):
        pass

    def exitIfCondition(self, ctx):
        d(-1)
        makeNode(NodeType.KeyWord, 16) # Then
        d(+1)

    # Enter function call
    def enterFunctionCall(self, ctx):
        name = ctx.functionName()
        if not name:
            fail(ctx, "unnamed callable")

        name = name.getText()

        # Attempt to find the method.
        found = findCallable(name)
        if found:
            type, index = found[0], found[1]
            if type == "condition": makeNode(NodeType.Condition, index)
            if type == "procedure": makeNode(NodeType.Procedure, index)
            if type == "function": # Function. Make sure it is called by dot access.
                if self.dotAccess == True:
                    fail(ctx, f"cannot call function \"{name}\" on an actor reference")
                else:
                    makeNode(NodeType.Function, index)
            d(+1)
            return
        elif self.dotAccess == False:
            global targetActor
            subroutine = targetActor.findMacro(name)
            if subroutine:
                makeNode(NodeType.SubRoutine, subroutine.offset)
                d(+1)
                return
            else:
                msg = f"no such method/subroutine \"{name}\" in actor {targetActor.name(instanceNames)}"
                suggestions = []
                for macro in targetActor.macros:
                    if macro.name.startswith(name[:10]): suggestions.append(macro.name)
                if len(suggestions) > 0:
                    msg += " - did you maybe mean one of the following?\n"
                    for s in suggestions:
                        msg += f"\t{s}\n"
                fail(ctx, msg)

        fail(ctx, f"no such callable method \"{name}\"")

        d(+1)

    # Exit function call
    def exitFunctionCall(self, ctx):
        d(-1)
        pass

    # Enter vector
    def enterVector(self, ctx):
        makeNode(NodeType.Vector, 0)
        d(+1)

    # Exit vector
    def exitVector(self, ctx):
        d(-1)

    # # Enter vector component
    # def enterVectorComponent(self, ctx):
    #     if ctx.getText() == "x" || ctx.getText() == "X": makeNode(NodeType.)
    #     makeNode(NodeType.Constant, int(ctx.getText()))
    #
    # # Exit vector component
    # def exitVectorComponent(self, ctx):
    #     pass

    # Enter expression sequence
    def enterExpressionSequence(self, ctx):
        pass

    # Exit expression sequence
    def exitExpressionSequence(self, ctx):
        #d(-1)
        pass

    # Enter single expression
    def enterSingleExpression(self, ctx):
        fieldAccessOperator = ctx.fieldAccessOperator()
        arithmeticOperator = ctx.arithmeticOperator()
        comparisonOperator = ctx.comparisonOperator()
        logicalOperator = ctx.logicalOperator()
        assignmentOperator = ctx.assignmentOperator()
        unaryOperator = ctx.unaryOperator()
        vectorComponent = ctx.vectorComponent()
        literal = ctx.literal()
        self = ctx.Self()
        actorReference = ctx.actorReference()

        def isVectorOp():
             # X op Y
            if len(ctx.children) > 2:
                if ctx.children[0].vector() or ctx.children[2].vector():
                    return True
            # Functions which return vectors
            #vectorFunctions = vectorFunctions()
            #if isVector

            return False

        if self:
            makeNode(NodeType.KeyWord, 19)

        if vectorComponent:
            if vectorComponent.getText() == "x" or vectorComponent.getText() == "X": makeNode(NodeType.Operator, 14)
            if vectorComponent.getText() == "y" or vectorComponent.getText() == "Y": makeNode(NodeType.Operator, 15)
            if vectorComponent.getText() == "z" or vectorComponent.getText() == "Z": makeNode(NodeType.Operator, 16)
            d(+1)

        if fieldAccessOperator:
            if fieldAccessOperator.getText() == ".": makeNode(NodeType.Operator, 13)
            self.dotAccess = True
            d(+1)

        if arithmeticOperator:
            if arithmeticOperator.getText() ==  "+": makeNode(NodeType.Operator, 17 if isVectorOp() else 0)
            if arithmeticOperator.getText() ==  "-": makeNode(NodeType.Operator, 18 if isVectorOp() else 1)
            if arithmeticOperator.getText() ==  "*": makeNode(NodeType.Operator, 20 if isVectorOp() else 2)
            if arithmeticOperator.getText() ==  "/": makeNode(NodeType.Operator, 21 if isVectorOp() else 3)
            if arithmeticOperator.getText() ==  "%": makeNode(NodeType.Operator, 5)
            if arithmeticOperator.getText() == "++": makeNode(NodeType.Operator, 10)
            if arithmeticOperator.getText() == "--": makeNode(NodeType.Operator, 11)
            d(+1)

        if comparisonOperator:
            if comparisonOperator.getText() == "==": makeNode(NodeType.Condition, 4)
            if comparisonOperator.getText() == "!=": makeNode(NodeType.Condition, 5)
            if comparisonOperator.getText() ==  "<": makeNode(NodeType.Condition, 6)
            if comparisonOperator.getText() ==  ">": makeNode(NodeType.Condition, 7)
            if comparisonOperator.getText() == "<=": makeNode(NodeType.Condition, 8)
            if comparisonOperator.getText() == ">=": makeNode(NodeType.Condition, 9)
            d(+1)

        if logicalOperator:
            if logicalOperator.getText() == "&&": makeNode(NodeType.Condition, 0)
            if logicalOperator.getText() == "||": makeNode(NodeType.Condition, 1)
            if logicalOperator.getText() ==  "^": makeNode(NodeType.Condition, 3)
            d(+1)

        if assignmentOperator:
            if assignmentOperator.getText() ==  "=": makeNode(NodeType.Operator, 12)
            if assignmentOperator.getText() == "+=": makeNode(NodeType.Operator, 6)
            if assignmentOperator.getText() == "-=": makeNode(NodeType.Operator, 7)
            if assignmentOperator.getText() == "*=": makeNode(NodeType.Operator, 8)
            if assignmentOperator.getText() == "/=": makeNode(NodeType.Operator, 9)
            d(+1)

        if unaryOperator:
            if unaryOperator.getText() == "+": pass # Do nothing
            if unaryOperator.getText() == "-": makeNode(NodeType.Operator, 19 if isVectorOp() else 4)
            if unaryOperator.getText() == "!": makeNode(NodeType.Condition, 2)
            d(+1)


        # if ctx.getChildCount() == 1 and literal:
        #     numericLiteral = literal.numericLiteral()
        #     # TODO: Handle strings
        #     makeNode(NodeType.Constant, literal.getText())
        #
        # if ctx.getChild
        #
        # if ctx.getChildCount() == 1 and actorReference:
        #     # TODO: Handle strings
        #     makeNode(NodeType.Constant, actorReference.getText())
        #

    # Exit single expression
    def exitSingleExpression(self, ctx):
        if ctx.arithmeticOperator(): d(-1)
        if ctx.assignmentOperator(): d(-1)
        if ctx.comparisonOperator(): d(-1)
        if ctx.logicalOperator(): d(-1)
        if ctx.unaryOperator(): d(-1)
        if ctx.vectorComponent(): d(-1)
        if ctx.fieldAccessOperator():
            self.dotAccess = False
            d(-1)

    # Enter literal
    def enterLiteral(self, ctx):
        if ctx.numericLiteral(): makeNode(NodeType.Constant, int(ctx.numericLiteral().getText()))
        if ctx.StringLiteral(): makeNode(NodeType.String, ctx.StringLiteral().getText())

    # Exit literal
    def exitLiteral(self, ctx):
        pass

    # Enter actor reference
    def enterActorReference(self, ctx):
        name = ctx.getText()
        if not name in instanceNames:
            msg = f"no such actor \"{name}\""
            suggestions = []
            for n in instanceNames:
                if n.startswith(name[:5]): suggestions.append(n)
            if len(suggestions) > 0:
                msg += " - did you maybe mean one of the following?\n"
                for s in suggestions:
                    msg += f"\t{s}\n"

            fail(ctx, msg)
        actor = findActor(name)
        makeNode(NodeType.ActorRef, actor.offset)

    # Enter DsgVar
    def enterDsgVar(self, ctx):
        if not ctx.numericLiteral(): fail(ctx, "dsgvar is missing numeric identifier")
        makeNode(NodeType.DsgVarRef2, int(ctx.numericLiteral().getText()))

    # Enter field
    def enterField(self, ctx):
        index = Fields.index(ctx.getText())
        makeNode(NodeType.Field, index)

    # Exit field
    def exitField(self, ctx):
        pass

# Print the node tree
def printTree():
    for node in nodes:
        print(f"{' ' * node[2] * 4}{NodeTypes[node[1]]}: {node[0]}    ({node[2]})")

# Write the node tree to a file.
# All object references are ignored.
def writeTree(fileName):
    f = open(fileName, "wb")
    for node in nodes:
        param, Type, depth = node[0], node[1], node[2]
        if type(param) is not int: param = 0

        f.write(ctypes.c_uint(swap32(param))) # Param
        f.write(ctypes.c_byte(0)) # Padding
        f.write(ctypes.c_byte(0)) # Padding
        f.write(ctypes.c_byte(0)) # Padding
        f.write(ctypes.c_byte(Type)) # Type
        f.write(ctypes.c_byte(0)) # Padding
        f.write(ctypes.c_byte(0)) # Padding
        f.write(ctypes.c_byte(depth)) # Depth
        f.write(ctypes.c_byte(0)) # Padding
    f.close()

# def arborist(tree):
#     for i in range(len(tree)):
#         current = tree[i]
#         if current[1] ==

def main(argv):
    if len(argv) < 5:
        print("usage: compile.py [sourcefile] [target_actor@rule] [fix.lvl] [level.lvl]")
        exit()

    sourceFile = argv[1]
    target = argv[2]
    fixFile = argv[3]
    levelFile = argv[4]

    global fix
    global level
    global targetActor

    fix = LVL(fixFile)
    level = LVL(levelFile)

    try:
        input_stream = FileStream(sourceFile)
    except FileNotFoundError:
        print(f"Could not find \"{sourceFile}\": no such file exists")
        exit()

    replacee = target.split('@')
    if len(replacee) < 2: sys.exit("No target actor or rule specified.")
    targetActorName = replacee[0]
    targetActorRule = replacee[1]

    fix.loadAsFix()
    level.loadAsLevel(fix)

    # level.otherFile = fix
    # fix.otherFile = level

    # Read actor instance names
    level.readInstanceNames(instanceNames)

    targetActor = findActor(targetActorName)
    if not targetActor:
        print("Invalid target actor. Specify one of the following:")
        for actor in level.actors:
            print(f"\t{actor.name(instanceNames)}")
        exit()

    if not targetActor.findMacro(targetActorRule):
        print("Invalid target replacee. Specify one of the following:")
        for macro in targetActor.macros:
            print(f"\t{macro.name}")
        exit()

    # for a in level.actors:
    #     print(a.name(instanceNames))

    # Set up the parser.
    lexer = GenericLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = GenericParser(stream)
    walker = ParseTreeWalker()
    listener = Listener()

    # Remove all error listeners.
    lexer.removeErrorListeners()
    # Fetch the source rule.
    tree = parser.source()
    # Process the tree.
    walker.walk(listener, tree)

    global depth; depth = 0
    makeNode(NodeType.EndMacro, 0)

    printTree()

    writeTree("test.bin")

if __name__ == '__main__':
    main(sys.argv)
