import os
import sys
sys.path.append(os.path.dirname(sys.path[0]))
import xlwt
from cfg import create_pda

if __name__ =='__main__':
    wb = xlwt.Workbook(encoding='utf-8', style_compression=0)  # 一个实例
    sheet = wb.add_sheet('scadePda', cell_overwrite_ok=True)  # 工作簿名称
    col = ('文法单元', '下推自动机')

    grammarString = ""
    x=0
    y=0
    with open("../SCADE_Grammar_Full.txt") as r_f:
        for line in r_f.readlines():
            grammarString +=line
            if line in ['\n', '\r\n']:
                # print("pda:")
                print(grammarString)
                pda = create_pda(grammarString)
                for i in range(len(grammarString)-1, -1, -1): # start from last line
                    if grammarString[i] == '\n':
                        grammarString=grammarString[:i] # strip empty line
                    else:
                        break
                sheet.write(x, y, grammarString)
                y = y+1

                # delete Start, Q, Q_loop for sub-grammar
                pdaString = pda.__repr__()
                stateTrans = pdaString.split("\n")
                if len(stateTrans) >= 3:
                    # print("stateTrans[0]", stateTrans[0])
                    # print("stateTrans[1]",stateTrans[1])
                    # print("stateTrans[2]",stateTrans[2])
                    # assert stateTrans[0].startswith("Start") # No need, start with grammar
                    assert stateTrans[1].startswith("Q0")
                    assert stateTrans[2].startswith("Q_loop")
                stateTrans = stateTrans[3:] # delete top 3 elements
                stateTransString = ""
                for stateTran in stateTrans:
                    stateTransString = stateTransString + str(stateTran).strip(")") + "\n"
                
                # print(stateTransString)
                sheet.write(x, y, stateTransString)
                x = x+1
                y = 0
                grammarString = ""
        wb.save('scade_pda_split.xls')
