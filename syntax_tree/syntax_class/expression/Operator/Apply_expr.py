import copy

from syntax_tree.syntax_class.expression.clock_expr import SyntaxClockExpr
from syntax_tree.syntax_class.expression.const_value import ConstValue
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr, expression_factory
from typing import TYPE_CHECKING

from syntax_tree.syntax_class.Exceptions import *
from syntax_tree.syntax_class.syntaxSymbol import SyntaxConstSymbol
from syntax_tree.syntax_class.syntaxType import SyntaxType

if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu, assign_lhs_to_rhs_expr, symbol2expr, generate_tmp_symbol_and_register
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope


class Operator_Apply_expr(SyntaxExpr):
    operator: SyntaxExpr
    paramExpr: SyntaxExpr
    '''参数表达式,用于推理'''

    def post_process(self, userOp: 'SyntaxUserOp'):
        self.returnNum = self.operator.returnNum
        self.rhsList = self.operator.rhsList

    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp: 'SyntaxUserOp'):
        result = self.operator.type_inference(lhs_type_list, userOp)
        self.set_lhs_type(result)
        self.lhsClockList = self.operator.lhsClockList
        self.appliedOpContextList = copy.copy(self.operator.appliedOpContextList)
        return result

    def generate_code(self, syntaxUserOp: 'SyntaxUserOp', genEqu: 'GenEqu'):
        # 这里把参数表达式拆成一个个returnNum为1的表达式，便于后续的处理
        if self.paramExprs is None:
            param_expr_list = self.paramExpr.objects[0]
        else:
            param_expr_list = self.paramExprs
        real_param_list = list()
        for param_expr in param_expr_list:
            if param_expr.returnNum == 1:
                real_param_list.append(param_expr)
            else:
                tmp_symbol_list = list()
                for i in range(param_expr.returnNum):
                    tmp_symbol, tmp_name = generate_tmp_symbol_and_register(syntaxUserOp, param_expr.lhsTypeList[i])
                    tmp_symbol.whenExpr = param_expr.lhsClockList[i]
                    tmp_symbol_list.append(tmp_name)
                    real_param_list.append(symbol2expr(tmp_symbol, tmp_name, param_expr.lhsTypeList[i], syntaxUserOp))
                param_code = param_expr.generate_code(syntaxUserOp, genEqu)
                pre_code = assign_lhs_to_rhs_expr(tmp_symbol_list, param_code, param_expr.lhsTypeList, genEqu.depth,
                                                  syntaxUserOp)
                genEqu.add_preEquations(pre_code)
        self.paramExprs = real_param_list

        if not self.appliedOpOutCName and \
                self.get_applied_op() is not None and self.get_applied_op().hasInternalState:
            my_op = syntaxUserOp.get_my_userOp()
            applied_op = self.get_applied_op()
            # 这里看到调用的op有内存，要向自己所属的op注册一个outc名字
            # 先检查一下cache
            if len(applied_op.inParams) == 0:
                if my_op.opReturnSymbolCache.get(applied_op.get_outC_name()) is None:
                    name = my_op.generate_name_for_outC_and_register(applied_op.get_outC_name())
                    my_op.opReturnSymbolCache[applied_op.get_outC_name()] = [name, []]
                else:
                    my_op.apply_exprs.remove(self)
                    name=my_op.opReturnSymbolCache[applied_op.get_outC_name()][0]
            else:
                name = my_op.generate_name_for_outC_and_register(applied_op.get_outC_name())
            self.set_applied_outC_name(name)
        self.operator.set_applied_outC_name(self.appliedOpOutCName)
        self.operator.set_params(self.paramExprs)
        return self.operator.generate_code(syntaxUserOp, genEqu)

    def set_params(self, params: list['SyntaxExpr']):
        self.operator.set_params(params)

    def set_param_expr(self, param_expr):
        self.operator.set_param_expr(param_expr)

    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type, subtype, scope, objects, returnNum)
        self.operator = objects[0]
        self.paramExpr = objects[1]
        self.set_param_expr(objects[1])

    def get_applied_op(self):
        return self.operator.get_applied_op()
