import copy

from syntax_tree.Exceptions import *
from collections import defaultdict, deque
from graph import *


# 拓扑排序和模板实例化操作
# 实例化还在写，虽然非常不想写，半年前的记忆触发了
class HasRhs:
    pass


class SyntaxType:
    pass


class SyntaxDataDefScope:
    pass


class ConstValue:
    pass


class SyntaxVariableSymbol:
    pass


class SyntaxScope:
    pass


class SyntaxExpr(HasRhs):
    pass


class SyntaxUserOp:
    pass


class ConstValue:
    """在expr间传递值的类，封装类型与值"""
    type: SyntaxType = None
    value: int or float or bool or str or list[ConstValue] or dict[str:ConstValue]

    def __init__(self, syntax_type, value):
        self.type = syntax_type
        self.value = value

    def type_belong_to(self, syntaxType: SyntaxType):
        return self.type <= syntaxType

    def get_size(self):
        return self.type.get_size()

    def __repr__(self):
        return f"{str(self.type)} value:{str(self.value)}"
    # 组合代替继承太爽啦


class HasRhs:
    rhsList: list[set[str]]
    '''记录了引用的变量，只有局部变量和signal用来排序,考虑到多返回值的情况，按顺序存放每个返回值所对应的依赖变量'''
    lhsTypeList: list
    '''记录了返回值的类型列表，按顺序存放每个返回值的对应类型, 存放syntaxtype，很好'''

    def __init__(self):
        self.rhsList = list()
        self.lhsTypeList = list()

    def absorb_rhs(self, tar):
        """将目标类的rhs吸收到右值中,即返回值增加
        Parameters:
            tar:有rhs的类，即expr，operator，equation
        """
        for rhs in tar.rhsList:
            self.rhsList.append(rhs)

    def add_empty_rhs(self):
        """添加一个空的右值列表"""
        self.rhsList.append(set())

    def set_rhs(self, rhs):
        """设置右值
        Parameters:
            rhs:右值列表,str格式
        """
        if rhs is None or not rhs:
            self.rhsList=[set()]
        else:
            self.rhsList = [set(rhs)]

    def add_rhs(self, rhs):
        """添加右值,返回值+1
        Parameters:
            rhs:右值列表,str格式
        """
        self.rhsList.append(set(rhs))

    def has_name_in_rhs(self, name):
        """返回rhs中是否有这个变量的名字"""
        for rhs in self.rhsList:
            if name in rhs: return True
        return False

    def add_lhs_type(self, type):
        """
        添加一个返回的左值类型
        Parameters:
            type:SyntaxType
        """
        self.lhsTypeList.append(type)

    def set_lhs_type(self, type_list):
        """
        设置返回的左值类型
        Parameters:
            type_list:[SyntaxType]
        """
        self.lhsTypeList = type_list


class SyntaxOperator(HasRhs):
    '''在Expr中的Apply_expr中的调用头部分，可以嵌套自己'''
    subtype: str
    '''operator的小类，看共享文档'''
    objects: list
    '''按顺序保存了具体的内容，具体看文档'''

    appliedUserOp: SyntaxUserOp
    '''为path_id时有效，保存了指向调用的userop的指针'''
    array_length:int
    '''为map fold等类型时有效，保存了对应数组的长度'''
    prefix_op_2_expr_dict = {
        # 双目
        ("$+$", "$-$", "$*$", "$/$", "$mod$", "$land$", "$lor$", "$lxor$", "$lsr$", "$lsl$"): ["Arith_expr", "binOp"],
        # ese
        ("$=$", "$<>$", "$<$", "$>$", "$<=$", "$>=$"): ["Relation_expr", "Relation_expr"],  # ese
        ("$and$", "$or$", "$xor$"): ["Bool_expr", "binOp"],  # ese
        ("$@$"): ["Array_expr", "at"],  # ee
        ("$times$"): ["Tempo_expr", "TIMES"],  # ee
        # 单目
        ("+$", "-$", "lnot$"): ["Arith_expr", "unary"],  # se
        ("not$"): ["Bool_expr", "NOT"],  # e
        ("reverse$"): ["Array_expr", "reverse"],  # e
    }

    def __init__(self, subtype: str):
        super().__init__()
        self.subtype = subtype
        self.objects = list()

    def add_object(self, object):
        self.objects.append(object)

    def set_array_length(self, length):
        self.array_length = length

    def __repr__(self):
        s = "operator::"
        s += self.subtype + "("
        for object in self.objects:
            s += str(object) + ","
        s = s[:-1]
        s += ")"
        return s


