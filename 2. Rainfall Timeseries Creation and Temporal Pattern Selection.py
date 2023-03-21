import pandas as pd
import os
from swmm_api import read_rpt_file, read_inp_file, read_out_file
from swmm_api import swmm5_run

########################### generate rainfall depth at each time step for different temporal patterns #################################
### data on rainfall distribution for an ensemble of 10 temporal patterns for each rainfall duration and frequency is available from Australia Rainfall and Runoff data hub
### The rainfall distribution data is in the form of % of rainfall fallen at each time step (increment)

ts = pd.read_excel("\_1_coogee_rainfallTimeSeries_incrementPercentage.xlsx")
# # print(ts.columns)  # Index([' Duration', ' TimeStep', ' AEP bin', 'AEP in %', 'Ttl rainfall depth(mm)',' Increments_Perc_at_1st_Time_step', 'Increments_Perc_at_2nd_Time_step'....]

## process all the timestep columns (starting from the 6th column, read the rainfall distribution in percentage at that time step and multiply it with total rainfall depth
for column in ts.columns[5:]:
       ts[column] = ts[column]* 0.01 * ts['Ttl rainfall depth(mm)']

ts.to_csv("\_2_coogee_rts_incrementDepth.csv")  ### checked in the excel file that the sum of all increment rainfall depth is equal to total rainfall depth

################################## Create new time series names for different rainfal temporal patterns  #################################
rtscsv = pd.read_csv("\_2_coogee_rts_incrementDepth.csv")

aeplst = rtscsv['AEP%'].tolist()
# print(len(aeplst))  #280 rainfall time series to process

## create rainfall time series names
aep = ["AEP_"]*280
alst1 = [str(i) + str(j) for i, j in zip(aeplst, aep)]
# print(alst1)

d = ["D"]*280
alst2 = [str(i) + str(j) for i, j in zip(alst1, d)]

duration = rtscsv['Duration'].tolist()
alst3 = [str(i) + str(j) for i, j in zip(alst2, duration)]

space = ["_"]*280
alst4 = [str(i) + str(j) for i, j in zip(alst3, space)]

tplist = rtscsv['TPNumber'].tolist()
# print(tplist)

res = [str(i) + str(j) for i, j in zip(alst4, tplist)]
print(str(res))

namelst = res
# print(type(namelst)) ## list
# ilst = rtscsv.index.tolist()
# for i in ilst:
#     rtscsv.loc[i,"TSName"] = namelst
rtscsv.loc[:,"TSName"] = namelst
# print(rtscsv["TSName"])


## set rainfall time series name as index column
rtscsv = rtscsv.set_index('TSName')
# print(rtscsv.index)

## counts the number of time steps needed for SWMM rainfall time series rows, store in column "timerow"
rtscsv["timerow"] =rtscsv['Duration']//rtscsv['TimeStep']  ## floor devision - generates integers
# print(rtscsv["timerow"])

## generate time steps in date/time formate for each rainfall timestep in the time series
time5 = pd.date_range('2017-01-01 00:05:00', '2017-01-01 01:35:00', freq= '5min')  ### for 15-90min duration, 5min interval
# print(type(time5)) #<class 'pandas.core.indexes.datetimes.DatetimeIndex'>
timelst5 =[]
for t in time5:
    # print(type(t))
    s = str(t)
    news = s.replace("2017-01-01 ",'')
    timelst5.append(news)
# print("timelist for 5min interval", timelst5)


time15 = pd.date_range('2017-01-01 00:15:00', '2017-01-01 07:00:00', freq= '15min')  ### for 180min-360 duration, 15min interval
# print(type(time15)) #<class 'pandas.core.indexes.datetimes.DatetimeIndex'>
timelst15 =[]
for t in time15:
    # print(type(t))
    s = str(t)
    news = s.replace("2017-01-01 ",'')
    timelst15.append(news)
# print("timelist for 15min interval",timelst15)

time30 = pd.date_range('2017-01-01 00:30:00', '2017-01-01 13:00:00', freq= '30min')  ### for 540-720min duration, 30min interval
# print(type(time30)) #<class 'pandas.core.indexes.datetimes.DatetimeIndex'>
timelst30 =[]
for t in time30:
    # print(type(t))
    s = str(t)
    news = s.replace("2017-01-01 ",'')
    timelst30.append(news)
