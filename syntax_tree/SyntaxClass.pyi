from typing import List, Dict, Set, Optional, Tuple, Any
from syntax_tree.Exceptions import *
from syntax_tree.graph import Vertex,Graph

class ConstValue:
    type: SyntaxType
    value: Any

    def __init__(self, syntax_type: SyntaxType, value: Any):...
    def type_belong_to(self, syntaxType: SyntaxType) -> bool:...
    def get_size(self) -> int:...
    def __repr__(self) -> str:...


class HasRhs:
    rhsList: List[Set[str]]
    lhsTypeList: List[SyntaxType]

    def __init__(self):...
    def absorb_rhs(self, tar: HasRhs):...
    def set_rhs(self, rhs: Optional[List[str]]):...
    def add_rhs(self, rhs: List[str]):...
    def has_name_in_rhs(self, name: str) -> bool:...
    def add_lhs_type(self, type: SyntaxType):...
    def set_lhs_type(self, type_list: List[SyntaxType]):...


class SyntaxOperator(HasRhs):
    subtype: str
    objects: List[Any]
    appliedUserOp: Optional[SyntaxUserOp]
    array_length: int
    prefix_op_2_expr_dict: dict[tuple:list[str]]

    def __init__(self, subtype: str):...
    def add_object(self, object: Any):...
    def set_array_length(self, length: int):...
    def __repr__(self) -> str:...


class SyntaxExpr(HasRhs):
    type: str
    subType: str
    objects: List[Any]
    scope: SyntaxScope
    syntaxSymbol: Optional[SyntaxVariableSymbol]
    idx_list: Optional[list[int]]
    appliedOp: Optional[SyntaxUserOp]
    appliedOpContextList: List[int]
    appliedOpOutCName: str
    returnNum: int
    binop_dict:dict[str,str]
    def __init__(self, type: str, subtype: str, scope: SyntaxScope, objects: Optional[List[Any]] = None, returnNum: int = 1):...
    def add_object(self, tar_object: Any, index: Optional[int] = None):...
    def set_symbol(self, symbol: SyntaxVariableSymbol):...
    def add_applied_Op(self, applied_Op: SyntaxUserOp, context_list: List[int]):...
    def __repr__(self) -> str:...
    def get_type_and_value_for_atom(self) -> Tuple[str, Any]:...


class SyntaxEquation(HasRhs):
    type: str
    expr: Optional[SyntaxExpr]
    controlBlockID: str
    assertID: str
    emit: bool
    lineno: int
    lhs: List[str]
    lhs2RhsDict: Dict[str, Any]
    vertex: Optional[Vertex]
    scope: SyntaxDataDefScope

    def __init__(self, type: str, lhs: List[str], lineno: int = -1):...
    def set_expr(self, expr: SyntaxExpr):...
    def set_vertex(self, vertex: Vertex):...
    def set_scope(self, scope: SyntaxDataDefScope):...
    def equation2str(self, depth: int = 0) -> str:...
    def dependent_on_param_directly(self, param_name: str) -> bool:...
    def dependent_on_equation_directly_and_get_correspond_lhs(self, tar_equation: SyntaxEquation) -> Optional[str]:...
    def get_dependent_equations(self) -> List[SyntaxEquation]:...
    def get_rhs_list_by_name(self, lhs: str) -> Optional[List[str]]:...
    def __repr__(self) -> str:...


class SyntaxType:
    name: str
    scope: Optional[SyntaxScope]
    type: str
    sizeExpr: Optional[SyntaxExpr]
    fields: Optional[list[list[str or 'SyntaxTypeSymbol']]]
    enumList: Optional[List[SyntaxConstSymbol]]
    value: Optional[str]
    arrayType: Optional[SyntaxType]
    basic_type: list[str]
    extend_type: list[str]
    hierarchy_dict: dict[str:str]
    _size: int or None
    min_size: Optional[int]
    def __init__(self, tar_type: str, scope: Optional[SyntaxScope] = None):...
    def __repr__(self) -> str:...
    def change_name(self) -> str:...
    def change_name_cast(self) -> str:...
    def generate_init_expr(self) -> str:...
    def belong_to(self, tar_type: SyntaxType) -> bool:...
    def __eq__(self, other: SyntaxType) -> bool:...
    def __ne__(self, other: SyntaxType) -> bool:...
    def __le__(self, other: SyntaxType) -> bool:...
    def __lt__(self, other: SyntaxType) -> bool:...
    def get_real_type(self) -> SyntaxType:...
    def is_basic_type(self) -> bool:...
    def resolve_path_id(self) -> SyntaxType:...
    def get_size(self) -> int:...
    def set_size(self, size: int):...
    def set_element_and_size(self, array_type: SyntaxType, size: int) -> SyntaxType:...
    def get_element_type_for_array(self) -> SyntaxType:...


