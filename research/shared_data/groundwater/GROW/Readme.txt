1 
 
GROW 1.0: Dataset Description 
 
 
 
 
 
 
©: Bäthge et al. 2026 / CC BY 4.0 
 
GROW (the global-scale integrated GROundWater package) is a global -scale, analysis-ready, 
quality-controlled dataset that combines groundwater depth or level time series from around 
the world with associated Earth system variables. The dataset contains > 200,000 time series 
from 55 countries, 91% from North America, India, Europe, and Australia,  in a daily, monthly, or 
yearly temporal resolution, accompanied by 36 time series or static attributes of 
meteorological, hydrological, geophysical, vegetation, and anthropogenic variables (e.g., 
precipitation, drainage density, rock type, NDVI, land use). 34 data flags regarding well 
features (e.g., coordinates and country), as well as time series characteristics (e.g., gap fraction 
or autocorrelation), facilitate quick data filtering.  
The dataset is organized in two files:  A table containing time series (grow_timeseries.csv/  
.parquet) and one table with static attributes (grow_attributes.csv/.parquet). The columns of 
the attributes and time series table are described in Table 1 & 2. 
Additionally, the attributes are given as json-file (grow_attributes.json) with well locations as 
geometry. This file can be opened directly in GIS programs. 
Citation 
This dataset is licensed under Creative Commons Attribution Non-Commercial ShareAlike 4.0 
International License (CC-BY-NC-SA 4.0; https://creativecommons.org/licenses/by-nc-
sa/4.0/) 
When using the data and/or the logo, please cite Bäthge et al. “A Global-Scale Time Series 
Dataset for Groundwater Studies within the Earth System” (full citation available on 
Zenodo) 
 
 
 
 

2 
 
Usage Notes 
The groundwater information is either given as water table depth or level dependent on the 
data source. Still, there are three columns in the time series table for every possible reference 
point (‘groundwater_depth_from_well_top_elevation_m’, ‘groundwater_depth_from_well 
_top_elevation_m’, ‘ groundwater_water_level_elevation_m_asl’). Per time series two 
columns will contain NA as the groundwater information is only given for one reference point. 
To derive both, depth from ground elevation and water level elevation , for the same time 
series, the ground elevation from either the provider (‘provider_ground_elevation_m_asl’) or 
the Merit DEM (‘ground_elevation_merit_m_asl’) can be used. To estimate water table depth, 
subtract the water level elevation  (‘groundwater_water_level_elevation_m_asl’) from the 
ground elevation  (‘provider_ground_elevation_m_asl’ or ‘ ground_elevation_merit_m_asl’). 
To estimate water level elevation, subtract the water table depth (‘groundwater_depth_from_ 
ground_elevation_m’) from the ground elevation. However, the ground elevation coming 
from the data provider is only given for 24% of the wells. It should also be noted that the 
MERIT DEM is a global raster product that  contains larger uncertainties compared to local 
information. These will be incorporated into the estimates water tables. The mean absolute 
difference between ground elevation from the provider and the MERIT DEM  is 8 m. The 
maximum difference even goes to 3442 m.   
 
The time series with different temporal resolutions are stored in a single table, all with the 
same unit of quantity (mm/year) for parameters such as precipitation. This enables the 
straightforward derivation of further aggregations across different time s eries resolutions, 
subsets, and statistics, regardless of the temporal resolution. Because 85% of the time series 
have a yearly resolution, quantitative units are provided for an annual period (mm/year). This 
means that monthly and daily time series also h ave units of mm/year. When the user wants 
to use only daily or monthly data, GROW can be easily subset and the unit can be transferred 
to the target resolution. An example of use that demonstrates how the data is subset and 
prepared is given on GitHub ( https://github.com/EarthSystemModelling/GROW/blob/main/ 
usage_example.py) and Zenodo (python_scripts).
3 
 
Table 1: Overview of columns in the attributes table (grow_attributes.csv/.parquet). The data source name is linked to the respective data access 
website. The license is linked to the according license description. 
 
Column name 
 
Unit Description Data source Licensed under 
GROW_ID  A unique identifier that can be used to assign the time 
series to the attributes. 
 
/ / 
original_ID_groundwater  (Adopted from the original datasets) The groundwater 
well identifier that is used in the original groundwater 
datasets. 
 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
name  (Adopted from the original datasets) Name of the well. IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
feature_type  (Adopted from the original datasets) Well type (e.g., 
"Water well"). 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
purpose  (Adopted from the original datasets) Purpose of the well 
(e.g., "Observation / monitoring"). 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
status  (Adopted from the original datasets) Status if well is still 
running ("Active") or not ("Abandoned" or "Collapsed"). 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
description  (Adopted from the original datasets) Further 
information about the well; usually a web link. 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
latitude  (Adopted from the original datasets) Latitude 
coordinates in WGS 84. 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
longitude  (Adopted from the original datasets) Longitude 
coordinates in WGS 84. 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
4 
 
 
provider_ground_elevation_m_asl m (Adopted from the original datasets) Surface elevation 
in meter above mean sea level provided in the original 
data source; given for 24 % of the wells.  
There is the suspicion, that missing ground elevations 
for wells in Chile are marked with “0”. For wells from 
Chile, there is no NA in the ground elevation from the 
original data provider but 30% of the records are 0. As 
this is only a suspicion, we did not replace them with 
‘NA’ but provide the information here. 
 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
