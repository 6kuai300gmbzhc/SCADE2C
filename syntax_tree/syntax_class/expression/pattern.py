from syntax_tree.syntax_class.expression import expression_factory,SyntaxExpr
from syntax_tree.syntax_class.expression.const_value import ConstValue
from syntax_tree.syntax_class.hasRhs import HasRhs


class SyntaxPattern(HasRhs):
    '''pattern类'''

    constExpr:SyntaxExpr or None
    '''等价的常量表达式'''

    value:str
    '''存储内容'''

    constValue: ConstValue or None
    '''计算出的常量value'''

    def __init__(self, _type, value,scope):
        super().__init__()
        self.value=value
        self.constValue = None
        if _type=="path_id":
            self.constExpr=expression_factory("Id_expr","Path_id",scope,[value])
        elif _type=="character":
            self.constExpr = expression_factory("Atom", "character", scope, [value])
        elif _type == 'true' or _type == 'false':
            self.constExpr=expression_factory("Atom", "bool_atom",scope,[value])
        elif _type=="_":
            # _ 没有对应的常量表达式
            self.constExpr=None
        else:
            if value.startswith("-"):
                self.constExpr=expression_factory(type="Arith_expr", sub_type="unary",scope=scope,objects=
                ["-",expression_factory(type="Atom", sub_type=_type, scope=scope,objects=[value[1:]])])
            else:
                self.constExpr=expression_factory(type="Atom", sub_type=_type, scope=scope,objects=[value])
    def post_process(self, userOp:'SyntaxUserOp'):
        if self.constExpr:
            self.constExpr.post_process(userOp)

            return None
        else:
            return None
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        if self.constExpr:
            result=self.constExpr.type_inference(lhs_type_list,userOp)
            self.set_lhs_type(self.constExpr.lhsTypeList)
            self.set_clock_list(self.constExpr.lhsClockList)
            return result
        else:
            self.set_lhs_type([])
            self.set_clock_list([])
            return []
    def generate_code(self,scope,genEqu):
        if self.constExpr is None:
            return "_"
        return self.constExpr.generate_code_const(scope,genEqu)
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope'):
        return self.constExpr.cal_const_value(required_type,scope)
    def __repr__(self):
        return str(self.constExpr)