# print("timelist for 30min interval", timelst30)


## create new dataframe to store time series results
header = ["name","date","time","value"]
newdf = pd.DataFrame(columns=header)
# print(newdf)

## generate time series name for each time step in a rainfall series (for SWMM Timeseries section)
namelst =[]
for i in rtscsv.index:
    # print("time series name", i)
    # print("number of rows needed for this time series", rtscsv.loc[i,"timerow"])
    repeatname = [i]*int(rtscsv.loc[i,"timerow"])
    # print(int(rtscsv.loc[i,"timerow"]) - len(repeatname))  ## repeatname datatype = list, checked the number of repeated names is correct
    namelst.extend(repeatname)
#
# print(len(namelst))  # contains 4200 entries
newdf["name"] = namelst


## generate time series in date/time in the form of SWMM Timeseries section
only5mindf = rtscsv[:120]   ## only processes time series with a time step of 5min
# print(only5mindf)

only15mindf =rtscsv[120:200] ## only processes time series with a time step of 15min
# print(only15mindf)

only30mindf= rtscsv[200:] ### only processes time series with a time step of 30min
# print(only30mindf)

timestep = []
for i in only5mindf.index:
    numofTimestep = int(rtscsv.loc[i, "timerow"])
    # print("timesteps required for time series",i,":",numofTimestep)
    timesteplst = timelst5[0:numofTimestep]
    timestep.extend(timesteplst)
    print("this is the timesteps required for time series",i,":",timelst5[0:numofTimestep])
    print("generated timesteps",len(timesteplst))
    print(len(timesteplst) - numofTimestep)  ## all results in 0, so no difference between the number of time steps required and the sliced timesteps.

for i in only15mindf.index:
    numofTimestep = int(rtscsv.loc[i, "timerow"])
    # print("timesteps required for time series",i,":",numofTimestep)
    timesteplst = timelst15[0:numofTimestep]
    timestep.extend(timesteplst)
    # print("this is the timesteps required for time series",i,":",timelst5[0:numofTimestep])
    # print("generated timesteps",len(timesteplst))
    # print(len(timesteplst) - numofTimestep)

for i in only30mindf.index:
    numofTimestep = int(rtscsv.loc[i, "timerow"])
    # print("timesteps required for time series",i,":",numofTimestep)
    timesteplst = timelst30[0:numofTimestep]
    timestep.extend(timesteplst)
    # print("this is the timesteps required for time series",i,":",timelst5[0:numofTimestep])
    # print("generated timesteps",len(timesteplst))
    # print(len(timesteplst) - numofTimestep)

# # # print(len(timestep))
# #
newdf["time"] = timestep

## enter actual rainfall depth for each time step ##

# print(rtscsv.columns)  ### output: Index(['Unnamed: 0', 'number', 'Duration', 'TimeStep', 'AEP', 'AEP%', 'TPNumber', 'Ttl rainfall depth(mm)', ' Increments_Perc_at_1st_Time_step', 'Increments_Perc_at_2nd_Time_step'....
# print(rtscsv.iloc[:,8])  ## slice all the row's for its rainfall depths data

for i in rtscsv.index:
    numofTimestep = int(rtscsv.loc[i, "timerow"])
    rainfall = []
    timesteprange = 8+numofTimestep
    # print(timesteprange)
    rain= rtscsv.iloc[:,8:timesteprange]

# print(rain)

rainfalldepth = []
for i in rain.index:
    eachrow = rain.loc[i]
    eachrow = eachrow.tolist()
    # print(eachrow)  #### contains nan values
    cleanedList = [x for x in eachrow if str(x) != 'nan'] ## removes all the nan values
    # print("cleanedlist\n", cleanedList)
    rainfalldepth.extend(cleanedList)

newdf["value"] = rainfalldepth

newdf.to_csv("\_3_coogee_rainfallTimeSeries.csv")
rtscsv.to_csv("\_2_coogee_rts_incrementDepth_updated.csv")

