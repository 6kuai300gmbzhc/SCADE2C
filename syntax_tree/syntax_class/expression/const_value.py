from typing import Optional
class ConstValue:
    """在expr间传递值的类，封装类型与值"""
    type: 'SyntaxType' = None
    value: int or float or bool or str or list['ConstValue'] or dict[str:'ConstValue']

    def __init__(self, syntax_type, value):
        self.type = syntax_type
        self.value = value

    def type_belong_to(self, syntaxType: 'SyntaxType'):
        return self.type <= syntaxType

    def get_size(self):
        return self.type.get_size()

    def __repr__(self):
        return f"{str(self.type)} value:{str(self.value)}"

    # 组合代替继承太爽啦
    def __eq__(self, other: 'ConstValue'):
        if not isinstance(other, ConstValue):
            return NotImplemented
        return self.type == other.type and self.value == other.value