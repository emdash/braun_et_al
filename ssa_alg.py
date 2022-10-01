# Python translation of:
#
# Simple and Efficient Construction of Static Single Assignment Form
# Matthias Braun, Sebastian Buchwald, Sebastian Hack, Roland Leißa,
# Christoph Mallon, and Andreas Zwinkau

# There are some gaps, which might be filled in by delving into
# citations, in particular:
#
# > Cytron et al. [10] presented an efficient algorithm for
# > constructing it. This algorithm can be found in all textbooks
# > presenting SSA form and is used by the majority of compilers.
#
# 0. Cytron, R., Ferrante, J., Rosen, B.K., Wegman, M.N., Zadeck,
# F.K.: Efficiently computing static single assignment form and the
# control dependence graph.  TOPLAS 13(4), 451–490 (Oct 1991)
#
# > There are also a range of construction algorithms, which aim for
# > simplicity instead. Brandis and Mössenböck [5] present a simple SSA
# > construction algorithm that directly works on the AST like our
# > algorithm. However, their algorithm is restricted to structured
# > control flow (no gotos) and does not construct pruned SSA form.
#
# Brandis, M.M., Mössenböck, H.: Single-pass generation of static
# single-assignment form for structured languages. ACM
# Trans. Program. Lang. Syst. 16(6), 1684–1698 (Nov 1994)

## Inferred Code

# This section is my work, and reasonable best guess for details not
# presented in the paper.

@dataclass
class IRNode:
    pass

@dataclass
class Value(IRNode):
    pass

@dataclass
class Undef(Value):
    pass

@dataclass
class Operation(Value):
    name: str
    operands: [Value]

@dataclass
class Phi(Operation):
    block: Block
    users: [Value]

    def appendOperand(self, operand):
        self.operands.append(operand)

    def replaceBy(self, replacement):
        # implementation depends on details of IR basically we iterate
        # self.users, looking through each operand, replacing
        # ourselves with `replacement`.
        pass

@dataclass
class Variable(Value):
    name = str

@dataclass
class Block(IRNode):
    # unsure if this should be a set or sequence
    preds: set()
    defs: {str: Value}
    sealed: bool

incompletePhis = {}

## This is derived directly from the listings as presented in the literature.

# Algorithm 1

def writeVariable(variable, block, value):
    block.defs[variable.name] = value

def readVariable(variable, block):
    if variable.name in block.defs:
        # local value numbering
        return block.defs[variable.name]
    # global value numbering
    return readVariableRecursive(variable, block)

# Algorithm 2

def readVariableRecursive(variable, block):
    if not block.sealed:
        # incomplete CFG
        incompletePhis[block][variable] = Phi(block)
    elif len(block.preds) == 1:
        # Optimize the common case of one predecessor: no phi needed.
        val = readVariable(variable, block.preds[0])
    else:
        # Break potential cycles with operandless phi
        val = Phi(block)
        writeVariable(variable, block, val)
        val = addPhiOperands(variable, val)
    writeVariable(variable, block, val)
    return val

def addPhiOperands(variable, phi):
    # Determine operands from predecessors
    for pred in phi.block.preds:
        phi.appendOperand(readVariable(variable, pred))
    return tryRemoveTrivialPhi(phi)

# Algorithm 3

def tryRemoveTrivialPhi(phi):
    same = None
    for op in phi.operands:
        if op is same or op is phi:
            # unique value or self-reference
            continue
        if same is not None:
            # The phi merges at least two values: not trivial
            return phi
        same = op
    if same is None:
        # the phi is unreachable or in the start block
        same = Undef()
    # remember all users except the phi itself
    users = phi.users.remove(phi)
    phi.replaceBy(same)

    # try to recursively remove all phi users, which might have become
    # trivial.
    for use in users:
        if isinstance(use, Phi):
            tryRemoveTrivialPhi(use)
    return same

# Algorithm 4

def sealBlock(block):
    for variable in incompletePhis[block]:
        addPhiOperands(variable, incompletePhis[block][variable])
    block.sealed = True
