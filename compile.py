import sys
import types
import ctypes
import io

from antlr4 import *
from parser.GenericLexer import GenericLexer
from parser.GenericListener import GenericListener
from parser.GenericParser import GenericParser

from table.r3types import *

nodes = []
depth = 1

def fail(ctx, reason):
    sys.exit(f"error, line {ctx.start.line}: " + reason)

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

# Listener
class Listener(GenericListener):

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
        if not found: fail(ctx, f"no such callable method \"{name.getText()}\"")

        type, index = found[0], found[1]
        if type == "condition": makeNode(NodeType.Condition, index)
        if type == "function": makeNode(NodeType.Function, index)
        if type == "procedure": makeNode(NodeType.Procedure, index)
        if type == "subroutine": makeNode(NodeType.SubRoutine, index)
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
        if ctx.fieldAccessOperator(): d(-1)

    # Enter literal
    def enterLiteral(self, ctx):
        if ctx.numericLiteral(): makeNode(NodeType.Constant, ctx.numericLiteral().getText())
        if ctx.StringLiteral(): makeNode(NodeType.String, ctx.StringLiteral().getText())

    # Exit literal
    def exitLiteral(self, ctx):
        pass

    # Enter actor reference
    def enterActorReference(self, ctx):
        makeNode(NodeType.ActorRef, ctx.getText())

    # Enter DsgVar
    def enterDsgVar(self, ctx):
        if not ctx.numericLiteral(): fail("dsgvar is missing numeric identifier")
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
    input_stream = FileStream(argv[1])

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