top_of_well_elevation_m_asl m (Adopted from the original datasets) Elevation of the 
top of the well in meter above mean sea level provided 
in the original data source; given for <1% of the wells. 
 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
total_drilling_depth_m m (Adopted from the original datasets) Total drilling depth 
for well construction. 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
country  (Adopted from the original datasets) Country in which 
the well is located. 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
address  (Adopted from the original datasets) Address of the well 
location. 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
aquifer_name  (Adopted from the original datasets) Name of the 
aquifer. 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
confinement  (Adopted from the original datasets) Information if well 
is confined or unconfined. 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
organisation  (Adopted from the original datasets) Organisation that 
provided the groundwater data. 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
5 
 
manager  (Adopted from the original datasets) Name of the well 
manager. 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
license  (Adopted from the original datasets) Data license for 
that particular groundwater time series and the 
respective attributes from the original dataset. 
 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
interval  Temporal resolution of the time series; either daily("d"), 
monthly ("MS") or yearly ("YS"). 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
aggregated_from_n_values_median  During the preprocessing of GROW, the original time 
series were aggregated to either daily, monthly, or 
yearly means to ensure qual time step intervals.  
 
‘aggregated_from_n_values_median’ indicates the 
median number of records that were aggregated to the 
daily, monthly or yearly means. 
"NA" indicates that the time series was not aggregated. 
 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
starting_date  First date of the time series in "YYYY-mm-dd" format. 
 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
ending_date  Last date of the time series in "YYYY-mm-dd" format. 
 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
length_years  Number of years that occur in a time series. 
 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
6 
 
autocorrelation  Indicates if the groundwater time series is 
autocorrelated (threshold: Spearman correlation >= 
0.6); either "True" or "False". 
 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
gap_fraction  Fraction of gaps in the groundwater time series. 
 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
 
CC BY-NC-SA 4.0 
negative_signs_wtd  Indicates whether time series with groundwater depth 
records contain negative values: 
• “No”- No negative values 
•  ” All”- Only negative values 
• “Some”- Some negative values 
• NA – Depth is not the reference point (it is 
water level instead) 
 
  
outliers_change_points  Indicates whether a time series contains outliers (noise 
or spikes) and/or change points (breaks - sudden 
increases or decreases of a variable). They were 
detected with the DBSCAN algorithm as in Nolte et al. 
(2024). 
Both can result from sensor failures. However, this can 
also be attributed to the natural variability of highly 
dynamic aquifers, weather extremes, or anthropogenic 
pumping. We flagged time series that potentially 
contain outliers and/or change points. The purpose of 
the flag is to be a first point of reference for anomalies 
(i.e. measurement errors, human impacts, extreme 
events). For actual time series repair, knowledge about 
the study area and visual inspection to validate detected 
outliers are highly recommended. Users who want to 
correct the time series can use the flag for prioritization. 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
7 
 
Instead of correction, the flagged time series could also 
be filtered out.  
 
plateaus  Indicates if uninterrupted sequences of the exact same 
water table (plateaus) occur (True) for:  
 
• >= 4 days (daily time series),  
• >= 2 months (monthly time series),  
• >= 2 year (yearly time series that are <20 years long) 
or 
• >= 3 years (yearly time series that are >= 20 years 
long)) 
 
or not (False). 
 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
trend_direction  Trend direction that is derived with the original Mann-
Kendall test from the python package pyMannKendall 
(Hussain & Mahmud, 2019); either "no trend", 
"increasing" or "decreasing".  
For autocorrelated time series, the Hamed and Rao 
Modified Mann Kendall test was used (Hamed & Rao, 
1998). 
The trend direction for time series containing 
groundwater depth records was switched (increasing <-
> decreasing) so that, for example, a rising water table 
(decreasing depth) is flagged as “increasing”. 
 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
trend_slope_m_year-1 m/year In case the trend was significant (p-value < 0.05), the 
slope is provided. 
The sign of the slope was switched for time series 
containing groundwater depth records so that 
decreasing water tables are associated with a negative 
slope. 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
8 
 
 
reference_point  (Adopted from the original datasets) Reference point for 
the water table measurements; either 'Water depth 
[from the top of the well]', 'Water depth [from the 
ground surface]' (both referred to as groundwater 
depth) or 'Water level elevation a.m.s.l.' (referred to as 
groundwater level). All are addresses as water table. 
 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
groundwater_mean_m m Mean water table per time series; either mean depth to 
water table or groundwater level elevation (see 
reference_point). 
 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
groundwater_median_m m Median water table per time series; either median 
depth to water table or groundwater level elevation (see 
reference_point). 
 
Derived from 
IGRAC 2025a & 
IGRAC 2025b 
CC BY-NC-SA 4.0 
koeppen_geiger_class  Original Koeppen-Geiger classification from Koeppen & 
Geiger (1936) for the period 1981-2010. 
 
