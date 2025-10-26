from syntax_tree.syntax_class.Exceptions import NotStaticExprException, TypeMismatchException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.scade_postprocess import set_rhs_default, flatten_list
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.syntaxType import SyntaxType
    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class List_expr_List_expr(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        # 列表有多个返回值
        # 嵌套列表视为其完全展开格式
        # 这里对这种情况进行处理,如果可以保证按后序处理语法树结构，就不用递归的检查了
        if not self.objects: return
        expr_list = self.objects[0]
        new_object_list = list()
        return_num = 0
        for sub_expr in expr_list:
            self.absorb_rhs(sub_expr)
            return_num += sub_expr.returnNum
            if sub_expr.type == "List_expr":
                # 因为还需要考虑到函数调用的因素，所以这里不可能全部的将list展开
                for o in sub_expr.objects[0]:
                    new_object_list.append(o)
            else:
                new_object_list.append(sub_expr)
        self.objects[0] = new_object_list
        self.returnNum = return_num
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        if not self.post_processed:
            self.post_process(userOp)
        # 需要每个表达式在后处理哪里先记一下自己返回多少个变量，可恶
        # ↑做好了，比想象的简单很多，大部分expr只接受一个输出
        # 然后根据子表达式的返回变量情况，把输入的变量类型发送下去做校验
        expr_list = self.objects[0]
        cur_index = 0
        actual_type_list = list()
        if len(lhs_type_list)!=self.returnNum:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        for sub_expr in expr_list:
            expect_num = sub_expr.returnNum
            actual_type = sub_expr.type_inference(lhs_type_list[cur_index:cur_index + expect_num], userOp)
            actual_type_list.extend(actual_type)
            cur_index += expect_num
            self.lhsClockList.extend(sub_expr.lhsClockList)
        self.set_lhs_type(actual_type_list)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        out_list=list()
        for expr in self.objects[0]:
            out_list.append(expr.generate_code(syntaxUserOp,genEqu))
        out_list=flatten_list(out_list)
        if self.returnNum==1:
            return out_list[0]
        else:
            return out_list
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':
        if len(self.objects[0]) != 1:
            raise NotStaticExprException(self)
        return self.objects[0][0].cal_const_value(required_type, scope)
