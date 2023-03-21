from swmmio import Model, inp, rpt, Nodes
from swmm5.swmm5tools import SWMM5Simulation
import pandas as pd
from swmm_api import read_rpt_file, read_inp_file
import time
import glob
import os


# ##create output dataframe index columns


resultindex = ["inp_file","Ttl_CmtArea(ha)","Ttl_ImpervArea(ha)","SYS_Ttl_Rf(10^6)","SYS_Peak_Rf(LPS)", "SYS_Ttl_Fld(10^6)","SYS_Flded_Nodes_count"]
simulation_reference_df = pd.DataFrame(columns=resultindex)

# inpfilelst = glob.glob('D:\SWMM practice Dec 2020\coogee_swmmfile\_250blk\_SA\_All_SWMM_files\_forvalidation\_allinpFiles\*.inp')

inpfilelst = glob.glob('D:\SWMM practice Dec 2020\coogee_swmmfile\_250blk\_ReRun_SA_2022\_validation\_newInps\*.inp')

print(inpfilelst)

for ind,v in enumerate(inpfilelst):
    print("index",ind)
    print("inp file processed", v)
    filename =v.replace("D:\SWMM practice Dec 2020\coogee_swmmfile\_250blk\_ReRun_SA_2022\_validation\_newInps\_",'')
    filename = filename.replace(".inp",'')
    print(filename)
    simulation_reference_df.loc[ind, "inp_file"] = filename

    ub = Model(v)
    sub250 = ub.inp.subcatchments
    sub250copy = sub250.copy()  ## ['Raingage', 'Outlet', 'Area', 'PercImperv', 'Width', 'PercSlope'
    sub250copy["ImpervArea"] = sub250copy['Area']* (sub250copy['PercImperv']/100)
    sub250copy["ttl_Area"] = sub250copy['Area'].sum()
    sub250copy["ttl_ImpervArea"] = sub250copy["ImpervArea"].sum()

    print("Total catchment area", sub250copy["ttl_Area"].unique())  #[288.4836]
    simulation_reference_df.loc[ind, "Ttl_CmtArea(ha)"] = sub250copy["ttl_Area"].unique()

    print("Total Imperv area",sub250copy["ttl_ImpervArea"].unique())  #[189.34759642]
    simulation_reference_df.loc[ind, "Ttl_ImpervArea(ha)"] = sub250copy["ttl_ImpervArea"].unique()

    st = SWMM5Simulation(v)
    sysrunoff = st.Results("SYS", "SYS",4)  # system runoff flow (LPS) by time step
    # sysrfrate = [(r) for r in sysrunoff]
    # for index,value in enumerate(sysrfrate):
    #     print(index,value)
    # print("system runoff rate",sysrfrate)
    sysrttlrf = (sum(sysrunoff) * int(st.SWMM_ReportStep))/1000000
    print("system total runoff", sysrttlrf)
    simulation_reference_df.loc[ind, "SYS_Ttl_Rf(10^6)"] = sysrttlrf

    sysrunoff = st.Results("SYS", "SYS",4)
    sysrfrate = [(r) for r in sysrunoff]
    sysPkrf = max(sysrfrate)
    print("system peak runoff rate", sysPkrf)
    simulation_reference_df.loc[ind,'SYS_Peak_Rf(LPS)']=sysPkrf

    fld = st.Results("SYS", "SYS",10)  # system flow lost to flooding (LPS) by time step # sysfld = ["%5.2f"% (i) for i in fld]  #取小数点后两位 数值
    sysfld = [(i) for i in fld]
    systtlfld = (sum(sysfld) * int(st.SWMM_ReportStep))/1000000
    # print("system total flood volume=", systtlfld)
    print("system total flood volume",systtlfld)
    simulation_reference_df.loc[ind, "SYS_Ttl_Fld(10^6)"] = systtlfld

    f=st.getFiles()
    # print(f)
    r = read_rpt_file(f[1])  # takes out rpt temp file (which is the second elemet in the f list, use swmm api to read rpt file, produce dataframe

    print(r.runoff_quantity_continuity)

    nodefloodsummary = r.node_flooding_summary  # read section onf node_flooding_summary - dtype dataframe
    # print('nodefloodsummary', nodefloodsummary)
    numberoffloodednodes = nodefloodsummary.shape[0]
    print(numberoffloodednodes)
    simulation_reference_df.loc[ind,"SYS_Flded_Nodes_count"]=numberoffloodednodes

    st.clean()  # cleans temp file (both rpt and dat)

simulation_reference_df.to_excel("D:\SWMM practice Dec 2020\coogee_swmmfile\_250blk\_ReRun_SA_2022\_validation\_floodresults_underDiffImpervRemoval_20220309.xlsx")