Af: Equatorial fully humid 
Am: Equatorial monsoonal 
As: Equatorial summer dry 
Aw: Equatorial winter dry 
BWk: Cold desert 
BWh: Hot desert 
BSk: Cold steppe 
BSh: Hot steppe 
Cfa: Warm temperate fully humid hot summer 
Cfb: Warm temperate fully humid warm summer 
Cfc: Warm temperate fully humid cool summer 
Csa: Warm temperate summer dry hot summer 
LCsb: Warm temperate summer dry warm summer 
Csc: Warm temperate summer dry cool summer 
CHELSA v2.1 - kg0 
by Karger et al. 
(2021) 
CC0 1.0 
9 
 
Cwa: Warm temperate winter dry hot summer 
Cwb: Warm temperate winter dry warm summer 
Cwc: Warm temperate winter dry cool summer 
Dfa: Snow fully humid hot summer 
Dfb: Snow fully humid warm summer 
Dfc: Snow fully humid cool summer 
Dfd: Snow fully humid extremely continental 
Dsa: Snow summer dry hot summer 
Dsb: Snow summer dry warm summer 
Dsc: Snow summer dry cool summer 
Dsd: Snow summer dry extremely continental 
Dwa: Snow winter dry hot summer 
Dwb: Snow winter dry warm summer 
Dwc: Snow winter dry cool summer 
Dwd: Snow winter dry extremely continental 
ET: polar tundra 
EF: polar frost 
 
hydrobelt_class  Hydrobelt classification after Meybeck et al. 2013a. The 
classification was reduced to 5 classes (based on Table 
1. in Meybeck et al. 2013a) which are characterized by 
average annual temperature and runoff. 
 
Meybeck et al. 
2013b 
CC-BY-3.0 
ground_elevation_merit_m_asl m Ground elevation in meter above mean sea level 
derived from the global MERIT DEM. 
MERIT DEM by 
Yamazaki et al. 
(2017) 
 
CC-BY-NC 4.0 
topographic_slope_degree ° Topographic slope in degrees. Geomorpho90m 
by Amatulli et al. 
(2020) 
 
CC-BY-4.0 
rock_type_0-100_m_class  Rock type class of subsurface between 0 and 100 m 
depth. 
GLiM by Hartmann 
& Moosdorf (2012) 
CC-BY-3.0 
10 
 
 
aquifer_type_class  Estimated aquifer type derived from rock_type_class 
and the World Karst Aquifer Map;  
either "porous", "fractured", “porous/fractured”, "karst" 
or "water_body". 
 
WHYMAP WOKAM 
by Chen et al. 
(2017) + GLiM by 
Hartmann & 
Moosdorf (2012) 
WHYMAP WOKAM: 
Terms and 
conditions + 
GLiM: CC-BY-3.0 
permeability_0-100_m_m-2 m² Permeability of subsurface between 0 and 100 m depth. 
 
GLHYMPS2.0 by 
Huscroft et al. 
(2018)   
 
CC-BY-4.0 
total_porosity_0-100_m_fraction  Total porosity of subsurface between 0 and 100 m 
depth. 
GLHYMPS by 
Gleeson et al. 
(2018) 
 
CC-BY-4.0 
soil_texture_0-30_cm_class  Soil texture class for the topsoil (0-30 cm); either 
"Organic", "Very Fine", "Fine", "Medium Fine", 
"Medium" and "Coarse". 
HiHydroSoil by 
Simons et al. 
(2020) 
 
“HiHydroSoil v2.0 
can be used freely 
and redistributed 
with attribution.” 
 
soil_texture_30-200_cm_class  Soil texture class for the subsoil (30-200 cm); either 
"Organic", "Very Fine", "Fine", "Medium Fine", 
"Medium" and "Coarse". 
HiHydroSoil by 
Simons et al. 
(2020) 
 
“HiHydroSoil v2.0 
can be used freely 
and redistributed 
with attribution.” 
 
soil_saturated_conductivity_0-
30_cm_cm_d-1 
cm/day Saturated Hydraulic Conductivity of topsoil (0-30 cm). HiHydroSoil by 
Simons et al. 
(2020) 
 
“HiHydroSoil v2.0 
can be used freely 
and redistributed 
with attribution.” 
 
soil_saturated_conductivity_30-
200_cm_cm_d-1 
cm/day Saturated Hydraulic Conductivity of subsoil (30 - 200 
cm). 
HiHydroSoil by 
Simons et al. 
(2020) 
 
“HiHydroSoil v2.0 
can be used freely 
and redistributed 
with attribution.” 
11 
 
 
distance_perennial_streams_m m The distance between perennial streams with 0.1 cubic 
metres per second flow threshold. 
Cuthbert & 
Gleeson et al. 
(2019) 
 
CC-BY-4.0 
drainage_density_m-1 m-1 Drainage density, calculated as sum of the river lengths 
per basin divided by the area of that basin. 
HydroRivers by 
Lehner & Grill 
(2013) + 
BasinATLAS by 
Linke et al. (2019) 
 
