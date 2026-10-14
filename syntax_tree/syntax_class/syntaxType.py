import copy
import sys
from .Exceptions import *
from .scope.scope import SyntaxScope
from typing import Optional
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .expression.expr_common import SyntaxExpr
class SyntaxType:
    """记录type类型"""
    name: str = None
    '''type_block ，用于重命名之后以str格式保存的名字，type表示其真实类型，这个只是记录了在type_block中定义的别名
    对enum类型，则指具体enum的类型名称
    '''

    scope: Optional['SyntaxScope'] = None
    '''这个type所属的scope,在大部分情况下是没用的，但是如果是path_id与typevar类型就需要依靠他来找到真实的type,
    并且enum类型需要依靠他在代码生成时生成名字
    所以对于以上两种来说是必填，其他的随便
    '''

    type: str
    '''类型,见文档
    typevar类型应该被当作path_id来对待
    额外加入other存储不在scade内部的类型，即函数的inc，outc等
    '''

    sizeExpr: 'SyntaxExpr' = None
    '''类型为array,signed,unsigned时有效，存储了数组的长度表达式
    必须在编译时可知，并且是严格大于0
    '''

    fields: Optional[list['SyntaxTypeSymbol']] = None
    '''类型为field_decl时有效，按顺序存储了SyntaxTypeSymbol'''

    enumList: Optional[list['SyntaxConstSymbol']] = None
    '''类型为enum时有效，存储了枚举类型的ID列表'''

    value: str = None
    '''类型为typevar，path_id时有效，存储了具体的名字，比如typevar 'T
    只是名字而已，而不是具体的类型
    '''

    arrayType: 'SyntaxType' = None
    '''类型为array时有效，存储了数组的类型'''

    _size: Optional[int] = None

    min_size: int = sys.maxsize
    '''作为类型推导的参数传递时，表达了可以允许的最低数组长度'''

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

    def get_copy(self):
        """获取自身的复制，与deepcopy不同，没有更换作用域的需要"""
        _copy=copy.copy(self)
        _copy.arrayType=copy.copy(self.arrayType)
        _copy.sizeExpr=copy.copy(self.sizeExpr)
        return _copy

    def __init__(self, tar_type: str, scope=None) -> None:
        self.type = tar_type
        self._size = None
        self.scope = scope
        self._real_type = None  # 给path_id的缓存
        self.fields = None
        self.enumList = list()
        need_scope_type = ("typevar", "array", "enum", "field_decl")
        if tar_type=="any":
            self.min_size=0
        if self.type in need_scope_type and self.scope is None:
            raise Exception(f"{self}的类型必须需要指定scope")

    def __repr__(self):
        s = ""
        s += "type:" + self.type + " "
        if self.arrayType:
            s += "arrayType:" + str(self.arrayType) + " "
        if self._size:
            s += f"size: {self._size}"
        elif self.sizeExpr:
            s += "sizeExpr:" + str(self.sizeExpr) + " "
        if self.fields:
            s += "Fields:{"
            for field in self.fields:
                s += field.name + ":" + str(field.syntaxType.get_real_type()) + ","
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
                s += self.get_real_type().type
            except Exception as e:
                s += ""
        return s

    def change_name(self):
        if self.type == "any":
            return "any"
        if self.type == "array":
            return f'array_{self.arrayType.change_name()}_{self.get_size()}'
        if self.type == "path_id" or self.type == "typevar":
            return self.resolve_path_id().change_name()
        if self.type == "enum":
            return f"{self.name}_{self.scope.get_global_name()}"
        if self.type == "field_decl":
            if self.name is None:
                tmp_name="tmp_struct"
                count=0
                while True:
                    name=tmp_name if count==0 else f"{tmp_name}_{count}"
                    count+=1
                    if self.scope.check_and_get_type_symbol(name) is None:
                        self.name=name
                        break
            return self.name if self.scope.get_global_name() == "" else f"{self.name}_{self.scope.get_global_name()}"
        return f'kcg_{self.type}' if self.type in self.basic_type else self.value

    def change_name_cast(self):
        if self.type == "array":
            raise Exception("array不适应于cast操作")
        if self.type in self.basic_type:
            return f'kcg_lit_{self.type}'
        if self.type == "path_id" or self.type == "typevar":
            return self.resolve_path_id().change_name_cast()
        if self.type == "enum":
            return f"{self.name}_{self.scope.get_global_name()}"
        print(f"{self}的类型无法确定")
        return ""

    def generate_init_expr(self):
        '''生成这个类型变量的初始值，给init函数准备的'''
        if self.type == "bool":
            return "kcg_true"
        elif self.type in self.basic_type:
            return f"kcg_lit_{self.type}(0)"
        elif self.type == "path_id" or self.type == "typevar":
            return self.resolve_path_id().generate_init_expr()
        elif self.type == "enum":
            default_value = self.enumList[0]
            return default_value.change_name()
            # 我也不知道应该生成什么，相信后人的智慧
            # 我恨过去的自己
            # 未来的我补充了一点
        else:
            return ""

    def belong_to(self, tar_type:'SyntaxType'):
        """此type是否包含于对应的type？
        Parameters:
            tar_type: 一个SyntaxType
        """
        if tar_type.type == "any": return True
        if self.type == "any": return True
        cur_type = self.get_real_type().type
        dst_type = tar_type.get_real_type().type
        if dst_type in self.extend_type:
            return cur_type in self.hierarchy_dict[dst_type]
        else:
            return cur_type == dst_type

    def __eq__(self, other: 'SyntaxType'):
        if not isinstance(other, SyntaxType):
            return NotImplemented
        if other.type=="any" or self.type=="any":return True
        cur_type = self.get_real_type()
        dst_type = other.get_real_type()
        if cur_type.type == "array":
            if dst_type.type != "array": return False
            return cur_type.arrayType == dst_type.arrayType and cur_type.get_size() == dst_type.get_size()
            # 数组需要尺寸和类型都一致
        elif cur_type.type == "field_decl":
            if dst_type.type != "field_decl":
                return False
            # 结构体类型比较结构体内部类型是否相等
            # 原来直接用等于就可以了啊，python真方便（
            return cur_type.fields == dst_type.fields
        else:
            return cur_type.get_real_type().type == dst_type.get_real_type().type

    def __ne__(self, other: 'SyntaxType'):
        if not isinstance(other, SyntaxType):
            return NotImplemented
        return not self.__eq__(other)

    def __le__(self, other):
        if not isinstance(other, SyntaxType):
            return NotImplemented
        return self.belong_to(other)

    def __lt__(self, other):
        if not isinstance(other, SyntaxType):
            return NotImplemented
        return self.__le__(other) and self.__ne__(other)

    def get_real_type(self) -> 'SyntaxType':
        if self.type == "path_id" or self.type == "typevar":
            return self.resolve_path_id()
        else:
            return self

    def is_basic_type(self):
        return self.get_real_type().type in self.basic_type

    def is_type_determined(self):
        real_type=self.get_real_type()
        if real_type.type=="array":
            return real_type.get_element_type_for_array().is_type_determined()
        return real_type.type not in self.extend_type

    def resolve_path_id(self) -> 'SyntaxType':
        if self.type != "path_id" and self.type != "typevar":
            raise Exception(f"{self}不是pathId或者typevar,而是{self.type}")
        if self.type=="path_id":
            type_symbol = self.scope.check_and_get_type_symbol(self.value)
            if type_symbol is None:
                raise UnknownIdentifierException(f"找不到{self.value}，在{self.scope.get_global_name()}内")
            return type_symbol.syntaxType.get_real_type()
        else:# typevar
            op=self.scope.get_my_userOp()
            template_type=op.typeVarSymbolTable.get(self.value)
            if template_type is None:
                raise UnknownIdentifierException(f"找不到{self.value}，在{self.scope.get_global_name()}内")
            return template_type.syntaxType


    def get_size(self):
        '''计算size表达式，得到一个int值'''
        if self._size is None:
            real_type=self.get_real_type()
            if real_type.type == "field_decl":
                size = len(real_type.fields)
            elif real_type.type == "array":
                if not real_type.sizeExpr.lhsTypeList:
                    real_type.sizeExpr.post_process(real_type.scope)
                    real_type.sizeExpr.type_inference([SyntaxType("integer")],real_type.scope)
                const_value = real_type.sizeExpr.cal_const_value(SyntaxType("integer"), real_type.scope)
                size = const_value.value
            elif real_type.type == "enum":
                size = len(real_type.enumList)
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
        if self.get_real_type().type=="any":
            return SyntaxType("any")
        if self.get_real_type().type != "array":
            raise TypeMismatchException(self, "array类型")
        return self.get_real_type().arrayType
    def get_element_for_fields(self,name):
        real_type=self.get_real_type()
        for field in real_type.fields:
            if field.name==name:
                return field
        return None
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
    const_expr:'SyntaxExpr'=None

    def __init__(self, name: str, syntaxType: Optional[SyntaxType] = None, visibility: str = "public", isImported=False):
        self.name = name
        self.syntaxType = syntaxType
        self.visibility = visibility
        self.isImported = isImported
        if not isImported:
            self.syntaxType.name = self.name

    def __repr__(self):
        s = ""
        s += self.visibility + " "
        s += self.name + " "
        if self.isImported:
            s += "is imported " + self.numericKind
        else:
            s += str(self.syntaxType)
        return s
    def __eq__(self, other):
        if not isinstance(other,SyntaxTypeSymbol):
            return NotImplemented
        return self.name==other.name and self.syntaxType==other.syntaxType