class SyntaxTypeSymbol:
    name: str
    visibility: str
    isImported: bool
    syntaxType: Optional[SyntaxType]
    numericKind: str

    def __init__(self, name: str, syntaxType: Optional[SyntaxType] = None, visibility: str = "public"):...
    def __repr__(self) -> str:...


class SyntaxConstSymbol:
    name: str
    visibility: str
    isImported: bool
    scope: SyntaxScope
    syntaxType: SyntaxType
    valueExpr: Optional[SyntaxExpr]
    __value: Optional[ConstValue]
    used: bool

    def __init__(self, name: str, scope: SyntaxScope, visibility: str = "public", imported: bool = False):...
    def __repr__(self) -> str:...
    def get_value(self) -> ConstValue:...
    def set_value(self, value: ConstValue):...
    def change_name(self) -> str:...


class SyntaxSensorSymbol:
    name: str
    syntaxType: SyntaxType

    def __init__(self, name: str):...
    def __repr__(self) -> str:...


class SyntaxGroupSymbol:
    name: str
    visibility: str
    groupExpr: List[SyntaxType]

    def __init__(self, name: str, visibility: str):...
    def __repr__(self) -> str:...


class SyntaxPattern(HasRhs):
    type: str
    value: str

    def __init__(self, type: str, value: str):...
    def __repr__(self) -> str:...


class SyntaxClockExpr(HasRhs):
    ID: str
    type: str
    pattern: Optional[SyntaxPattern]

    def __init__(self, ID: str, type: str):...
    def __repr__(self) -> str:...


class SyntaxVariableSymbol:
    name: str
    isClock: bool
    isProbe: bool
    isOutput: bool
    isInput: bool
    syntaxType: SyntaxType
    whenExpr: Optional[SyntaxClockExpr]
    defaultExpr: Optional[SyntaxExpr]
    lastExpr: Optional[SyntaxExpr]
    postExpr: Optional[List[str]] or Optional[str]

    def __init__(self, name: str, isClock: bool, isProbe: bool):...
    def __repr__(self) -> str:...


class SyntaxScope:
    type: str
    name: str
    prevScope: Optional[SyntaxPackageScope]
    childScopeTable: Dict[str, SyntaxScope]
    visibility: str
    anonymousScopeCount: int
    annoymousTmpCount: int
    initSymbolSet: Set[SyntaxVariableSymbol]
    tmpParams: List[SyntaxVariableSymbol]

    def __init__(self, type: str, name: str, prevScope: Optional[SyntaxScope], visibility: str):...
    @property
    def hasInternalState(self) -> bool:...
    def add_childScope(self, childScope: SyntaxScope):...
    def get_childScope(self, scopeName: str) -> Optional[SyntaxScope]:...
    def childScope2str(self, depth: int = 0) -> str:...
    def generate_name_for_subScope(self) -> str:...
    def get_global_name(self) -> str:...
    def add_tmpSymbol(self, tmpSymbol: SyntaxVariableSymbol):...
    def get_tmpSymbol(self, tmpSymbolName: str) -> Optional[SyntaxVariableSymbol]:...
    def get_localVariable_InThisAndPreEnv(self, name) -> Optional[SyntaxVariableSymbol]:...
    def get_my_userOp(self) -> SyntaxUserOp:...
    def get_my_op_or_state(self) -> SyntaxScope:...
    def get_my_package(self) -> SyntaxPackageScope:...
    def resolve_path(self, path_list: List[str]) -> SyntaxPackageScope:...
    def resolve_path_id(self, path_id: str) -> Tuple[SyntaxPackageScope, str]:...
    def check_and_get_userOp(self, path_id: str) -> Optional[SyntaxUserOp]:...
    def check_and_get_constant_param(self, param_path_id: str) -> Optional[SyntaxConstSymbol]:...
    def check_and_get_type_symbol(self, type_path_id: str) -> Optional[SyntaxTypeSymbol]:...
    def var_change_name(self, name: str) -> str:...


class SyntaxIfBlock:
    conditionExpr: SyntaxExpr
    scope: SyntaxDataDefScope
    thenBlock: Any
    elseBlock: Any

    def __init__(self, expr: SyntaxExpr, thenBlock, elseBlock, scope):
        ...

    def __repr__(self) -> str:
        ...

    def block2str(self, depth: int = 0) -> str:
        ...


class SyntaxMatchBlock:
    switchExpr: SyntaxExpr
    matchList: List[Tuple[SyntaxPattern, str]]

    def __init__(self, expr: SyntaxExpr, matchList: List[Tuple[SyntaxPattern, str]]):
        ...

    def __repr__(self) -> str:
        ...

    def block2str(self, depth: int = 0) -> str:
        ...