Both: CC-BY-4.0 
glacier_cover_fraction 
 
 Fraction of glacier cover of surface catchment from 
HydroAtlas level 9 basins in which the well is located. 
BasinATLAS by 
Linke et al. (2019) 
 
CC-BY-4.0 
permafrost_cover_fraction 
 
 Fraction of permafrost cover of surface catchment from 
HydroAtlas level 9 basins in which the well is located. 
BasinATLAS by 
Linke et al. (2019) 
 
CC-BY-4.0 
days_with_snow_cover_average_days_ 
year-1 
 Average number of days per year with snow depth > 0 
m; derived by the daily mean snow depth from ERA5-
Land. 
ERA5-Land by 
Muñoz-Sabater et 
al. (2024); 
Copernicus Climate 
Change Service 
(2024) 
 
Licence to use 
Copernicus 
Products 
groundwater_dependent_ 
ecosystems_class 
 Groundwater-dependent ecosystems class, either 'Lotic', 
'Terrestrial, lentic, and lotic (all)', 'Terrestrial and lentic', 
'Lentic and lotic', 'Terrestrial', 'Terrestrial and lotic', 
'Lentic' or 'No GDE'. 
 
Huggins et al. 
(2023) 
CC BY-NC-SA 4.0 
main_landuse_class  Main land use class per well; main land use is that land 
use whose mean fraction over time is the highest; either 
“cropland_irrigated”, “cropland_rainfed”, “pastures”,  
“urbanareas”, “forests_and_natural_vegetation”; 
ISIMIP3a input 
data, Volkholz & 
Ostberg (2024) 
CC0 1.0 
12 
 
derived by the yearly land use fractions in the time 
series table. 
 
groundwaterscapes_ID_class  Groundwaterscapes - "Landscape units with specific and 
broadly occurring configurations of groundwater-
connected system functions" (Huggings et al., 2024a, 
p.2). 
 
• 1: Arid and desert regions with minimal functions - 
Large storage capacity 
• 2: Arid and desert regions with minimal functions - 
Small storage capacity and moderately effective 
national governance 
• 3: Arid and desert regions with minimal functions - 
Small storage capacity and ineffective national 
governance 
• 4: Underserved populations and ineffective national 
governance - Some terrestrial GDEs amid generally 
limited functions 
• 5: Underserved populations and ineffective national 
governance - Large storage capacity, moderate 
climate coupling, and some terrestrial GDEs 
• 6: Earth system functions in non-agricultural regions 
- Some terrestrial GDEs 
• 7: Earth system functions in non-agricultural regions 
- Effective national governance and some terrestrial 
GDEs 
• 8: Moderate GDEs and/or Earth system functions in 
nations with effective governance - Large storage 
capacity and moderate climate coupling 
• 9: Moderate GDEs and/or Earth system functions in 
nations with effective governance - Small storage 
capacity and very effective national governance 
Huggings et al. 
(2024b) 
CC-BY-4.0 
13 
 
• 10: Agricultural regions with high groundwater 
dependence - Smallholder farming and moderately 
effective national governance 
• 11: Agricultural regions with high groundwater 
dependence - Large farms with effective national 
governance 
• 12: Agricultural regions with lower dependence on 
groundwater - Moderate climate interactions, few 
aquatic GDEs, large farms 
• 13: Agricultural regions with lower dependence on 
groundwater - Large farms situated among GDEs 
• 14: Extensive GDEs in non-agricultural regions - 
Small storage capacity, underserved populations, 
and ineffective national governance 
• 15: Extensive GDEs in non-agricultural regions - 
Large storage capacity, large range in underserved 
populations, and ineffective national governance 
 
 
 
 
 
 
 
 
 
 
14 
 
Table 2: Overview of columns in the time series table (grow_timeseries.csv/.parquet). The data source name is linked to the respective data access 
website. The license is linked to the according license description. 
 
Column name 
 
Unit Description Data source Licensed under 
GROW_ID  A unique identifier that can be used to assign the 
time series to the attributes. 
 
/ / 
interval  Temporal resolution of the time series; either 
daily("d"), monthly ("MS") or yearly ("YS"). 
Derived from IGRAC 
2025a & IGRAC 2025b 
 
CC BY-NC-SA 4.0 
date  Timestamp of the record in "YYYY-mm-dd" 
format. 
 
Derived from IGRAC 
2025a & IGRAC 2025b 
 
CC BY-NC-SA 4.0 
year  Year of the record in "YYYY" format. 
 
Derived from IGRAC 
2025a & IGRAC 2025b 
 
CC BY-NC-SA 4.0 
month  Month of the record in "YYYY-mm" format. 
 
Derived from IGRAC 
2025a & IGRAC 2025b 
 
CC BY-NC-SA 4.0 
aggregated_from_n_values  During the preprocessing of GROW, the original 
time series were aggregated to either daily, 
monthly, or yearly means to ensure qual time 
step intervals.  
 
‘aggregated_from_n_values’ indicates the 
number of records that were aggregated to this 
record. 
"NA" indicates that the time series was not 
aggregated. 
 
