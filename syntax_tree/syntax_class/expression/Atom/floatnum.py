from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr

from typing import TYPE_CHECKING

from syntax_tree.syntax_class.expression.const_value import ConstValue
from syntax_tree.syntax_class.syntaxType import SyntaxType

if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Atom_floatnum(SyntaxExpr):
    name:str
    '''id名称'''
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        # 要求只能提供一个左值类型，所以需要校验
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, data_def)
        given_type, _ = self.get_type_and_value_for_atom()
        syntax_type = SyntaxType(given_type)
        if lhs_type_list[0] <= syntax_type:
            self.set_lhs_type([lhs_type_list[0]])
        elif syntax_type <= lhs_type_list[0]:
            self.set_lhs_type([syntax_type])
        else:
            raise TypeMismatchException(f"{self}有type为{syntax_type}", lhs_type_list, data_def)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        _type: SyntaxType = self.lhsTypeList[0]
        return f"{_type.change_name_cast()}({self.objects[0]})"
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':
        if not required_type<=SyntaxType("float"):
            raise TypeMismatchException(self.objects[0],required_type,scope)
        if not self.lhsTypeList:
            self.type_inference([required_type],scope)
        return ConstValue(syntax_type=self.lhsTypeList[0], value=int(self.objects[0]))