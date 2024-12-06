from SyntaxClass import *
from scade_preprocess import *

def SyntaxUserOp_generate(syntaxUserOp):
    for elem in syntaxUserOp.equations:
        print(type(elem))

def scade_generate(root_operator):
    print(root_scope.type,len(root_scope.symbolTable),len(root_scope.childScopeTable))
    for k,v in root_scope.userOpTable.items():
        SyntaxUserOp_generate(v)

def scade_parse(input_path:str,root_operator:str):
    parser = yacc(debug=1, start="Program")

    file = open(input_path, 'r')
    strs = file.read()

    pattern1 = r'#pragma [a-zA-Z0-9_!"$#%&\'()*+,\-./:;_<=>?@\\^`|{}~\s]*?#end'
    strs = re.sub(pattern1, '', strs, flags=re.MULTILINE)

    pattern2 = r'\#[\w]+'
    strs = re.sub(pattern2, '', strs)

    pattern3 = re.compile(r'/\*.*?\*/', re.DOTALL)
    strs = re.sub(pattern3, '', strs)

    print("=======strs=====\n", strs)
    string_tokens = get_tokens(strs)
    scade_lexer.set_tokens(string_tokens)
    nodes = parser.parse(strs, lexer=scade_lexer)

    scade_generate(root_operator)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-i', '--input_path', required=True, type=str)
    argParser.add_argument('-r', '--root_operator', required=True, type=str)
    args = argParser.parse_args()
    scade_parse(args.input_path, args.root_operator)