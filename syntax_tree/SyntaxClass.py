from syntax_tree.Exceptions import *
from collections import defaultdict, deque

class SyntaxOperator:
    '''在Expr中的Apply_expr中的调用头部分，可以嵌套自己'''
    subtype: str
    '''operator的小类，看共享文档'''
    objects: list
    '''按顺序保存了具体的内容，具体看文档'''
    rhs: set[str]
    '''记录了引用的变量，只有局部变量和signal用来排序'''

    def __init__(self, subtype: str):
        self.subtype = subtype
        self.objects = list()
        self.rhs = set()

    def add_object(self, object):
        self.objects.append(object)
        # 这里合并一下rhs，只有expr，和operator有rhs
        if isinstance(object, SyntaxExpr) or isinstance(object, SyntaxOperator):
            self.rhs |= object.rhs

    def __repr__(self):
        s = "operator::"
        s += self.subtype + "("
        for object in self.objects:
            s += str(object) + ","
        s = s[:-1]
        s += ")"
        return s


class SyntaxExpr:
    """保存expr，右值表达式，可以递归的自己包含自己"""
    type: str
    '''Id_expr  一个ID
    | Atom 一个数，true，false之类的
    | Tempo_expr 各种expr时间运算
    | Arith_expr 各种expr约束，单目双目运算
    | Relation_expr 各种expr比较运算
    | List_expr 空或有的expr表
    | Switch_expr if/switch expr
    | Bool_expr 各种expr布尔运算
    | Struct_expr 结构体取数
    | Array_expr 数组运算
    | Apply_expr 函数调用
    | Mixed_constructor 结构体/数组的混合构造器
    '''

    subType: str
    '''上面大类中对应的每个小类（很多），具体看共享文档'''
    objects: list
    '''按顺序保存了具体的内容，具体看文档'''
    rhs: set[str]
    '''引用到的右值集合，用来给equations排序,只有变量没有函数，因为排序不需要函数
    只有局部变量和signal
    '''

    def __init__(self, type: str, subtype: str):
        self.type = type
        self.subType = subtype
        self.objects = list()
        self.rhs = set()

    def add_object(self, object):
        self.objects.append(object)
        if self.type=="Tempo_expr" and (self.subType=="PRE" or self.subType=="FBY"):return#这两个都是引用过去的变量，没有因果关系
        if isinstance(object, list):
            for expr in object:
                if isinstance(expr, list):
                    for t in expr:
                        self.rhs |= self.get_rhs(t)
                else:
                    self.rhs |= self.get_rhs(expr)
        else:
            self.rhs |= self.get_rhs(object)

    def get_rhs(self, object) -> set:
        # 这里登记右值列表，只留变量，和信号（不包括带pre的),只有expr和operator有
        if isinstance(object, SyntaxExpr) or isinstance(object, SyntaxOperator):
            return object.rhs
        # 在这里把右值加入，只有Id_expr下的Path_id和singlequoteLv6id需要新增rhs，其余情况都是合并
        if self.type != "Id_expr": return set()
        # pathId也去掉，只留下当前作用域的ID，就是只有局部变量和signal
        if (self.subType == "Path_id" and "::" not in str(object)) or self.subType == "singlequoteLv6id":
            output = set()
            output.add(str(object))
            return output
        return set()

    def __repr__(self):
        s = ""
        s += self.type + "::" + self.subType + "("
        for object in self.objects:
            s += str(object) + ","
        s = s[:-1]
        s += ")"
        return s


