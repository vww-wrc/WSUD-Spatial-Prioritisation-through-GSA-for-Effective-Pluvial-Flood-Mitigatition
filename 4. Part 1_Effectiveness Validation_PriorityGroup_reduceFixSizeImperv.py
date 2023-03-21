import os.path

import csv
import pandas as pd
from swmmio import Model, inp, rpt
import glob
############## 1. Generate lists containing subcatchment names for the Top 19 sub, mid 19 sub and last 19 subs

toplst= ["S31","S39","S49","S57","S59","S74","S75","S85","S16","S58","S66","S67","S51","S56","S65","S83","S84","S86","S40"]
# print(top)
print("Top 19 subs are:",toplst)

midlst = ['S48', 'S69', 'S76', 'S14', 'S33', 'S55', 'S68', 'S47', 'S50', 'S41', 'S60', 'S52', 'S64', 'S77', 'S24', 'S46', 'S22', 'S23', 'S30']
# print(mid)
print("Mid 19 subs are", midlst) #

lastlst = ['S32', 'S53', 'S61', 'S73', 'S94', 'S93', 'S5', 'S7', 'S13', 'S15', 'S17', 'S21', 'S25', 'S34', 'S38', 'S42', 'S62', 'S78', 'S95']
print("Last 19 subs are",lastlst) #

# ############# 2. Read SWMM model - basefile
inpfileLst = glob.glob("D:\SWMM practice Dec 2020\coogee_swmmfile\_250blk\_ReRun_SA_2022\_updatedSWMMfiles\*.inp")

saveFolder= "\_validation\_newInps"

