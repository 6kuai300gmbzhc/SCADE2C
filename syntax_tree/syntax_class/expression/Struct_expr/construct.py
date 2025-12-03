from syntax_tree.scade_type_inference import clock_inference_sync
from syntax_tree.exclude_from_deepcopy import exclude_from_deepcopy
from syntax_tree.syntax_class.Exceptions import UnknownIdentifierException, TypeMismatchException
from syntax_tree.syntax_class.expression.List_expr.List_expr import List_expr_List_expr
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr

from typing import TYPE_CHECKING
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
if TYPE_CHECKING:
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.syntaxType import SyntaxType, SyntaxTypeSymbol
    from syntax_tree.syntax_class.scope.scope import SyntaxScope

class Struct_expr_construct(SyntaxExpr):
    structName:str
    callDict:dict
    tarStruct:'SyntaxTypeSymbol'
    def post_process(self, userOp:'SyntaxUserOp'):
        # 里面有dict，需要手动处理
        rhs_set=set()
        for expr in self.callDict.values():
            expr.post_process(userOp)
            for rhs in expr.rhsList:
                rhs_set |= rhs
        self.set_rhs(rhs_set)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        if len(lhs_type_list)!=1:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        required_type=lhs_type_list[0]
        if required_type.get_real_type().type=='any':
            # 如果是any类型就要去自己捏一个新的type并添加
            pass
            # p[0] = lex_value("field_decl")
            # p[0].type = p[1].value
            # type_symbol = SyntaxTypeSymbol(p[1].value, p[3])
            # p[0].value = type_symbol

            # p[0] = SyntaxType(tar_type="field_decl", scope=cur_scope)
            # p[0].fields = list()
            # p[0].fields.append(p[2].value)
            # p[0].fields.extend(p[3].value)
        #
        #     p[0] = SyntaxTypeSymbol(name=p[2].value, syntaxType=p[3], visibility=visibility)
        #     p[0].isImported = False
        # global cur_scope
        # cur_scope.add_typeSymbol(p[0])
        else:
            tar_type=required_type.get_real_type()
        sub_clock_list=list()
        # todo 顺序必须和声明顺序一样 何意味
        for sub_type_symbol in tar_type.fields:
            corres_expr:SyntaxExpr=self.callDict.get(sub_type_symbol.name)
            if corres_expr is None:
                raise UnknownIdentifierException(sub_type_symbol.name)
            corres_expr.type_inference([sub_type_symbol.syntaxType],userOp)
            sub_clock_list.append(corres_expr.lhsClockList[0])
        self.set_lhs_type([tar_type])
        self.set_clock_list(clock_inference_sync(sub_clock_list))
        return self.lhsTypeList

    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        struct_type=self.lhsTypeList[0]
        struct_symbol,struct_name=generate_tmp_symbol_and_register(syntaxUserOp,struct_type,f"struct_{struct_type.name}")
        for type_symbol in struct_type.fields:
            if (expr:=self.callDict.get(type_symbol.name)) is not None:
                expr_code = expr.generate_code(syntaxUserOp, genEqu)
            else:
                if type_symbol.const_expr is None:
                    raise Exception(f"结构体{struct_type}需要给{type_symbol}参数赋值")
                type_symbol.const_expr.type_inference([type_symbol.syntaxType.get_real_type()],syntaxUserOp)
                expr_code = type_symbol.const_expr.generate_code(syntaxUserOp, genEqu)
            genEqu.add_preEquations(
                assign_lhs_to_rhs_expr(f"{struct_name}.{type_symbol.name}", expr_code, [type_symbol.syntaxType.get_real_type()], genEqu.depth,
                                       syntaxUserOp))

        return struct_name
    def generate_code_const(self,scope,genEqu):
        sub_code_list=list()
        for name, expr in self.callDict.items():
            sub_code_list.append(f"    .{name}={expr.generate_code_const(scope,genEqu)},\n")
        code=f"{{\n{''.join(sub_code_list)}}}"
        return code
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        self.callDict=objects[0]
        ...