class SyntaxEquation:
    """保存一句scade的equation，用来排序和生成代码，包含左值和右值"""
    type: str
    '''euqaion的类型，包括simple_equation，assume，guarantee，emission，control_block'''
    expr: SyntaxExpr = None
    '''右值，
    对simple_equation为Syntaxexpr
    对assert为Syntaxexpr
    对emission为Syntaxexpr,如果为None则无条件emit
    对control_block为None
    '''
    controlBlockID: str
    '''仅type为control_block时有效，保存了对应block的名字
    没有填名字的block会自动给他们生成一个名字，确保能够搜索到
    这个block的具体内容会存放在当前作用域的子作用域列表里面
    '''
    assertID: str
    '''仅类型为assume，guarantee生效，保存带比较的ID名称
    assert语句不会改变这个ID的取值，所以不是左值
    '''
    emit: bool = True
    '''在状态机里的状态转移语句里，有可能在一句emission前没有emit关键词
    这个成员变量记录了这种情况，具体作用还不清楚
    对于其他情况则完全没有作用'''
    lineno: int
    '''此语句在原文中的行号
    如果为-1则是遍历时加上去的
    '''

    lhs: list[str]
    '''左值列表，可以由0-多个ID组成，
    对control_block来说就是return的值，用来排序
    对emission来说是括号内的signal变量,带'形式的
    对simple_equation来说就是左值
    对assert来说是空列表
    '''
    rhs: set[str]
    '''对应表达式的右值变量的集合，如果没有右值变量，则为空集合'''

    def __init__(self, type: str, lhs: list, lineno: int):
        self.type = type
        self.lhs = lhs
        self.rhs = set()
        self.lineno = lineno

    def set_expr(self, expr: SyntaxExpr):
        self.expr = expr
        self.rhs = expr.rhs

    def equation2str(self, depth=0):
        s = "    " * depth + "行号" + ": " + str(self.lineno) + " "
        s += " rhs: ("
        for rhsSymbol in self.rhs:
            s += rhsSymbol + ","
        if len(self.rhs) > 0: s = s[:-1]
        s += ") "
        if self.type == "assume" or self.type == "guarantee":
            s += self.type + " " + self.assertID + " : " + str(self.expr)
            return s
        if self.type == "emission": s += "emit "
        s+=" lhs:"
        s += "("
        if len(self.lhs) > 0:
            for symbol in self.lhs:
                s += str(symbol) + ","
            s = s[:-1]
        else:
            s += " "
        s += ")"
        if self.type == "emission":
            if self.expr:
                s += " if " + str(self.expr)
            return s
        s += " = "
        if self.type != "control_block":
            if self.expr: s += str(self.expr)
        else:
            s += self.controlBlockID

        return s

    def __repr__(self):
        return self.equation2str()


class SyntaxType:
    pass


class SyntaxType:
    """记录type类型"""
    name: str
    '''type_block ，用于重命名之后的str，type表示其真实类型'''

    type: str
    '''类型，int8，枚举类型等'''

    sizeExpr: int = None
    '''类型为signed，unsigned时有效，存储了对应整数值'''

    fields: dict = None
    '''类型为field_decl时有效，存储了ID:SyntaxTypeSymbol的键值对'''

    enumList: list = None
    '''类型为enum时有效，存储了枚举类型的ID列表'''

    value: str = None
    '''类型为typevar，path_id时有效，存储了具体的内容'''

    listType: SyntaxType = None
    '''类型为list时有效，存储了数组的类型'''

    listExpr: SyntaxExpr = None
    '''类型为list时有效，存储了数组的长度表达式
    必须在编译时可知，并且是严格大于0
    '''

    basic_type = ['bool','int8','int16','int32','int64','uint8','uint16','uint32','uint64','float32','float64','char']

    def __init__(self, type: str) -> None:
        self.type = type

    def __repr__(self):
        s = ""
        s += "type:" + self.type + " "
        if self.sizeExpr:
            s += "sizeExpr:" + str(self.sizeExpr)
        if self.fields:
            s += "Fields:{"
            for ID, field in self.fields.items():
                s += ID + ":" + str(field) + ","
            s = s[:-1]
            s += "}"
        if self.enumList:
            s += "EnumList:{"
            for ID in self.enumList:
                s += ID + ","
            s = s[:-1]
            s += "}"
        if self.value:
            s += self.value
        if self.listType:
            s += "listType:" + str(self.listType) + " "
            s += "listSizeExpr:" + str(self.listExpr)
        return s

    def change_name(self):
        return f'kcg_{self.type}' if self.type in self.basic_type else self.type

class SyntaxTypeSymbol:
    """人为定义的类型变量，输入到符号表里面"""
    name: str
    '''自定义变量名字'''
    visibility: str
    '''可见性，public/private'''

    isImported: bool
    '''是不是imported'''

    syntaxType: SyntaxType = None
    '''组合的类型类别,不为imported时有效'''

    numericKind: str = None
    '''类型为imported时有效，存储了引用的类型'''

    def __init__(self, name: str, visibility: str):
        self.name = name
        self.visibility = visibility

    def __repr__(self):
        s = ""
        s += self.visibility + " "
        s += self.name + " "
        if self.isImported:
            s += "is imported " + self.numericKind
        else:
            s += str(self.syntaxType)
        return s