Derived from IGRAC 
2025a & IGRAC 2025b 
CC BY-NC-SA 4.0 
15 
 
Number of values that were aggregated to this 
record; "NA" indicates that the time series was 
not aggregated. 
 
outliers_change_points  Indicates whether a record was detected to be an 
outlier (noise or spikes) or belongs to a sequence 
after a change point (breaks - sudden increases or 
decreases of a variable). They were detected with 
the DBSCAN algorithm as in Nolte et al. (2024). 
 
Both can result from sensor failures. However, 
this can also be attributed to the natural 
variability of highly dynamic aquifers, weather 
extremes, or anthropogenic pumping. We flagged 
time series that potentially contain outliers 
and/or change points. The purpose of the flag is 
to be a first point of reference for anomalies (i.e. 
measurement errors, human impacts, extreme 
events). For actual time series repair, knowledge 
about the study area and visual inspection to 
validate detected outliers are highly 
recommended. Users who want to correct the 
time series can use the flag to find the suspicious 
records. 
 
Derived from IGRAC 
2025a & IGRAC 2025b 
 
plateaus  Marks uninterrupted sequences of the exact 
same water table (plateaus) when the sequence 
is as long as:  
 
• >= 4 days (daily time series),  
• >= 2 months (monthly time series),  
• >= 2 year (yearly time series that are <20 
years long) or 
Derived from IGRAC 
2025a & IGRAC 2025b 
CC BY-NC-SA 4.0 
16 
 
• >= 3 years (yearly time series that are >= 20 
years long)) 
with the length of the sequence. 
 
groundwater_depth_from_ 
ground_elevation_m 
m (Adopted from the original datasets) Depth to 
water table from ground surface.  
IGRAC 2025a & IGRAC 
2025b 
 
CC BY-NC-SA 4.0 
groundwater_depth_from_ 
well_top_elevation_m 
m (Adopted from the original datasets) Depth to 
water table from the top of the well. 
 
IGRAC 2025a & IGRAC 
2025b 
CC BY-NC-SA 4.0 
groundwater_water_level_ 
elevation_m_asl 
m (Adopted from the original datasets) 
Groundwater level elevation in meters above sea 
level. 
 
IGRAC 2025a & IGRAC 
2025b 
CC BY-NC-SA 4.0 
groundwater_filled_depth_from_ 
ground_elevation_m 
m (Adopted from the original datasets) Depth to 
water table from ground surface; gaps are linearly 
interpolated.  
 
Derived from IGRAC 
2025a & IGRAC 2025b 
CC BY-NC-SA 4.0 
groundwater_filled_depth_from_ 
well_top_elevation_m 
m (Adopted from the original datasets) Depth to 
water table from the top of the well; gaps are 
linearly interpolated. 
 
Derived from IGRAC 
2025a & IGRAC 2025b 
CC BY-NC-SA 4.0 
groundwater_filled_water_level_ 
elevation_m_asl 
m (Adopted from the original datasets) 
Groundwater level elevation in meters above sea 
level; gaps are linearly interpolated. 
 
Derived from IGRAC 
2025a & IGRAC 2025b 
 
CC BY-NC-SA 4.0 
precipitation_mswep_mm_year-1 mm/ 
year 
Precipitation sum in mm/year based on 3-hourly 
data. 
MSWEP V2 by (Beck et 
al., 2019) 
 
CC-BY-NC 4.0 
precipitation_gpcc_mm_year-1 mm/ 
year 
Precipitation sum in mm/year based on monthly 
data; for daily time series, each day within a 
GPCC by Schneider et al. 
(2022) 
“The GPCC provides 
unrestricted access to its 
gridded monthly and 
17 
 
month is matched with the corresponding value 
for that month.  
 
daily precipitation data 
sets for climate 
monitoring purposes and 
related research. All 
users are requested to 
refer to the GPCC and 
the product specific DOI 
(Digital Object Identifier) 
reference as provided 
with the products” 
 
potential_evapotranspiration_era5 
_mm_year-1 
mm/ 
year 
Potential evapotranspiration sum in mm/year 
based on daily data. 
ERA5-Land by Muñoz-
Sabater et al. (2024); 
Copernicus Climate 
Change Service (2024) 
 
Licence to use 
Copernicus Products 
potential_evapotranspiration_gleam 
_mm_year-1 
mm/ 
year 
Potential evapotranspiration sum in mm/year 
based on daily data. 
GLEAM4 by Miralles et 
al. (2025) 
 
CC-BY-NC 4.0 
actual_evapotranspiration_ 
mm_year-1 
mm/ 
year 
Actual evapotranspiration sum in mm/year based 
on daily data. 
GLEAM4 by Miralles et 
al. (2025) 
 
CC-BY-NC 4.0 
interception_mm_year-1 mm/ 
year 
Interception sum in mm/year based on daily data. GLEAM4 by Miralles et 
al. (2025) 
 
CC-BY-NC 4.0 
air_temperature_°C °C Mean air temperature based on daily data. ERA5-Land by Muñoz-
Sabater et al. (2024); 
Copernicus Climate 
Change Service (2024) 
 
