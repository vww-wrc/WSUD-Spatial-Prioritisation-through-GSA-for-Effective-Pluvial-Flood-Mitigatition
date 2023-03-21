import sys
import os
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn' on "A value is trying to be set on a copy of a slice from a DataFrame" when writing to reference dataframe
from swmmio import Model, inp, rpt
from swmm5.swmm5tools import SWMM5Simulation
from swmm_api import read_rpt_file
import numpy as np
from SALib.sample import fast_sampler
from SALib.analyze import fast
from SALib.plotting.bar import plot as barplot
from os.path import isfile
import time
import datetime
import matplotlib.pyplot as plt

# store starting time
begin = time.time()
print("begin time",datetime.datetime.now())

############################# Update this section ##################################################################
############################# Update line 45 for the number of samples per subjob ##################################
############################# If want to create more columns in output dataframe - update line 56 #################

inpfile = '/srv/scratch/z5327368/z5327368/250blk_1AEP_D90/_250blk_1AEP_D90_8_20220124_copy2.inp'
parametercsv="/srv/scratch/z5327368/z5327368/250blk_1AEP_D90/1AEP_D90_setN10000.csv"
reference_id="20220125_1AEP_D90_8_n10000_newOutfall"
outputcsv_folder= "20220125_1AEP_D90_8_n10000_newOutfall" 

####################################################################################################################
indexkey = "PBS_ARRAY_INDEX"
arrayjobindex=os.getenv(indexkey)
ajindex = int(arrayjobindex)

tmpdir = os.environ["TMPDIR"]

print("This simulation is from", sys.argv[0])  ## this prints the py file name - sys.argv[0] produces the environmental variable for file name 
print("Reference ID", reference_id)
print("inpfile used:",inpfile)
print("parametercsv used", parametercsv)
print("output csv stored in /srv/scratch/z5327368/z5327368/OutputCSV/",outputcsv_folder)
print("this is array job No.", arrayjobindex) 

## read parameter csv file and select the rows for this subjob 
df = pd.read_csv(parametercsv, header=0)
print("shape of parameter csv", df.shape)
dfindex= list(df.index.values)  #convert the index of dataframe into a list 
 
########################### UPDATE the numbers multiplied by arrayjob index ########################################## 
ilst = dfindex[(ajindex-1)*190:ajindex*190]  # select the range of rows for this run - in this case, 190 sets for 1 loop with 3000 subjobs in total - chained by 6 batches, each batch has 500 subjobs
print("number of rows assessed", len(ilst))
# print("rows assessed", ilst)

############################################ 
##create output dataframe index columns 
subcat = df.columns[1:].tolist()  #create a list format of subcat indices (S1, S2, S3 etc)
indexlist = ["set_name"]
for sub in subcat:
    indexlist.append(sub)

resultindex = ["SYS_Ttl_Rf","SYS_Peak_Rf", "SYS_Ttl_Fld","SYS_PeakVol_Ttl_Fld","SUB_Max_Peak_Rf", "SYS_Flded_Nodes_count", "Nodes_Ttl_Fld_Volume", "Nodes_Max_Hrs_Flded", "Nodes_MaxFldRate", "Nodes_Ave_MaxFldRate", "Time_of_Max_Occurence"]
indexlist.extend(resultindex)
# print(indexlist)  # this is the full column list for the output dataframe 

simulation_reference_df = pd.DataFrame(columns=indexlist)