class SyntaxConstSymbol:
    """常量，为imported时没有初值"""

    name: str
    '''自定义变量名字'''

    visibility: str
    '''可见性，public/private'''

    isImported: bool
    '''是不是imported'''

    syntaxType: SyntaxType
    '''组合的类型类别,一直有效'''

    valueExpr: SyntaxExpr = None
    '''常量对应值，不为imported时有效
    此处的表达式必须可在编译时计算出数值！
    '''

    def __init__(self, name: str, visibility: str):
        self.name = name
        self.visibility = visibility

    def __repr__(self):
        s = ""
        s += self.visibility + " "
        s += self.name + " "
        s += str(self.syntaxType) + " "
        if self.isImported:
            s += "is imported "
        else:
            s += "=" + str(self.valueExpr)
        return s


class SyntaxSensorSymbol:
    name: str
    '''自定义变量名字'''

    syntaxType: SyntaxType
    '''组合的类型类别,一直有效'''

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        s = ""
        s += self.name + " "
        s += str(self.syntaxType)
        return s


class SyntaxGroupSymbol:
    name: str
    '''自定义变量名字'''
    visibility: str
    '''可见性，public/private'''
    groupExpr: list
    '''group内容，存有内部各SyntaxType类型'''

    def __init__(self, name, visibility):
        self.name = name
        self.visibility = visibility
        self.groupExpr = list()

    def __repr__(self):
        s = ""
        s += self.visibility + " "
        s += self.name + " "
        s += "as{ "
        for type in self.groupExpr:
            s += str(type) + " "
        s += "}"
        return s


class SyntaxPattern:
    '''pattern类'''
    type: str
    '''具体的pattern类型
    Path_id
    | CHARACTER
    | INTEGERNUM
    | TYPED_INTEGER
    | Bool_atom
    | UNDERLINE
    对应的lex_value的strs'''
    value: str
    '''类型对应的内容'''

    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return self.value


class SyntaxClockExpr:
    ID: str
    '''clockexpr中必须的LV6ID'''
    type: str
    '''ID:LV6ID
       notID:NOT LV6ID
       pattern:LPARENTHESE LV6ID MATCH Pattern RPARENTHESE
    '''
    pattern: SyntaxPattern = None
    '''仅type为match时不为none'''

    def __init__(self, ID: str, type: str):
        self.ID = ID
        self.type = type

    def __repr__(self):
        s = ""
        if self.type == "ID":
            s = self.ID
        elif self.type == "notID":
            s = "not " + self.ID
        elif self.type == "pattern":
            s = self.ID + " match " + str(self.pattern)
        else:
            s = "ERROR IN TYPE"
        return s


class SyntaxVariableSymbol:
    name: str
    '''自定义变量名字'''
    isClock: bool
    '''是不是clock'''
    isProbe: bool
    '''是不是probe'''
    isOutput: bool
    '''是不是output，用于代码生成时输出变量需要转化为outC，不能遍历outParams(init,tmp)'''
    isInput: bool
    '''是不是input，用于代码生成时输出变量需要转化为inC'''
    syntaxType: SyntaxType
    '''组合的类型类别,一直有效'''
    whenExpr: SyntaxClockExpr = None
    '''对应whenexpr的值,可以为none'''
    defaultExpr: SyntaxExpr = None
    '''对应default的值，可以为none'''
    lastExpr: SyntaxExpr = None
    '''对应last的值，可以为none'''

    def __init__(self, name: str, isClock: bool, isProbe: bool):
        self.name = name
        self.isClock = isClock
        self.isProbe = isProbe
        self.isOutput = False
        self.isInput = False

    def __repr__(self):
        s = ""
        if self.isClock: s += "clock "
        if self.isProbe: s += "probe "
        s += self.name
        s += " as "
        s += str(self.syntaxType)
        if self.whenExpr:
            s += "when "
            s += str(self.whenExpr)
        if self.defaultExpr:
            s += "default = "
            s += str(self.defaultExpr)
        if self.lastExpr:
            s += "last = "
            s += str(self.lastExpr)
        return s


class SyntaxScope:
    name: str
    '''名字'''
    pass  # 这里是为了让下面的成员变量能识别到自己，删掉就识别不到了