class SyntaxExpr(HasRhs):
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
    scope: SyntaxScope
    '''这个expr所处作用域'''

    syntaxSymbol = None
    '''Id_expr时，存储的对应symbol，会用到它的,ID没有，很合理'''

    appliedOpDict: dict[SyntaxUserOp:list[int]]
    """需要统计每个userOP调用其他函数的数量,仅在为Apply_expr,且调用了某个函数时有效
    让operator返回他调用的函数情况！一个字典，key为userOp,value为list，逐层保存，比如map (map func<<2>>)<<3>>
    会得到一个字典：{func:[3,2]}
    一个expr只会调用一个op，所以这个字典肯定只有一对key-value
    在类型推导环节填写
    """
    returnNum: int = 1
    """这个表达式返回的值的数量，默认为1
    tempo类型除了time
    list类型
    函数调用
    if/case类型均可返回多个，其他返回一个
    """

    binop_dict = {"+": "+", "-": "-", "*": "*", "/": "/", "mod": "%", "land": "&", "lor": "|", "lxor": "^",
                  "lsr": ">>", "lsl": "<<"}
    unary_op_set = {"+", "-", "lnot"}
    relation_dict = {"=": "==", "<>": "!=", "<": "<", ">": ">", "<=": "<=", ">=": ">="}
    bool_unary_set = {"not", "#"}
    bool_binary_dict = {"and": " & ", "or": " | ", "xor": " ^ "}
    other = {"reverse", "times", "@"}

    # apply_Expr中的prefixOP接受以上所有类型的运算，除了#，且运算规则也是完全相同的
    def __init__(self, type: str, subtype: str, scope: SyntaxScope, objects: list or None = None, returnNum=1):
        super().__init__()
        self.type = type
        self.subType = subtype
        if objects is None:
            self.objects = []
        else:
            self.objects = objects
        self.scope = scope
        self.appliedOpDict = dict()
        self.returnNum = returnNum

    def add_object(self, tar_object, index: int = None):
        if index is None:
            self.objects.append(tar_object)
        else:
            self.objects.insert(index, tar_object)

    def set_symbol(self, symbol):
        self.syntaxSymbol = symbol

    def add_applied_Op(self, applied_Op, context_list):
        self.appliedOpDict[applied_Op] = context_list

    def __repr__(self):
        s = ""
        s += self.type + "::" + self.subType + "("
        if self.objects:
            for object in self.objects:
                s += str(object) + ","
            s = s[:-1]
        s += ")"
        if self.lhsTypeList:
            s += " as "
            if len(self.lhsTypeList) == 1:
                s += self.lhsTypeList[0].get_real_type()
            else:
                s += f"({','.join([t.get_real_type() for t in self.lhsTypeList])})"
        return s

    def get_type_and_value_for_atom(self):
        """以str的格式返回这个atom类型的expr值的具体数据类型到底是什么"""
        if self.type != "Atom":
            raise TypeMismatchException(self, "bool")
        subtype = self.subType
        content = self.objects[0]
        if subtype == "bool_atom":
            given_type = 'bool'
            given_value = content == "true"
        elif subtype == "integernum":
            #也可以转为float
            given_type = 'numeric'
            given_value = int(content, 0)
        elif subtype == "floatnum":
            given_type = 'float'
            given_value = float(content)
        elif subtype == "character":
            given_type = 'char'
            given_value = content[1::-1]  # 去掉了前后的引号
        elif subtype == "typed_integer":
            t = content.split("_")
            given_type = 'int'.join(t[1].split("i"))
            given_value = int(t[0], 0)
        else:  # typed_float
            t = content.split("_")
            given_type = f"float{t[1][1:]}"
            given_value = t[0]
        return given_type, given_value


class SyntaxEquation(HasRhs):
    """保存一句scade的equation，用来排序和生成代码，包含左值和右值"""
    type: str
    '''euqaion的类型，包括simple_equation，assume，guarantee，emission，control_block'''
    expr: SyntaxExpr = None
    '''右值，
    对simple_equation为Syntaxexpr
    对assert为Syntaxexpr
    对emission为Syntaxexpr,无条件emit会填一个为true的expr
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
    对assert来说是一个_即忽略左值
    '''
    lhs2RhsDict: dict
    '''存储lhs到rhs列表的字典，说实话有点冗余了，但是也没办法就这样吧'''
    vertex: Vertex = None
    '''这个句子所对应的图节点'''

    scope: SyntaxDataDefScope
    '''这个句子所属于的作用域'''

    def __init__(self, type: str, lhs: list, lineno: int=-1):
        super().__init__()
        self.type = type
        self.lhs = lhs
        self.lineno = lineno
        self.lhs2RhsDict = dict()

    def set_expr(self, expr: SyntaxExpr):
        self.expr = expr

    def set_vertex(self, vertex):
        self.vertex = vertex

    def set_scope(self, scope: SyntaxDataDefScope):
        self.scope = scope

    def equation2str(self, depth=0):
        s = "    " * depth + "行号" + ": " + str(self.lineno) + " "
        if self.type == "assume" or self.type == "guarantee":
            s += self.type + " " + self.assertID + " : " + str(self.expr)
            return s
        if self.type == "emission": s += "emit "
        s += " lhs:"
        s += "("
        if len(self.lhs) > 0:
            if self.lhsTypeList:
                s += ",".join(
                    [f"{str(self.lhs[index])} as {self.lhsTypeList[index].get_real_type()}" for index in
                     range(len(self.lhs))])
            else:
                s += ",".join([f"{str(self.lhs[index])}" for index in range(len(self.lhs))])
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

    def dependent_on_param_directly(self, param_name) -> bool:
        """这个句子是否直接依赖于这个变量？输入变量名称"""
        for ls in self.rhsList:
            if param_name in ls: return True
        return False

    def dependent_on_equation_directly_and_get_correspond_lhs(self, tar_equation) -> str or None:
        """判断自己是否直接依赖tar，即检测自己的右值是否和tar的左值重合,如果依赖的话则返回对应的lhs，否则返回None"""
        for lhs in tar_equation.lhs:
            if self.dependent_on_param_directly(lhs): return lhs
        return None

    def get_dependent_equations(self) -> list:
        """这个句子所依赖的全部句子"""
        return [vertex.value for vertex in self.vertex.get_all_from_vertexes()]

    def get_rhs_list_by_name(self, lhs: str):
        """找到这个句子中，lhs所对应的rhs列表，没有则为None"""
        return self.lhs2RhsDict.get(lhs)

    def __repr__(self):
        return self.equation2str()


