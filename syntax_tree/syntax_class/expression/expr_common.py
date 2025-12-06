import functools
import re
import struct
from abc import ABC, abstractmethod, ABCMeta

from syntax_tree.exclude_from_deepcopy import exclude_from_deepcopy
from .clock_expr import SyntaxClockExpr
from ..Exceptions import *
from typing import TYPE_CHECKING
from ..hasRhs import HasRhs


if TYPE_CHECKING:
    from ..syntaxType import SyntaxType
    from ..scope.scope import SyntaxScope
    from .const_value import ConstValue
    from ..syntaxSymbol import SyntaxVariableSymbol
def wrap_method(original_method):
    """包装原始方法，使其在执行前调用process_subexpr_default方法"""
    @functools.wraps(original_method)
    def wrapper(self, *args, **kwargs):
        if self.post_processed:
            return self.__post_result
        from syntax_tree.scade_postprocess import process_subexpr_default,after_post_process
        process_subexpr_default(self, *args, **kwargs)
        result = original_method(self, *args, **kwargs)
        after_post_process(self, *args, **kwargs)
        self.post_processed=True
        self.__post_result=result
        return result
    return wrapper

class ExpressionMeta(type,metaclass=ABCMeta):
    registry = {}
    def __new__(mcls, name, bases, ns):
        cls = super().__new__(mcls, name, bases, ns)
        key = name
        mcls.registry[key] = cls
        original_foo = ns['post_process']
        wrapped_foo = wrap_method(original_foo)
        setattr(cls, 'post_process', wrapped_foo)
        return cls
def expression_factory(type:str,sub_type: str,scope:'SyntaxScope', objects=None,returnNum=1) -> 'SyntaxExpr':
    cls = ExpressionMeta.registry.get(f"{type}_{sub_type}")
    if cls is None:
        raise ValueError(f"Unknown expression: {type}_{sub_type}")
    if objects is None:
        objects=list()
    return cls(type,sub_type,scope,objects,returnNum)
def int_to_expression(number:int,scope)->'SyntaxExpr':
    return expression_factory("Atom","integernum",scope,[str(number)])
def bool_to_expression(bool_value:bool,scope)->'SyntaxExpr':
    return expression_factory("Atom","bool_atom",scope,[str(bool_value).lower()])