class SyntaxScope:
    """作用域父类"""

    type: str
    '''为data_def,function,node,package,if_block,match_block,automaton,automaton_state'''
    name: str
    '''名字'''
    prevScope: SyntaxScope
    '''父作用域'''
    childScopeTable: dict
    '''子作用域'''
    visibility: str = "public"
    '''可见性，默认为public'''
    anonymousScopeCount: int = 1
    '''匿名scope计数器，给匿名的block生成名字'''

    def __init__(self, type, name, prevScope, visibility):
        self.type = type
        self.name = name
        self.prevScope = prevScope
        self.visibility = visibility
        self.childScopeTable = dict()
        self.equations = list()

    def add_childScope(self, childScope: SyntaxScope) -> None:
        self.childScopeTable[childScope.name] = childScope

    def get_childScope(self, scopeName) -> SyntaxScope:
        if scopeName in self.childScopeTable.keys():
            return self.childScopeTable[scopeName]
        else:
            return None

    def childScope2str(self, depth=0):
        s = ""
        s += "    " * depth + "\033[32mchildScope:\033[0m\n"
        for _, scope in self.childScopeTable.items():
            s += scope.scope2str(depth=depth + 1)
        return s

    def generate_name_for_subScope(self):
        s = self.name
        s += "^subScope^"
        s += str(self.anonymousScopeCount)
        self.anonymousScopeCount += 1
        return s
    def get_global_name(self):
        if self.prevScope is None:return self.name
        else:return self.prevScope.get_global_name()+"::"+self.name


class SyntaxIfBlock:
    conditionExpr: SyntaxExpr
    '''条件语句'''
    thenBlock: object
    '''为str存data_def的ID，或者存一个IfBlock对象'''
    elseBlock: object
    '''为str存data_def的ID，或者存一个IfBlock对象'''

    def __init__(self, expr: SyntaxExpr, thenBlock, elseBlock):
        self.conditionExpr = expr
        self.thenBlock = thenBlock
        self.elseBlock = elseBlock

    def __repr__(self):
        return self.block2str(0)

    def block2str(self, depth=0):
        s = ""
        s += "    " * depth + "if " + str(self.conditionExpr) + "\n"
        s += "    " * depth + "then "
        if isinstance(self.thenBlock, SyntaxIfBlock):
            s += "\n" + self.thenBlock.block2str(depth + 1)
        else:
            s += self.thenBlock
        s += "\n"
        s += "    " * depth + "else "
        if isinstance(self.elseBlock, SyntaxIfBlock):
            s += "\n" + self.elseBlock.block2str(depth + 1)
        else:
            s += str(self.elseBlock)
        return s


class SyntaxMatchBlock:
    switchExpr: SyntaxExpr
    '''用于switch的语句'''
    matchList: list
    '''保存（SyntaxPattern.指向data_def的ID）的列表'''

    def __init__(self, expr: SyntaxExpr, matchList: list):
        self.switchExpr = expr
        self.matchList = matchList

    def __repr__(self):
        return self.block2str(0)

    def block2str(self, depth=0):
        depth += 1
        s = ""
        s += "    " * depth
        s += "switch " + str(self.switchExpr) + "\n"
        for match in self.matchList:
            s += "    " * depth + str(match[0]) + " : " + str(match[1]) + "\n"
        s = s[:-1]
        return s


class SyntaxClockedScope(SyntaxScope):
    type: str
    '''为if_block或者match_block'''
    name: str
    '''名字'''
    prevScope: SyntaxScope
    '''父作用域'''
    childScopeTable: dict
    '''子作用域'''
    visibility: str = "public"
    '''可见性，默认为public'''
    block: SyntaxIfBlock or SyntaxMatchBlock
    '''组合的block，根据type决定具体类型'''

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)

    def __repr__(self):
        return self.scope2str(0)

    def get_localVariable_InThisAndPreEnv(self, name: str) -> SyntaxVariableSymbol or None:
        return self.prevScope.get_localVariable_InThisAndPreEnv(name)
    def get_return_symbolTable(self):
        '''汇聚子block的返回值集合，合并起来
        如果有某个子状态没有返回语句，还要把默认值给他加上，很无语
        '''
        output=dict()
        for _,childScope in self.childScopeTable.items():
            child_return_table=childScope.get_return_symbolTable()
            for name,symbol in child_return_table.items():
                if name not in output.keys():
                    output[name]=symbol
        for _,childScope in self.childScopeTable.items():
            #再来一遍，这次把缺少的默认表达式补上去
            child_return_table=childScope.get_return_symbolTable()
            for name,symbol in output.items():
                if name in child_return_table.keys():continue#有了就不管了
                equation=SyntaxEquation(type="simple_equation", lhs=[name],lineno=-1)
                if not symbol.defaultExpr:#没有默认表达式就报错
                    if symbol.lastExpr:
                        equation.set_expr(symbol.lastExpr)
                        print(equation)
                        childScope.add_equation(equation)
                    else:raise InitializationErrorException(name)
                else:
                    equation.set_expr(symbol.defaultExpr)
                    print(equation)
                    childScope.add_equation(equation)
        return output
    def scope2str(self, depth):
        s = "    " * depth
        s += "\033[31m" + self.type + " as "
        s += self.name
        s += "\033[0m"
        s += "\n"
        s += self.block.block2str(depth=depth + 1) + "\n"
        s += self.childScope2str(depth=depth)
        return s


