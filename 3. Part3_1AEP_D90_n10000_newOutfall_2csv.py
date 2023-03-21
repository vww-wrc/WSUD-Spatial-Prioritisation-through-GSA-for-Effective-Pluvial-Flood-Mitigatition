import pandas as pd
import numpy as np
from swmmio import Model, inp, rpt
from swmm5.swmm5tools import SWMM5Simulation
from SALib.analyze import fast
from SALib.plotting.bar import plot as barplot
import matplotlib.pyplot as plot
import glob
import time
import datetime
import os
import sys

# store starting time
begin = time.time()

###################### Modify this section: new output csv names, output csv sub folder name, and inp file name ##########################
###################### If want to change the model output used in sensitivity analysis, change Y in line 51 #########################
bs = SWMM5Simulation('/srv/scratch/z5327368/z5327368/250blk_1AEP_D90/_250blk_1AEP_D90_8_20220124_copy2.inp')
outputcsv = "20220125_1AEP_D90_8_n10000_newOutfall"  # subfolder name for output csvs, created under /home/z5327368/OutputCSV/, also used for naming final csvs 
csv_list = glob.glob('/srv/scratch/z5327368/z5327368/OutputCSV/20220125_1AEP_D90_8_n10000_newOutfall/*.csv') # remember to have / after folder name

## this version has updated line 87-90 on plotting SA results in bar charts 

###############################################################################################################   
# glob all output csvs (from line 21, csv_list = glob.glob)
print(csv_list)
print("number of csvs",len(csv_list))

# merge csvs and produce final csv, then sort the rows in the final csv - stored as sorted csv
first_file = True
merged_csv_path = '/srv/scratch/z5327368/z5327368/OutputCSV/finalcsv/merged_csv/merged_{0}.csv'.format(outputcsv)
sorted_csv_path = '/srv/scratch/z5327368/z5327368/OutputCSV/finalcsv/sorted_{0}.csv'.format(outputcsv)
stored_csv_path = '/home/z5327368/OutputCSV/finalcsv/sorted_{0}.csv'.format(outputcsv)

for f in csv_list:
    data = pd.read_csv(f)
    if first_file:
        data.to_csv(merged_csv_path, index=False)
        first_file = False
    else:
        data.to_csv(merged_csv_path, index=False, header=False, mode='a')

sortdata =pd.read_csv(merged_csv_path)
print(type(sortdata))
final=sortdata.sort_values(by="Unnamed: 0",axis=0)
final.to_csv(sorted_csv_path,index=False)
final.to_csv(stored_csv_path,index=False) ## stores result final csv to home directory for back up 

########## Read result dataframe for sensitivity analysis
df = pd.read_csv(sorted_csv_path, header=0)
print("shape of sorted csv", df.shape)
print("columns of results csv",df.columns)

Y = df["SYS_PeakVol_Ttl_Fld"]  #choose the model output of interest for Sensitivity analysis
print("shape of Y - SYS_PeakVol_Ttl_Fld", Y.shape)

subcat= bs.Subcatch()
impevoption = [0,100]
boundslist = []
for n in range(len(subcat)):
    boundslist.append(impevoption)    #create list of parameter boundaries for all subcatchments/parameters
# print(boundslist)

# Define the model inputs
problem = {
    'num_vars': len(subcat),
    'names': subcat,
    'bounds': boundslist
}
# print(problem)

### perform analysis
Si = fast.analyze(problem, Y, M=4, print_to_console=False)
print(Si)

Si_df = Si.to_df()  #Convert dict structure into Pandas DataFrame.
barplot(Si_df)  ## plots results in bar chart
plot.title(outputcsv)
plot.savefig("/srv/scratch/z5327368/z5327368/SAresults/{0}_SA_result.png".format(outputcsv))
Si_df.to_csv("/srv/scratch/z5327368/z5327368/SAresults/{0}_SA_result.csv".format(outputcsv))
Si_df.to_csv("/home/z5327368/SAresults/{0}_SA_result.csv".format(outputcsv))  ## stores SA result to home directory for backup

####### second sensitivity analysis based on flood volumen alone 
# Y2 = df["SYS_Ttl_Fld"]  #choose the model output of interest for Sensitivity analysis
# print("shape of Y2 SYS_Ttl_Fld", Y2.shape)

# subcat= bs.Subcatch()
# impevoption = [0,100]
# boundslist = []
# for n in range(len(subcat)):
#     boundslist.append(impevoption)    #create list of parameter boundaries for all subcatchments/parameters
# # print(boundslist)

# # Define the model inputs
# problem = {
#     'num_vars': len(subcat),
#     'names': subcat,
#     'bounds': boundslist
# }
# # print(problem)

# ### perform analysis
# Si2 = fast.analyze(problem, Y2, M=4, print_to_console=False)
# print(Si2)

# Si2_df = Si2.to_df()  #Convert dict structure into Pandas DataFrame.
# barplot(Si2_df)  ## plots results in bar chart
# plot.title(outputcsv)
# plot.savefig("/srv/scratch/z5327368/z5327368/SAresults/{0}_SA_result_fld_only.png".format(outputcsv))
# Si2_df.to_csv("/srv/scratch/z5327368/z5327368/SAresults/{0}_SA_result_fld_only.csv".format(outputcsv))
# Si2_df.to_csv("/home/z5327368/SAresults/{0}_SA_result_fld_only.csv".format(outputcsv))  ## stores SA result to home directory for backup


time.sleep(1)   # store end time
end = time.time()

# total time taken
print(f"Total runtime of the program is {(end - begin)/60}min")
 

