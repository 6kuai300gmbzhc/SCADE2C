import xlwt
import os
import sys
print("hello")
if __name__ == '__main__':
    print("hello")
    workbook=xlwt.Workbook()
    sheet=workbook.add_sheet("Sheet1")
    sheet.write(0,0,'文法')
    sheet.write(0,1,'完成情况')
    sheet.write(0,2,'对应的C代码')
    count=1
    print("count=",count)

    with open('../grammar_file/scade_grammar.txt','r') as f:
        data=""
        for line in f:
            if line=='\n':
                print("data=",data)
                sheet.write(count,0,data)
                sheet.write(count,1,'完成')
                data=""
                count+=1
            else:
                data+=line
                print("line=",line)
    print("count=",count)
    workbook.save('grammar.xls')
    print("finish")