class SyntaxDataDefScope(SyntaxScope):  # 在data_def下，只有状态机和clocked_block直接作为他的子作用域了
    """data_def对应scope，用于user_op，control_block中的scope
    包含signal和local声明部分
    """
    type: str
    '''为data_def'''
    name: str
    '''名字'''
    prevScope: SyntaxScope
    '''父作用域，指向一个package'''
    childScopeTable: dict
    '''子作用域'''

    visibility: str = "public"
    '''可见性，默认为public'''
    equations: list
    '''该作用域中的scade语句，在data_def下的作用域才有语句，上层的作用域（package）只有声明'''
    signalSymbolSet: set
    '''存放signal类型，保存signal的ID集合,signal的ID没有‘，只有ID本身的部分'''
    localSymbolTable: dict
    '''存放局部变量，变量名字->SyntaxVariableSymbol'''
    returnSymbolsTable: dict
    '''存放了当前作用域修改的，外部作用域的变量，变量名字->SyntaxVariableSymbol'''
    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.signalSymbolSet = set()
        self.localSymbolTable = dict()
        self.returnSymbolsTable=dict()
    def add_equation(self, input_equation: SyntaxEquation):
        # 直接放进去，遍历完所有语句之后再进行排序
        self.equations.append(input_equation)
        #更新返回列表
        for lhs in input_equation.lhs:
            if lhs=="_": return
            if "'" not in lhs and not self.get_localVariable(lhs):
                symbol=self.get_localVariable_InThisAndPreEnv(lhs)
                if not symbol:raise UnknownIdentifierException(lhs)
                self.returnSymbolsTable[lhs]=symbol

    def get_localVariable(self, name: str) -> SyntaxVariableSymbol or None:
        '''在当前作用域找局部变量'''
        if name not in self.localSymbolTable.keys():
            return None
        else:
            return self.localSymbolTable[name]

    def get_localVariable_InThisAndPreEnv(self, name: str)->SyntaxVariableSymbol or None:
        '''递归的找局部变量'''
        if name in self.localSymbolTable.keys():
            return self.localSymbolTable[name]
        else:
            return self.prevScope.get_localVariable_InThisAndPreEnv(name)

    def get_return_symbolTable(self):
        '''获取此作用域修改的上层作用域中的变量，不包括信号，path_id是只读的不用管他'''
        return self.returnSymbolsTable

    def topologySort(self):
        edges = list()
        nodes = {node: False for node in self.equations}
        # 更新一下依赖的关系
        for input_equation in nodes:
            for equation in nodes:
                if is_dependent(input_equation, equation):  # 输入句子依赖这个句子
                    edges.append([equation, input_equation])
        # Step 1: 构建图的邻接表和入度字典
        graph = defaultdict(list)
        in_degree = {node: 0 for node in nodes}

        for u, v in edges:
            graph[u].append(v)
            in_degree[v] += 1

        # Step 2: 找到所有入度为 0 的节点
        queue = deque([node for node in nodes if in_degree[node] == 0])

        # Step 3: 拓扑排序
        topo_order = []

        while queue:
            node = queue.popleft()
            topo_order.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(topo_order) != len(self.equations): raise EquationDependentException(self.get_global_name() + "存在循环引用")
        self.equations = topo_order

    def set_signalSymbolList(self, signalSymbolList: list):
        self.signalSymbolSet = set(signalSymbolList)

    def add_localSymbols(self, localSymbolList: list):
        for symbol in localSymbolList:
            self.localSymbolTable[symbol.name] = symbol

    def scope2str(self, depth=0):
        s = "    " * depth
        s += "\033[31m" + self.type + " as "
        prev_list = list()
        p = self.prevScope
        while p is not None:
            prev_list.append(p.name)
            p = p.prevScope
        for prev_scope in reversed(prev_list):
            s += prev_scope + "::"
        s += self.name
        s += "\033[0m"
        s += "\n"
        s += self.signalSymbolSet2str(depth=depth)
        s += self.localSymbolTable2str(depth=depth)
        s += self.childScope2str(depth=depth)
        s += self.equations2str(depth=depth)
        return s

    def signalSymbolSet2str(self, depth=0):
        s = ""
        s += "    " * depth + "\033[33msignalSymbolSet:\033[0m\n"
        if len(self.signalSymbolSet) > 0:
            s += "    " * depth + "    "
            for ID in self.signalSymbolSet:
                s += ID + ","
            s = s[:-1]
            s += "\n"
        return s

    def localSymbolTable2str(self, depth=0):
        s = ""
        s += "    " * depth + "\033[33mlocalSymbolTable:\033[0m\n"
        for ID, symbol in self.localSymbolTable.items():
            s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        return s

    def equations2str(self, depth=0):
        s = ""
        s += "    " * depth + "\033[34mequations:\033[0m\n"
        for equation in self.equations:
            s += equation.equation2str(depth=depth + 1) + "\n"
        return s


