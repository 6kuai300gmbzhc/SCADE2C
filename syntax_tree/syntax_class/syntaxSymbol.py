from .syntaxType import SyntaxType
from .expression.clock_expr import SyntaxClockExpr
from .expression.expr_common import SyntaxExpr
from .expression.const_value import ConstValue
from .scope.scope import SyntaxScope
class SyntaxVariableSymbol:
    """局部变量，即在var内部所声明的变量，不包括signal，这一点非常好，因为一个局部变量最多只能是一个equation的左值"""
    _name: str
    '''自定义变量名字'''
    scope: 'SyntaxScope'
    ''' 所属作用域'''
    isClock: bool
    '''是不是clock'''
    isProbe: bool
    '''是不是probe'''
    _isOutput: bool
    '''是不是output，用于代码生成时输出变量需要转化为outC，不能遍历outParams(init,tmp)'''
    isInput: bool
    '''是不是input，用于代码生成时输出变量需要转化为inC'''
    syntaxType: SyntaxType
    '''组合的类型类别,一直有效'''
    whenExpr: SyntaxClockExpr = None
    '''对应whenexpr的值,可以为none'''
    defaultExpr: SyntaxExpr = None
    '''对应default的值，可以为none'''
    lastExpr: SyntaxExpr = None
    '''对应last的值，可以为none'''
    postExpr: list[str] or str = None
    '''pre和init使用，init最好在程序的最后设置为false，pre在程序最后添加上该周期的值
    last也用了
    这个expr是让此symbol在data_def的最后，添加关于此symbol的一些操作
    '''

    def __init__(self, name: str, scope: 'SyntaxScope', isClock: bool=False, isProbe: bool=False):
        self._name = name
        self.isClock = isClock
        self.isProbe = isProbe
        self.isInput = False
        self._isOutput = False
        self.scope = scope
        # 默认情况就是任意时钟
        self.whenExpr= SyntaxClockExpr.init_clock_base(scope)
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self,name):
        self._update_name_output(name)
        self._name=name
    @property
    def isOutput(self):
        return self._isOutput
    @isOutput.setter
    def isOutput(self,value):
        if not self._isOutput and value:
            # 由false变true
            self._output_add_name(self.name)
        elif self._isOutput and not value:
            # 由true变false
            self._output_remove_name(self.name)
        self._isOutput=value
    def _update_name_output(self,new_name):
        if self.isOutput:
            self._output_remove_name(self.name)
            self._output_add_name(new_name)
    def _output_remove_name(self,old_name):
        op=self.scope.get_my_userOp()
        if old_name in op.outCNameSet:
            op.outCNameSet.remove(old_name)
    def _output_add_name(self,name):
        op = self.scope.get_my_userOp()
        op.outCNameSet.add(name)
    def __repr__(self):
        s = ""
        if self.isClock: s += "clock "
        if self.isProbe: s += "probe "
        s += self.name
        s += " as "
        s += str(self.syntaxType.type)
        if self.whenExpr:
            s += "when "
            s += str(self.whenExpr)
        if self.defaultExpr:
            s += "default = "
            s += str(self.defaultExpr)
        if self.lastExpr:
            s += "last = "
            s += str(self.lastExpr)
        return s
class SyntaxConstSymbol:
    """常量，为imported时没有初值"""

    name: str
    '''自定义变量名字'''

    visibility: str
    '''可见性，public/private'''

    isImported: bool
    '''是不是imported'''

    scope: 'SyntaxScope'
    '''此变量声明时所处于的scope，应该是package'''

    syntaxType: SyntaxType
    '''组合的类型类别,一直有效'''

    valueExpr: SyntaxExpr = None
    '''常量对应值，不为imported时有效
    此处的表达式必须可在编译时计算出数值！
    '''

    __value: ConstValue or None
    '''具体计算出来的数值，使用get_value方法来访问
    也存储了枚举类型值
    '''

    used: bool = False
    '''
    这个变量有没有被用过，没用过的不会参与生成
    '''

    def __init__(self, name: str, scope, visibility: str = "public", imported=False):
        self.name = name
        self.visibility = visibility
        self.scope = scope
        self.__value = None
        self.isImported = imported
        self.syntaxType=SyntaxType("any")

    def __repr__(self):
        s = ""
        s += self.visibility + " "
        s += self.name + " "
        s += str(self.syntaxType) + " "
        if self.isImported:
            s += "is imported "
        else:
            s += "=" + str(self.valueExpr)
        return s

    def get_value(self):
        """获取值"""
        if self.__value is None:
            self.__value = self.valueExpr.cal_const_value(SyntaxType("any"), self.scope).value
        return self.__value

    def set_value(self, value):
        self.__value = value

    def change_name(self):
        return f"{self.name}_{self.scope.get_global_name()}"
class SyntaxSensorSymbol:
    name: str
    '''自定义变量名字'''

    syntaxType: SyntaxType
    '''组合的类型类别,一直有效'''

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        s = ""
        s += self.name + " "
        s += str(self.syntaxType)
        return s
class SyntaxGroupSymbol:
    name: str
    '''自定义变量名字'''
    visibility: str
    '''可见性，public/private'''
    groupExpr: list
    '''group内容，存有内部各SyntaxType类型'''

    def __init__(self, name, visibility):
        self.name = name
        self.visibility = visibility
        self.groupExpr = list()

    def __repr__(self):
        s = ""
        s += self.visibility + " "
        s += self.name + " "
        s += "as{ "
        for type in self.groupExpr:
            s += str(type) + " "
        s += "}"
        return s
