class GenEqu:
    expr: str
    '''可直接用于赋值的代码'''
    preEquations: list
    '''若需要使用到中间变量，中间变量的定义需要在该equation之前，是一个列表，列表里的元素是一个C语句'''

    depth: int
    '''这个语句所需要的缩进，默认是0'''

    def __init__(self, depth=0):...

    def add_preEquations(self, equations:str)->None:...

    def __str__(self):...