from typing import Optional

from syntax_tree.syntax_class.syntaxType import SyntaxType
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.syntax_class.expression.clock_expr import SyntaxClockExpr

class HasRhs:
    rhsList: list[set[str]]
    '''记录了引用的变量，只有局部变量和signal用来排序,考虑到多返回值的情况，按顺序存放每个返回值所对应的依赖变量'''
    lhsTypeList: list[SyntaxType]
    '''记录了返回值的类型列表，按顺序存放每个返回值的对应类型, 存放syntaxtype，很好'''
    lhsClockList: list['SyntaxClockExpr']
    '''记录了返回值的时钟类型，按顺序存放每个返回值的时钟表达式'''
    allUsedSymbolNames:set[str]
    '''记录了其右值所引用的全部变量名字'''

    def __init__(self):
        self.rhsList = list()
        self.lhsTypeList = list()
        self.lhsClockList = list()
        self.allUsedSymbolNames=set()
    def set_clock_list(self,clock_list:list):
        self.lhsClockList=clock_list

    def absorb_rhs(self, tar):
        """将目标类的rhs吸收到右值中,即返回值增加
        Parameters:
            tar:有rhs的类，即expr，operator，equation
        """
        for rhs in tar.rhsList:
            self.rhsList.append(rhs)

    def set_rhs(self, rhs):
        """设置右值
        Parameters:
            rhs:右值列表,str格式
        """
        if isinstance(rhs,str):
            self.rhsList=[set([rhs])]
            return
        if rhs is None or not rhs:
            self.rhsList = [set()]
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
def union_rhsLists(rhsList_list:list[list[set[str]]])->list[set[str]]:
    """把输入expr列表的右值列表按位取并集"""
    length=len(rhsList_list[0])
    out_list=[set()]*length
    for rhs_list in rhsList_list:
        if len(rhs_list)!=length:
            raise Exception(f"在{rhsList_list}中，存在expr的返回长度不一样")
        for i,rhs in enumerate(rhs_list):
            out_list[i]|=rhs
    return out_list
def add_rhs_to_each(src_list,dst_list):
    """把src中的所有右值逐个加到dst里面"""
    tar_rhs=set().union(*src_list)
    output=list()
    for rhs in dst_list:
        output.append(rhs|tar_rhs)
    return output