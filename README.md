# Scade2C


##  快速启动 Getting started
需要安装python reliance：
- ply

实现下推自动机生成，以及Scade程序的词法识别，运行`python main.py`

## 文法介绍 About Scade Grammar Lex

不要修改 `SCADE_Grammar_Full.txt` 文件。

DO NOT CHANGE FILE `SCADE_Grammar_Full.txt`.

词法分析基本参照Scade language reference manual的文法；
`ID`, `NAME` 为标识符，是一种token，需要手动编写正则表达式 `t_ID`, `t_NAME`；
值得注意的是，该官方文档中的 `INTEGER`, `CHAR`, `FLOAT` 等实际上表示的是token，但是同时存在`integer`, `char`, `float`这样的关键字，故在我们的文法当中将表示为token的部分改为了`integernum`, `character`, `floatnum`避免ply词法分析的错误； 类似地，文法中有 `typed_integer` 和 `typed_float`也在token中被定义；
Scade没有`int`关键字；

与Lustre不同的是，Scade中有大量特殊的运算符，包括`.`, `->`, `|`，（甚至有`$`？待验证，如果有的话美元符号不能作为空的意思出现）, 所以文法中表示生成式的符号为`::=`；

其他说明：
- #pragma ….. #end 之间的内容表示注释
- #2 等加数字的也要额外处理，但SCADE文法里面并没有说明#2的意义
- 没有隐式转换
- 没有带副作用的表达式（没有i++，没有a += b，没有函数调用的副作用）
- 没有函数作为参数传递。



## 简单语句的语法分析+代码生成

使用 ply.lex 进行词法分析，ply.yacc 进行语法分析，主要写在 `scade_compile.py` 中；

yacc是自底向上的分析方法，最接近终结符、最底层的`def p_xxx(p)`最先被分析到，将右侧的生成式`p[1]...p[n]`规约到左侧非终结符`p[0]`中；其中`p[i]`存储的是在词法分析器中定义的 `class lex_value`。

```python
class lex_value:
    def __init__(self, strs = "", value = "", Type = "", scope = "") -> None:
        self.strs = strs
        self.value = value
        self.type = Type
        self.objects = list()

        self.scope = scope

        self.entity = None
        self.syms = list()
        self.rets = list()
```

lex_value 类的 `strs`字段存储的是该Token/非终结符的名称，一般用来判断是否是'lv6id', 'node', 某种产生式

lex_value 类的 `value`字段为源程序字面值，如果是数值那么存储的是对应数值；

lex_value 类的 `objects`是一个list（在lustre2c项目中写成了`values`），存储右侧生成式的多个lex_value对象

生成式写在 `def p_xxx(p):`的下面一个注释区，不以函数名为准

```python
def p_expression_plus(p):
    'expression : expression PLUS term'
    #   ^            ^        ^    ^
    #  p[0]         p[1]     p[2] p[3]

    p[0] = p[1] + p[3]
```



- 以lustre2c项目的lustre_compile部分代码为例：
  - 生成式右侧仍有非终结符，如果该生成式长度为2，即右侧只有一个vardecl，那么直接规约到左侧
  - 如果该生成式长度为4，即有`<vardecllist> ; <vardecl>` 那么把后续的子生成式的`objects`也添加到左侧的objects list中，以继续给上层取用分析