class SyntaxType:
    """记录type类型"""
    name: str
    '''type_block ，用于重命名之后以str格式保存的名字，type表示其真实类型，这个只是记录了在type_block中定义的别名
    对enum类型，则指具体enum的类型名称
    '''

    scope: SyntaxScope or None
    '''这个type所属的scope,在大部分情况下是没用的，但是如果是path_id与typevar类型就需要依靠他来找到真实的type,
    并且enum类型需要依靠他在代码生成时生成名字
    所以对于以上两种来说是必填，其他的随便
    '''

    type: str
    '''类型，int8，枚举类型等field_decl,array,signed,unsigned,typevar,path_id,enum
    见文档
    typevar类型应该被当作path_id来对待
    '''

    sizeExpr: SyntaxExpr = None
    '''类型为array,signed,unsigned时有效，存储了数组的长度表达式
    必须在编译时可知，并且是严格大于0
    '''

    fields: dict = None
    '''类型为field_decl时有效，存储了ID:SyntaxTypeSymbol的键值对'''

    enumList: list = None
    '''类型为enum时有效，存储了枚举类型的ID列表'''

    value: str = None
    '''类型为typevar，path_id时有效，存储了具体的名字，比如typevar 'T
    只是名字而已，而不是具体的类型
    '''

    arrayType: SyntaxType = None
    '''类型为array时有效，存储了数组的类型'''

    basic_type = ['bool', 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64', 'float32',
                  'float64', 'char', 'ID']
    extend_type = ['integer', 'float', 'signed', 'unsigned', 'numeric', 'any']
    # 有点蠢
    hierarchy_dict = {
        'any': {''' 全部类型'''},
        'numeric': {'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64',
                    'float32', 'float64', 'integer', 'float', 'signed', 'unsigned', 'numeric'},
        'integer': {'integer', 'signed', 'unsigned',
                    'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64'},
        'signed': {'signed', 'int8', 'int16', 'int32', 'int64'},
        'unsigned': {'unsigned', 'uint8', 'uint16', 'uint32', 'uint64'},
        'float': {'float32', 'float64'}
    }

    def __init__(self, tar_type: str,scope=None) -> None:
        self.type = tar_type
        self._size = None
        self.scope=scope
        self._real_type=None# 给path_id的缓存

    def __repr__(self):
        s = ""
        s += "type:" + self.type + " "
        if self.arrayType:
            s += "arrayType:" + str(self.arrayType) + " "
        if self.sizeExpr:
            s += "sizeExpr:" + str(self.sizeExpr) + " "
        if self.fields:
            s += "Fields:{"
            for ID, field in self.fields.items():
                s += ID + ":" + str(field) + ","
            s = s[:-1]
            s += "}"
        if self.enumList:
            s += "EnumList:{"
            for ID in self.enumList:
                s += ID.name + ","
            s = s[:-1]
            s += "}"
        if self.value:
            s += self.value + " "
            try:
                s+=self.get_real_type()
            except Exception as e:
                s+=""
        return s

    def change_name(self):
        if self.type == "array":
            return f'array_{self.arrayType.type}_{self.get_size()}'
        if self.type=="path_id" or self.type=="typevar":
            return self.resolve_path_id().change_name()
        if self.type=="enum":
            return f"{self.name}_{self.scope.get_global_name()}"
        return f'kcg_{self.type}' if self.type in self.basic_type else self.value

    def generate_init_expr(self):
        '''生成这个类型变量的初始值，给init函数准备的'''
        if self.type == "bool":
            return "kcg_true"
        elif self.type in self.basic_type:
            return f"kcg_lit_{self.type}(0)"
        elif self.type=="path_id" or self.type=="typevar":
            return self.resolve_path_id().generate_init_expr()
        elif self.type=="enum":
            default_value=self.enumList[0]
            return default_value.change_name()
            # 我也不知道应该生成什么，相信后人的智慧
            # 我恨过去的自己
            # 未来的我补充了一点
        else:
            return ""

    def belong_to(self, tar_type):
        """此type是否包含于对应的type？
        Parameters:
            tar_type: 一个SyntaxType
        """
        if tar_type.type == "any": return True
        cur_type = self.get_real_type()
        dst_type = tar_type.get_real_type()

        if dst_type in self.extend_type:
            return cur_type in self.hierarchy_dict[dst_type]
        else:
            return cur_type == dst_type

    def __eq__(self, other: SyntaxType):
        if not isinstance(other, SyntaxType):
            return NotImplemented
        if self.type != "array":
            return self.get_real_type() == other.get_real_type()
        else:
            return self.arrayType == other.arrayType and self.get_size() == other.get_size()
            # 数组需要尺寸和类型都一致

    def __ne__(self, other: SyntaxType):
        return not self.__eq__(other)

    def __le__(self, other):
        if not isinstance(other, SyntaxType):
            return NotImplemented
        return self.belong_to(other)

    def __lt__(self, other):
        if not isinstance(other, SyntaxType):
            return NotImplemented
        return self.__le__(other) and self.__ne__(other)

    def get_real_type(self):
        if self.type == "path_id" or self.type == "typevar":
            return self.resolve_path_id().type
        else:
            return self.type

    def is_basic_type(self):
        return self.get_real_type() in self.basic_type

    def resolve_path_id(self):
        if self.type!="path_id" and self.type!="typevar":
            raise Exception(f"{self}不是pathId或者typevar,而是{self.type}")
        type_symbol=self.scope.check_and_get_type_symbol(self.value)
        if type_symbol is None:
            raise UnknownIdentifierException(f"找不到{self.value}，在{self.scope.get_global_name()}内")
        return type_symbol.syntaxType
    def get_size(self):
        '''计算size表达式，得到一个int值'''
        if self._size is None:
            if self.type == "field_decl":
                size = len(self.fields.keys())
            elif self.type == "array":
                from syntax_tree.scade_const_expression import cal_const_expr
                const_value = cal_const_expr(self.sizeExpr)
                if not const_value.type_belong_to(SyntaxType("integer")):
                    raise NotStaticExprException(self.sizeExpr)
                size = const_value.value
            elif self.type == "enum":
                size = len(self.enumList)
            else:
                size = 1
            self._size = size
        return self._size

    def set_size(self, size: int):
        """直接设定长度，覆盖长度表达式（如有）"""
        self._size = size

    def set_element_and_size(self, array_type, size):
        self.arrayType = array_type
        self.set_size(size)
        return self

    def get_element_type_for_array(self):
        """获取数组元素的类型"""
        if self.type != "array":
            raise TypeMismatchException(self, "array类型")
        return self.arrayType


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

    def __init__(self, name: str, syntaxType:SyntaxType or None,visibility: str="public"):
        self.name = name
        self.syntaxType=syntaxType
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

    scope:SyntaxScope
    '''此变量声明时所处于的scope，应该是package'''

    syntaxType: SyntaxType
    '''组合的类型类别,一直有效'''

    valueExpr: SyntaxExpr = None
    '''常量对应值，不为imported时有效
    此处的表达式必须可在编译时计算出数值！
    '''

    __value: ConstValue
    '''具体计算出来的数值，使用get_value方法来访问
    也存储了枚举类型值
    '''

    def __init__(self, name: str, scope,visibility: str = "public", imported=False):
        self.name = name
        self.visibility = visibility
        self.scope=scope
        self.__value = None
        self.isImported = imported

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

    def get_value(self):
        """获取值"""
        if self.__value is None:
            from syntax_tree.scade_const_expression import cal_const_expr
            self.__value = cal_const_expr(self.valueExpr).value
        return self.__value

    def set_value(self, value):
        self.__value = value
    def change_name(self):
        return f"{self.name}_{self.scope.get_global_name()}"
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


