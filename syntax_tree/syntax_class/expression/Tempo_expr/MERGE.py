from syntax_tree.scade_type_inference import type_inference_on_groups
from syntax_tree.syntax_class.Exceptions import UnknownIdentifierException, TypeMismatchException
from syntax_tree.syntax_class.expression.clock_expr import SyntaxClockExpr
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.syntax_class.hasRhs import union_rhsLists, add_rhs_to_each
from typing import TYPE_CHECKING
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
from syntax_tree.syntax_class.syntaxSymbol import SyntaxVariableSymbol
from syntax_tree.syntax_class.syntaxType import SyntaxType
if TYPE_CHECKING:

    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Tempo_expr_MERGE(SyntaxExpr):
    clk_symbol:SyntaxVariableSymbol
    merge_case_list:list[SyntaxExpr]
    '''进行merge的表达式列表'''
    allowed_clk_cases:list[str]
    '''表达式需要符合的时钟'''
    def post_process(self, userOp:'SyntaxUserOp'):
        self.returnNum = self.merge_case_list[0].returnNum # 太逆天了,其实就是拿第一个case的expr
        self.rhsList = union_rhsLists([case.rhsList for case in self.merge_case_list])

        # 从表达式中获取值
        if self.objects[0].get_type()!="Id_expr_Path_id":
            raise Exception(f"{self}的第一个参数必须是一个id指向clock变量")
        self.clk_symbol=userOp.get_localVariable_InThisAndPreEnv(self.objects[0].name)
        if self.clk_symbol is None:
            raise UnknownIdentifierException(self.objects[0])
        if not self.clk_symbol.isClock:
            raise Exception(f"{self.objects[0]}需要是clock类型")
        self.rhsList=add_rhs_to_each([self.clk_symbol.name],self.rhsList)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        # 对merge情况，需要校验时钟条件是否与对应表达式匹配，是否能够拼凑成完整的时钟
        # 需要分bool情况和枚举情况两种
        # 设置时钟为无时钟
        clk_type = self.clk_symbol.syntaxType.get_real_type()
        clk_name = self.clk_symbol.name
        if clk_type==SyntaxType("bool"):
            self.allowed_clk_cases=["true","false"]
        elif clk_type.type=="enum":
            self.allowed_clk_cases=[const_symbol.name for const_symbol in clk_type.enumList]
        else:
            raise Exception(f"{self}的时钟变量只支持枚举类型和布尔类型")
        actual_types = type_inference_on_groups([case for case in self.merge_case_list], lhs_type_list, userOp)
        self.set_lhs_type(actual_types)
        if len(self.allowed_clk_cases)!=len(self.merge_case_list):
            raise Exception(f"{self}中,有时钟的case没有补全，无法拼凑成为基础时钟流")
        for allowed_clk,case in zip(self.allowed_clk_cases,self.merge_case_list):
            cond=allowed_clk
            sub_expr:SyntaxExpr=case
            sub_clk_list=sub_expr.lhsClockList
            if cond=="true":
                is_fit=all([sub_clk.ID==clk_name and sub_clk.type=="ID" for sub_clk in sub_clk_list])
            elif cond=="false":
                is_fit=all([sub_clk.ID==clk_name and sub_clk.type=="notID" for sub_clk in sub_clk_list])
            else:
                is_fit=all([sub_clk.ID==clk_name and sub_clk.type=="enum"
                            and sub_clk.enum_name==cond for sub_clk in sub_clk_list])
            if not is_fit:
                raise TypeMismatchException(cond,clk_type,userOp)
        self.set_clock_list([SyntaxClockExpr.init_clock_base(userOp)] * self.returnNum)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        tmp_name_list=list()
        for lhs_type in self.lhsTypeList:
            tmp_symbol,tmp_name=generate_tmp_symbol_and_register(syntaxUserOp,lhs_type)
            tmp_name_list.append(tmp_name)

        depth=genEqu.depth
        pre_code=f"{'    '*depth}switch({syntaxUserOp.var_change_name(self.clk_symbol.name)}){{\n"
        for cond,case in zip(self.allowed_clk_cases,self.merge_case_list):
            if cond in {'true','false'}:
                case_code=f"{'    '*depth}case kcg_{cond}:\n"
            else:
                case_code = f"{'    ' * depth}case {syntaxUserOp.var_change_name(cond)}:\n"
            sub_gen_equ=GenEqu(depth+1)
            sub_expr_code=case.generate_code(syntaxUserOp,sub_gen_equ)

            case_code+="".join(sub_gen_equ.preEquations)
            case_code+=assign_lhs_to_rhs_expr(tmp_name_list,sub_expr_code,self.lhsTypeList,depth+1,syntaxUserOp)
            case_code+=f"{'    '*(depth+1)}break;\n"
            pre_code+=case_code
        pre_code+=f"{'    '*depth}}}\n"
        genEqu.add_preEquations(pre_code)
        return tmp_name_list if len(tmp_name_list)>1 else tmp_name_list[0]
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        self.merge_case_list=self.objects[1]
        ...

