from syntax_tree.graph import Graph
from syntax_tree.scade_generate import generate_tmp_symbol_and_register
from syntax_tree.syntax_class.Exceptions import NoInitialStateException, ManyInitialStateException, \
    InitializationErrorException
from syntax_tree.syntax_class.equation import LeftItemId

from syntax_tree.syntax_class.scope.scope import SyntaxScope
from syntax_tree.syntax_class.scope.data_def import SyntaxDataDefScope
from typing import TYPE_CHECKING

from syntax_tree.syntax_class.syntaxSymbol import SyntaxVariableSymbol

if TYPE_CHECKING:

    from syntax_tree.syntax_class.expression import SyntaxExpr
class SyntaxArrow:
    '''记录了一条状态机的转移指令,包括了actions，fork'''
    action: str=None
    '''一个action就是一个作用域,这里记录了该作用域的ID
    一定会有一个，因为可能需要填充一些默认表达式
    '''
    type: str
    '''记录此arrow状态
    为restart，resume，if
    if代表还可以递归展开
    '''
    target: str
    '''type为restart，resume有效，记录了对应的ID名字'''
    targetIndex: int = 0
    '''type为restart，resume有效，记录了这个转移的序号，每个state单独排序
    只有强转移有这个序号，其他的就是0
    '''
    ifExprList: list
    '''type为if时有效，保存了存有(SyntaxExpr,SyntaxArrow)的列表，对应语法的if和elsif部分'''
    elseExpr: 'SyntaxArrow' or None = None
    '''type为if时可能有效，不一定会有else语句，若不为None则存储了else对应的arrow'''
    state:'SyntaxState'
    '''自身所处的state'''
    returned_symbols:list[SyntaxVariableSymbol] = None
    '''自身修改的所有外部变量'''
    def __init__(self, type: str, state:"SyntaxState",target: str = None, ifExpr: list = None, elseExpr: 'SyntaxArrow' = None):
        self.type = type
        self.state=state
        if type == "if":
            self.ifExprList = ifExpr
            self.elseExpr = elseExpr
        else:
            self.target = target
            self.elseExpr = None
            self.ifExprList=list()

    def set_action(self, action: str):
        self.action = action

    @property
    def sub_arrows(self):
        for if_expr in self.ifExprList:
            yield if_expr[1]
        if self.elseExpr:
            yield self.elseExpr

    def get_transfer_arrows(self) -> list['SyntaxArrow']:
        """递归的从arrow里面找目标转移状态"""
        if self.type != "if":
            return [self]
        out = list()
        for expr in self.ifExprList:
            out += expr[1].get_transfer_arrows()
        if self.elseExpr:
            out += (self.elseExpr.get_transfer_arrows())
        return out
    def get_all_actions(self)->list[str]:
        out = list()
        if self.action:
            out.append(self.action)
        for sub_arrow in self.sub_arrows:
            out+=sub_arrow.get_all_actions()
        return out
    def get_all_returned_symbols(self)->list[SyntaxVariableSymbol]:
        """统计自己所修改的所有外部变量"""
        if self.returned_symbols is not None:return self.returned_symbols
        actions=self.get_all_actions()
        returned_symbols=list()
        for action in actions:
            data_def=self.state.get_childScope(action)
            for returned_symbol in data_def.returnSymbolsTable.values():
                if not returned_symbol.defaultExpr and not returned_symbol.lastExpr:
                    raise Exception(f"{returned_symbol}缺少default或last表达式")
                returned_symbols.append(returned_symbol)
        self.returned_symbols=returned_symbols
        return returned_symbols

    def set_default_equations(self,symbols:list[SyntaxVariableSymbol])->None:
        """合理的分配这些需要设置默认表达式的变量
        即只处理那些自己并没有修改的外部变量
        """
        action_scope=self.state.get_childScope(self.action)
        def add_default_expr(symbol_list):
            from syntax_tree.syntax_class.equation import SyntaxEquation
            for symbol in symbol_list:
                # 这里不可继续展开了，那么就把接收到的symbol都塞到自己的action里
                expr = symbol.defaultExpr if symbol.defaultExpr is not None else symbol.lastExpr
                equation = SyntaxEquation(type="simple_equation", lhs=[LeftItemId(symbol.scope, symbol.name)],
                                          lineno=-1, scope=action_scope)
                equation.set_expr(expr)
                action_scope.add_equation(equation)

        sub_symbols = [symbol for symbol in symbols if
                       symbol.name not in action_scope.returnSymbolsTable.keys()
                       ]
        # 把自己action里面提到的东西去掉
        if self.type!="if":
            add_default_expr(sub_symbols)
        else:
            # 还能展开
            returned_symbols_for_sub_arrows = set()
            # 看一眼分支里面返回情况的并集，把输入列表和并集做差得到需要添加到自己里面的变量
            for sub_arrow in self.sub_arrows:
                returned_symbols_for_sub_arrows.update(sub_arrow.get_all_returned_symbols())
            symbol_for_self=[symbol for symbol in sub_symbols if symbol not in returned_symbols_for_sub_arrows]
            symbol_for_sub_arrows=[symbol for symbol in sub_symbols if symbol in returned_symbols_for_sub_arrows]
            add_default_expr(symbol_for_self)
            for sub_arrow in self.sub_arrows:
                sub_arrow.set_default_equations(symbol_for_sub_arrows)





    def set_index(self, index: int) -> int:
        """给这个arrow和他包含的arrow都设置targetIndex，返回下一个arrow的index序号"""
        if self.type != "if":
            '''递归终点'''
            self.targetIndex = index
            return index + 1
        else:
            for ifList in self.ifExprList:
                arrow = ifList[1]
                index = arrow.set_index(index)
            if self.elseExpr:
                index = self.elseExpr.set_index(index)
            return index

    def __repr__(self):
        return self.arrow2str(0)

    def arrow2str(self, depth=0):
        s = ""
        if self.action:
            s += "action:"
            s += self.action + " "
        if self.type != "if":
            s += str(self.targetIndex) + " " + self.type + " " + self.target
        else:
            s += '\n'
            for Ifexpr in self.ifExprList:
                s += "    " * depth + "if " + str(Ifexpr[0]) + " " + Ifexpr[1].arrow2str(depth=depth + 1) + "\n"
            if self.elseExpr:
                s += "    " * depth + "else " + self.elseExpr.arrow2str(depth=depth + 1)
        return s


