


class SyntaxSentence:
    """语句类，保存一句scade语句，用来排序和生成代码"""
    objects: list
    relyList: list


class SyntaxSymbol:
    """语法树symbol父类"""
    '''后续加入'''


class SyntaxScope:
    name: str
    '''名字'''
    pass  # 这里是为了让下面的成员变量能识别到自己，删掉就识别不到了



class SyntaxScope:
    """作用域父类，记录当前作用域下的符号表和scade语句"""

    type: str
    '''分为user_op(填function/automaton)，package，data_def三种，分别对应三种不同的子类'''
    name: str
    '''名字'''
    prevScope: SyntaxScope
    '''父作用域'''
    childScopeTable: dict
    '''子作用域'''
    symbolTable: dict
    '''符号表'''
    sentences: list[SyntaxSentence]
    '''该作用域中的scade语句'''
    visibility: str = "public"
    '''可见性，默认为public'''
    def __init__(self,type,name,prevScope,visibility):
        self.type=type
        self.name=name
        self.prevScope=prevScope
        self.visibility=visibility
        self.childScopeTable=dict()
        self.symbolTable=dict()
        self.sentences=list()
    def add_childScope(self,childScope:SyntaxScope)->None:
        self.childScopeTable[childScope.name]=childScope


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
class SyntaxConstSymbol:
    """常量，为imported时没有初值"""

    name:str
    '''自定义变量名字'''

    visibility:str
    '''可见性，public/private'''

    isImported:bool
    '''是不是imported'''

    syntaxType:SyntaxType
    '''组合的类型类别,一直有效'''

    integerNum: int = None
    '''常量对应值，不为imported时有效'''

    def __init__(self,name:str,visibility:str):
        self.name=name
        self.visibility=visibility
    def __repr__(self):
        s = ""
        s += self.visibility + " "
        s += self.name + " "
        s += str(self.syntaxType)+" "
        if self.isImported:
            s += "is imported "
        else:
            s += "=" + str(self.integerNum)
        return s
class SyntaxSensorSymbol:
    name:str
    '''自定义变量名字'''

    syntaxType:SyntaxType
    '''组合的类型类别,一直有效'''

    def __init__(self,name:str):
        self.name=name
    def __repr__(self):
        s=""
        s += self.name + " "
        s += str(self.syntaxType)
        return s
class SyntaxGroupSymbol:
    name:str
    '''自定义变量名字'''
    visibility:str
    '''可见性，public/private'''
    groupExpr:list
    '''group内容，存有内部各SyntaxType类型'''

    def __init__(self,name,visibility):
        self.name=name
        self.visibility=visibility
        self.groupExpr=list()
    def __repr__(self):
        s=""
        s += self.visibility + " "
        s += self.name + " "
        s += "as{ "
        for type in self.groupExpr:
            s+=str(type)+" "
        s+="}"
        return s

class SyntaxDataDefScope(SyntaxScope):
    """data_def对应scope，用于user_op，control_block中的scope
    包含signal和local声明部分
    """
    type: str
    '''分为user_op(填function/automaton)，package，data_def三种，分别对应三种不同的子类'''
    name: str
    '''名字'''
    prevScope: SyntaxScope
    '''父作用域，指向一个package'''
    childScopeTable: dict
    '''子作用域'''
    symbolTable: dict
    '''符号表'''
    sentences: list[SyntaxSentence]
    '''该作用域中的scade语句'''
    visibility: str = "public"
    '''可见性，默认为public'''

class SyntaxUserOp(SyntaxSymbol, SyntaxScope):
    """记录func或者node，既作为symbol，也作为一种scope存在"""
    type: str
    '''分为user_op(填function/automaton)，package，data_def三种，分别对应三种不同的子类'''
    name: str
    '''名字'''
    prevScope: SyntaxScope
    '''父作用域，指向一个package'''
    childScopeTable: dict
    '''子作用域'''
    symbolTable: dict
    '''符号表'''
    sentences: list[SyntaxSentence]
    '''该作用域中的scade语句'''
    visibility: str = "public"
    '''可见性，默认为public'''

    optBody:SyntaxDataDefScope = None
    '''组合一个datadef作为自己的optbody，为None就是没有body'''
    sizeDecl: list
    '''输入的size参数，其中每个值都是const'''
    inParams: list
    '''输入参数，是一个变量声明列表'''
    outParams: list
    '''输出参数，是一个变量声明列表'''
    numericKind: str=None
    '''如果是模板方法则填入对应类型，不是则为None'''
    whereDecl: list
    '''声明的模板类型'''
    speceDecl: str=None
    '''声明的SPECIALIZE类型，存放一个pathID，没有声明则为None'''
    def __init__(self, type, name, prevscope,visibility):
        super().__init__(type,name,prevscope,visibility)
        self.inParams=list()
        self.outParams=list()
        self.whereDecl=list()
    def set_sizeDecl(self,sizeDecl:list):
        self.sizeDecl=sizeDecl
    def userOp2str(self,depth=0):
        s="    "*depth
        s+="\033[31muserOp as "+self.type+" "
        prev_list=list()
        p=self.prevScope
        while p is not None:
            prev_list.append(p.name)
            p=p.prevScope
        for prev_scope in reversed(prev_list):
            s+=prev_scope+"::"
        s+=self.name
        if self.sizeDecl:
            s+="<<"
            for decl in self.sizeDecl:
                s+=decl+","
            s=s[:-1]
            s+=">>"
        s+="("
        # for inParam in self.inParams:
        #     s+=inParam+","
        # s=s[:-1]
        s+=")"
        s+=" returns ("
        # for outParam in self.outParams:
        #     s+=outParam+","
        # s=s[:-1]
        s+=")"
        if self.numericKind:
            s+=" where "
            for decl in self.whereDecl:
                s+=decl+","
            s=s[:-1]
            s+=" is "+self.numericKind
        if self.speceDecl:
            s+=" specialize "+ self.speceDecl
        s+="\033[0m"
        s+="\n"


        return s