class SyntaxPattern(HasRhs):
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
        super().__init__()
        self.type = type
        self.value = value

    def __repr__(self):
        return self.value


class SyntaxClockExpr(HasRhs):
    ID: str
    '''clockexpr中必须的LV6ID'''
    type: str
    '''ID:LV6ID
       notID:NOT LV6ID
       pattern:LPARENTHESE LV6ID MATCH Pattern RPARENTHESE
    '''
    pattern: SyntaxPattern = None
    '''仅type为pattern时不为none'''

    def __init__(self, ID: str, type: str):
        super().__init__()
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
    """局部变量，即在var内部所声明的变量，不包括signal，这一点非常好，因为一个局部变量最多只能是一个equation的左值"""
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
    postExpr: SyntaxExpr = None
    '''pre和init使用，init最好在程序的最后设置为false，pre在程序最后添加上该周期的值
    last也用了
    这个expr是让此symbol在data_def的最后，添加关于此symbol的一些操作
    '''

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
        s += str(self.syntaxType.type)
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
    annoymousTmpCount: int = 0
    '''创建中间变量使用的init'''
    initVar: SyntaxVariableSymbol
    '''时态算子使用的init,每个作用域只有一个init'''
    hasInternalState: bool = False
    '''该作用域内是否存在内存，例如control_block与一些时态算子等'''
    initSymbolSet: set
    '''其子作用域内的所有init变量集合,在userop范围内不能重名，userop以上为空集合'''
    tmpParams: list

    def __init__(self, type, name, prevScope, visibility):
        self.type = type
        self.name = name
        self.prevScope = prevScope
        self.visibility = visibility
        self.childScopeTable = dict()
        self.equations = list()
        self.initVar = None
        self.tmpParams = list()
        self.initSymbolSet = set()

    def add_childScope(self, childScope: SyntaxScope) -> None:
        self.childScopeTable[childScope.name] = childScope

    def get_childScope(self, scopeName) -> SyntaxScope:
        if scopeName in self.childScopeTable.keys():
            return self.childScopeTable[scopeName]
        else:
            return None

    def childScope2str(self, depth=0):
        if not self.childScopeTable: return ""
        s = ""
        s += "    " * depth + "\033[32mchildScope:\033[0m\n"
        for _, scope in self.childScopeTable.items():
            s += scope.scope2str(depth=depth + 1)
        return s

    def generate_name_for_subScope(self):
        s = self.name
        s += "_subScope_"
        s += str(self.anonymousScopeCount)
        self.anonymousScopeCount += 1
        return s

    def get_global_name(self):
        if self.prevScope is None:  # 是global
            return "global"
        elif self.prevScope.name == "*global":
            return self.name
        else:
            return self.prevScope.get_global_name() + "_" + self.name

    def set_init_var(self):
        if self.initVar == None:
            self.initVar = SyntaxVariableSymbol(f"{self.initSymbol}", False, False)
            self.initVar.isOutput = True
            self.initVar.syntaxType = SyntaxType("bool")
            postExpr = SyntaxExpr(type="Atom", subtype="bool_atom", scope=self)
            postExpr.add_object("true")
            self.initVar.postExpr = postExpr
            self.add_tmpSymbol(self.initVar)
        return self.initVar

    def add_tmpSymbol(self, tmpSymbol):
        self.tmpParams.append(tmpSymbol)

    def get_tmpSymbol(self, tmpSymbolName):
        for symbol in self.tmpParams:
            if symbol.name == tmpSymbolName: return symbol
        return None

    def hasInternalState_InThisAndPreEnv(self):
        '''迭代的设置这个与其上层的作用域，标记其为有内存'''
        self.hasInternalState = True
        if self.prevScope is not None:
            self.prevScope.hasInternalState_InThisAndPreEnv()

    def get_my_userOp(self):
        """返回此作用域对应的userOp作用域"""
        if self.type == "package": raise Exception(f"{self.name}是一个package")
        op_scope = self
        while op_scope.type != "function" and op_scope.type != "node":
            op_scope = op_scope.prevScope
        return op_scope

    def get_my_package(self):
        if self.type == "package":
            return self
        return self.get_my_userOp().prevScope

    def resolve_path(self, path_list: list):
        """解析Path类型，直接返回对应的package,输入数组格式,即split::后的"""
        cur_package = self.get_my_package()
        # 先根据path第一个找到对应package，然后逐层向下找
        if len(path_list) == 0:
            return cur_package
        tar_package = cur_package.get_package_InThisAndPreEnv(path_list[0])
        if not tar_package:
            raise UnknownIdentifierException(f"找不到{path_list[0]}")
        for package_name in path_list[1:]:
            tar_package = tar_package.get_package(package_name)
            if not tar_package:
                raise UnknownIdentifierException(f"找不到{path_list[0]}")
        return tar_package

    def resolve_path_id(self, path_id: str):
        """解析path_id，返回对应package和id"""
        path_id_list = path_id.split("::")
        if len(path_id_list) > 1:
            return self.resolve_path(path_id_list[:-1]), path_id_list[-1]
        else:
            return self.get_my_package(), path_id

    def check_and_get_userOp(self, path_id: str):
        """根据路径找到对应的userop，没有则返回None
         Parameters:
            path_id: 带::的路径，指向某个userop
        """
        target_package, op_name = self.resolve_path_id(path_id)
        return target_package.get_userOp(op_name)

    def check_and_get_constant_param(self, param_path_id):
        """检查这个参数是不是一个常数，如果是则返回syntaxconstSymbol，否则返回None
        注意常数也可能声明在userop里
        """
        if self.type!="package":
            userOp=self.get_my_userOp()
            const_param=userOp.get_size_symbol(param_path_id)
            if const_param is not None:
                return const_param
        tar_package, name = self.resolve_path_id(param_path_id)
        const_param = tar_package.get_const_symbol(name)
        return const_param

    def check_and_get_type_symbol(self, type_path_id):
        """根据路径找到对应的type_decl，没有则返回None
         Parameters:
            type_path_id: 指向某个type_decl,可以没有：：
        """
        if self.type!="package":
            userOp=self.get_my_userOp()
            type_symbol=userOp.get_type_var_symbol(type_path_id)
            if type_symbol is not None:
                return type_symbol
        tar_package, name = self.resolve_path_id(type_path_id)
        return tar_package.get_type_symbol(name)


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
        output = dict()
        for _, childScope in self.childScopeTable.items():
            child_return_table = childScope.get_return_symbolTable()
            output.update(child_return_table)
        for _, childScope in self.childScopeTable.items():
            # 再来一遍，这次把缺少的默认表达式补上去
            child_return_table = childScope.get_return_symbolTable()
            for name, symbol in output.items():
                if name in child_return_table.keys(): continue  # 有了就不管了
                equation = SyntaxEquation(type="simple_equation", lhs=[name], lineno=-1)
                if not symbol.defaultExpr:  # 没有默认表达式就报错
                    if symbol.lastExpr:
                        equation.set_expr(symbol.lastExpr)
                        childScope.add_equation(equation)
                    else:
                        raise InitializationErrorException(name)
                else:
                    equation.set_expr(symbol.defaultExpr)
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
    '''存放局部变量，变量名字->SyntaxVariableSymbol,signal不属于这个集合'''
    returnSymbolsTable: dict
    '''存放了当前及下级作用域修改的，外部作用域的变量，变量名字->SyntaxVariableSymbol'''
    initSymbol: str = ""
    '''这个作用域内专用的init变量，每个data_def拥有自己的init变量'''

    equationDependentGraph: Graph
    """标识语句依赖关系的单向图"""
    lhs2EquationDict: dict
    """左值名字找对应句子的dict，没有signal！！"""

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.signalSymbolSet = set()
        self.localSymbolTable = dict()
        self.returnSymbolsTable = dict()
        self.equationDependentGraph = Graph()
        self.lhs2EquationDict = dict()

    def is_param_declared_externally(self, param_name):
        """判断这个变量是不是在此作用域的外部定义的"""
        # 当前作用域找不到这个变量，但是上面的作用域找到了，说明是一个要返回的变量
        symbol = self.get_localVariable(param_name)
        if symbol is None:
            symbol = self.get_localVariable_InThisAndPreEnv(param_name)
        else:
            return False
        if symbol is None:
            raise UnknownIdentifierException(f"{param_name} in {self.get_global_name()}")
        else:
            return True

    def add_equation(self, input_equation: SyntaxEquation):
        # 直接放进去，遍历完所有语句之后再进行排序
        # 还有各种设置索引和句子所属作用域
        self.equations.append(input_equation)
        self.equationDependentGraph.addVertex(input_equation)
        input_equation.set_scope(self)
        # 更新返回列表
        for lhs in input_equation.lhs:
            if lhs == "_": return

            if input_equation.type == "emission":
                # 信号部分单独处理一下,找不到就报错
                if not self.have_signal_InThisAndPreEnv(lhs):
                    raise UnknownIdentifierException(lhs + " in " + str(input_equation))
            else:
                if self.is_param_declared_externally(lhs):
                    self.returnSymbolsTable[lhs] = self.get_localVariable_InThisAndPreEnv(lhs)
                self.lhs2EquationDict[lhs] = input_equation

    def get_equation_by_lhs(self, lhs):
        return self.lhs2EquationDict.get(lhs)

    def get_localVariable(self, name: str) -> SyntaxVariableSymbol or None:
        '''在当前作用域找局部变量'''
        if name not in self.localSymbolTable.keys():
            return self.get_tmpSymbol(name)
        else:
            return self.localSymbolTable[name]

    def get_localVariable_InThisAndPreEnv(self, name: str) -> SyntaxVariableSymbol or None:
        '''递归的找局部变量'''
        local_symbol=self.get_localVariable(name)
        if local_symbol is None:
            return self.prevScope.get_localVariable_InThisAndPreEnv(name)
        else:
            return local_symbol

    def have_signal_InThisAndPreEnv(self, name: str) -> bool:
        '''递归的校验有没有这个signal'''
        if self.type == "function" or self.type == "node":
            # 上层不可能有signal了，不再往上层寻找
            return name in self.signalSymbolSet
        # 上层还能接着找
        if name in self.signalSymbolSet:
            return True
        else:
            if not isinstance(self.prevScope, SyntaxDataDefScope):
                # 上层是automaton或者control_block就跳过这一层
                return self.prevScope.prevScope.have_signal_InThisAndPreEnv(name)
            return self.prevScope.have_signal_InThisAndPreEnv(name)

    def generate_name_for_tmp(self, postfix="tmp"):
        '''生成一个没有被用过的变量名，用来代码生成'''
        count = 1

        name = f"{self.get_global_name()}_{postfix}_{str(count)}"
        while self.get_localVariable_InThisAndPreEnv(name) is not None:
            count += 1
            name = f"{self.get_global_name()}_{postfix}_{str(count)}"
        return name

    def var_change_name(self, name):
        symbol = self.get_localVariable_InThisAndPreEnv(name)
        if symbol is None:
            symbol = self.get_tmpSymbol(name)
        if symbol is not None:
            if symbol.isOutput:
                return f"outC->{symbol.name}"
            elif symbol.isInput:
                return f"inC->{symbol.name}"
            else:
                return symbol.name
        else:
            # raise Exception("???")
            symbol=self.check_and_get_constant_param(name)
            if symbol is None:
                raise ValueError(f"var_change_name error , name:{name}")
            return symbol.change_name()


    def get_return_symbolTable(self):
        '''获取此作用域修改的上层作用域中的变量，不包括信号，path_id是只读的不用管他'''
        return self.returnSymbolsTable

    def generate_init_name_and_check(self) -> str:
        """生成一个用来初始化的名字，将该名字作为此作用域的initsymbol名字。并确保没重名的情况，最高到函数级别不重名即可"""
        name = "init"
        num = 1
        op_scope = self.get_my_userOp()
        # 函数级别
        init_name = name + str(num)
        while not (self.get_localVariable_InThisAndPreEnv(init_name) is None and
                   not self.have_signal_InThisAndPreEnv(init_name) and
                   not init_name in op_scope.initSymbolSet):
            num += 1
            init_name = name + str(num)
        # 保证最上层没有，然后逐层向上更新initSymbolSet，考虑到状态机嵌入的情况，不同的data_def都保存一份
        cur_scope = self
        while cur_scope.type != "function" and cur_scope.type != "node":
            cur_scope = cur_scope.prevScope
            cur_scope.initSymbolSet.add(init_name)
        self.initSymbol = init_name
        return init_name
        # return一下吧，万一有用呢

    def hasInternalState_InThisAndPreEnv(self):
        """对data_def的情况，要重写逻辑
        每个作用域都要有自己的init变量，在子作用域里的语句需要依赖此init变量来进行操作
        在官方的scade代码生成里情况是这样的
        在创建此作用域内的变量后，还需向上更新，让上层作用域持有其下所有子作用域的init变量列表，在init与reset函数内会用到
        """
        if self.hasInternalState: return
        self.hasInternalState = True
        # 添加init变量，更新变量列表
        self.generate_init_name_and_check()

        if self.prevScope is not None and not self.prevScope.hasInternalState:
            self.prevScope.hasInternalState_InThisAndPreEnv()

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
        if self.hasInternalState:
            s += " initSymbol as "
            s += self.initSymbol + " "
        s += "\033[0m"
        s += "\n"
        s += self.signalSymbolSet2str(depth=depth)
        s += self.localSymbolTable2str(depth=depth)
        s += self.childScope2str(depth=depth)
        s += self.equations2str(depth=depth)
        return s

    def signalSymbolSet2str(self, depth=0):
        if not self.signalSymbolSet: return ""
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
        if not self.localSymbolTable: return ""
        s = ""
        s += "    " * depth + "\033[33mlocalSymbolTable:\033[0m\n"
        for ID, symbol in self.localSymbolTable.items():
            s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        return s

    def equations2str(self, depth=0):
        if not self.equations: return ""
        s = ""
        s += "    " * depth + "\033[34mequations:\033[0m\n"
        for equation in self.equations:
            s += equation.equation2str(depth=depth + 1) + "\n"
        return s


