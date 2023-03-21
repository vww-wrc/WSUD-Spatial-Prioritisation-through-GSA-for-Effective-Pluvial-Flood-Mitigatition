from os.path import basename, dirname
from os import close, remove
from tempfile import mkstemp
import geopandas as gpd
import pandas as pd
import csv
import numpy as np
import datetime


# swmm_file_name = 'Example SWMM Inpute File_250sizeblk_1AEP_D90_8_20220124.inp'

def read_data(ub_shp_name):
    # Read relevant data from UB shp results and convert into a dictionary (key: Block_ID) for easy iteration.
    # TODO - change to gather UB block data in dictionary "data_dict" containing...
    #  {'BlockID', 'Slope_PCT', 'downID', 'Blk_EIF', 'geometry', 'area', 'width'}
    data = gpd.read_file(ub_shp_name)

    lu_res_com_list = ['pLU_RES', 'pLU_COM', 'pLU_ORC', 'pLU_CIV', 'pLU_RD', 'pLU_TR']
    lu_industry_list = ['pLU_LI', 'pLU_HI', 'pLU_NA']
    lu_green_list = ['pLU_PG', 'pLU_REF', 'pLU_UND', 'pLU_WAT', 'pLU_FOR', 'pLU_SVU']
    block_area = data['geometry'].area.values[0]  # m2
    data['area'] = block_area / 10000.  # m2 to ha

    data['LU_RES_COM'] = data[lu_res_com_list].sum(axis=1) * block_area
    data['LU_INDUSTRY'] = data[lu_industry_list].sum(axis=1) * block_area
    data['LU_GREEN'] = data[lu_green_list].sum(axis=1) * block_area
    data['new_geo'] = [list(data.geometry.exterior[row_id].coords) for row_id in range(data.shape[0])]
    data['width'] = data['geometry'].length / 4.  # .length calculates circumference
    data_dict = data.set_index('BlockID').to_dict('index')

    df = pd.DataFrame.from_dict(data_dict, orient="index")
    # print(df.index)  ## block IDs
    # print(df.columns)  ## 'BasinID', 'CentreX', 'CentreY', 'Neighbours', 'Active',...'Blk_EIF', 'Blk_TIF', 'Blk_RoofsA', 'geometry', 'area', 'new_geo', 'width'
    # print(df['new_geo']) # contains lists of coordinates
    sub_df = df[['area','Active','Blk_EIF','width','Slope_PCT','new_geo']]
    sub_dfcopy = sub_df.copy()
    # print(sub_df.columns)  #['area', 'Active', 'Blk_EIF', 'width', 'Slope_PCT']
    print("Original # of blocks",sub_df.shape)  ## 101 subcatchments

    areadeleted = []
    subdeleted = []
    sub_dfcopy_indexLst = sub_dfcopy.index.tolist()

    ### remove subcatchment and round up area based on % of blk area within Coogee Boundary #########
    # for i in sub_dfcopy_indexLst:
    #     active = sub_dfcopy.loc[i,"Active"]
    #     if active < 0.1:
    #         print("Sub",i,"has less than 20% area in coogee boundary")
    #         areadeleted.append(active)
    #         subdeleted.append(i)
    # ttlAreaRemoved = sum(areadeleted)   #TODO: update the size of block area for different block files
    # print("Total Area (ha) removed ", ttlAreaRemoved )   ## 0.2678 * 6.25ha
    # print("blocks removed:", subdeleted) ## [4, 6, 26, 29, 44, 54, 63, 70, 82, 92]
    #
    # sub_dfcopy.drop(sub_dfcopy[sub_dfcopy["Active"] < 0.1].index, inplace= True) ### TODO: update rule based on line 52
    #
    # # print(sub_dfcopy)
    # print("# of blocks after sieving", sub_dfcopy.shape)  ## 58 blks, but need to manually removed blk 43
    sub_updated_indexlst= sub_dfcopy.index.tolist()

    return data_dict, data, sub_dfcopy, sub_updated_indexlst