for originalInp in inpfileLst:
    # print(originalInp)
    removeName = "\_updatedSWMMfiles\_250blk_"
    newfile=originalInp.replace(removeName,'')
    newfile=newfile.replace("_20220124.inp",'')
    print(newfile)

    ub = Model(originalInp)
    sub=ub.inp.subcatchments
    # # print(sub.columns) #'Raingage', 'Outlet', 'Area', 'PercImperv', 'Width', 'PercSlope'

    arealst= sub["Area"].tolist()
    print("Smallest subcatchment has area of",min(arealst), "ha")  ## 1.0713 ha

    # ######### 3 Create a copy of the subcatchment section to generate new impervious area info
    subcopy = sub.copy()
    sublst = subcopy.index.tolist()
    subcopy["originalImperArea"]= subcopy["Area"]*subcopy['PercImperv']*0.01
    # print(originalImperArea)
    print("Smallest size of impervious area in a subcatchment",subcopy["originalImperArea"].min())  ## 0.6093011036639999 - smallest size of impervious area in a subcatchment
    # #
    # #
    ### 4 A. Generate new Subcatchment Section with evenly remove 0.2ha impervious area in all 57 subs (11.4ha in total)
    for s in sublst:
        # print("original subcatchment area for sub",s, "is", subcopy.loc[s,"Area"])
        # print("original imperv % for sub",s, "is", subcopy.loc[s,"PercImperv"],"%")
        # print("original imperv area for sub", s, "is", subcopy.loc[s,"originalImperArea"])
        subcopy.loc[s,"NewImpervArea"] = subcopy.loc[s,"originalImperArea"] - 0.2  ## remove 0.2 ha of impervious area in each subcatchment
        subcopy.loc[s,"NewPerc%"] = ((subcopy.loc[s,"originalImperArea"]- 0.2)/subcopy.loc[s,"Area"])*100  ## recalculate the new impervious area percentage in each subcatchment
        # print("new imperv area for sub",s,"is",subcopy.loc[s,"NewPerc%"], "%")

    # print(subcopy["PercImperv"])
    # print(subcopy["NewPerc%"])

    diff = subcopy["PercImperv"] - subcopy["NewPerc%"]
    print(diff.astype(bool).sum(axis=0))  ## 57 subcatchment all changed

    sub["PercImperv"] = subcopy["NewPerc%"]
    ub.inp.save("{0}\_{1}_b_all_subs_02HaRemoved_20220308.inp".format(saveFolder,newfile))

    ######### 4 B remove 0.6ha in top ranking 19 subs (11.4ha in total)
    mostImpt_ImpervArea =[]

    subcopy["NewPerc%"] = subcopy["PercImperv"]  ## copy all original values of imperv % to new colume - so that the following loop only replace those in the mostImport list.

    for m in toplst:
        # print("original subcatchment area for sub", m, "is", subcopy.loc[m, "Area"])
        # print("original imperv % for sub", m, "is", subcopy.loc[m, "PercImperv"], "%")
        subcopy.loc[m, "originalImpervArea"] = subcopy.loc[m, "Area"]*subcopy.loc[m, "PercImperv"] * 0.01
        # print("original imperv area for sub", m, "is", subcopy.loc[m,"originalImpervArea"])
        mostImpt_ImpervArea.append(subcopy.loc[m,"originalImpervArea"])

        subcopy.loc[m, "NewImpervArea"] = subcopy.loc[m, "originalImpervArea"] - 0.6  ## remove 0.6 ha of impervious area in each subcatchment
        subcopy.loc[m, "NewPerc%"] = ((subcopy.loc[m, "originalImpervArea"] - 0.6)/subcopy.loc[m, "Area"])*100  ## recalculate the new impervious area percentage in each subcatchment
        # print("new imperv area for sub", m, "is", subcopy.loc[m, "NewPerc%"], "%")

    # print(min(mostImpt_ImpervArea))  ## smallest impervious area in top 19 subcatchment is 3.3765ha

    # print(subcopy["PercImperv"])
    # print(subcopy["NewPerc%"])
    diff = subcopy["PercImperv"] - subcopy["NewPerc%"]
    print("number of updated subcatchments with new impervious area %",diff.astype(bool).sum(axis=0))

    sub["PercImperv"] = subcopy["NewPerc%"]
    ub.inp.save("{0}\_{1}_c_Top19subs_06HaRemoved.inp".format(saveFolder,newfile))


    ########## 4 C remove 0.6ha in middle ranking 19 subs (28.5ha in total)
    midImpt_ImpervArea =[]
    subcopy["NewPerc%"] = subcopy["PercImperv"]  ## copy all original values of imperv % to new colume - so that the following loop only replace those in the mostImport list.

    for m in midlst:
        # print("original subcatchment area for sub", m, "is", subcopy.loc[m, "Area"])
        # print("original imperv % for sub", m, "is", subcopy.loc[m, "PercImperv"], "%")
        subcopy.loc[m, "originalImpervArea"] = subcopy.loc[m, "Area"]*subcopy.loc[m, "PercImperv"] * 0.01
        # print("original imperv area for sub", m, "is", subcopy.loc[m,"originalImpervArea"])
        midImpt_ImpervArea.append(subcopy.loc[m,"originalImpervArea"])

        subcopy.loc[m, "NewImpervArea"] = subcopy.loc[m, "originalImpervArea"] - 0.6  ## remove 0.6 ha of impervious area in each subcatchment
        subcopy.loc[m, "NewPerc%"] = ((subcopy.loc[m, "originalImpervArea"] - 0.6)/subcopy.loc[m, "Area"])*100  ## recalculate the new impervious area percentage in each subcatchment
        # print("new imperv area for sub", m, "is", subcopy.loc[m, "NewPerc%"], "%")

    # print(min(midImpt_ImpervArea))  ## smallest impervious area in middle ranking 19 subcatchment 1.77862896746

    # print(subcopy["PercImperv"])
    # print(subcopy["NewPerc%"])

    diff = subcopy["PercImperv"] - subcopy["NewPerc%"]
    print("number of updated subcatchments with new impervious area %", diff.astype(bool).sum(axis=0))

    sub["PercImperv"] = subcopy["NewPerc%"]
    ub.inp.save("{0}\_{1}_d_mid19_subs_06haremoved.inp".format(saveFolder,newfile))

    ########### 4 D remove 0.6ha in bottom ranking 19 subs (11.4ha in total)
    leastImpt_ImpervArea =[]
    subcopy["NewPerc%"] = subcopy["PercImperv"]  ## copy all original values of imperv % to new colume - so that the following loop only replace those in the mostImport list.

    for m in lastlst:
        # print("original subcatchment area for sub", m, "is", subcopy.loc[m, "Area"])
        # print("original imperv % for sub", m, "is", subcopy.loc[m, "PercImperv"], "%")
        subcopy.loc[m, "originalImpervArea"] = subcopy.loc[m, "Area"]*subcopy.loc[m, "PercImperv"] * 0.01
        # print("original imperv area for sub", m, "is", subcopy.loc[m,"originalImpervArea"])
        leastImpt_ImpervArea.append(subcopy.loc[m,"originalImpervArea"])

        subcopy.loc[m, "NewImpervArea"] = subcopy.loc[m, "originalImpervArea"] - 0.6  ## remove 0.6 ha of impervious area in each subcatchment
        subcopy.loc[m, "NewPerc%"] = ((subcopy.loc[m, "originalImpervArea"] - 0.6)/subcopy.loc[m, "Area"])*100  ## recalculate the new impervious area percentage in each subcatchment
        # print("new imperv area for sub", m, "is", subcopy.loc[m, "NewPerc%"], "%")

    # print("smallest imperv area in last 19 sub",min(leastImpt_ImpervArea))  ## smallest impervious area in top 19 subcatchment is 0.609ha

    # print(subcopy["PercImperv"])
    # print(subcopy["NewPerc%"])

    diff = subcopy["PercImperv"] - subcopy["NewPerc%"]
    print("number of updated subcatchments with new impervious area %", diff.astype(bool).sum(axis=0))

    sub["PercImperv"] = subcopy["NewPerc%"]
    ub.inp.save("{0}\_{1}_e_last19_subs_06haremoved.inp".format(saveFolder,newfile))