class SyntaxClockedScope(SyntaxScope):
    block: SyntaxIfBlock or SyntaxMatchBlock
    prevScope: 'SyntaxDataDefScope'
    childScopeTable: dict
    visibility: str = "public"
    type: str
    '''为if_block或者match_block'''
    name: str

    def __init__(self, type: str, name: str, prevscope: SyntaxScope, visibility: str):
        ...

    def __repr__(self) -> str:
        ...

    def get_localVariable_InThisAndPreEnv(self, name: str) -> SyntaxVariableSymbol or None:
        ...

    def get_return_symbolTable(self) -> Dict[str, SyntaxVariableSymbol]:
        ...

    def scope2str(self, depth: int = 0) -> str:
        ...


class SyntaxDataDefScope(SyntaxScope):
    type: str
    name: str
    prevScope: SyntaxScope
    childScopeTable: Dict[str, SyntaxScope]
    visibility: str
    equations: List[SyntaxEquation]
    signalSymbolSet: Set[str]
    localSymbolTable: Dict[str, SyntaxVariableSymbol]
    returnSymbolsTable: Dict[str, SyntaxVariableSymbol]
    initVar: Optional[SyntaxVariableSymbol]
    equationDependentGraph: Graph
    lhs2EquationDict: Dict[str, SyntaxEquation]

    def __init__(self, type: str, name: str, prevscope: SyntaxScope, visibility: str):
        ...

    def is_param_declared_externally(self, param_name: str) -> bool:
        ...

    def add_equation(self, input_equation: SyntaxEquation):
        ...

    def get_equation_by_lhs(self, lhs: str) -> Optional[SyntaxEquation]:
        ...

    def get_localVariable(self, name: str) -> SyntaxVariableSymbol or None:
        ...

    def get_localVariable_InThisAndPreEnv(self, name: str) -> SyntaxVariableSymbol or None:
        ...

    def have_signal_InThisAndPreEnv(self, name: str) -> bool:
        ...

    def generate_name_for_tmp(self, postfix: str = "tmp") -> str:
        ...

    def set_init_var(self) -> SyntaxVariableSymbol:
        ...

    def var_change_name(self, name: str) -> str:
        ...

    def get_return_symbolTable(self) -> Dict[str, SyntaxVariableSymbol]:
        ...

    def set_signalSymbolList(self, signalSymbolList: List[str]):
        ...

    def add_localSymbols(self, localSymbolList: List[SyntaxVariableSymbol]):
        ...

    def scope2str(self, depth: int = 0) -> str:
        ...

    def signalSymbolSet2str(self, depth: int = 0) -> str:
        ...

    def localSymbolTable2str(self, depth: int = 0) -> str:
        ...

    def equations2str(self, depth: int = 0) -> str:
        ...


class SyntaxArrow:
    action: Optional[str]
    type: str
    target: Optional[str]
    targetIndex: int
    ifExprList: List[Tuple[SyntaxExpr, SyntaxArrow]]
    elseExpr: Optional[SyntaxArrow]

    def __init__(self, type: str, target: Optional[str] = None, ifExpr: Optional[List[Tuple[SyntaxExpr, SyntaxArrow]]] = None, elseExpr: Optional[SyntaxArrow] = None):
        ...

    def set_action(self, action: str):
        ...

    def get_transfer_arrows(self) -> List[SyntaxArrow]:
        ...

    def set_index(self, index: int) -> int:
        ...

    def __repr__(self) -> str:
        ...

    def arrow2str(self, depth: int = 0) -> str:
        ...


class SyntaxState(SyntaxDataDefScope):
    prevScope: 'SyntaxAutomaton'
    isInitial: bool
    isFinal: bool
    unlessTransitions: List[Tuple[SyntaxExpr, SyntaxArrow]]
    untilTransitions: List[Tuple[SyntaxExpr, SyntaxArrow]]
    synchroArrow: Optional[SyntaxArrow]
    actionChildScopeList: List[SyntaxDataDefScope]
    apply_exprs: List[SyntaxExpr]

    def __init__(self, type: str, name: str, prevscope: SyntaxScope, visibility: str):
        ...

    def set_synchroArrow(self, synchroArrow: SyntaxArrow):
        ...

    def set_unlessTransitions(self, unlessTransitions: List[Tuple[SyntaxExpr, SyntaxArrow]]):
        ...

    def set_untilTransitions(self, untilTransitions: List[Tuple[SyntaxExpr, SyntaxArrow]]):
        ...

    def add_action_subscope(self, action: SyntaxDataDefScope):
        ...

    def get_strong_transfer_arrows(self) -> List[SyntaxArrow]:
        ...

    def get_enum_name(self) -> str:
        ...

    def __repr__(self) -> str:
        ...

    def scope2str(self, depth: int = 0) -> str:
        ...


