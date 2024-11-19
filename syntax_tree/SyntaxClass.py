



class SyntaxSymbol:
    """语法树symbol父类"""
    Kind: str
    '''类型，var，sensor，const，user_op等。
    为type则可以转为SyntaxTypeSymbol，为user_op则可以转为SyntaxUserOpSymbol
    否则为SyntaxBaseSymbol
    '''

    Name: str
    '''名字'''


class SyntaxSentence:
    """语句类，保存一句scade语句，用来排序和生成代码"""
    objects: list[SyntaxSymbol]
    relyList: list



class SyntaxScope:
    pass  # 这里是为了让下面的成员变量能识别到自己，删掉就识别不到了



class SyntaxScope:
    """作用域父类，记录当前作用域下的符号表和scade语句"""

    type: str
    '''分为user_op(填function/automaton)，package，data_def三种，分别对应三种不同的子类'''
    name: str
    '''名字'''
    prevScope: SyntaxScope
    '''父作用域'''
    childScopeList: list[SyntaxScope]=None
    '''子作用域'''
    symbolTable: dict=None
    '''符号表'''
    sentences: list[SyntaxSentence]=None
    '''该作用域中的scade语句'''
    def __init__(self,type,name,prevScope):
        self.type=type
        self.name=name
        self.prevScope=prevScope


class SyntaxType:
    """记录type类型"""
    type: str
    '''类型，int8，枚举类型等'''

    integerNum:int=None
    '''类型为signed，unsigned时有效，存储了对应整数值'''

    fields:dict=None
    '''类型为field_decl时有效，存储了ID:SyntaxTypeSymbol的键值对'''

    enumList:list=None
    '''类型为enum时有效，存储了枚举类型的ID列表'''

    def __init__(self,type:str)->None:
        self.type=type
    def __repr__(self):
        s=""
        s+="type:"+self.type+" "
        if self.integerNum:
            s+=str(self.integerNum)+" "
        if self.fields:
            s+="Fields:{"
            for ID,field in self.fields.items():
                s+=ID+":"+str(field)+" "
            s+="}"
        if self.enumList:
            s+="EnumList:{"
            for ID in self.enumList:
                s+=ID+" "
            s+="}"
        return s

class SyntaxTypeSymbol:
    """人为定义的类型变量，输入到符号表里面"""
    name:str
    '''自定义变量名字'''
    visibility:str
    '''可见性，public/private'''

    isImported:bool
    '''是不是imported'''

    syntaxType:SyntaxType=None
    '''组合的类型类别,不为imported时有效'''

    numericKind:str=None
    '''类型为imported时有效，存储了引用的类型'''

    def __init__(self,name:str,visibility:str):
        self.name=name
        self.visibility=visibility
    def __repr__(self):
        s=""
        s+=self.visibility+" "
        s+=self.name+" "
        if self.isImported:
            s+="is imported "+self.numericKind
        else:s+=str(self.syntaxType)
        return s


class SyntaxBaseSymbol(SyntaxSymbol):
    """记录各种变量类型，包括sensor，const，group等"""



class SyntaxUserOpSymbol(SyntaxSymbol, SyntaxScope):
    """记录func或者node，既作为symbol，也作为一种scope存在"""



class SyntaxPackageScope(SyntaxScope):
    """package对应scope，用于package和program
    包含子package，group，type，const，sensor与user_op声明
    program也算作package scope的一种，名字为 *global（防止重名）
    """
    typeSymbolTable:dict=dict()
    '''类型定义的符号表，类型名字->SyntaxTypeSymbol'''
    def __init__(self, type, name, prevscope):
        super().__init__(type, name, prevscope)
    def __repr__(self):
        s="scope "
        s+=self.name+" as "+ self.type
        s+="\ntypeSymbolTable:\n"
        for ID,symbol in self.typeSymbolTable.items():
            s+="    "+ID+":"+str(symbol)+"\n"
        return s
    def add_typeSymbol(self,typeSymbol:SyntaxTypeSymbol)->None:
        self.typeSymbolTable[typeSymbol.name]=typeSymbol



class SyntaxDataDefScope(SyntaxScope):
    """data_def对应scope，用于user_op，control_block中的scope
    包含signal和local声明部分
    """


def reOrderScope(scope:SyntaxScope)->None:
    print("REORDER BEGIN")
    pass

def get_syntax_tree(root_scope:SyntaxScope,depth:int=0)->str:
    s=""
    for i in range(depth):s+=" "
    s+=str(root_scope)
    if root_scope.childScopeList:
        for child in root_scope.childScopeList:
            s+=get_syntax_tree(child,depth+1)
    return s