Licence to use 
Copernicus Products 
snow_depth_m m Mean snow depth based on daily data. The 
original dataset contains very small negative 
ERA5-Land by Muñoz-
Sabater et al. (2024); 
Licence to use 
Copernicus Products 
18 
 
values (mostly -7.345365e-24). They were 
overwritten with 0. 
Copernicus Climate 
Change Service (2024) 
 
days_with_snow_cover_days_ 
year-1 
 Number of days per year with snow cover > 0 m. 
Derived by the daily mean snow depth from 
ERA5-Land. 
For daily and monthly time series, each day or 
month is matched with the corresponding value 
of that particular year. 
 
ERA5-Land by Muñoz-
Sabater et al. (2024); 
Copernicus Climate 
Change Service (2024) 
 
Licence to use 
Copernicus Products 
ndvi_ratio  Mean NDVI (Normalized Difference Vegetation 
Index) based on daily data. 
1981-2013: AVHRR NDVI 
by Vermote & NOAA 
CDR Program (2018) 
 
2014-2024: VIIRS NDVI 
by Vermote, E. & NOAA 
CDR Program (2022) 
 
“[T]he CDR data sets are 
non-proprietary, publicly 
available, and no 
restrictions are placed 
upon their use” 
lai_low_vegetation_ratio  Mean Leaf Area Index of low vegetation based on 
daily data. 
ERA5-Land by Muñoz-
Sabater et al. (2024); 
Copernicus Climate 
Change Service (2024) 
 
Licence to use 
Copernicus Products 
lai_high_vegetation_ratio  Mean Leaf Area Index of high vegetation based 
on daily data. 
ERA5-Land by Muñoz-
Sabater et al. (2024); 
Copernicus Climate 
Change Service (2024) 
 
Licence to use 
Copernicus Products 
withdrawal_industrial_m3_year-1 m³ / 
year 
Annual total water withdrawal for the industrial 
sector; multi-model ensemble mean of H08, PCR-
GLOBWB, and WaterGAP; based on yearly data; 
for daily and monthly time series, each 
ISIMIP3a input data, 
Wada et al. (2022) 
CC0 1.0 
19 
 
day[month] within a month[year] is matched with 
the corresponding value for that month[year]. 
 
withdrawal_domestic_m3_year-1 m³ / 
year 
Annual total water withdrawal for the domestic 
sector; multi-model ensemble mean of H08, PCR-
GLOBWB, and WaterGAP; based on yearly data; 
for daily and monthly time series, each 
day[month] within a month[year] is matched with 
the corresponding value for that month[year]. 
 
ISIMIP3a input data, 
Wada et al. (2022) 
CC0 1.0 
urban_area_fraction  Fraction of urban area in 0.5° raster grid in which 
the well is located; based on yearly data; for daily 
and monthly time series, each day[month] within 
a month[year] is matched with the corresponding 
value for that month[year]. 
 
ISIMIP3a input data; 
Volkholz & Ostberg 
(2024) 
CC0 1.0 
pastures_fraction  Fraction of pastures area in 0.5° raster grid in 
which the well is located; based on yearly data; 
for daily and monthly time series, each 
day[month] within a month[year] is matched with 
the corresponding value for that month[year]. 
 
ISIMIP3a input data; 
Volkholz & Ostberg 
(2024) 
CC0 1.0 
cropland_rainfed_fraction  Fraction of rainfed cropland area in 0.5° raster 
grid in which the well is located; based on yearly 
data; for daily and monthly time series, each 
day[month] within a month[year] is matched with 
the corresponding value for that month[year]. 
 