def is_dependent(src: SyntaxEquation, dest: SyntaxEquation):
    '''判断src是否依赖dest，即检测src的右值是否和dest的左值重合'''
    for lhs in dest.lhs:
        if lhs in src.rhs:
            return True
    return False


class SyntaxArrow:
    pass


class SyntaxArrow:
    '''记录了一条状态机的转移指令,包括了actions，fork'''
    action: str = None
    '''一个action就是一个作用域,这里记录了该作用域的ID'''
    type: str
    '''记录此arrow状态
    为restart，resume，if
    if代表还可以递归展开
    '''
    target: str
    '''type为restart，resume有效，记录了对应的ID名字'''
    ifExprList: list
    '''type为if时有效，保存了存有(SyntaxExpr,SyntaxArrow)的列表，对应语法的if和elsif部分'''
    elseExpr: SyntaxArrow = None
    '''type为if时可能有效，不一定会有else语句，若不为None则存储了else对应的语句'''

    def __init__(self, type: str, target: str = None, ifExpr: list = None, elseExpr: SyntaxArrow = None):
        self.type = type
        if type == "if":
            self.ifExprList = ifExpr
            self.elseExpr = elseExpr
        else:
            self.target = target

    def set_action(self, action: str):
        self.action = action

    def __repr__(self):
        return self.arrow2str(0)

    def arrow2str(self, depth=0):
        s = ""
        if self.action:
            s += "action:"
            s += self.action + " "
        if self.type != "if":
            s += self.type + " " + self.target
        else:
            for Ifexpr in self.ifExprList:
                s += "if " + str(Ifexpr[0]) + " " + Ifexpr[1].arrow2str(depth=depth + 1)
            if self.elseExpr:
                s += self.elseExpr.arrow2str(depth=depth + 1)
        return s


class SyntaxState(SyntaxDataDefScope):
    '''状态机的状态类'''
    isInitial: bool = False
    isFinal: bool = False
    type: str
    '''automaton_state'''
    unlessTransitions: list
    '''强转移列表,保存了存有（SyntaxExpr，SyntaxArrow）的列表'''
    untilTransitions: list
    '''弱转移列表,保存了存有（SyntaxExpr，SyntaxArrow）的列表'''
    synchroArrow: SyntaxArrow = None
    '''同步转移，可为None'''

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.untilTransitions = list()
        self.unlessTransitions = list()

    def set_synchroArrow(self, synchroArrow: SyntaxArrow):
        self.synchroArrow = synchroArrow

    def set_unlessTransitions(self, unlessTransitions: list):
        self.unlessTransitions = unlessTransitions

    def set_untilTransitions(self, untilTransitions: list):
        self.untilTransitions = untilTransitions

    def __repr__(self):
        return self.state2str(0)

    def state2str(self, depth=0):
        s = "    " * depth + "\033[32m"
        if self.isInitial: s += "init "
        if self.isFinal: s += "final "
        s += "state " + self.name + "\033[30m" + "\n"
        for unlessTrans in self.unlessTransitions:
            s += "    " * (depth + 1) + "\033[35m"
            s += "unless if " + str(unlessTrans[0]) + " then "
            s += unlessTrans[1].arrow2str(depth=depth + 2)
            s += "\033[30m\n"
        for untilTrans in self.untilTransitions:
            s += "    " * (depth + 1) + "\033[35m"
            s += "until if " + str(untilTrans[0]) + " then "
            s += untilTrans[1].arrow2str(depth=depth + 2)
            s += "\033[30m\n"
        if self.synchroArrow:
            s += "    " * (depth + 1) + "\033[35msynchro "
            s += self.synchroArrow.arrow2str(depth=depth + 1)
            s += "\033[30m\n"
        return s


