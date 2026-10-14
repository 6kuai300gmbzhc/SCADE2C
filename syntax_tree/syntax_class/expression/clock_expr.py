from typing import Optional
from syntax_tree.syntax_class.Exceptions import UnknownIdentifierException, TypeMismatchException
from typing import TYPE_CHECKING

from syntax_tree.syntax_class.hasRhs import HasRhs

if TYPE_CHECKING:
    from syntax_tree.syntax_class.syntaxSymbol import SyntaxVariableSymbol
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

class SyntaxClockExpr(HasRhs):
    ID: str
    '''clockexpr中必须的LV6ID
    若为_则为任意时钟
    '''
    type: str
    '''ID:LV6ID
       notID:NOT LV6ID
       enum:LPARENTHESE LV6ID MATCH Pattern RPARENTHESE
    '''
    #todo 记得改 和lusre一样，只接受pattern是一个枚举类型
    tar_symbol:'SyntaxVariableSymbol' =None
    '''对应的clock标志'''
    enum_name:str = None
    '''在类型为enum时有效，记录了时钟成立是需要匹配的枚举类型名'''
    scope:'SyntaxUserOp'
    ignore_clock_check:bool=False
    '''是否忽略检查，应用在常量表达式的时钟上'''
    def __init__(self, ID: str, type: str,scope:'SyntaxUserOp'):
        super().__init__()
        self.ID = ID
        self.type = type
        self.scope=scope
    @staticmethod
    def init_clock_base(scope):
        '''一个基础时钟'''
        return SyntaxClockExpr(ID="_",type="ID",scope=scope)
    @staticmethod
    def init_clock_any(scope):
        '''一个忽略检查的基础时钟'''
        clk=SyntaxClockExpr(ID="_",type="ID",scope=scope)
        clk.ignore_clock_check=True
        return clk
    def post_process(self,syntaxUserOp:'SyntaxUserOp'):
        if self.ID !="_":
            self.set_tar_symbol()
            if self.type=="enum":
                const_symbol=syntaxUserOp.check_and_get_constant_param(self.enum_name)
                if const_symbol is None:
                    raise UnknownIdentifierException(self.enum_name)
                if self.tar_symbol.syntaxType!=const_symbol.syntaxType:
                    raise TypeMismatchException(self.enum_name,self.tar_symbol.syntaxType,syntaxUserOp)
            self.set_rhs(self.ID)
        else:
            self.set_rhs(None)
    def generate_code(self):
        if self.ID=="_":
            if self.type=="ID":
                return 'kcg_true'
            elif self.type=="notID":
                return 'kcg_false'
        code =""
        if self.tar_symbol is None:
            self.set_tar_symbol()
        if self.tar_symbol.whenExpr.ID!="_":
            code +=self.tar_symbol.whenExpr.generate_code()+" && "
        if self.type=="ID":
            code +=self.scope.var_change_name(self.tar_symbol.name)
        elif self.type=="notID":
            code +="!" + self.scope.var_change_name(self.tar_symbol.name)
        else:
            code +=f"{self.scope.var_change_name(self.tar_symbol.name)}=={self.scope.var_change_name(self.enum_name)}"
        return code
    def set_tar_symbol(self):
        self.tar_symbol = self.scope.get_localVariable(self.ID)
        if self.tar_symbol is None:
            raise UnknownIdentifierException(self.ID)
    def fit(self,clock_expr:'SyntaxClockExpr'):
        """是否兼容"""
        if self.ignore_clock_check or clock_expr.ignore_clock_check:
            return True
        if self.ID=="_" and clock_expr.ID=="_":
            return True
        elif self.ID=="_" or clock_expr.ID=="_":
            return False
        if self.tar_symbol is None:
            self.set_tar_symbol()
        if clock_expr.tar_symbol is None:
            clock_expr.set_tar_symbol()
        return self.tar_symbol is clock_expr.tar_symbol and self.type==clock_expr.type

    def __repr__(self):
        s = ""
        if self.type == "ID":
            s = self.ID
        elif self.type == "notID":
            s = "not " + self.ID
        else:
            s = f"{self.enum_name}({self.ID})"
        return s