ISIMIP3a input data, 
Volkholz & Ostberg 
(2024) 
CC0 1.0 
cropland_irrigated_fraction  Fraction of irrigated cropland area in 0.5° raster 
grid in which the well is located; based on yearly 
data; for daily and monthly time series, each 
day[month] within a month[year] is matched with 
the corresponding value for that month[year]. 
ISIMIP3a input data, 
Volkholz & Ostberg 
(2024) 
CC0 1.0 
20 
 
 
forests_natural_vegetation_fraction  Fraction of forests and natural vegetation area in 
0.5° raster grid in which the well is located; based 
on yearly data; for daily and monthly time series, 
each day[month] within a month[year] is 
matched with the corresponding value for that 
month[year]. 
ISIMIP3a input data, 
Volkholz & Ostberg 
(2024) 
CC0 1.0 
 
 
References: 
Amatulli, G., McInerney, D., Sethi, T., Strobl, P ., & Domisch, S. (2020). Geomorpho90m, empirical evaluation and accuracy assessment of global high-
resolution geomorphometric layers. Scientific Data, 7(1), 162. https://doi.org/10.1038/s41597-020-0479-6 (Last accessed on 2024-03-28) 
Beck, H. E., Wood, E. F., Pan, M., Fisher, C. K., Miralles, D. G., Van Dijk, A. I. J. M., McVicar, T. R., & Adler, R. F. (2019). MSWEP V2 Global 3-Hourly 0.1° 
Precipitation: Methodology and Quantitative Assessment. Bulletin of the American Meteorological Society, 100(3), 473–500. https://doi.org/10.1175/BAMS-
D-17-0138.1 (Last accessed on 2025-11-01) 
Chen, Z., Goldscheider, N., Auler, A., Bakalowicz, M., Broda, S., Drew, D., Hartmann, J., Jiang, G., Moosdorf, N., Richts, A., Stevanovic, Z., Veni, G., Dumont, A., 
Aureli, A., Clos, P ., & Krombholz, M. (2017). World Karst Aquifer Map (WHYMAP WOKAM) [Dataset]. BGR, IAH, KIT , UNESCO. 
https://doi.org/10.25928/B2.21_SFKQ-R406 (Last accessed on 2024-07-01) 
Cuthbert, M. O., Gleeson, T., Moosdorf, N., Befus, K. M., Schneider, A., Hartmann, J., & Lehner, B. (2019). Global patterns and dynamics of climate–
groundwater interactions. Nature Climate Change, 9(2), 137–141. https://doi.org/10.1038/s41558-018-0386-4 (Last accessed on 2024-10-21) 
Copernicus Climate Change Service, Climate Data Store. (2024). ERA5-Land post-processed daily statistics from 1950 to present [Dataset]. Copernicus Climate 
Change Service (C3S) Climate Data Store (CDS). https://doi.org/10.24381/CDS.E9C9C792 (Last accessed on 2025-11-01) 
Gleeson, T. (2018). GLobal HYdrogeology MaPS (GLHYMPS) of permeability and porosity [Dataset]. Borealis. https://doi.org/10.5683/SP2/DLGXYO (Last 
accessed on 2025-04-15) 
Hamed, K. H., & Ramachandra Rao, A. (1998). A modified Mann-Kendall trend test for autocorrelated data. Journal of Hydrology, 204(1–4), 182–196. 
https://doi.org/10.1016/S0022-1694(97)00125-X 
21 
 
Hartmann, J., & Moosdorf, N. (2012). Global Lithological Map Database v1.0 (gridded to 0.5° spatial resolution) [Dataset]. PANGAEA. 
https://doi.org/10.1594/PANGAEA.788537 (Last accessed on 2024-07-01) 
Huscroft, J., Gleeson, T., Hartmann, J., & Börker, J. (2018). Compiling and mapping global permeability of the unconsolidated and consolidated Earth: GLobal 
HYdrogeology MaPS 2.0 (GLHYMPS 2.0). [Supporting Data] [Dataset]. Borealis. https://doi.org/10.5683/SP2/TTJNIU (Last accessed on 2024-07-02) 
Huggins, X., Gleeson, T., Serrano, D., Zipper, S., Jehn, F., Rohde, M. M., Abell, R., Vigerstol, K., & Hartmann, A. (2023). Data from: Overlooked risks and 
opportunities in groundwatersheds of the world’s protected areas (Version 1.0) [Dataset]. Borealis. https://doi.org/10.5683/SP3/P3OU3A (Last accessed on 
2024-09-19) 
Huggins, X., Gleeson, T., Villholth, K. G., Rocha, J. C., & Famiglietti, J. S. (2024a). Groundwaterscapes: A Global Classification and Mapping of Groundwater’s 
Large-Scale Socioeconomic, Ecological, and Earth System Functions. Water Resources Research, 60(10), e2023WR036287. 
https://doi.org/10.1029/2023WR036287 
Huggins, X., Gleeson, T., Villholth, K. G., Rocha, J. C., & Famiglietti, J. S. (2024b). Data and code from: Groundwaterscapes: A global classification and 
mapping of groundwater’s large-scale socioeconomic, ecological, and Earth system functions (Version 1.0) [Dataset]. Borealis. 
https://doi.org/10.5683/SP3/MFYCWV (Last accessed on 2024-10-21) 
Hussain, Md., & Mahmud, I. (2019). pyMannKendall: A python package for non parametric Mann Kendall family of trend tests. Journal of Open Source 
Software, 4(39), 1556. https://doi.org/10.21105/joss.01556 
IGRAC. (2025a). The Global Groundwater Monitoring Network (GGMN) [Dataset]. IGRAC. https://doi.org/10.58154/6Z0Y-DA34 (Last accessed on 2025-08-
18) 
IGRAC. (2025b). Groundwater Observations Repository [Dataset]. Retrieved from https://ggis.un-igrac.org/view/repository/. Retrieved from https://ggis.un-
igrac.org/view/repository/ (Last accessed on 2025-08-18) 
Karger, D. N., Conrad, O., Böhner, J., Kawohl, T., Kreft, H., Soria-Auza, R. W., Zimmermann, N. E., Linder, H. P ., & Kessler, M. (2021). Climatologies at high 
resolution for the earth’s land surface areas CHELSA V2.1 [Dataset]. EnviDat. https://doi.org/10.16904/ENVIDAT.228.V2.1 (Last accessed on 2024-11-13) 
Koeppen, W., & Geiger, R. (1936). Handbuch der Klimatologie. Gebrüder Borntraeger. 
Lehner, B., & Grill, G. (2013). Global river hydrography and network routing: Baseline data and new approaches to study the world’s large river systems. 
Hydrological Processes, 27(15), 2171–2186. https://doi.org/10.1002/hyp.9740 (Last accessed on 2024-09-26) 
Linke, S., Lehner, B., Ouellet Dallaire, C., Ariwi, J., Grill, G., Anand, M., Beames, P ., Burchard-Levine, V., Maxwell, S., Moidu, H., Tan, F., & Thieme, M. (2019). 
Global hydro-environmental sub-basin and river reach characteristics at high spatial resolution. Scientific Data, 6(1), 283. https://doi.org/10.1038/s41597-
019-0300-6 (Last accessed on 2025-03-27) 
22 
 
