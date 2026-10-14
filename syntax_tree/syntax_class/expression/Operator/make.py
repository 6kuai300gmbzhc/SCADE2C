from typing import Optional
from syntax_tree.scade_generate import generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
from syntax_tree.scade_type_inference import clock_inference_sync
from syntax_tree.syntax_class.Exceptions import UnknownIdentifierException, TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr
from syntax_tree.syntax_class.hasRhs import add_rhs_to_each
from syntax_tree.syntax_class.syntaxType import SyntaxType


class Operator_make(SyntaxExpr):
    paramExpr:SyntaxExpr
    '''参数表达式，应该是一个list表达式'''
    struct_type:SyntaxType
    '''要做的结构体'''
    def post_process(self, data_def):
        tar_type_name = self.objects[0]
        self.struct_type = data_def.check_and_get_type_symbol(tar_type_name).syntaxType.get_real_type()
        if self.struct_type is None or self.struct_type.type!= "field_decl":
            raise UnknownIdentifierException(tar_type_name)
        self.paramExpr.post_process(data_def)
        rhs=list(set())
        rhs=add_rhs_to_each(self.paramExpr.rhsList,rhs)
        self.set_rhs(rhs)
    def type_inference(self, lhs_type_list, data_def):
        required_type = lhs_type_list[0].get_real_type()

        if len(lhs_type_list) != 1 or required_type != self.struct_type:
            raise TypeMismatchException(self, lhs_type_list, data_def)

        fields = self.struct_type.fields
        given_types: list[SyntaxType] = [field.syntaxType for field in fields]
        self.paramExpr.type_inference(given_types,data_def)
        self.set_lhs_type([self.struct_type])
        self.set_clock_list(clock_inference_sync(self.paramExpr.lhsClockList))
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp, genEqu):
        if len(self.struct_type.fields)!=len(self.paramExprs):
            raise Exception("不对")
        struct_symbol,struct_name=generate_tmp_symbol_and_register(syntaxUserOp,self.struct_type,f"struct_{self.struct_type.name}")
        for type_symbol,expr in zip(self.struct_type.fields,self.paramExprs):
            expr_code = expr.generate_code(syntaxUserOp, genEqu)
            genEqu.add_preEquations(
                assign_lhs_to_rhs_expr(f"{struct_name}.{type_symbol.name}", expr_code, [type_symbol.syntaxType.get_real_type()], genEqu.depth,
                                       syntaxUserOp))

        return struct_name
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type, subtype, scope, objects, returnNum)
    def set_param_expr(self,param_expr):
        self.paramExpr=param_expr
    def set_params(self,params:list['SyntaxExpr']):
        self.paramExprs=params