## writing rainfall time series to SWMM inp file####################################
timeseries = pd.read_csv("\_3_coogee_rainfallTimeSeries.csv")
print(timeseries.columns) #['Unnamed: 0', 'name', 'date', 'time', 'value']
# timeseries = timeseries.set_index('name ')
tsindex = timeseries.index.tolist()
# print(tsindex)

inpFile = open("\Example SWMM Inpute File_250sizeblk_1AEP_D90_8_20220124_Timeseries_Section.txt",'w')

inpFile.write('\n[TIMESERIES]\n'
              ';;Name           Date       Time       Value\n'
              ';;-------------- ---------- ---------- ----------\n')

for n in tsindex:
        inpFile.write('' + str(timeseries.loc[n,'name']) +  '                  ' +str(timeseries.loc[n,"time"]) + '  ' + str(timeseries.loc[n,"value"]) + '\n')

inpFile.close()

## create different SWMM inp files with different rainfall time series as [RAINGAGE] - source

###### divide rainfall time series into three groups based in time interval
rtscsv = pd.read_csv("\_2_coogee_rts_incrementDepth_updated.csv")
# print(rtscsv.columns)
rtscsv= rtscsv.set_index('TSName')
rtsindex = rtscsv.index.tolist()

only5minlst = rtsindex[:120]
# print(only5minlst)

only15minlst =rtsindex[120:200]
# print(only15minlst[0])

only30minlst= rtsindex[200:]
# print(only30minlst[0])

# generate inp files for 5min, 15min and 30min interval [RAINGAGE] section #######

# example: for rainfall time series with 5min intervals
for i in only5minlst:
  basefile = open('Example SWMM Inpute File_250sizeblk_1AEP_D90_8_20220124_for5minInterval.inp', "r")
  originalline = "rain_1           VOLUME    00:05    1.0      TIMESERIES 50AEP_D15_1  "  ## changed interval and first time series name in the list
  # print("original rainfall source", originalline)
  updatedline = "rain_1           VOLUME    00:05    1.0      TIMESERIES " + str(i)        ## changed interval
  print("updated rainfall source",updatedline)
  newfile = open(f"Example SWMM Inpute File_250sizeblk_1AEP_D90_8_20220124_for5minInterval_new_{i}.inp", "w")
  for line in basefile:
      newfile.write(line)
  newfile.close()
  basefile.close()

  new = open(f"Example SWMM Inpute File_250sizeblk_1AEP_D90_8_20220124_for5minInterval_new_{i}.inp", "rt")
  newfilelines = new.read()
  # print("original rainfall source", originalline)
  # print("updated rainfall source", updatedline)
  newfilelines = newfilelines.replace(originalline, updatedline)
  new.close()
  new= open(f"Example SWMM Inpute File_250sizeblk_1AEP_D90_8_20220124_for5minInterval_new_{i}.inp", "wt")
  new.write(newfilelines)
  newfile.close()

####### Temporal Pattern Selection #############
## run all SWMM files with different temporal patterns and save catchment peak flow data
rts_timeseries= pd.read_csv("\_2_coogee_rts_incrementDepth_updated.csv")
TSNamelst = rts_timeseries["TSName"].tolist()

## create result dataframe:
resultDataframe = pd.DataFrame(index=TSNamelst)

inpFileFolder ="\SWMMfiles_with_diff_rainfall_time_series"
for ind,filename in enumerate(TSNamelst):
    print(ind)
    print(filename)

    inp =f"{inpFileFolder}\_{filename}.inp"
    swmm5_run(inp)
    out = read_out_file(f"{inpFileFolder}\_{filename}.out")
    df_output = out.to_frame()
    # print(df_output)
    # print(df_output.columns.tolist())
    sysrunoffSeries = df_output[('system', '', 'runoff')].tolist()
    peakFlowRate = max(sysrunoffSeries)
    print(peakFlowRate)
    resultDataframe.loc[filename, "system peakflow (LPS)"] = peakFlowRate

    out.close()
    os.remove(f"{inpFileFolder}\_{filename}.out")
    os.remove(f"{inpFileFolder}\_{filename}.rpt")

resultDataframe.to_csv("_CatchmentPeakFlow_under_diff_rainfall.csv")

