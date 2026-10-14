from typing import Optional
import copy




def exclude_from_deepcopy(*exclude_attributes):
    """
    在类中添加一个特殊属性 _exclude_from_deepcopy，
    并重写 __deepcopy__ 方法以排除指定的成员变量。
    """

    def decorator(cls):
        # 添加一个特殊属性来存储需要排除的成员变量名称
        cls._exclude_from_deepcopy = exclude_attributes

        # 重写 __deepcopy__ 方法
        def __deepcopy__(self, memo=None):
            if memo is None:
                memo = dict()
            # 创建一个新实例
            new_instance = cls.__new__(cls)
            memo[id(self)] = new_instance

            # 遍历实例的 __dict__，深拷贝所有属性
            for attr_name, attr_value in self.__dict__.items():
                # 豁免的属性不需要deepcopy而直接共享
                if attr_name not in cls._exclude_from_deepcopy:
                    setattr(new_instance, attr_name, copy.deepcopy(attr_value, memo))
                else:
                    if isinstance(attr_value, list):
                        setattr(new_instance, attr_name, copy.copy(attr_value))
                    else:
                        setattr(new_instance, attr_name, attr_value)
            from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
            from syntax_tree.syntax_class.scope.package import SyntaxPackageScope
            if isinstance(self,SyntaxUserOp):
                print(f"{self.name}被copy啦")
            if isinstance(self,SyntaxPackageScope):
                print(f"package {self.name}被copy了")
            return new_instance

        # 将重写的 __deepcopy__ 方法绑定到类上
        cls.__deepcopy__ = __deepcopy__
        return cls

    return decorator