class SyntaxAutomaton(SyntaxScope):
    type: str
    name: str
    prevScope: SyntaxDataDefScope
    childScopeTable: Dict[str, SyntaxDataDefScope]
    visibility: str
    stateTable: Dict[str, SyntaxState]
    transferGraph: Graph
    transferCount: int

    def __init__(self, type: str, name: str, prevscope: SyntaxDataDefScope, visibility: str):
        ...

    def add_state(self, state: SyntaxState):
        ...

    def add_edge(self, from_name: str, to_name: str, arrow: SyntaxArrow):
        ...

    def get_init_state(self) -> SyntaxState:
        ...

    def get_return_symbolTable(self) -> Dict[str, SyntaxVariableSymbol]:
        ...

    def __repr__(self) -> str:
        ...

    def scope2str(self, depth: int = 0) -> str:
        ...

    def graph2str(self, depth: int = 0) -> str:
        ...


class SyntaxUserOp(SyntaxDataDefScope):
    type: str
    name: str
    prevScope: SyntaxScope
    childScopeTable: Dict[str, SyntaxScope]
    equations: List[SyntaxEquation]
    visibility: str
    isImported: bool
    sizeParams: list[SyntaxConstSymbol]
    inParams: List[SyntaxVariableSymbol]
    outParams: List[SyntaxVariableSymbol]
    numericKind: Optional[str]
    typeVarSymbolTable: Dict[str, SyntaxTypeSymbol]
    specDecl: Optional[str]
    dependentFunctions: List[str]
    apply_exprs: List[SyntaxExpr]
    output2inputDependents: List[List[int]]

    def __init__(self, type: str, name: str, prevscope: SyntaxScope, visibility: str, isImported: bool = False):
        ...

    def set_sizeDecl(self, sizeDecl: List[str]):
        ...

    def get_size_symbol(self, name: str) -> Optional[SyntaxConstSymbol]:
        ...

    def set_outParams(self, outParams: List[SyntaxVariableSymbol]):
        ...

    def get_localVariable(self, name: str) -> SyntaxVariableSymbol or None:
        ...

    def get_localVariable_InThisAndPreEnv(self, name: str) -> SyntaxVariableSymbol or None:
        ...

    def add_dependent_function(self, path: str):
        ...

    def add_input_output_dependency(self, input_index: int, output_index: int):
        ...

    def isTemplate(self) -> bool:
        ...

    def add_type_var(self, type_var_name: str):
        ...

    def get_type_var_symbol(self, type_var_name: str) -> Optional[SyntaxTypeSymbol]:
        ...

    def get_inC_name(self) -> str:
        ...

    def get_outC_name(self) -> str:
        ...

    def scope2str(self, depth: int = 0) -> str:
        ...

    def __repr__(self) -> str:
        ...


class SyntaxPackageScope(SyntaxScope):
    type: str
    name: str
    prevScope: SyntaxScope
    childScopeTable: Dict[str, SyntaxScope]
    sentences: List[Any]
    visibility: str
    typeSymbolTable: Dict[str, SyntaxTypeSymbol]
    constSymbolTable: Dict[str, SyntaxConstSymbol]
    sensorSymbolTable: Dict[str, SyntaxSensorSymbol]
    groupSymbolTable: Dict[str, SyntaxGroupSymbol]
    userOpTable: Dict[str, SyntaxUserOp]
    openPackageList: List[str]

    def __init__(self, type: str, name:str, prevscope: SyntaxScope, visibility: str):
        ...

    def scope2str(self, depth: int = 0) -> str:
        ...

    def __repr__(self) -> str:
        ...

    def add_typeSymbol(self, typeSymbol: SyntaxTypeSymbol) -> None:
        ...

    def add_constSymbol(self, constSymbol: SyntaxConstSymbol) -> None:
        ...

    def add_sensorSymbol(self, sensorSymbol: SyntaxSensorSymbol) -> None:
        ...

    def add_groupSymbol(self, groupSymbol: SyntaxGroupSymbol) -> None:
        ...

    def add_userOp(self, userOp: SyntaxUserOp) -> None:
        ...

    def add_open_package(self, path: str) -> None:
        ...

    def var_change_name(self, name: str) -> str:
        ...

    def get_package(self, package_name: str) -> Optional[SyntaxPackageScope]:
        ...

    def get_userOp(self, userOp_name: str) -> Optional[SyntaxUserOp]:
        ...

    def get_package_InThisAndPreEnv(self, package_name: str) -> Optional[SyntaxPackageScope]:
        ...

    def is_global(self) -> bool:
        ...

    def open(self, tar_package: SyntaxPackageScope) -> None:
        ...

    def get_const_symbol(self, symbol_name: str) -> Optional[SyntaxConstSymbol]:
        ...

    def get_type_symbol(self, type_name: str) -> Optional[SyntaxTypeSymbol]:
        ...