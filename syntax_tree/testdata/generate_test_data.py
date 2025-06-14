import random
import os
def generate(input_types,name,data_num):
    if not os.path.exists(f"./syntax_tree/testdata"):
        os.makedirs(f"./syntax_tree/testdata")
    scade_out=""
    c_out:list[list[str]]=[[] for i in range(len(input_types))]
    for i in range(data_num):
        for c,_type in enumerate(input_types):
            v=""
            if _type=="float32":
                v=format(random.random()*100,".2f")
            elif _type=="bool":
                v="true" if random.random()>0.5 else "false"
            scade_out += v + " "
            c_out[c].append(v)
        scade_out+="\n"
    with open(f"./syntax_tree/testdata/test_data_{name}_scade.in","w") as test_data:
        test_data.write(scade_out)
    with open(f"./syntax_tree/testdata/test_data_{name}_c.txt", "w") as c_data:
        c_data.write("\n".join([",".join([c_out[i][j] for j in range(len(c_out[i]))]) for i in range(len(c_out))]))
if __name__ == "__main__":
    generate(["float32","float32","bool"],"DisplayLogic",100)