# ## creates a new dataframe to store results of the final time series and peak runoff volume
columName = ["TS",'AEP','Duration','system peakflow (LPS)']
selectedrts = pd.DataFrame(columns=columName)

#### creates lists to store results of final time series and peak runoff rate
clsTS = []
clsTSPRVlst = []

duration = []
AEP = []

# #### group every 10 rows in the resultDataframe time series name (10 rainfall temporal patterns for each duration and AEP)
for g, v in resultDataframe.groupby(resultDataframe.index//10):   # 50 groups, starting from 0
    print("This is Group Number", g)
    print(v)

    meanPkVolume = v['system peakflow (LPS)'].mean()  # calculate the mean of peak runoff volume in 10 rainfall temporal patterns
    closestMeanTS = abs(v['system peakflow (LPS)'] - meanPkVolume).idxmin()  ## find the time series SWMM file that produces peak runoff rate closest to mean of 10 temporal patterns
    print("Row with TS closest to mean Peak Runoff rate",closestMeanTS)
    # print(type(closestMeanTS))  #'numpy.int64'
    clsTSName = v.loc[closestMeanTS,'TS_name']  # produces the SWMM file name that uses the time series closest to the mean of peak runoff volume
    print("Name of selected TS",clsTSName)  ## format: 20%AEP_90min_8
    # print("in Group",g, ",", clsTSName, "produces the peak runoff volume closest to mean")  ## produces the name of time series  ## format: 5AEP_D720_9
    clsTS.append(clsTSName)  ## stores the name of time series in to clsTS list
    aep = clsTSName[:clsTSName.index("%AEP")]  ## slices the AEP value before the chacracters of AEP and stores it into AEP list  e.g. : extracts 5 from 5AEP_D720_9
    # print("aep of the selected TS",aep)
    AEP.append(aep)
    dur_part1 = clsTSName[clsTSName.index("_"):]  ## slices content after the letter D in 5AEP_D720_9 -> produces  _90min_2
    print(dur_part1)
    dur_part2 = dur_part1[:dur_part1.index("min")]  ## slices content before the character "_" -> produces _90
    print(dur_part2)
    dur_part3 = dur_part2.replace("_",'')   ## removes _ -> produces 90 - duration information
    # print("duration of the selected TS",dur_part3)
    duration.append(dur_part3)     # stores it to duration list
    closestPRV = v.loc[closestMeanTS,'system peakflow (LPS)']  # reads the peak runoff rate generated by the time series closest to mean of peak runoff rate
    # print(closestPRV)
    clsTSPRVlst.append(closestPRV) ## stores the peak runoff volume in to clsTSPRVlst
#
selectedrts["TS"] = clsTS
selectedrts['AEP'] = AEP

selectedrts['Duration'] = duration
selectedrts['Duration']=pd.to_numeric(selectedrts['Duration'], errors='coerce')

selectedrts['system peakflow (LPS)'] =clsTSPRVlst
selectedrts['system peakflow (LPS)'] =pd.to_numeric(selectedrts['system peakflow (LPS)'], errors='coerce')

print(selectedrts)
selectedrts.to_csv("_TemporalPatterns_fullresults.csv")


### generate representative temporal patters for 15min to 9hr duration under each AEP (individual csv result files for each AEP)
for i,v in selectedrts.groupby(["AEP"]):
    # print(i)
    # print(v)
    GroupAEP = int(v["AEP"].unique())
    print(GroupAEP)
    sortedAEP = v.sort_values(by=['Duration'])
    sortedAEP.to_csv(f"_temporalPattern_for_{GroupAEP}AEP.csv")  ## stores rainfall time series producing closest to average peak runoff

# ### Group rainfall time series under each AEP for comparison between different durations
# # selectedrts = selectedrts.groupby(["AEP", "Duration"]).sum()
# # print(selectedrts)   ### note that this does not keep the selected time series names in the dataframe. Only AEP, Duration and SYS_Peak_Rf_Volume and SYS_Ttl_Fld are stored in the df.
selectedrts = selectedrts.groupby(["AEP","Duration","TS"]).sum()
# print(selectedrts)

selectedrts.to_excel("_Results_for_Temporalpatternselection.xlsx")