class SyntaxArrow:
    pass


class SyntaxArrow:
    '''记录了一条状态机的转移指令,包括了actions，fork'''
    action: str or None = None
    '''一个action就是一个作用域,这里记录了该作用域的ID'''
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
    elseExpr: SyntaxArrow or None = None
    '''type为if时可能有效，不一定会有else语句，若不为None则存储了else对应的语句'''

    def __init__(self, type: str, target: str = None, ifExpr: list = None, elseExpr: SyntaxArrow = None):
        self.type = type
        if type == "if":
            self.ifExprList = ifExpr
            self.elseExpr = elseExpr
        else:
            self.target = target
            self.elseExpr = None

    def set_action(self, action: str):
        self.action = action

    def get_transfer_arrows(self) -> list[SyntaxArrow]:
        """递归的从arrow里面找目标转移状态"""
        if self.type != "if":
            return [self]
        out = list()
        for expr in self.ifExprList:
            out += expr[1].get_transfer_arrows()
        if self.elseExpr:
            out += (self.elseExpr.get_transfer_arrows())
        return out

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
    actionChildScopeList: list[SyntaxDataDefScope]
    '''该状态下所有arrow中action对应的datadef'''

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.untilTransitions = list()
        self.unlessTransitions = list()
        self.actionChildScopeList = list()

    def set_synchroArrow(self, synchroArrow: SyntaxArrow):
        self.synchroArrow = synchroArrow

    def set_unlessTransitions(self, unlessTransitions: list):
        index = 1
        for trans in unlessTransitions:
            arrows = trans[1].get_transfer_arrows()
            for arrow in arrows:
                # 状态的前一个作用域必定是automaton
                self.prevScope.add_edge(self.name, arrow.target, arrow)
                index = arrow.set_index(index)
        self.unlessTransitions = unlessTransitions

    def set_untilTransitions(self, untilTransitions: list):
        self.untilTransitions = untilTransitions
        for trans in untilTransitions:
            arrows = trans[1].get_transfer_arrows()
            for arrow in arrows:
                # 状态的前一个作用域必定是automaton
                self.prevScope.add_edge(self.name, arrow.target, arrow)

    def add_action_subscope(self, action: SyntaxDataDefScope):
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
    transferGraph: Graph
    '''状态转移图，一个单向图,节点为状态名字，边为arrow'''

    transferCount: int
    '''记录了这个状态机转移的总数'''

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.transferGraph = Graph()
        self.stateTable = dict()

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

    def get_localVariable_InThisAndPreEnv(self, name: str) -> SyntaxVariableSymbol or None:
        return self.prevScope.get_localVariable_InThisAndPreEnv(name)

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
                equation = SyntaxEquation(type="simple_equation", lhs=[name], lineno=-1)
                if not symbol.defaultExpr:  # 没有默认表达式就报错
                    raise InitializationErrorException(childScope.get_global_name() + " : " + name)
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
        s += "\n"
        s += "    " * depth
        s += "has transitions:\n"
        s += "\033[0m"
        s += self.graph2str(depth + 1)

        for name, state in self.stateTable.items():
            s += state.state2str(depth=depth + 1)
        s += self.childScope2str(depth=depth)
        return s

    def graph2str(self, depth=0):
        out = ""
        for vertex in self.transferGraph:
            out += f"\033[32m{'    ' * depth}{vertex.value}:\n\033[0m"
            out += f"{'    ' * depth}TO:{len(vertex.get_to_vertexes())}\n\033[33m"
            for to_vertex in vertex.get_to_vertexes():
                connection = vertex.get_to_connection(to_vertex)
                out += f"{'    ' * depth}{connection.type} {to_vertex.value}\n"

            out += f"\033[0m{'    ' * depth}FROM:{len(vertex.get_from_vertexes())}\n\033[33m"
            for from_vertex in vertex.get_from_vertexes():
                connection = vertex.get_from_connection(from_vertex)
                out += f"{'    ' * depth}{connection.type} {from_vertex.value}\n"
            out += "\n"
        return out + "\033[0m"


