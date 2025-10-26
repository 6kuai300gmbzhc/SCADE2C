class EquationDependentException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class UserOpDependentException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class MultipleFlowDefinitionException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class UnknownIdentifierException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
class IncompatibleClockException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
class InitializationErrorException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class ManyInitialStateException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class ParamMismatcheException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class NoInitialStateException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class TypeMismatchException(Exception):
    def __init__(self, value, required_type, data_def=None):
        self.value = value
        self.required_type = required_type
        self.data_def=data_def

    def __str__(self):
        if self.data_def is None:
            return repr(f"{self.value}被要求提供{str(self.required_type)}")
        else:
            return repr(f"{self.value}被要求提供{str(self.required_type)},在{self.data_def.get_global_name()}中")

class TemplateException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class NotStaticExprException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(f"{self.value}不适用于static表达式")

class CanNotInstantiateException(Exception):
    def __init__(self, userOp,param_expr,reason):
        self.userOp=userOp
        self.param_expr=param_expr
        self.reason=reason

    def __str__(self):
        return repr(f"{self.userOp.get_global_name()}无法就{self.param_expr}进行模板函数实例化,因为{self.reason}")
class UnsatisfiableSizeException(Exception):
    def __init__(self,obj,required_size,given_size):
        self.obj=obj
        self.required_size=required_size
        self.given_size=given_size
    def __str__(self):
        return repr(f"{self.obj}有size为{self.required_size},但是却访问了下标为{self.given_size}处的数据")

class CanNotInstantiatePackageException(Exception):
    def __init__(self,stub,reason):
        self.stub=stub
        self.reason=reason
    def __str__(self):
        return f"无法进行model实例化操作:{self.stub},因为{self.reason}"