class SyntaxState(SyntaxDataDefScope):
    '''状态机的状态类'''
    prevScope: 'SyntaxAutomaton'
    isInitial: bool = False
    isFinal: bool = False
    type: str
    '''automaton_state'''
    name: str
    unlessTransitions: list
    '''强转移列表,保存了存有（SyntaxExpr，SyntaxArrow）的列表'''
    untilTransitions: list
    '''弱转移列表,保存了存有（SyntaxExpr，SyntaxArrow）的列表'''
    synchroArrow: SyntaxArrow = None
    '''同步转移，可为None'''
    actionChildScopeList: list['SyntaxDataDefScope']
    '''该状态下所有arrow中action对应的datadef'''
    apply_exprs: list['SyntaxExpr']
    '''记录了这个state下所有函数调用的情况，用来进行reset
    '''
    returnSymbolInUntilActions:list[SyntaxVariableSymbol]
    '''在弱action中提到的所有集合'''
    returnSymbolInUnlessActions: list[SyntaxVariableSymbol]
    '''在强action中提到的所有集合'''
    def add_apply_expr(self,expr):
        self.get_my_userOp().add_apply_expr(expr)
        self.apply_exprs.append(expr)
    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.untilTransitions = list()
        self.unlessTransitions = list()
        self.actionChildScopeList = list()
        self.apply_exprs = list()
        self.returnSymbolInUntilActions=list()
        self.returnSymbolInUnlessActions=list()

    def set_synchroArrow(self, synchroArrow: SyntaxArrow):
        # todo 可能syncarrow中有action进行赋值操作,此时需要特别处理
        # todo 或者说整个syncarrow都缺乏处理
        self.synchroArrow = synchroArrow

    def set_unlessTransitions(self, unlessTransitions: list):
        index = 1
        return_symbols=list()
        for trans in unlessTransitions:
            arrows = trans[1].get_transfer_arrows()
            # 获取此变量所修改的所有外部变量
            arrow_returned_symbols=trans[1].get_all_returned_symbols()
            return_symbols.extend(arrow_returned_symbols)

            for arrow in arrows:
                # 状态的前一个作用域必定是automaton
                self.prevScope.add_edge(self.name, arrow.target, arrow)
                index = arrow.set_index(index)
        for trans in unlessTransitions:
            # 将这些变量分发下去填充默认表达式
            trans[1].set_default_equations(return_symbols)
        self.returnSymbolInUnlessActions=return_symbols
        self.unlessTransitions = unlessTransitions

    def set_untilTransitions(self, untilTransitions: list):
        self.untilTransitions = untilTransitions
        return_symbols=list()
        for trans in untilTransitions:
            arrows = trans[1].get_transfer_arrows()
            # 获取此变量所修改的所有外部变量
            arrow_returned_symbols=trans[1].get_all_returned_symbols()
            return_symbols.extend(arrow_returned_symbols)

            for arrow in arrows:
                # 状态的前一个作用域必定是automaton
                self.prevScope.add_edge(self.name, arrow.target, arrow)
        for trans in untilTransitions:
            # 将这些变量分发下去填充默认表达式
            trans[1].set_default_equations(return_symbols)
        self.returnSymbolInUntilActions=return_symbols

    def add_action_subscope(self, action: 'SyntaxDataDefScope'):
        self.actionChildScopeList.append(action)

    def get_strong_transfer_arrows(self) -> list[SyntaxArrow]:
        """获取这个状态可能抵达的其他状态的arrow，只有强转移"""
        out = list()
        for unless in self.unlessTransitions:
            out += unless[1].get_transfer_arrows()
        return out

    def get_enum_name(self) -> str:
        """获取这个状态在代码生成中的枚举类型名字"""
        return f"SSM_st_{self.get_global_name()}"

    def __repr__(self):
        return self.scope2str(0)

    def scope2str(self, depth=0):
        s = "    " * depth + ""
        if self.isInitial: s += "init "
        if self.isFinal: s += "final "
        s += "state " + self.name + "" + "\n"
        for unlessTrans in self.unlessTransitions:
            s += "    " * (depth + 1) + ""
            s += "unless if " + str(unlessTrans[0]) + " then "
            s += unlessTrans[1].arrow2str(depth=depth + 2)
            s += "\n"
        for untilTrans in self.untilTransitions:
            s += "    " * (depth + 1) + ""
            s += "until if " + str(untilTrans[0]) + " then "
            s += untilTrans[1].arrow2str(depth=depth + 2)
            s += "\n"
        if self.synchroArrow:
            s += "    " * (depth + 1) + "synchro "
            s += self.synchroArrow.arrow2str(depth=depth + 1)
            s += "\n"
        return s


