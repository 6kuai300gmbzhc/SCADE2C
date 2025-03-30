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
        if not hasattr(self,"data_def"):
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