class SyntaxAutomaton(SyntaxScope):
    '''状态机类，一个状态机由多个状态组成，这些状态都会被记录在其子作用域表里'''
    type: str
    '''automaton'''
    name: str
    '''名字'''
    prevScope: SyntaxScope
    '''父作用域'''
    childScopeTable: dict
    '''子作用域'''
    visibility: str = "public"
    '''可见性，默认为public'''
    stateTable: dict
    '''保存状态机的状态字典，状态名字->SyntaxState'''

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.stateTable = dict()

    def add_state(self, state: SyntaxState):
        self.stateTable[state.name] = state

    def get_localVariable_InThisAndPreEnv(self, name: str) -> SyntaxVariableSymbol or None:
        return self.prevScope.get_localVariable_InThisAndPreEnv(name)
    def get_return_symbolTable(self):
        '''汇聚子block的返回值集合，合并起来
        如果有某个子状态没有返回语句，还要把默认值给他加上，很无语
        '''
        output=dict()
        for _,childScope in self.childScopeTable.items():
            child_return_table=childScope.get_return_symbolTable()
            for name,symbol in child_return_table.items():
                if name not in output.keys():
                    output[name]=symbol
        for _,childScope in self.childScopeTable.items():
            #再来一遍，这次把缺少的默认表达式补上去
            child_return_table=childScope.get_return_symbolTable()
            for name,symbol in output.items():
                if name in child_return_table.keys():continue#有了就不管了
                equation=SyntaxEquation(type="simple_equation", lhs=[name],lineno=-1)
                if not symbol.defaultExpr:#没有默认表达式就报错
                    raise InitializationErrorException(name)
                else:
                    equation.set_expr(symbol.defaultExpr)
                    childScope.add_equation(equation)
        return output
    def __repr__(self):
        return self.scope2str(0)

    def scope2str(self, depth=0):
        s = "    " * depth
        s += "\033[31m" + self.type + " as "
        s += self.name
        s += "\033[0m"
        s += "\n"
        for name, state in self.stateTable.items():
            s += state.state2str(depth=depth + 1)
        s += self.childScope2str(depth=depth)
        return s


class SyntaxUserOp(SyntaxDataDefScope):
    """记录func或者node，既作为symbol，也作为一种scope存在"""
    type: str
    '''分为function和node两种'''
    name: str
    '''名字'''
    prevScope: SyntaxScope
    '''父作用域，指向一个package'''
    childScopeTable: dict
    '''子作用域'''
    equations: list
    '''该作用域中的scade语句'''
    visibility: str = "public"
    '''可见性，默认为public'''

    sizeDecl: list
    '''输入的size参数，其中每个值都是const'''
    inParams: list  # 存SyntaxVariableSymbol
    '''输入参数，是一个变量声明列表'''
    outParams: list # 存SyntaxVariableSymbol
    '''输出参数，是一个变量声明列表'''
    tmpParams: list # 存SyntaxVariableSymbol
    '''中间参数，是一个变量声明列表'''
    numericKind: str = None
    '''如果是模板方法则填入对应类型，不是则为None'''
    whereDecl: list = None
    '''声明的模板类型'''
    specDecl: str = None
    '''声明的SPECIALIZE类型，存放一个pathID，没有声明则为None'''

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.inParams = list()
        self.outParams = list()
        self.tmpParams = list()
        self.whereDecl = list()
        self.sizeDecl = list()

    def set_sizeDecl(self, sizeDecl: list):
        self.sizeDecl = sizeDecl
    def get_localVariable(self, name: str) -> SyntaxVariableSymbol or None:
        '''在当前作用域找局部变量，包括输入输出参数'''
        if name not in self.localSymbolTable.keys():
            for symbol in self.inParams:
                if name==symbol.name:
                    return symbol
            for symbol in self.outParams:
                if name==symbol.name:
                    return symbol
            for symbol in self.tmpParams:
                if name == symbol.name:
                    return symbol
            return None
        else:
            return self.localSymbolTable[name]

    def get_localVariable_InThisAndPreEnv(self, name: str)->SyntaxVariableSymbol or None:
        '''递归的找局部变量，包括输入输出参数'''
        return self.get_localVariable(name)#上层不可能有变量了
    def userOp2str(self, depth=0):
        s = "    " * depth
        s += "\033[31muserOpScope as " + self.type + " "
        prev_list = list()
        p = self.prevScope
        while p is not None:
            prev_list.append(p.name)
            p = p.prevScope
        for prev_scope in reversed(prev_list):
            s += prev_scope + "::"
        s += self.name
        if self.sizeDecl:
            s += "<<"
            for decl in self.sizeDecl:
                s += decl + ","
            s = s[:-1]
            s += ">>"
        s += "( "
        for inParam in self.inParams:
            s += str(inParam) + ","
        s = s[:-1]
        s += ")"
        s += " returns ( "
        for outParam in self.outParams:
            s += str(outParam) + ","
        s = s[:-1]
        s += ")"
        if self.numericKind:
            s += " where "
            for decl in self.whereDecl:
                s += decl + ","
            s = s[:-1]
            s += " is " + self.numericKind
        if self.specDecl:
            s += " specialize " + self.specDecl
        s += "\033[0m"
        s += "\n"
        s += self.signalSymbolSet2str(depth=depth + 1)
        s += self.localSymbolTable2str(depth=depth + 1)
        s += self.equations2str(depth=depth + 1)
        s += self.childScope2str(depth=depth + 1)
        return s

    def var_change_name(self,name):
        symbol = self.get_localVariable(name)
        if symbol != None:
            if symbol.isOutput:
                return f"outC->{symbol.name}"
            elif symbol.isInput:
                return f"inC->{symbol.name}"
            else:
                return symbol.name
        else:
            raise ValueError(f"var_change_name error , name:{name}")

    def __repr__(self):
        return self.userOp2str()