class SyntaxAutomaton(SyntaxScope):
    '''状态机类，一个状态机由多个状态组成，这些状态都会被记录在其子作用域表里'''
    type: str
    '''automaton'''
    name: str
    '''名字'''
    stateNxtName:str=""
    '''在对应op中outc内对应的名字，代码生成阶段填写'''
    prevScope: 'SyntaxDataDefScope'
    '''父作用域'''
    childScopeTable: dict['SyntaxDataDefScope']
    '''子作用域'''
    visibility: str = "public"
    '''可见性，默认为public'''
    stateTable: dict
    '''保存状态机的状态字典，状态名字->SyntaxState'''
    transferGraph: Graph
    '''状态转移图，一个单向图,节点为状态名字，边为arrow'''

    transferCount: int
    '''记录了这个状态机转移的总数'''

    reset_nxt_symbol:SyntaxVariableSymbol

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.transferGraph = Graph()
        self.stateTable = dict()
        self.reset_nxt_symbol=None

    def add_state(self, state: SyntaxState):
        self.transferGraph.addVertex(state.name)
        self.stateTable[state.name] = state

    def add_edge(self, from_name, to_name, arrow):
        self.transferGraph.addEdge(from_name, to_name, arrow)

    def get_init_state(self) -> SyntaxState:
        init_state = None
        for name, state in self.stateTable.items():
            if state.isInitial:
                if init_state is None:
                    init_state = state
                else:
                    raise ManyInitialStateException(self.name + "有大于1个初始状态了")
        if init_state is None:
            raise NoInitialStateException(self.name + "没有初始状态")
        else:
            return init_state

    def get_return_symbolTable(self):
        '''汇聚子block的返回值集合，合并起来
        如果有某个子状态没有返回语句，还要把默认值给他加上，很无语
        '''
        output = dict()
        for _, childScope in self.childScopeTable.items():
            child_return_table = childScope.get_return_symbolTable()
            output.update(child_return_table)
        for _, childScope in self.childScopeTable.items():
            # 再来一遍，这次把缺少的默认表达式补上去
            child_return_table = childScope.get_return_symbolTable()
            for name, symbol in output.items():
                if name in child_return_table.keys(): continue  # 有了就不管了
                from syntax_tree.syntax_class.equation import SyntaxEquation
                equation = SyntaxEquation(type="simple_equation", lhs=[LeftItemId(symbol.scope,name)], lineno=-1,scope=symbol.scope)
                if not symbol.defaultExpr:
                    # 没有默认表达式，为此变量保留值
                    # 将其设为output以解决
                    symbol.isOutput=True
                    # raise InitializationErrorException(childScope.get_global_name() + " : " + name)
                else:
                    equation.set_expr(symbol.defaultExpr)
                    childScope.add_equation(equation)
        return output

    def __repr__(self):
        return self.scope2str(0)

    def scope2str(self, depth=0):
        s = "    " * depth
        s += "" + self.type + " as "
        s += self.name
        s += "\n"
        s += "    " * depth
        s += "has transitions:\n"
        s += ""
        s += self.graph2str(depth + 1)

        for name, state in self.stateTable.items():
            s += state.scope2str(depth=depth + 1)
        s += self.childScope2str(depth=depth)
        return s

    def graph2str(self, depth=0):
        out = ""
        for vertex in self.transferGraph:
            out += f"{'    ' * depth}{vertex.value}:\n"
            out += f"{'    ' * depth}TO:{len(vertex.get_to_vertexes())}\n"
            for to_vertex in vertex.get_to_vertexes():
                connection = vertex.get_to_connection(to_vertex)
                out += f"{'    ' * depth}{connection.type} {to_vertex.value}\n"

            out += f"{'    ' * depth}FROM:{len(vertex.get_from_vertexes())}\n"
            for from_vertex in vertex.get_from_vertexes():
                connection = vertex.get_from_connection(from_vertex)
                out += f"{'    ' * depth}{connection.type} {from_vertex.value}\n"
            out += "\n"
        return out + ""