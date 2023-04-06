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
    dotAccess = False
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

        # Attempt to find the method.
        found = findCallable(name.getText())
        if found:
            type, index = found[0], found[1]
            if type == "condition": makeNode(NodeType.Condition, index)
            if type == "procedure": makeNode(NodeType.Procedure, index)
            if type == "function": # Function. Make sure it is called by dot access.
                if self.dotAccess == True:
                    fail(ctx, f"cannot call function \"{name.getText()}\" on an actor reference")
                else:
                    makeNode(NodeType.Function, index)
            return
        elif self.dotAccess == False:
            name = name.getText()
            global targetActor
            subroutine = targetActor.findMacro(name)
            if subroutine:
                makeNode(NodeType.SubRoutine, subroutine.offset)
            else:
                msg = f"no such subroutine \"{name}\" in actor {targetActor.name(instanceNames)}"
                suggestions = []
                for macro in targetActor.macros:
                    if macro.name.startswith(name[:10]): suggestions.append(macro.name)
                if len(suggestions) > 0:
                    msg += " - did you maybe mean one of the following?\n"
                    for s in suggestions:
                        msg += f"\t{s}\n"
                fail(ctx, msg)

        fail(ctx, f"no such callable method \"{name.getText()}\"")

        d(+1)

    # Exit function call
    def exitFunctionCall(self, ctx):
        d(-1)

    # Enter vector
    def enterVector(self, ctx):
        makeNode(NodeType.Vector, 0)
        d(+1)

    # Exit vector
    def exitVector(self, ctx):
        d(-1)

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
        conditionalOperator = ctx.conditionalOperator()
        assignmentOperator = ctx.assignmentOperator()
        literal = ctx.literal()
        actorReference = ctx.actorReference()

        if fieldAccessOperator:
            if fieldAccessOperator.getText() == ".": makeNode(NodeType.Operator, 13)
            self.dotAccess = True
            d(+1)

        if arithmeticOperator:
            if arithmeticOperator.getText() ==  "+": makeNode(NodeType.Operator, 0)
            if arithmeticOperator.getText() ==  "-": makeNode(NodeType.Operator, 1)
            if arithmeticOperator.getText() ==  "*": makeNode(NodeType.Operator, 2)
            if arithmeticOperator.getText() ==  "/": makeNode(NodeType.Operator, 3)
            if arithmeticOperator.getText() ==  "%": makeNode(NodeType.Operator, 5)
            if arithmeticOperator.getText() == "++": makeNode(NodeType.Operator, 10)
            if arithmeticOperator.getText() == "--": makeNode(NodeType.Operator, 11)
            d(+1)

        if conditionalOperator:
            if conditionalOperator.getText() == "&&": makeNode(NodeType.Condition, 0)
            if conditionalOperator.getText() == "||": makeNode(NodeType.Condition, 1)
            if conditionalOperator.getText() ==  "!": makeNode(NodeType.Condition, 2)
            if conditionalOperator.getText() ==  "^": makeNode(NodeType.Condition, 3)
            if conditionalOperator.getText() == "==": makeNode(NodeType.Condition, 4)
            if conditionalOperator.getText() == "!=": makeNode(NodeType.Condition, 5)
            if conditionalOperator.getText() ==  "<": makeNode(NodeType.Condition, 6)
            if conditionalOperator.getText() ==  ">": makeNode(NodeType.Condition, 7)
            if conditionalOperator.getText() == "<=": makeNode(NodeType.Condition, 8)
            if conditionalOperator.getText() == ">=": makeNode(NodeType.Condition, 9)
            d(+1)

        if assignmentOperator:
            if assignmentOperator.getText() ==  "=": makeNode(NodeType.Operator, 12)
            if assignmentOperator.getText() == "+=": makeNode(NodeType.Operator, 6)
            if assignmentOperator.getText() == "-=": makeNode(NodeType.Operator, 7)
            if assignmentOperator.getText() == "*=": makeNode(NodeType.Operator, 8)
            if assignmentOperator.getText() == "/=": makeNode(NodeType.Operator, 9)
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
        if ctx.conditionalOperator(): d(-1)
        if ctx.fieldAccessOperator():
            self.dotAccess = False
            d(-1)

    # Enter literal
    def enterLiteral(self, ctx):
        if ctx.numericLiteral(): makeNode(NodeType.Constant, ctx.numericLiteral().getText())
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
        makeNode(NodeType.DsgVarRef, ctx.numericLiteral().getText())

    # Enter field
    def enterField(self, ctx):
        makeNode(NodeType.Field, ctx.getText())

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

        f.write(ctypes.c_uint(param)) # Param
        f.write(ctypes.c_byte(Type)) # Type
        f.write(ctypes.c_byte(depth)) # Depth
    f.close()

def main(argv):
    if len(argv) < 4:
        print("usage: compile.py <fix.lvl> <level.lvl> <sourcefile>")
        exit()

    fixFile = argv[1]
    levelFile = argv[2]
    sourceFile = argv[3]

    global fix
    global level
    global targetActor

    fix = LVL(fixFile)
    level = LVL(levelFile)
    input_stream = FileStream(sourceFile)

    fix.loadAsFix()
    level.loadAsLevel(fix)

    # fix.fillInPointers()
    # level.fillInPointers()

    # level.otherFile = fix
    # fix.otherFile = level

    level.readInstanceNames(instanceNames)
    #level.loadActors()

    targetActor = findActor("Rayman")
    if not targetActor:
        print("invalid target actor")
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

    #writeTree("test.bin")

if __name__ == '__main__':
    main(sys.argv)
