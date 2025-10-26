from syntax_tree.syntax_class.expression import SyntaxExpr
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
            self.constExpr=SyntaxExpr("Id_expr","Path_id",scope,[value])
        elif _type=="character":
            self.constExpr = SyntaxExpr("Atom", "character", scope, [value])
        elif _type == 'true' or _type == 'false':
            self.constExpr=SyntaxExpr("Atom", "bool_atom",scope,[value])
        elif _type=="_":
            # _ 没有对应的常量表达式
            self.constExpr=None
        else:
            if value.startswith("-"):
                self.constExpr=SyntaxExpr(type="Arith_expr", subtype="unary",scope=scope,objects=
                ["-",SyntaxExpr(type="Atom", subtype=_type, scope=scope,objects=[value[1:]])])
            else:
                self.constExpr=SyntaxExpr(type="Atom", subtype=_type, scope=scope,objects=[value])

    def __repr__(self):
        return str(self.constExpr)