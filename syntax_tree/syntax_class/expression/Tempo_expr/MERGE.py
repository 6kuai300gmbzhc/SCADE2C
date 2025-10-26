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
    merge_case_list:list[[str,SyntaxExpr]]
    # todo merge参数第一个为clock修饰的符号，允许枚举和bool
    # todo 在scade中，按顺序而非指定clock对表达式进行merge，枚举类型按声明顺序，bool按先true后false来处理
    def post_process(self, userOp:'SyntaxUserOp'):
        self.returnNum = self.merge_case_list[0][1].returnNum # 太逆天了,其实就是拿第一个case的expr
        self.rhsList = union_rhsLists([case[1].rhsList for case in self.merge_case_list])

        self.clk_symbol=userOp.get_localVariable(self.objects[0])
        if self.clk_symbol is None:
            raise UnknownIdentifierException(self.objects[0])
        self.rhsList=add_rhs_to_each([self.clk_symbol.name],self.rhsList)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        # 对merge情况，需要校验时钟条件是否与对应表达式匹配，是否能够拼凑成完整的时钟
        # 需要分bool情况和枚举情况两种
        # 设置时钟为无时钟
        clk_type = self.clk_symbol.syntaxType.get_real_type()
        clk_name = self.clk_symbol.name
        if clk_type==SyntaxType("bool"):
            allowed_clk_cases={"true","false"}
        elif clk_type.type=="enum":
            allowed_clk_cases={const_symbol.name for const_symbol in clk_type.enumList}
        else:
            raise Exception(f"{self}的时钟变量只支持枚举类型和布尔类型")
        actual_types = type_inference_on_groups([case[1] for case in self.merge_case_list], lhs_type_list, userOp)
        self.set_lhs_type(actual_types)
        for case in self.merge_case_list:
            cond=case[0]
            if cond in allowed_clk_cases:
                allowed_clk_cases.remove(cond)
            else:
                raise Exception(f"{self}中，{cond}条件重复或类型与{self.clk_symbol.name}的类型不符")

            sub_expr:SyntaxExpr=case[1]
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
        if len(allowed_clk_cases) !=0:
            # 有缺少的条件没有补全
            raise Exception(f"{self}中,有时钟的case没有补全，无法拼凑成为基础时钟流")
        self.set_clock_list([SyntaxClockExpr.init_clock_base(userOp)] * self.returnNum)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        tmp_name_list=list()
        for lhs_type in self.lhsTypeList:
            tmp_symbol,tmp_name=generate_tmp_symbol_and_register(syntaxUserOp,lhs_type)
            tmp_name_list.append(tmp_name)

        depth=genEqu.depth
        pre_code=f"{'    '*depth}switch({syntaxUserOp.var_change_name(self.clk_symbol.name)}){{\n"
        for case in self.merge_case_list:
            case_code=f"{'    '*depth}case {syntaxUserOp.var_change_name(case[0])}:\n"
            sub_gen_equ=GenEqu(depth+1)
            sub_expr_code=case[1].generate_code(syntaxUserOp,sub_gen_equ)

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

