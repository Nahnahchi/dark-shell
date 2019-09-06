from os import listdir
from os.path import isfile, join, dirname
import inspect


if __name__ == "__main__":
    print(dirname(inspect.getfile(inspect.currentframe())))
    '''
    mypath = "C:/Users/sawal/PycharmProjects/EventLog/res/items"
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    output = "items/all_items.txt"
    for file in onlyfiles:
        with open("items/%s" % file, "r") as f:
            lines = f.readlines()
            for line in lines:
                with open(output, "a") as o:
                    ln = line.split()
                    o.write("\"" + "".join(ln[3:]) + "\": None,\n")
    '''
    '''
    output = "upgrade_materials"
    raw = open("raw.txt", "r")
    items = raw.readlines()
    num = 3
    for x in items:
        item = x.split()
        bonf = ""
        for i in item:
            bonf += " "
            for j in i:
                if j != "(" and j != ")" and j != "#" and j != "," and j != ":":
                    bonf += j
        bonf = bonf.split()
        if len(bonf) > 2:
            for i in range(len(bonf))[num:]:
                if i != 1:
                    bonf[i] = "-" + bonf[i]
        with open("%s.txt" % output, "a") as b:
            b.write(" ".join(bonf[0:num]) + " " + "".join(bonf[num:]).lower()[1:] + "\n")
    '''