class SyntaxPackageScope(SyntaxScope):
    """package对应scope，用于package和program
    包含子package，group，type，const，sensor与user_op声明
    program也算作package scope的一种，名字为 *global（防止重名）
    """

    type: str
    '''分为user_op(填function/automaton)，package，data_def三种，分别对应三种不同的子类'''
    name: str
    '''名字'''
    prevScope: SyntaxScope
    '''父作用域'''
    childScopeTable: dict
    '''子作用域'''
    symbolTable: dict
    '''符号表'''
    sentences: list[SyntaxSentence]
    '''该作用域中的scade语句'''
    visibility: str = "public"
    '''可见性，默认为public'''

    typeSymbolTable:dict
    '''类型定义的符号表，类型名字->SyntaxTypeSymbol'''
    constSymbolTable:dict
    '''常量定义符号表，类型名字->SyntaxConstSymbol'''
    sensorSymbolTable:dict
    '''sensor定义符号表，类型名字->SyntaxSensorSymbol'''
    groupSymbolTable:dict
    '''group定义符号表，类型名字->SyntaxGroupSymbol'''
    userOpTable:dict
    '''函数，node的自定义符号表，因为path寻路只寻package所以独立出来，类型名字->SyntaxUserOpSymbol'''
    def __init__(self, type, name, prevscope,visibility):
        super().__init__(type, name, prevscope,visibility)
        self.typeSymbolTable=dict()
        self.constSymbolTable=dict()
        self.sensorSymbolTable=dict()
        self.groupSymbolTable=dict()
        self.userOpTable=dict()
    def package2str(self, depth=0):
        s="    "*depth
        s+="\033[31mscope "
        prev_list=list()
        p=self.prevScope
        while p is not None:
            prev_list.append(p.name)
            p=p.prevScope
        for prev_scope in reversed(prev_list):
            s+=prev_scope+"::"
        s+=self.name+" as "+ self.type
        s+="\033[0m"
        s+="\n"
        s+="    "*depth+"\033[33mtypeSymbolTable:\033[0m\n"
        for ID,symbol in self.typeSymbolTable.items():
            s+="    "*depth+"    "+ID+":"+str(symbol)+"\n"
        s+="    "*depth+"\033[33mconstSymbolTable:\033[0m\n"
        for ID,symbol in self.constSymbolTable.items():
            s+=" "*depth+"    "+ID+":"+str(symbol)+"\n"
        s+="    "*depth+"\033[33msensorSymbolTable:\033[0m\n"
        for ID,symbol in self.sensorSymbolTable.items():
            s+="    "*depth+"    "+ID+":"+str(symbol)+"\n"
        s+="    "*depth+"\033[33mgroupSymbolTable:\033[0m\n"
        for ID,symbol in self.groupSymbolTable.items():
            s+="    "*depth+"    "+ID+":"+str(symbol)+"\n"
        s+="    "*depth+"\033[32muserOpTable:\033[0m\n"
        for ID,symbol in self.userOpTable.items():
            s+=symbol.userOp2str(depth=depth+1)
        s+="    "*depth+"\033[32mchildScope:\033[0m\n"
        for _,scope in self.childScopeTable.items():
            s+=scope.package2str(depth=depth + 1)
        return s
    def __repr__(self):
        return self.package2str()
    def add_typeSymbol(self,typeSymbol:SyntaxTypeSymbol)->None:
        self.typeSymbolTable[typeSymbol.name]=typeSymbol
    def add_constSymbol(self, constSymbol:SyntaxConstSymbol)->None:
        self.constSymbolTable[constSymbol.name]=constSymbol
    def add_sensorSymbol(self,sensorSymbol:SyntaxSensorSymbol)->None:
        self.sensorSymbolTable[sensorSymbol.name]=sensorSymbol
    def add_groupSymbol(self,groupSymbol:SyntaxGroupSymbol)->None:
        self.groupSymbolTable[groupSymbol.name]=groupSymbol
    def add_userOp(self,userOp:SyntaxUserOp)->None:
        self.userOpTable[userOp.name]=userOp


def reOrderScope(scope:SyntaxScope)->None:
    print("REORDER BEGIN")
    pass