# @exclude_from_deepcopy('appliedOp')
# 不可以在父类使用，copy出来的会变成父类
class SyntaxExpr(HasRhs,metaclass=ExpressionMeta):
    """保存expr，右值表达式，可以递归的自己包含自己"""
    type: str
    '''Id_expr  一个ID
    | Atom 一个数，true，false之类的
    | Tempo_expr 各种expr时间运算
    | Arith_expr 各种expr约束，单目双目运算
    | Relation_expr 各种expr比较运算
    | List_expr 空或有的expr表
    | Switch_expr if/with expr
    | Bool_expr 各种expr布尔运算
    | Struct_expr 结构体取数
    | Array_expr 数组运算
    | Apply_expr 函数调用
    '''

    subType: str
    '''上面大类中对应的每个小类（很多），具体看共享文档'''
    objects: list
    '''按顺序保存了具体的内容，具体看文档'''
    scope: 'SyntaxScope'
    '''这个expr所处作用域'''

    syntaxSymbol: 'SyntaxVariableSymbol' = None
    '''Id_expr时，存储的对应symbol，会用到它的,ID没有，很合理'''

    idx_list: list[int]
    '''array_expr时存储的下标列表适用于get,get_default,slice'''
    appliedOpOutCName: str = None
    """
    很蠢，但是又想不到别的方法
    仅在为Apply_expr,且调用了某个node类型的op时有效
    这个变量存储被调用的函数在outC内的名字,为了防止重名
    若调用了function，则现场生成临时变量，不需要这个结构
    """
    appliedOp: 'SyntaxUserOp' = None
    """
    仅在为Apply_expr,且调用了某个函数时有效
    保存了被调用的目标函数是什么
    在类型推导环节填写
    """
    appliedOpContextList: list[int]
    """
    仅在为Apply_expr,且调用了某个函数时有效
    让operator返回他调用的函数情况，比如map (map func<<2>>)<<3>>
    会得到[3,2]
    在类型推导环节填写
    """
    paramExprs:list['SyntaxExpr']=None
    '''代码生成环节用于传递参数的表达式列表
    其中所有表达式的returnNum必须为1，即仅返回单一的变量
    '''
    def add_applied_Op(self, applied_Op, context_list):
        self.appliedOp = applied_Op
        self.appliedOpContextList = context_list
    def set_applied_outC_name(self,name):
        self.appliedOpOutCName=name

    returnNum: int = 1
    """这个表达式返回的值的数量，默认为1
    tempo类型除了time
    list类型
    函数调用
    if/case类型均可返回多个，其他返回一个
    """
    clockMode:str = "sync"
    """是否需要为子表达式对齐时钟
    目前有三种模式
    sync，子表达式时钟需对齐
    latest，不需对齐，但是需要有最大延迟
    any，不管
    有些表达式（比如apply）可以不用对齐
    """
    binop_dict = {"+": "+", "-": "-", "*": "*", "/": "/", "mod": "%", "land": "&", "lor": "|", "lxor": "^",
                  "lsr": ">>", "lsl": "<<","div":"/"}
    unary_op_set = {"+", "-", "lnot"}
    relation_dict = {"=": "==", "<>": "!=", "<": "<", ">": ">", "<=": "<=", ">=": ">="}
    bool_unary_set = {"not", "#"}
    bool_binary_dict = {"and": " & ", "or": " | ", "xor": " ^ "}
    other = {"reverse", "times", "@"}

    # apply_Expr中的prefixOP接受以上所有类型的运算，除了#，且运算规则也是完全相同的
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__()
        self.type = type
        self.subType = subtype
        if objects is None:
            self.objects = []
        else:
            self.objects = objects
        self.scope = scope
        self.returnNum = returnNum
        self.appliedOpContextList = list()
        self.idx_list = list()

        self.post_processed=False
        self.__post_result=None
    def get_type(self):
        return self.type+"_"+self.subType
    def set_symbol(self, symbol):
        self.syntaxSymbol = symbol
    @abstractmethod
    def set_params(self,params:list['SyntaxExpr']):
        """expr有需要更换参数表达式的需求，即在apply调用的时候"""
        self.paramExprs=params

    @abstractmethod
    def set_param_expr(self,param_expr):
        """初始化时设置参数表达式，有时需要向下递归设置，不要忘了"""
        raise Exception("不行")

    def is_clock_expr(self):
        """是否是一个clock属性的变量"""
        return True


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
                s += self.lhsTypeList[0].get_real_type().type
            else:
                s += f"({','.join([t.get_real_type().type for t in self.lhsTypeList])})"
        if self.lhsClockList:
            s += " when "+self.lhsClockList.__repr__()
        return s

    @abstractmethod
    def post_process(self, userOp):
        raise Exception(f"{self}为何？")

    @abstractmethod
    def type_inference(self, lhs_type_list, userOp):
        raise Exception(f"{self}为何？{type(self)}")

    @abstractmethod
    def generate_code(self, syntaxUserOp, genEqu):
        ...
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':
        # 默认情况不支持计算常量表达式
        raise NotStaticExprException(self)
    def get_applied_op(self):
        return None
    def generate_code_const(self,scope,genEqu):
        # 默认的常量表达式生成方法
        # 有可能没有，则报错，或者有自定义的生成方法
        return self.generate_code(scope,genEqu)
    def get_type_and_value_for_atom(self):
        """以str的格式返回这个atom类型的expr值的具体数据类型到底是什么,然后也返回了对应的值"""
        if self.type != "Atom":
            raise TypeMismatchException(self, "bool")
        subtype = self.subType
        content = self.objects[0]
        if subtype == "bool_atom":
            given_type = 'bool'
            given_value = content == "true"
        elif subtype == "integernum":
            # 也可以转为float
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

def can_fit_type(num:int or float,type_str:str)->bool:
    if type_str.startswith("float"):
        return float_can_fit_type(num,type_str)
    elif type_str.startswith("uint") or type_str.startswith("int"):
        return int_can_fit_type(num,type_str)
    else:
        raise Exception(f"为啥?{type_str}")
def int_can_fit_type(int_num:int, type_str:str):

    if type_str.startswith('uint'):
        bits = int(type_str.lstrip('uint'))
        return 0 <= int_num <= (1 << bits) - 1
    else:
        bits = int(type_str.lstrip('int'))
        return -(1 << (bits - 1)) <= int_num < (1 << (bits - 1))
def float_can_fit_type(float_num: float, type_str: str) -> bool:
    type_str = type_str.lower()
    if type_str == "float32":
        try:
            struct.pack('f', float_num)
            return True
        except OverflowError:
            return False
    elif type_str == "float64":
        try:
            struct.pack('d', float_num)
            return True
        except OverflowError:
            return False
    else:
        raise ValueError("输入的类型不对，应该是'float32'或者'float64'.")