Meybeck, M., Kummu, M., & Dürr, H. H. (2013a). Global hydrobelts and hydroregions: Improved reporting scale for water-related issues? Hydrology and 
Earth System Sciences, 17(3), 1093–1111. https://doi.org/10.5194/hess-17-1093-2013 (Last accessed on 2024-11-13) 
Meybeck, M., Kummu, M., & Dürr, H. H. (2013b). Global hydrobelts and hydroregions [Dataset]. PANGAEA. https://doi.org/10.1594/PANGAEA.806957 (Last 
accessed on 2024-11-13) 
Miralles, D. G., Bonte, O., Koppa, A., Baez-Villanueva, O. M., Tronquo, E., Zhong, F., Beck, H. E., Hulsman, P ., Dorigo, W., Verhoest, N. E. C., & Haghdoost, S. 
(2025). GLEAM4: Global land evaporation and soil moisture dataset at 0.1° resolution from 1980 to near present. Scientific Data, 12(1), 416. 
https://doi.org/10.1038/s41597-025-04610-y (Last accessed on 2025-08-16) 
Muñoz Sabater, J., Comyn-Platt, H., Hersbach, H., Bell, B., Berrisford, P ., Biavati, G., Horányi, A., Muñoz Sabater, J., Nicolas, J., Peubey, C., Radu, R., Rozum, I., 
Schepers, D., Simmons, A., Soci, C., Dee, D., Thépaut, J.-N., Cagnazo, C., & Cucchi, M. (2024). ERA5-land post-processed daily-statistics from 1950 to present 
[Dataset]. Copernicus Climate Change Service (C3S) Climate Data Store (CDS). https://doi.org/10.24381/cds.e9c9c792 (Last accessed on 2025-11-01) 
Nolte, A., Haaf, E., Heudorfer, B., Bender, S., & Hartmann, J. (2024). Disentangling coastal groundwater level dynamics in a global dataset. Hydrology and 
Earth System Sciences, 28(5), 1215–1249. https://doi.org/10.5194/hess-28-1215-2024 
Schneider, U., Hänsel, S., Finger, P ., Rustemeier, E., & Ziese, M. (2022). GPCC Full Data Monthly Product Version 2022 at 0.25°: Monthly Land-Surface 
Precipitation from Rain-Gauges built on GTS-based and Historical Data [Dataset]. Global Precipitation Climatology Centre (GPCC) at Deutscher Wetterdienst. 
https://doi.org/10.5676/DWD_GPCC/FD_M_V2022_025 (Last accessed on 2024-09-27) 
Simons, G., Koster, R., & Droogers, P . (2020). HiHydroSoil v2.0—A high resolution soil map of global hydraulic properties (Wageningen, The Netherlands). 
FutureWater report 134. (Last accessed on 2025-03-25) 
Vermote, E. & NOAA CDR Program. (2018). NOAA Climate Data Record (CDR) of AVHRR Normalized Difference Vegetation Index (NDVI) (Version 5) [Dataset]. 
NOAA National Centers for Environmental Information. https://doi.org/10.7289/V5ZG6QH9 (Last accessed on 2024-08-29) 
Vermote, E. & NOAA CDR Program. (2022). NOAA Climate Data Record (CDR) of VIIRS Normalized Difference Vegetation Index (NDVI) (Version 1) [Dataset]. 
NOAA National Centers for Environmental Information. https://doi.org/10.25921/GAKH-ST76 (Last accessed on 2025-11-01) 
Volkholz, J., & Ostberg, S. (2024). ISIMIP3a landuse input data (Version 1.3) [Dataset]. ISIMIP Repository. https://doi.org/10.48364/ISIMIP .571261.3 (Last 
accessed on 2025-04-01) 
Wada, Y ., Flörke, M., Hanasaki, N., Schmied, H. M., Gosling, S. N., & Schewe, J. (2022). ISIMIP3a water abstraction input data (Version 1.0) [Dataset]. ISIMIP 
Repository. https://doi.org/10.48364/ISIMIP .228996 (Last accessed on 2025-03-18) 
Yamazaki, D., Ikeshima, D., Tawatari, R., Yamaguchi, T., O’Loughlin, F., Neal, J. C., Sampson, C. C., Kanae, S., & Bates, P . D. (2017). A high-accuracy map of 
global terrain elevations. Geophysical Research Letters, 44(11), 5844–5853. https://doi.org/10.1002/2017GL072874 (Last accessed on 2024-07-12) 