##loop through selected rows 
for i in ilst:
    print(i)
    row = df.iloc[i,1:]  # parameter input dataframe has first column as index, so need to start reading from the second column 
    paralst=row.values.tolist()  #read parameter inputs and convert it to a list to be put into subcatchment dataframe 
    # print("this is paralst", paralst)
    mymodel = Model(inpfile)
    nodes = mymodel.nodes.dataframe
    links = mymodel.links.dataframe
    subs = mymodel.subcatchments.dataframe
    Subcatchments = mymodel.inp.subcatchments
    subscopy = mymodel.inp.subcatchments.copy()
    # print("original ['PercImperv']=",subscopy['PercImperv'])
    # print("new parameter:", paralst)
    subscopy['PercImperv'] = paralst  
    # print("modified PercImpv:", subscopy['PercImperv'])
    Subcatchments.PercImperv = subscopy['PercImperv']
    new_inp_file = "{0}/set_{1}_{2}.inp".format(tmpdir, arrayjobindex, i)
    mymodel.inp.save(new_inp_file)
    
    setname = "set_{0}_{1}.inp".format(arrayjobindex,i) 
    simulation_reference_df.loc[i,"set_name"] = setname
    simulation_reference_df.loc[i, subcat] = paralst
    
    st = SWMM5Simulation(new_inp_file)
    sysrunoff = st.Results("SYS", "SYS",4)  # system runoff flow (CFS) by time step
    systtlrf = sum(sysrunoff) * int(st.SWMM_ReportStep)
    # print("system total runoff volume=", systtlrf)
    simulation_reference_df.loc[i,"SYS_Ttl_Rf"] = systtlrf
    
    sysrunoff = st.Results("SYS", "SYS", 4)  # system runoff flow (CFS) by time step
    pkflowrate = max(sysrunoff)  ## peak flow rate
    peakflow = pkflowrate * int(st.SWMM_ReportStep)
    # print("system peak runoff volume=", peakflow)
    simulation_reference_df.loc[i,"SYS_Peak_Rf"] = peakflow
    
    fld = st.Results("SYS", "SYS",10)  # system flow lost to flooding (CFS) by time step # sysfld = ["%5.2f"% (i) for i in fld]  #取小数点后两位 数值
    sysfld = [(i) for i in fld]
    systtlfld = sum(sysfld) * int(st.SWMM_ReportStep)
    print("system total flood volume=", systtlfld)
    simulation_reference_df.loc[i, "SYS_Ttl_Fld"] = systtlfld
    
    combinedflw = peakflow + systtlfld
    # print("SYS_PeakVol_Ttl_Fld_combined = ",combinedflw)
    simulation_reference_df.loc[i,"SYS_PeakVol_Ttl_Fld"] =  combinedflw
    
    f = st.getFiles()  # list of files related to this run and their locations in the computer - inp, rpt, dat. Stored in f (dtype:list)
                       #print([isfile(outputfiles) for outputfiles in f])  # check if the files exist in the operating system. return: True/False
    r = read_rpt_file(f[1])  # takes out rpt temp file (which is the second elemet in the f list, use swmm api to read rpt file, produce dataframe
    ######### reads subcatchment runoff summary
    rptsubrfsummary = r.subcatchment_runoff_summary
                       # print("rpt subcatchment runoff summary",rptsubrfsummary)

    peakrf = rptsubrfsummary["Peak_Runoff_LPS"]
    maxpeakrf = max(peakrf)
    # print("largest peak runoff rate=", max(peakrf))  # largest value of peak runoff rates in subcatchments
    simulation_reference_df.loc[i, "SUB_Max_Peak_Rf"] = max(peakrf)

    ########## reads node flooding summary
    nodefloodsummary = r.node_flooding_summary  # read section onf node_flooding_summary - dtype dataframe
                       # print('nodefloodsummary', nodefloodsummary)
    if not nodefloodsummary.empty:
        flooded_nodes_count = len(nodefloodsummary.index)  # count number of rows/ nodes listed in the flood summary
        # print('number of flooded nodes', flooded_nodes_count)
        simulation_reference_df.loc[i,"SYS_Flded_Nodes_count"] = flooded_nodes_count

        ndtllfldvolume = sum(nodefloodsummary["Total_Flood_Volume_10^6 ltr"])
        # print("node total flood volume(10^6 gal)=", ndtllfldvolume)
        simulation_reference_df.loc[i, "Nodes_Ttl_Fld_Volume"] = ndtllfldvolume

        maxhrfld = max(nodefloodsummary["Hours_Flooded"])
        # print("longest hrs flooded", maxhrfld)
        simulation_reference_df.loc[i, "Nodes_Max_Hrs_Flded"] = maxhrfld

        ndmaxfldrate = max(nodefloodsummary["Maximum_Rate_LPS"])
        # print("largest max flood rate at nodes",ndmaxfldrate)
        simulation_reference_df.loc[i, "Nodes_MaxFldRate"] = ndmaxfldrate

        ndmeanfldrate = sum(nodefloodsummary["Maximum_Rate_LPS"]) / len(nodefloodsummary["Maximum_Rate_LPS"])
        # print("average max flood rate at nodes", ndmeanfldrate)
        simulation_reference_df.loc[i, "Nodes_Ave_MaxFldRate"] = ndmeanfldrate

        maxfldtime = min(nodefloodsummary['Time of Max_Occurrence_days hr:min'])
        # print("earliest occurance of max rate", maxfldtime)
        simulation_reference_df.loc[i, "Time_of_Max_Occurence"] = maxfldtime
        
        simulation_reference_df.to_csv("/srv/scratch/z5327368/z5327368/OutputCSV/{0}/{1}_output.csv".format(outputcsv_folder, arrayjobindex)) #saves referencedf into csv
        st.clean()  # cleans temp file (both rpt and dat)
                # print([isfile(x) for x in f]) # do they exist in the operating system.

    else:
        print("No node flooding")
        simulation_reference_df.loc[i, "SYS_Flded_Nodes_count"] = 0
        simulation_reference_df.loc[i, "Nodes_Ttl_Fld_Volume"] = 0
        simulation_reference_df.loc[i, "Nodes_Max_Hrs_Flded"] =0
        simulation_reference_df.loc[i, "Nodes_MaxFldRate"]=0
        simulation_reference_df.loc[i, "Nodes_Ave_MaxFldRate"] =0
        simulation_reference_df.loc[i, "Time_of_Max_Occurence"] = 0
        
        simulation_reference_df.to_csv("/srv/scratch/z5327368/z5327368/OutputCSV/{0}/{1}_output.csv".format(outputcsv_folder, arrayjobindex)) #saves referencedf into csv
        st.clean()  # cleans temp file (both rpt and dat)
                # print([isfile(x) for x in f]) # do they exist in the operating system.
    
time.sleep(1)
# store end time
end = time.time()
print("end time", datetime.datetime.now())

# total time taken
print(f"Total runtime of the program is {(end - begin)/60/60}hr")

