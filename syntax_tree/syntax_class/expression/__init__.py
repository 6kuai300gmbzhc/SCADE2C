import importlib
import pkgutil
from pathlib import Path

# 先把基类和工厂方法暴露出去
from .expr_common import SyntaxExpr, expression_factory
# 2. 只扫描「顶层包」的下一级子目录
_root = Path(__file__).parent           # animals/
for sub_dir in _root.iterdir():
    if not sub_dir.is_dir():
        continue                       # 跳过普通文件
    if sub_dir.name.startswith('__'):  # 跳过 __pycache__ 等
        continue
    # 把目录名当成子包名，import 里面的所有模块
    pkg_name = f"{__name__}.{sub_dir.name}"
    for _, mod_name, _ in pkgutil.iter_modules([str(sub_dir)]):
        full_name = f"{pkg_name}.{mod_name}"
        importlib.import_module(full_name)