class SyntaxUserOp(SyntaxDataDefScope):
    """记录func或者node，作为一种scope存在
    被调用时的名字为他的global_name
    """
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
    isImported: bool
    '''是不是imported'''
    sizeDecl: dict
    '''输入的size参数，其中每个值都是const,存名字->SyntaxConstSymbol'''
    inParams: list  # 存SyntaxVariableSymbol
    '''输入参数，是一个变量声明列表'''
    outParams: list  # 存SyntaxVariableSymbol
    '''输出参数，是一个变量声明列表'''
    # tmpParams: list # 存SyntaxVariableSymbol
    # '''中间参数，是一个变量声明列表'''
    numericKind: str = None
    '''如果是模板方法则填入对应类型，不是则为None'''
    typeVarSymbolTable: dict[str:SyntaxTypeSymbol]
    '''声明的模板类型,使用类型变量来记录模板类型，方便查找与替换'''
    specDecl: str = None
    '''声明的SPECIALIZE类型，存放一个pathID，没有声明则为None'''
    dependentFunctions: list
    '''此函数依赖的其他函数的路径列表'''
    apply_exprs: list[SyntaxExpr]
    '''记录了这个op下所有函数调用的情况，用来给代码生成环节添加outC
    '''
    output2inputDependents: list[list[int]]
    '''记录此函数中，输出参数对输入参数的因果关系,二维数组，依次给output记录其依赖的input的列表，均为对应数组下标
    注意，在此userop没有返回值的时候，也会存在依赖关系，就好像存在一个默认的返回值一样。
    所以要注意区分，不能依靠这个表来判断函数的返回值情况，只有outParams才行
    '''

    def __init__(self, type, name, prevscope, visibility, isImported=False):
        super().__init__(type, name, prevscope, visibility)
        self.inParams = list()
        self.outParams = list()
        self.typeVarSymbolTable=dict()
        # self.tmpParams = list()
        self.sizeDecl = dict()
        self.dependentFunctions = list()
        self.output2inputDependents = list()
        self.isImported = isImported
        self.apply_exprs = list()

    def set_sizeDecl(self, sizeDecl: list):
        # 所有的sizeDecl都是正整数，设置成unsigned类型
        for name in sizeDecl:
            const_symbol = SyntaxConstSymbol(name=name,scope=self)
            const_symbol.syntaxType = SyntaxType(tar_type="unsigned")
            self.sizeDecl[name] = const_symbol

    def get_size_symbol(self,name):
        return self.sizeDecl.get(name)

    def set_outParams(self, outParams):
        self.outParams = outParams
        if not self.outParams:
            self.output2inputDependents.append([])
            return
        for para in self.outParams:
            para.isOutput = True
            self.output2inputDependents.append([])

    def get_localVariable(self, name: str) -> SyntaxVariableSymbol or None:
        '''在当前作用域找局部变量，包括输入输出参数'''
        if name not in self.localSymbolTable.keys():
            for symbol in self.inParams:
                if name == symbol.name:
                    return symbol
            for symbol in self.outParams:
                if name == symbol.name:
                    return symbol
            for symbol in self.tmpParams:
                if name == symbol.name:
                    return symbol
            return None
        else:
            return self.localSymbolTable[name]

    def get_localVariable_InThisAndPreEnv(self, name: str) -> SyntaxVariableSymbol or None:
        '''递归的找局部变量，包括输入输出参数'''
        return self.get_localVariable(name)  # 上层不可能有变量了

    def add_dependent_function(self, path):
        if path in self.dependentFunctions: return
        self.dependentFunctions.append(path)

    def add_input_output_dependency(self, input_index, output_index):
        """在这两个输入/输出参数之间建立因果关系"""
        if input_index in self.output2inputDependents[output_index]: return
        self.output2inputDependents[output_index].append(input_index)

    def isTemplate(self):
        return self.numericKind is not None

    def add_type_var(self,type_var_name):
        self.typeVarSymbolTable[type_var_name]=\
            SyntaxTypeSymbol(name=type_var_name,syntaxType=SyntaxType(self.numericKind))

    def get_type_var_symbol(self,type_var_name):
        return self.typeVarSymbolTable.get(type_var_name)

    def add_apply_expr(self, expr: SyntaxExpr):
        self.apply_exprs.append(expr)

    def get_inC_name(self):
        return f"inC_{self.get_global_name()}"

    def get_outC_name(self):
        return f"outC_{self.get_global_name()}"

    def userOp2str(self, depth=0):
        s = "    " * depth
        s += "\033[31m"
        if self.isImported:
            s += " imported "
        s += "userOpScope as " + self.type + " "
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
            for decl in self.sizeDecl.keys():
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
            for decl in self.typeVarSymbolTable.keys():
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
    '''子作用域,这里只保存了子package'''
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

    openPackageList: list
    '''打开的其他package列表，存一个到目标package的路径，需要根据当前package的位置去寻找离他最近的那个'''

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.typeSymbolTable = dict()
        self.constSymbolTable = dict()
        self.sensorSymbolTable = dict()
        self.groupSymbolTable = dict()
        self.userOpTable = dict()
        self.openPackageList = list()

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
        if self.openPackageList:
            s += "    " * depth + "\033[33mopen packages:\033[0m\n"
            for package in self.openPackageList:
                s += "    " * depth + "    " + package + "\n"
        if self.typeSymbolTable:
            s += "    " * depth + "\033[33mtypeSymbolTable:\033[0m\n"
            for ID, symbol in self.typeSymbolTable.items():
                s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        if self.constSymbolTable:
            s += "    " * depth + "\033[33mconstSymbolTable:\033[0m\n"
            for ID, symbol in self.constSymbolTable.items():
                s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        if self.sensorSymbolTable:
            s += "    " * depth + "\033[33msensorSymbolTable:\033[0m\n"
            for ID, symbol in self.sensorSymbolTable.items():
                s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        if self.groupSymbolTable:
            s += "    " * depth + "\033[33mgroupSymbolTable:\033[0m\n"
            for ID, symbol in self.groupSymbolTable.items():
                s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        if self.userOpTable:
            s += "    " * depth + "\033[32muserOpTable:\033[0m\n"
            for ID, symbol in self.userOpTable.items():
                s += symbol.userOp2str(depth=depth + 1)
        if self.childScopeTable:
            s += "    " * depth + "\033[32mchildScope:\033[0m\n"
            for _, scope in self.childScopeTable.items():
                if scope.type == "package": s += scope.package2str(depth=depth + 1)
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
        # self.childScopeTable[userOp.name]=userOp

    def add_open_package(self, path) -> None:
        self.openPackageList.append(path)

    def var_change_name(self, name):
        # generate_id_expr_path_id函数中syntaxUserOp可能为UserOp，此时需要添加inC，outC，可能是package，为了防止package情况下，没有var_change_name。
        return name

    def get_package(self, package_name):
        return self.childScopeTable.get(package_name)

    def get_userOp(self, userOp_name):
        return self.userOpTable.get(userOp_name)

    def get_package_InThisAndPreEnv(self, package_name):
        tar_package = self.get_package(package_name)
        if tar_package: return tar_package
        if self.is_global(): return None
        return self.prevScope.get_package_InThisAndPreEnv(package_name)

    def is_global(self):
        return self.name == "*global"

    def open(self, tar_package):
        """打开对应package，将各种symbol复制到此处"""
        print(f"{self.name}打开了{tar_package.name}")
        self.typeSymbolTable |= tar_package.typeSymbolTable
        self.constSymbolTable |= tar_package.constSymbolTable
        self.sensorSymbolTable |= tar_package.sensorSymbolTable
        self.groupSymbolTable |= tar_package.groupSymbolTable

    def get_const_symbol(self, symbol_name):
        return self.constSymbolTable.get(symbol_name)

    def get_type_symbol(self, type_name):
        return self.typeSymbolTable.get(type_name)
