import copy

from syntax_tree.syntax_class.expression.clock_expr import SyntaxClockExpr
from syntax_tree.syntax_class.expression.const_value import ConstValue
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr, expression_factory
from typing import TYPE_CHECKING

from syntax_tree.syntax_class.Exceptions import *
from syntax_tree.syntax_class.syntaxSymbol import SyntaxConstSymbol
from syntax_tree.syntax_class.syntaxType import SyntaxType
if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Operator_PREFIXOP(SyntaxExpr):
    predefOp: str
    '''包括双目和单目运算符'''
    #\$(\+|-|\*|/|mod|=|<>|<|>|<=|>=|@|times|and|or|xor|land|lor|lxor|lsl|lsr)\$|(\+|-|not|lnot|reverse)\$'
    equivalent_expr:SyntaxExpr
    '''所有predefop都可以写成等价的其他expr的形式
    这些expr包括普通的expr，比如and or等
    以及迭代器算子比如map等
    '''
    equivalent_expr_dict={
        ("$+$","$-$","$*$","$/$","$mod$","$land$","$lor$","$lxor$","$lsl$","$lsr$"):["Arith_expr","binOp"],
        ("$and$", "$or$", "$xor$"): ["Bool_expr", "binOp"],
        ("$=$", "$<>$", "$<$", "$<=$", "$>$","$>=$"): ["Relation_expr", "Relation_expr"],

        ("not$"): ["Bool_expr", "NOT"],
        ("+$", "-$", "lnot$"): ["Arith_expr", "unary"],

        ("$times$"):["Tempo_expr","TIMES"],
        ("$@$"):["Array_expr","at"],
        ("reverse$"):["Array_expr","reverse"]
    }
    def post_process(self, userOp:'SyntaxUserOp'):
        # 整成等价表达式，不管那么多
        result=self.equivalent_expr.post_process(userOp)
        self.rhsList=self.equivalent_expr.rhsList
        self.returnNum=self.equivalent_expr.returnNum
        return result
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        result=self.equivalent_expr.type_inference(lhs_type_list,userOp)
        self.set_lhs_type(result)
        self.set_clock_list(self.equivalent_expr.lhsClockList)
        self.appliedOpContextList=copy.copy(self.equivalent_expr.appliedOpContextList)
        return result
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        params=self.paramExprs
        self.equivalent_expr.set_params(params)
        self.equivalent_expr.appliedOpOutCName=self.appliedOpOutCName
        code=self.equivalent_expr.generate_code(syntaxUserOp,genEqu)
        return code
    def set_params(self,params:list['SyntaxExpr']):
        self.paramExprs=params
    def set_param_expr(self,param_expr):
        # 这里进行初始化等价表达式
        predefOp=self.predefOp
        for key,value in self.equivalent_expr_dict.items():
            if predefOp in key:
                actual_op=predefOp.replace("$","")
                sub_type=value[1]
                _type=value[0]
                objects=[]
                if sub_type=="Relation_expr" or sub_type=="binOp":
                    objects=[param_expr.objects[0],actual_op]
                elif sub_type=="NOT":
                    objects=param_expr.objects[0]
                elif sub_type=="unary":
                    objects=[actual_op,param_expr.objects[0][0]]
                elif sub_type=="at" or sub_type=="TIMES":
                    objects=param_expr.objects[0]
                    # todo 记得改一下两个表达式的语法
                elif sub_type=="reverse":
                    objects=param_expr.objects[0]
                self.equivalent_expr=expression_factory(value[0],value[1],self.scope,objects)
                break
        else:
            # python 的抽象语法
            raise UnknownIdentifierException(f"{predefOp}不是一个predefop")
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        self.predefOp=objects[0]
