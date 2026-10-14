from typing import Optional
import re

def analyse_out_scade(f_name, variables)->dict:
    with open(f"{f_name}", "r") as file:
        v_dict:dict[str,list[str]]={name:list() for name in variables}
        while line:=file.readline():
            if not line.startswith("OUTPUT"):continue
            line=line.strip("\n")
            line=line.replace(" ","")
            name_value_pair=line.split("/")[-1].split("=")
            name=name_value_pair[0]
            value=name_value_pair[1]
            if (i := can_be_float(value)) is not None:
                value = i
            elif (i := can_be_int(value)) is not None:
                value = i
            elif re.match(r'false|true',value):
                value=1 if value=="true" else 0
            v_dict[name].append(value)
        return v_dict
def can_be_int(s: str) -> Optional[int]:
    if not isinstance(s, str):
        return None
    try:
        i=int(s)
        return i
    except ValueError:
        return None
def can_be_float(s: str) -> Optional[float]:
    if not isinstance(s, str):
        return None
    try:
        i=float(s)
        return i
    except ValueError:
        return None
def anaylyse_out_c(name):
    with open(name,"r") as file:
        v_dict:dict[str,list[float]]=dict()
        cur_name=""
        while line:=file.readline().strip("\n"):
            if cur_name=="":
                cur_name=line
                v_dict[cur_name]=list()
            else:
                for value in line.split(', ')[:-1]:
                    if (i:=can_be_float(value)) is not None:
                        value=i
                    elif (i:=can_be_int(value)) is not None:
                        value=i
                    elif re.match(r'false|true',value):
                        value=1 if value=="true" else 0
                    v_dict[cur_name].append(value)
                cur_name=""
        return v_dict
def anaylyse_and_draw(tar_dir,name):
    import drawGraph as drawGraph
    c_file_name=f"test_data_{name}_c_out.txt"
    scade_file_name=f"test_data_{name}_scade.out"

    c_dict=anaylyse_out_c(tar_dir+"/"+c_file_name)
    scade_dict = analyse_out_scade(tar_dir+"/"+scade_file_name, c_dict.keys())
    for key in scade_dict.keys():
        scade_v=scade_dict[key]
        c_v=c_dict[key]
        drawGraph.draw_graph(tar_dir+"/"+"img"+"/"+name,(c_v,scade_v),key,name)
def anaylyse_and_compare(c_file_path,scade_file_path):
    c_dict=anaylyse_out_c(c_file_path)
    scade_dict = analyse_out_scade(scade_file_path, c_dict.keys())
    for key in c_dict.keys():
        c_v,l_v=c_dict[key],scade_dict[key]
        if len(c_v)!=len(l_v):
            return False,f"{key}这里返回长度不一样"
        for c,l in zip(c_v,l_v):
            if isinstance(c,str) and isinstance(l,str):
                err_cond=c!=l
            else:
                avg=(c+l)/2
                diff=abs(c-l)
                if avg==0:
                    err_cond=diff!=0
                else:
                    err_cond=diff > abs(avg) / 1000
            if err_cond:
                return False, f"{key}这里{c}与{l}不相等"
    return True,"ok"
def main():
    name="cruise_control"
    tar_dir=f"./test/{name}/kcg"
    main_node_name="cruise_control"
    anaylyse_and_draw(tar_dir,main_node_name)
if __name__=="__main__":
    main()
    # import drawGraph as drawGraph
    # c_dict=anaylyse_out_c("C:\\Users\\48665\\Desktop\\scade\\aircraft_brake_system\\KCG\\test_data_airdynamic_c_out.txt")
    # scade_dict = anaylyse_out_c("C:\\Users\\48665\\PycharmProjects\\scade\\test\\aircraft_brake_system\kcg\\test_data_airdynamic_c_out.txt")
    # for key in scade_dict.keys():
    #     scade_v=scade_dict[key]
    #     c_v=c_dict[key]
    #     drawGraph.draw_graph("."+"/"+"img/airdynamic",(c_v,scade_v),key,"ffff")
