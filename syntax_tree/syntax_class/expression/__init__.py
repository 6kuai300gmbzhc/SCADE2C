# 先把基类和工厂方法暴露出去
from .expr_common import SyntaxExpr, expression_factory
from .Arith_expr.binOp import Arith_expr_binOp
from .Arith_expr.cast import Arith_expr_cast
from .Arith_expr.unary import Arith_expr_unary
from .Array_expr.at import Array_expr_at
from .Array_expr.construct import Array_expr_construct
from .Array_expr.get import Array_expr_get
from .Array_expr.getdefault import Array_expr_getdefault
from .Array_expr.list import Array_expr_list
from .Array_expr.reverse import Array_expr_reverse
from .Array_expr.slice import Array_expr_slice
from .Array_expr.transpose import Array_expr_transpose
from .Atom.bool_atom import Atom_bool_atom
from .Atom.floatnum import Atom_floatnum
from .Atom.integernum import Atom_integernum
from .Atom.typed_float import Atom_typed_float
from .Atom.typed_integer import Atom_typed_integer
from .Bool_expr.binOp import Bool_expr_binOp
from .Bool_expr.HASHTAG import Bool_expr_HASHTAG
from .Bool_expr.NOT import Bool_expr_NOT
from .generalized.get import generalized_get
from .Id_expr.lastSinglequoteLv6id import Id_expr_lastSinglequoteLv6id
from .Id_expr.Path_id import Id_expr_Path_id
from .Id_expr.singlequoteLv6id import Id_expr_singlequoteLv6id
from .List_expr.List_expr import List_expr_List_expr
from .Mixed_constructor.Mixed_constructor import Mixed_constructor_Mixed_constructor
from .Operator.activate import Operator_activate
from .Operator.activateDefault import Operator_activateDefault
from .Operator.activateInitDefault import Operator_activateInitDefault
from .Operator.Apply_expr import Operator_Apply_expr
from .Operator.flatten import Operator_flatten
from .Operator.iterator import Operator_iterator
from .Operator.iterator_mw import Operator_iterator_mw
from .Operator.make import Operator_make
from .Operator.Path_id import Operator_Path_id
from .Operator.PREFIXOP import Operator_PREFIXOP
from .Operator.restart import Operator_restart
from .Relation_expr.Relation_expr import Relation_expr_Relation_expr
from .Struct_expr.construct import Struct_expr_construct
from .Struct_expr.get import Struct_expr_get
from .Switch_expr.CASE import Switch_expr_CASE
from .Switch_expr.IF import Switch_expr_IF
from .Tempo_expr.ARROW import Tempo_expr_ARROW
from .Tempo_expr.FBY import Tempo_expr_FBY
from .Tempo_expr.MERGE import Tempo_expr_MERGE
from .Tempo_expr.PRE import Tempo_expr_PRE
from .Tempo_expr.TIMES import Tempo_expr_TIMES
from .Tempo_expr.WHEN import Tempo_expr_WHEN

# import os
# import sys
# import importlib
# import pkgutil
# from pathlib import Path
#
# # 获取打包后的临时解压目录
# if getattr(sys, 'frozen', False):
#     # 打包后的环境
#     _root = Path(sys._MEIPASS)
# else:
#     # 开发环境
#     _root = Path(__file__).parent
#
# # 遍历顶层包的子目录
# for sub_dir in _root.iterdir():
#     if not sub_dir.is_dir():
#         continue  # 跳过普通文件
#     if sub_dir.name.startswith('__'):  # 跳过 __pycache__ 等
#         continue
#
#     # 构造包名
#     pkg_name = f"{__name__}.{sub_dir.name}"
#
#     # 动态导入模块
#     try:
#         # 尝试直接导入模块
#         for _, mod_name, _ in pkgutil.iter_modules([str(sub_dir)]):
#             full_name = f"{pkg_name}.{mod_name}"
#             importlib.import_module(full_name)
#     except FileNotFoundError:
#         # 如果 iter_modules 失败，尝试手动导入
#         for mod_name in os.listdir(sub_dir):
#             if mod_name.endswith('.py') and not mod_name.startswith('__'):
#                 full_name = f"{pkg_name}.{mod_name[:-3]}"
#                 importlib.import_module(full_name)