![7554a6c4002f99c86463a5a3788a745](https://s2.loli.net/2023/10/09/BoNx3bgVudQ2Ym4.png)

​	![image-20231009160627632](https://s2.loli.net/2023/10/09/EHMwQhpfIAkNBFq.png)



## 符号表和作用域

使用`Symbol`和`SymbolTable`两个大类

```python
# 1.使用一个符号表存储变量、函数、类型
# 2.使用符号表树实现作用域

class Symbol:
    def __init__(self, Name=None, Kind=None, Type=None,Public=True,External=False,isPackage=False,PackageName='',isStatemachine=False,StatemachineName='') -> None:
        self.Name = Name  # 标识符的名字, 通常是一个 lv6id
        self.Kind = Kind  # 标识符的类型：常量(Const) 变量(Var) 类型(Type) 节点(Node) 包(Package) 状态(State) 状态机(StateMachine)
                          # Sensor

        self.Type = Type  # Type类型(int , float)
        self.Public=Public
        self.External=External

        self.IsPackage=isPackage
        self.PackageName=PackageName

        self.isStatemachine=isStatemachine
        self.StateMachineName=StatemachineName

        # self.VarType = VarType             #常量、变量等类型标识符的数据类型
        # self.TypeType = TypeType           #类型定义的基本类型，或者Struct、Enum
        # self.IsArray = IsArray
        # self.Size = Size                   #数组类型的大小
        # self.Clock = Clock                 #变量的时钟

        self.IsInput=False
        self.IsReturn = False

        self.Value = None  # 常量、变量等的值

        self.FieldList = dict()  # 结构体变量的成员-类型和枚举变量的名字-整数值
        self.FieldValueList = dict()  # 结构体变量的成员-默认值

        self.StateList = list() # 用于保存当前node里的状态机的状态列表主要保存init状态, 用于生成init和reset函数
        self.Params = list()  # 函数标识符的参数列表
        self.Returns = list()  # 函数标识符的返回值列表
        self.StaticParams = list()  # 函数的静态参数列表
        self.StaticArgs = list()
        self.Code = list()  # 函数标识符的代码

class SymbolTable:
    def __init__(self, EnvName=None, PrevTable=None) -> None:
        self.EnvName = EnvName	   # 当前作用域的名字，初始全局为 Global，如果遇到node，那么新建SymbolTable, EnvName 即为node的lv6id
        self.SymbolTable = dict()  # {Symbol.Name: Symbol}
        self.PrevTable = PrevTable # 父作用域，类型也是一个SymbolTable
        self.ChildTableList = list() # 子作用域，SymbolTable的列表，目前还没用到
```

一个package里面可以有很多个node，需要进入下一层作用域，一个node里面可能有一个有名或无名的状态机，但不需要进入下一层作用域

例如遇到了新的node名或者function名：

```python
def p_user_op_decl_Lv6id(p):
    'User_op_decl_Lv6id : LV6ID'
    p[0]=p[1]
    # 上层作用域将该 id 加入自己的符号表，以备后续使用 PrevTable.getSymbol(id) 获取该符号(Node/function)以便进一步获取对应的参数列表/状态列表等
    global thisEnv
    symbol=Symbol(p[1].value,'Package') # TODO: 这里Kind也可以是一个Node?
    thisEnv.setSymbol(p[1].value,symbol)
    # TODO: 进入新的作用域
    
    newEnv = SymbolTable(p[1].value, thisEnv) # thisEnv设置为newEnv的PrevTable,父作用域
    thisEnv.ChildTableList.append(newEnv)
    thisEnv = newEnv
    print('进入新的作用域: ', thisEnv.EnvName)
```

返回到node或function的上层时，要恢复旧的作用域：

```python

#每一个function和node都会产生一个对应其函数名的.h和.c文件
def p_user_op_decl(p):
    'User_op_decl : Op_kind Interface_status User_op_decl_Lv6id User_op_decl_1 In_Params RETURNS Out_Params User_op_decl_2 User_op_decl_3 Opt_body'
    # print(p[3].value)
    global thisEnv
    symbol=thisEnv.getSymbol(p[3].value) # 该symbol名字在 User_op_decl_Lv6id已经被set
    if isStatemachine==1:
        symbol.isStatemachine==True # 该node name为状态机名字
        print('状态机', p[3].value, '的状态列表: ', symbol.StateList)
        print('TODO: 即将构建reset, init函数body传给generate_c_file')
    for idx in p[5].objects:
        # print(idx.strs,idx.value)
        symbol.Params.append(idx.value)
    for idx in p[7].objects:
        symbol.Returns.append(idx.value)
    generate_head_file(symbol)
    generate_c_file(symbol,p[10].value)  # TODO: 加入 init, reset 函数 body

    # TODO: 恢复上层作用域
    thisEnv = thisEnv.PrevTable
    print('恢复上层作用域: ', thisEnv.EnvName)
```





TODO：Symbol创建子类，Var, Package, Node, Function, Statemachine, 实例化具体的子类



## 项目进展 Project status

2023-06-20: 基本完成PDA生成和词法分析; Still in progress.

2023-10-09: 实现node, function等`.c, .h`代码文件生成，Simple_equation, automaton的until弱迁移函数主体

| 时间       | 任务                                                         |
| ---------- | ------------------------------------------------------------ |
| 2023-12-3  | 修改了init问题，使每个->和fby对应不同的init（后续可以优化，不同的作用域对应不同的init），完成了Control_block中的Clocked_block文法，修改了Equation中的Control_block Return中Return的文法(Return文法貌似没什么用处...) |
| 2024-01-07 | 完成了struct_expr文法，并仿真测试PFD程序，修改遇到的问题后，代码生成正确。 |


Author: Shanshan Wang, Qianhui Xu