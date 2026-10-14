from typing import Optional
from syntax_tree.scade_type_inference import type_inference_on_binop, clock_inference_sync
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr, expression_factory
from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.syntaxType import SyntaxType
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Relation_expr_Relation_expr(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        self.subExpr.post_process(userOp)
        set_rhs_default(self)
        self.subExpr.returnNum = sum([expr.returnNum for expr in self.objects[0]])
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        # =与<>不对子类型做限制
        # 其他情况，则限制为numeric
        # 两侧的类型必须一致
        # 返回类型肯定是bool，不用讨论
        if len(lhs_type_list) != 1 and lhs_type_list[0] != SyntaxType('bool'):
            raise TypeMismatchException(self, lhs_type_list, userOp)

        op = self.objects[1]
        if op == "=" or op == "<>":
            required_type = SyntaxType("any")
        else:
            required_type = SyntaxType("numeric")
        type_inference_on_binop([required_type,required_type],userOp,self.subExpr,True)
        self.set_clock_list(clock_inference_sync(self.subExpr.lhsClockList))
        self.set_lhs_type([SyntaxType('bool')])
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        op = self.objects[1]
        sub_codes = self.subExpr.generate_code(syntaxUserOp, genEqu)
        ele_type=self.subExpr.lhsTypeList[0].get_real_type()
        if ele_type.is_basic_type() or ele_type.type=="enum":
            if op == '<>':
                op = '!='
            elif op == '=':
                op = '=='
            return f"({sub_codes[0]} {op} {sub_codes[1]})"
        elif ele_type.type=="array" or ele_type.type=="field_decl":
            # 如果是数组或结构体用逐元素对比
            if op=='<>' or op=='=':
                cmp_op=self.relation_dict[op]
            else:
                raise Exception(f'{self.subExpr.lhsTypeList[0]}不支持{op}')
            tmp_symbol, tmp_name = generate_tmp_symbol_and_register(syntaxUserOp, SyntaxType("bool"))
            lft_symbol,lft_name = generate_tmp_symbol_and_register(syntaxUserOp, ele_type)
            rht_symbol, rht_name = generate_tmp_symbol_and_register(syntaxUserOp, ele_type)
            depth=genEqu.depth
            genEqu.add_preEquations(assign_lhs_to_rhs_expr(lft_name,sub_codes[0],ele_type,depth,syntaxUserOp))
            genEqu.add_preEquations(assign_lhs_to_rhs_expr(rht_name, sub_codes[1], ele_type, depth, syntaxUserOp))
            genEqu.add_preEquations(f"{'    ' * depth}{tmp_name} = kcg_true;\n")
            # 初始化tmp_name为true
            def generate_cmp_code(syntax_type: SyntaxType, left_name,right_name, depth=1) -> str:
                # 让tmp_name对逐个元素的对比进行与运算
                syntax_type = syntax_type.get_real_type()
                if syntax_type.is_basic_type() or syntax_type.type == "enum":
                    return f"{'    ' * depth}{tmp_name} = {tmp_name} && ({left_name} == {right_name});\n"
                if syntax_type.type == "array":
                    _code = ""
                    idx = "idx" if depth == 1 else f"idx_{str(depth)}"
                    _code += f"{'    ' * (depth)}for(kcg_size {idx}=0;{idx}<{syntax_type.get_size()};{idx}++){{\n" \
                             f"{generate_cmp_code(syntax_type.get_element_type_for_array(), f'{left_name}[{idx}]',f'{right_name}[{idx}]', depth + 1)}" \
                             f"{'    ' * (depth)}}}\n"
                    return _code
                if syntax_type.type == "field_decl":
                    _code = ""
                    for type_symbol in syntax_type.fields:
                        _code += generate_cmp_code(type_symbol.syntaxType, f"{left_name}.{type_symbol.name}",f"{right_name}.{type_symbol.name}",
                                                    depth + 1)
                    return _code
                print(syntax_type)
                raise Exception("为什么")
            genEqu.add_preEquations(generate_cmp_code(ele_type,lft_name,rht_name,depth))
            return tmp_name
        else:
            raise Exception(f"{self}需要更精确的类型")
    def set_params(self,params:list['SyntaxExpr']):
        self.subExpr.objects[0]=[params[0],params[1]]
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        self.subExpr=expression_factory("List_expr","List_expr",scope,[self.objects[0]])
        ...
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':...
