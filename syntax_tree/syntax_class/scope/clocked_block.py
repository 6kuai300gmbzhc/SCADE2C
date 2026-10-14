from typing import Optional
from syntax_tree.syntax_class.Exceptions import InitializationErrorException
from syntax_tree.syntax_class.equation import LeftItemId

from syntax_tree.syntax_class.expression import SyntaxExpr
from syntax_tree.syntax_class.scope.scope import SyntaxScope


class SyntaxIfBlock:
    conditionExpr: SyntaxExpr
    '''条件语句'''
    scope: 'SyntaxDataDefScope'
    '''此block所处scope'''
    thenBlock: object
    '''为str存data_def的ID，或者存一个IfBlock对象'''
    elseBlock: object
    '''为str存data_def的ID，或者存一个IfBlock对象'''

    def __init__(self, expr: SyntaxExpr, thenBlock, elseBlock, scope):
        self.conditionExpr = expr
        self.thenBlock = thenBlock
        self.elseBlock = elseBlock
        self.scope = scope

    def __repr__(self):
        return self.block2str(0)

    def block2str(self, depth=0):
        s = ""
        s += "    " * depth + "if " + str(self.conditionExpr) + "\n"
        s += "    " * depth + "then "
        if isinstance(self.thenBlock, SyntaxIfBlock):
            s += "\n" + self.thenBlock.block2str(depth + 1)
        else:
            s += self.thenBlock
        s += "\n"
        s += "    " * depth + "else "
        if isinstance(self.elseBlock, SyntaxIfBlock):
            s += "\n" + self.elseBlock.block2str(depth + 1)
        else:
            s += str(self.elseBlock)
        return s


class SyntaxMatchBlock:
    switchExpr: SyntaxExpr
    '''用于switch的语句'''
    matchList: list
    '''保存（SyntaxPattern.指向data_def的ID）的列表'''
    scope: 'SyntaxDataDefScope'
    '''此block所处scope'''
    def __init__(self, expr: SyntaxExpr, matchList: list,scope):
        self.switchExpr = expr
        self.matchList = matchList
        self.scope=scope

    def __repr__(self):
        return self.block2str(0)

    def block2str(self, depth=0):
        depth += 1
        s = ""
        s += "    " * depth
        s += "switch " + str(self.switchExpr) + "\n"
        for match in self.matchList:
            s += "    " * depth + str(match[0]) + " : " + str(match[1]) + "\n"
        s = s[:-1]
        return s


class SyntaxClockedScope(SyntaxScope):
    type: str
    '''为if_block或者match_block'''
    name: str
    '''名字'''
    prevScope: 'SyntaxDataDefScope'
    '''父作用域'''
    childScopeTable: dict
    '''子作用域'''
    visibility: str = "public"
    '''可见性，默认为public'''
    block: SyntaxIfBlock or SyntaxMatchBlock
    '''组合的block，根据type决定具体类型'''

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)

    def __repr__(self):
        return self.scope2str(0)

    def get_return_symbolTable(self):
        '''汇聚子block的返回值集合，合并起来
        如果有某个子状态没有返回语句，还要把默认值给他加上，很无语
        '''
        output = dict()
        for _, childScope in self.childScopeTable.items():
            child_return_table = childScope.get_return_symbolTable()
            output.update(child_return_table)
        for _, childScope in self.childScopeTable.items():
            # 再来一遍，这次把缺少的默认表达式补上去
            child_return_table = childScope.get_return_symbolTable()
            for name, symbol in output.items():
                if name in child_return_table.keys(): continue  # 有了就不管了
                from syntax_tree.syntax_class.equation import SyntaxEquation
                equation = SyntaxEquation(type="simple_equation", lhs=[LeftItemId(symbol.scope,name)], lineno=-1,scope=symbol.scope)
                if not symbol.defaultExpr:  # 没有默认表达式就报错
                    if symbol.lastExpr:
                        symbol.isOutput=True
                        # equation.set_expr(symbol.lastExpr)
                        # childScope.add_equation(equation)
                    else:
                        raise InitializationErrorException(name)
                else:
                    equation.set_expr(symbol.defaultExpr)
                    childScope.add_equation(equation)
        return output
    def scope2str(self, depth):
        s = "    " * depth
        s += "" + self.type + " as "
        s += self.name
        s += ""
        s += "\n"
        s += self.block.block2str(depth=depth + 1) + "\n"
        s += self.childScope2str(depth=depth)
        return s