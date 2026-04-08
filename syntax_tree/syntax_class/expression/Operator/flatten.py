from syntax_tree.scade_generate import generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
from syntax_tree.scade_type_inference import clock_inference_sync
from syntax_tree.syntax_class.Exceptions import UnknownIdentifierException, TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr
from syntax_tree.syntax_class.hasRhs import add_rhs_to_each, union_rhsLists
from syntax_tree.syntax_class.syntaxType import SyntaxType


class Operator_flatten(SyntaxExpr):
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
        param_rhs=[set.union(*self.paramExpr.rhsList)]
        rhs=param_rhs*len(self.struct_type.fields)
        rhs=add_rhs_to_each(self.paramExpr.rhsList,rhs)
        self.returnNum=len(self.struct_type.fields)
        self.rhsList=rhs
    def type_inference(self, lhs_type_list, data_def):
        fields = self.struct_type.fields
        given_types: list[SyntaxType] = [field.syntaxType for field in fields]
        if len(lhs_type_list) != len(fields)\
                or not all([given_type<=field_type for given_type,field_type in zip(given_types,lhs_type_list)]):
            raise TypeMismatchException(self, lhs_type_list, data_def)

        self.paramExpr.type_inference([self.struct_type],data_def)
        self.set_lhs_type(given_types)
        self.set_clock_list(self.paramExpr.lhsClockList)
        return self.lhsTypeList
    def generate_code(self, data_def, genEqu):

        tar_expr = self.paramExprs[0]
        tar_type = tar_expr.lhsTypeList[0].get_real_type()
        if tar_expr.type != "Id_expr":
            tmp_symbol, tmp_name = generate_tmp_symbol_and_register(data_def, tar_type)
            genEqu.add_preEquations(
                assign_lhs_to_rhs_expr(tmp_name, tar_expr.generate_code(data_def, genEqu),
                                       self.lhsTypeList, genEqu.depth, data_def))
            tar_struct_name = tmp_name
        else:
            tar_struct_name = tar_expr.generate_code(data_def, genEqu)

        fields = self.struct_type.fields
        out_cods = [f"{tar_struct_name}.{field.name}" for field in fields]
        return out_cods
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type, subtype, scope, objects, returnNum)
    def set_param_expr(self,param_expr):
        self.paramExpr=param_expr
    def set_params(self,params:list['SyntaxExpr']):
        self.paramExprs=params