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

## 项目进展 Project status
2023-06-20: Still in progress.

Author: Shanshan Wang