def write_raingages(inpFile, raingageInterval,timeseries_name):
    """
    :param
        rain_format:
            'VOLUME' - time series values are (mm), which are converted into (mm/hour) by SWMM using provided Interval
            'INTENSITY' - time series values are (mm/hour)
            'CUMULATIVE' - not sure

        raingageInterval:
            time series step - TODO: read from time series
    """
    raingage_name = "rain_1"
    rain_format = 'VOLUME'

    inpFile.write('\n[RAINGAGES]\n'
                  ';;Name           Format    Interval SCF      Source\n'
                  ';;-------------- --------- ------ ------ ----------\n'
                  '' + str(raingage_name) + '           ' + str(rain_format) + '    ' + str(raingageInterval) +
                  '   1.0 TIMESERIES ' + str(timeseries_name) + '\n')

def write_subcatchments(inpFile, raingage_name,sub_dfcopy, sub_updated_indexlst):
    """
    Takes all parameters from UB output shp file and uses fixed rain gage.
    """

    sum = 0
    # write header
    inpFile.write('\n[SUBCATCHMENTS]\n'
                  ';;Name           Rain Gage        Outlet           Area     %Imperv   Width    %Slope   CurbLen  SnowPack\n'
                  ';;-------------- ---------------- ---------------- -------- -------- -------- -------- -------- ----------------\n')

    for i in sub_updated_indexlst:
        # print("S", i, "has block area of", sub_dfcopy.loc[i,'area'], "with",sub_dfcopy.loc[i,'Active']," portion in Coogee" )
        inpFile.write(
            '' + "S" + str(i) + '               ' + str(raingage_name) + '           ' + str("downID") + '            '   ## no entries in downID
            + str(round(sub_dfcopy.loc[i,'area'] * sub_dfcopy.loc[i,'Active'],4)) + '    '
            + str(round(sub_dfcopy.loc[i,'Blk_EIF'] * 100, 6)) + '     ' + str(sub_dfcopy.loc[i,'width']) + '    '
            + str(sub_dfcopy.loc[i,'Slope_PCT']) + '      0   \n')

        subArea = sub_dfcopy.loc[i,'area'] * sub_dfcopy.loc[i,'Active']
        sum =sum + subArea
    # print(sum)



def write_subareas(inpFile, n_imp, n_perv, s_imp, s_perv, pct_zero, sub_updated_indexlst):
    """
    This section will be used to calibrate simulation to the catchment. It has Manning's coef (n) and available poding
    storage (s) for impervious and pervious surfaces.

    pct_zero - percentage of impervious surfaces that have zero storage. Physically these surfaces are roads and ground
    level paved surfaces, which have nearly immediate routing. The rest are surfaces like roofs, which physically don't
    have surface storage, but use storage as a way to attenuate (delay) flow. We can calibrate or estimate this parameter.
    """

    inpFile.write('\n[SUBAREAS]\n'
                  ';;Subcatchment   N-Imperv   N-Perv     S-Imperv   S-Perv     PctZero    RouteTo    PctRouted\n'
                  ';;-------------- ---------- ---------- ---------- ---------- ---------- ---------- ----------\n')
    for s in sub_updated_indexlst:
        inpFile.write(
            '' + "S" + str(s) + '   ' + str(n_imp) + '    ' + str(n_perv) + '     ' + str(s_imp) + '   ' + str(
            s_perv) + '    ' + str(pct_zero) + '   OUTLET   \n')