class SyntaxPackageScope(SyntaxScope):
    """package对应scope，用于package和program
    包含子package，group，type，const，sensor与user_op声明
    program也算作package scope的一种，名字为 *global（防止重名）
    """
    type: str
    '''为package'''
    name: str
    '''名字'''
    prevScope: SyntaxScope
    '''父作用域'''
    childScopeTable: dict
    '''子作用域'''
    sentences: list
    '''该作用域中的scade语句'''
    visibility: str = "public"
    '''可见性，默认为public'''

    typeSymbolTable: dict
    '''类型定义的符号表，类型名字->SyntaxTypeSymbol'''
    constSymbolTable: dict
    '''常量定义符号表，常量名字->SyntaxConstSymbol'''
    sensorSymbolTable: dict
    '''sensor定义符号表，sensor名字->SyntaxSensorSymbol'''
    groupSymbolTable: dict
    '''group定义符号表，group名字->SyntaxGroupSymbol'''
    userOpTable: dict
    '''函数，node的自定义符号表，因为path寻路只寻package所以独立出来，userop名字->SyntaxUserOpSymbol'''

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.typeSymbolTable = dict()
        self.constSymbolTable = dict()
        self.sensorSymbolTable = dict()
        self.groupSymbolTable = dict()
        self.userOpTable = dict()

    def package2str(self, depth=0):
        s = "    " * depth
        s += "\033[31mscope "
        prev_list = list()
        p = self.prevScope
        while p is not None:
            prev_list.append(p.name)
            p = p.prevScope
        for prev_scope in reversed(prev_list):
            s += prev_scope + "::"
        s += self.name + " as " + self.type
        s += "\033[0m"
        s += "\n"
        depth = depth + 1
        s += "    " * depth + "\033[33mtypeSymbolTable:\033[0m\n"
        for ID, symbol in self.typeSymbolTable.items():
            s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        s += "    " * depth + "\033[33mconstSymbolTable:\033[0m\n"
        for ID, symbol in self.constSymbolTable.items():
            s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        s += "    " * depth + "\033[33msensorSymbolTable:\033[0m\n"
        for ID, symbol in self.sensorSymbolTable.items():
            s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        s += "    " * depth + "\033[33mgroupSymbolTable:\033[0m\n"
        for ID, symbol in self.groupSymbolTable.items():
            s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        s += "    " * depth + "\033[32muserOpTable:\033[0m\n"
        for ID, symbol in self.userOpTable.items():
            s += symbol.userOp2str(depth=depth + 1)
        s += "    " * depth + "\033[32mchildScope:\033[0m\n"
        for _, scope in self.childScopeTable.items():
            if scope.type=="package":s += scope.package2str(depth=depth + 1)
        return s

    def __repr__(self):
        return self.package2str()

    def add_typeSymbol(self, typeSymbol: SyntaxTypeSymbol) -> None:
        self.typeSymbolTable[typeSymbol.name] = typeSymbol

    def add_constSymbol(self, constSymbol: SyntaxConstSymbol) -> None:
        self.constSymbolTable[constSymbol.name] = constSymbol

    def add_sensorSymbol(self, sensorSymbol: SyntaxSensorSymbol) -> None:
        self.sensorSymbolTable[sensorSymbol.name] = sensorSymbol

    def add_groupSymbol(self, groupSymbol: SyntaxGroupSymbol) -> None:
        self.groupSymbolTable[groupSymbol.name] = groupSymbol

    def add_userOp(self, userOp: SyntaxUserOp) -> None:
        self.userOpTable[userOp.name] = userOp
        self.childScopeTable[userOp.name]=userOp


