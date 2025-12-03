from syntax_tree.scade_generate import generate_tmp_symbol_and_register
from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.Exceptions import TypeMismatchException, UnknownIdentifierException
from syntax_tree.syntax_class.expression import SyntaxExpr

from typing import TYPE_CHECKING



if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.syntaxSymbol import SyntaxVariableSymbol
    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Id_expr_lastSinglequoteLv6id(SyntaxExpr):
    name:str
    '''id名称'''
    tar_symbol:'SyntaxVariableSymbol'
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
        name = self.objects[0]
        self.name = name[1:]  # 去掉开头的'
        self.tar_symbol = userOp.get_localVariable_InThisAndPreEnv(self.name)
        if not self.tar_symbol:
            raise UnknownIdentifierException(self.name)
        if self.tar_symbol.lastExpr:
            self.tar_symbol.lastExpr.post_process(userOp)
    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        # 要求只能提供一个左值类型，所以需要校验
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, data_def)
        required_type = lhs_type_list[0]

        expr_type = self.tar_symbol.syntaxType
        if expr_type <= required_type:
            self.set_lhs_type([expr_type])
        else:
            raise TypeMismatchException(f"{self}有type为{expr_type.get_real_type()}", required_type.get_real_type(),
                                        data_def)
        if self.tar_symbol.lastExpr:
            self.tar_symbol.lastExpr.type_inference([expr_type],data_def)
        self.set_clock_list([self.tar_symbol.whenExpr])
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        """last的情况总是记录这个值上个周期的值，在状态机外与pre相同，在状态机内，pre会读出目标变量在这个状态内上次改变的值"""
        # 向outC中新添加一个变量
        # 例如b=last 'a,添加tmp_a，句子变成：
        # b=outC->tmp_a;outC->tmp_a=a;

        syntaxUserOp.get_my_op_or_state().set_init_var()
        # 在对应变量声明的作用域里加入这个变量，承接last的作用
        if (last_symbol:=self.tar_symbol.get_last_symbol()) is None:
            tmp_var, tmp_var_name = generate_tmp_symbol_and_register(self.tar_symbol.scope,
                                                                     self.tar_symbol.syntaxType,
                                                                     f"{self.name}_mem_last",isOutPut=True)
            self.tar_symbol.set_last_symbol(tmp_var)
        else:
            tmp_var,tmp_var_name=last_symbol,last_symbol.name
        tmp_var.postExpr = f"{syntaxUserOp.var_change_name(tmp_var_name)} = {syntaxUserOp.var_change_name(self.name)};\n"
        tmp_var.lastExpr = self.tar_symbol.lastExpr
        out_name = syntaxUserOp.var_change_name(tmp_var_name)
        return out_name
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)