def write_infiltration(inpFile,  infiltration_min_rate, infiltration_max_rate,sub_updated_indexlst):
    """
    Factors for Infiltration calculation. Currently set-up for Horton and Modified-Horton infiltration calculation,
    but we can expend it to Green-Ampt if needed. All factors depend on soil characteristics.

    :param
        max_rate - maximum infiltration rate for the soil type - 25-350mm/hr - CALIBRATION ???
        min_rate - Equal to soil's saturated hydraulic cond. Probably needs to be CALIBRATION PARAMETER!
        decay - Typical values range 2-7 (1/hour)
        dry_time - Time needed for soil to dry completely - typically 2-14 days
        max_infil - Maximum infiltration volume possible (mm, 0 if not applicable). It can be estimated as the
        difference between a soil's porosity and its wilting point times the depth of the infiltration zone.
    """
    max_rate = infiltration_max_rate
    decay = 2
    dry_time = 7
    max_infil = 0
    inpFile.write('\n[INFILTRATION]\n'
                  ';;Subcatchment   MaxRate    MinRate    Decay      DryTime    MaxInfil\n'
                  ';;-------------- ---------- ---------- ---------- ---------- ----------\n')
    for s in sub_updated_indexlst:
        inpFile.write('' + "S"+ str(s) + '        ' + str(max_rate) + '         ' + str(infiltration_min_rate) + '        '
                      + str(decay) + '       ' + str(dry_time) + '        ' + str(max_infil) + '\n')

def coordinates(inpFile,sub_dfcopy, sub_updated_indexlst):
    inpFile.write('\n[Polygons]\n'
                  ';;Subcatchment   X-Coord            Y-Coord\n'
                  ';;-------------- ------------------ ------------------\n')

    for s in sub_updated_indexlst:
        # print(sub_dfcopy.loc[s,'new_geo'])  ## list
        # coordlst = sub_dfcopy.loc[s,'new_geo']
        # # xcoord = [item[0] for item in coordlst]
        # xcoord = coordlst[0][1]
        # print(xcoord)
        for i in range(4):
            inpFile.write('' + "S"+ str(s) + '           ' + str(sub_dfcopy.loc[s,'new_geo'][i][0]) + '             '
                          + str(sub_dfcopy.loc[s,'new_geo'][i][1]) + '\n')

    inpFile.close()

#### input parameters and files
#1. Write to:
inpFile = open('folder\Example SWMM Inpute File_250sizeblk_1AEP_D90_8_20220124.inp',"w")

#2. Read UrbanBEATS generated shapefiles - different block size can be selected

coogee_250 = r"Coogee_MGA_250BY250_Blocks.shp"
coogee_350 = r"\Coogee_MGA_350by350_Blocks.shp"
coogee_500 = r"\Coogee_MGA_500BY500_Blocks.shp"
coogee_200 = r"\Coogee_MGA_200BY200_Blocks.shp"

# 3. raingage name for Subcatchment section
raingage_name = "rain_1"

# 4. parameters for Subarea section
n_imp = 0.024
n_perv= 0.15 # for most subs, but need to modify for some
s_imp = 5.0
s_perv = 45.0
pct_zero = 0  # % of impervious area without depression storage. Althought SWMM application recommands this value to be 25%, it is set to 0 here because we want to take into account initial loss

# 5. parameters for Infiltration section - NOTE: standard parameters are set in the Infiltration section code above
infiltration_max_rate = 5   # for most, remember to reduce the rate for less permeable soil group (Hydrologic Soil Group C in the top corner of the Catchment)
infiltration_min_rate = 5


# TODO: UPDATE shapefile info, data_dic and dat:
## call all the functions

#### for 250 block
#1. read UB shapefile:
coogee_250_df = read_data((coogee_250))
data_dic250 = coogee_250_df[0]
dat250 = coogee_250_df[1]
sub_dfcopy250 = coogee_250_df[2]
sub_updated_indexlst250 = coogee_250_df[3]

#2. raingage section
# raingageInterval = "00:05"
# timeseries_name = " "
# write_raingages(inpFile, raingageInterval,timeseries_name)

#2. subcatchment section
write_subcatchments(inpFile, raingage_name,sub_dfcopy250,sub_updated_indexlst250)

#3. subarea section
write_subareas(inpFile, n_imp, n_perv, s_imp, s_perv, pct_zero,sub_updated_indexlst250)

#4. infiltration section
write_infiltration(inpFile,infiltration_min_rate, infiltration_max_rate,sub_updated_indexlst250)

#5. coordinates section
coordinates(inpFile,sub_dfcopy250,sub_updated_indexlst250)

inpFile.close()


