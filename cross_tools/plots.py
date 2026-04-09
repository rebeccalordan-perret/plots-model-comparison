"""Code to produce plots for the CROSS model result comparison"""

# Copyright (c) 2024, ETH Zurich, Energy Science Center, Adriana Marcucci
# Distributed under the terms of the Apache License, Version 2.0.


# Import all the libraries 
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sb
from matplotlib.patches import Patch
import matplotlib.ticker as ticker
import inspect
import os


class Plots:

    def __init__(self, fileResults,model_list,scenarios,sceColors,folder_plots):

        """ 
        Generic class to upload the data and produce the plots for the model comparison

        Attributes:
            fileResults: Name of the file with the results
            model_list: list of dictionary with model names and the color to use for each model
            scenarios: list with the scenario names
            sceColors: list with the color for the scenarios
            folder_plots: path to folder_plots
        """
        

        # Get the models names
        self.models = {f['id']: f['name'] for f in model_list}
        self.modelsid = [ f['id'] for f in model_list ]
        self.model_colors = [ f['color'] for f in model_list ]
        self.typicalDays = {}
        self.typicalDays['summer'] = {
                                    'name':  {f['id']: f['summer'] for f in model_list},
                                    'value': {f['id']: f['summerDay'] for f in model_list}
                                }
                                
        self.typicalDays['winter'] =  {
                                    'name':  {f['id']: f['winter'] for f in model_list},
                                    'value': {f['id']: f['winterDay'] for f in model_list}
                                }
        
        os.makedirs(folder_plots, exist_ok=True)
        self.folder_plots = folder_plots
        
        # Read the file with the data
        self.allData = self.__readData(fileResults) 
        
        self.yearsModel = self.__getReportedYearsByModel()
        self.sce = scenarios
        self.sceColors = sceColors
        self.sceModel = self.__getReportedScenariosByModel()
        self.sceVariants= self.__getReportedSceVariants()
        
        
        #Calculate net imports and exports
        self.__calculateNets()
        
        # For the following variables we do a pre-processing:
        # We make sure that if the var 'cat' wasn't reported, we calculate it from the subcategories
        # The variable '(varName,cat)' will be created and can be used later in the code
        # This guarantees that we can compare even if models report different levels of aggregation 


        subcats = [
            {'varName':'electricity_supply',
             'time_resolution':['annual','typical-day'],
             'data':[
                 {'cat':'spv','subcats':['spv_rooftop','spv_facade','spv_mountain','spv_agriculture']},
                 {'cat':'wind','subcats':['wind_on','wind_off']},
                 {'cat':'methane_pp','subcats':["methane_chp_ccs","methane_chp_woccs","methane_oc_woccs","methane_oc_ccs","methane_cc_woccs","methane_cc_ccs"]},
                 {'cat':'liquids_pp','subcats':['liquids_chp_woccs','liquids_chp_ccs','liquids_oc_woccs','liquids_oc_ccs','liquids_cc_woccs','liquids_cc_ccs']},
                 {'cat':'waste_pp','subcats':['waste_chp_woccs','waste_chp_ccs','waste_cc_woccs','waste_cc_ccs']},
                 {'cat':'wood_pp','subcats':['wood_chp_woccs','wood_chp_ccs','wood_cc_woccs','wood_cc_ccs']},
                 {'cat':'hydrogen_pp','subcats':['hydrogen_chp','hydrogen_cc']},
                 ]},
            {'varName':'space_heat_useful_energy_supply',
             'time_resolution':['annual'],
             'data':[
                 {'cat':'heat_pump','subcats':['air_source','ground_source','water_source']}, 
                 {'cat':'boiler_wood','subcats':['boiler_wood_chips','boiler_wood_pellets']},
                 ]},
            {'varName':'district_heat_useful_energy_supply',
             'time_resolution':['annual'],
             'data':[
                 {'cat':'heat_pump','subcats':['air_source','ground_source','water_source']}, 
                 {'cat':'boiler_wood','subcats':['boiler_wood_chips','boiler_wood_pellets']},
                 ]},
            {'varName':'process_heat_useful_energy_production',
             'time_resolution':['annual'],
             'data':[
                 {'cat':'heat_pump','subcats':['air_source','ground_source','water_source']}, 
                 {'cat':'boiler_wood','subcats':['boiler_wood_chips','boiler_wood_pellets']},
                 ]},
            {'varName':'h2_fec',
             'time_resolution':['annual'],
             'data':[
                 {'cat':'passenger','subcats':['passenger_road_public','passenger_road_private']}, 
                 {'cat':'freight_road','subcats':['truck','ldv']}, 
                 {'cat':'storage','subcats':['h2_short_storage','h2_long_storage']}, 
                 ]},
            {'varName':'methane_fec',
             'time_resolution':['annual'],
             'data':[
                 {'cat':'passenger','subcats':['passenger_road_public','passenger_road_private']}, 
                 {'cat':'freight_road','subcats':['truck','ldv']}, 
                 ]},
            {'varName':'methane_supply',
             'time_resolution':['annual'],
             'data':[
                 {'cat':'gasification_methane','subcats':['wood_gasification_methane','waste_gasification_methane']}, 
                 ]},
            {'varName':'liquids_fec',
             'time_resolution':['annual'],
             'data':[
                 {'cat':'passenger','subcats':['passenger_road_public','passenger_road_private']}, 
                 {'cat':'freight_road','subcats':['truck','ldv']}, 
                 ]},
            {'varName':'electricity_consumption',
             'time_resolution':['annual','typical-day'],
             'data':[
                 {'cat':'process_heat','subcats':['process_heat_boiler_electrode','process_heat_heater_elec','process_heat_heat_pump']}, 
                 {'cat':'space_heating','subcats':['space_heating_boiler_electrode','space_heating_heater_elec','space_heating_heat_pump']}, 
                 {'cat':'fuel_production','subcats':['electrolysis','power_to_liquid']}, 
                 {'cat':'rail','subcats':['passenger_rail','freight_rail']}, 
                 {'cat':'freight_road','subcats':['truck','ldv']}, 
                 {'cat':'passenger','subcats':['road_public','road_private']}, 
                 ]},
            ]

        self.__checkSubcategories(subcats)
        
        variables = ['total_system_costs','carbon_price']
        self.__checkVariablesNoSub(variables)
        
        varList_supply_net = ['hydro_dam','hydro_ror','nuclear','spv','wind','geothermal_pp',"methane_pp",'fuel_cell_methane',
                           'hydrogen_pp','fuel_cell_h2','liquids_pp','waste_pp','wood_pp','net_storage_out','net_imports']
        
        self.__calculateTotalSupply(varList_supply_net)
        
        
        self.allData = (
            self.allData
              .set_index(['scenario_name','scenario_variant','model','variable',
                          'use_technology_fuel','time_resolution','timestamp'])
              .sort_index()
        )
    
        self.allData = self.allData.fillna(0)
        
        self.annualData = self.allData.loc[(slice(None),slice(None),slice(None),slice(None),slice(None),'annual',slice(None)),'value'].to_frame()
        
        
        
        # ---- Print info for the user ----
        print("=== Plots object initialized ===\n")
        
        print("Attributes:")
        for name, value in self.__dict__.items():
            print(f"  {name}: {type(value).__name__}")
        
        print("\nMethods:")
        for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
            if not name.startswith("_"):   # skip internal methods
                print(f"  {name}()")
        print("\n================================\n")
        
        
        
        
        # # Hourly data
        # self.seasons = ["summer","winter"]  
        # self.hourlyData = {}
        # for season in self.seasons:
        #     seasondata =[]
        #     for m in self.modelsid:
        #         season_m = self.allData.loc[(slice(None),slice(None),slice(None),slice(None),'typical-day',self.typicalDays[season]['value'][m]),'value']
        #         seasondata.append(season_m)
            
        #     self.hourlyData[season]= pd.concat(seasondata, axis=0, ignore_index=False,sort=True)
                
        # self.posNegData = {}
       
    #  Reads the annual data from the csv file from CROSSHub
    #  returns a dataFrame with all the data
    def __readData(self,fileResults):
        
        data = pd.read_csv(fileResults+'.csv', index_col=[],header=[0])
        
        #  remove columns that are not used 
        data.drop(columns=['scenario_group','uploaded_by','uploaded_at','country'],inplace=True)
                        
        # Get the annual values and make them numeric instead of text
        data['value']=pd.to_numeric(data['value'])
        
        # Correct the unit
        data['value']=data.apply(lambda x: x.value * self.__correctUnit(x.time_resolution,x.unit),axis=1)
        data = data.drop(['unit'], axis=1)

        # Make timestamp either an int for annual or a datetime for hourly data 
        # annual → int year
        mask_annual = data['time_resolution'] == 'annual'
        data.loc[mask_annual, 'timestamp'] = (
            data.loc[mask_annual, 'timestamp']
            .astype(int)
        )
        
        # Hourly-based → datetime (minute precision)
        mask_hourly = data['time_resolution'].isin(['typical-day', 'hourly'])
        data.loc[mask_hourly, 'timestamp'] = (
            pd.to_datetime(
                data.loc[mask_hourly, 'timestamp'],
                dayfirst=True,
                errors='coerce'
            )
            .dt.floor('min')
        )
       
        return data
    
    def __correctUnit(self,timeResolution,unit):
        annual_factors = {'twh':1,'gwh':1/1000, 'mwh':1/1e6,'gj':1/3.6,'mtco2':1,'gtco2':1000,'gw':1,'mw':1/1000,'bchf':1,'mchf':1/1000,'chf/tco2':1}
        hourly_factors = {'gw':1,'gwh/h':1, 'mw':1/1000,'mwh/h':1/1000}
        if timeResolution == 'annual':
            if unit.lower() in annual_factors.keys():
                return annual_factors[unit.lower()]
            else:
                return 0
        elif timeResolution == 'typical-day':
            if unit.lower() in hourly_factors.keys():
                return hourly_factors[unit.lower()]
            else: 
                return 0
            
    def __getReportedYearsByModel(self):
        years =  {}
        for m in self.modelsid:
            data_annual_m = self.allData.loc[
                (self.allData["model"] == m) &
                (self.allData["time_resolution"] == "annual"),
                "timestamp"
            ]
            years_m = (
                pd.to_numeric(data_annual_m, errors='coerce')
                  .dropna()
                  .astype(int)
                  .unique()
                  .tolist()
                  )
            years[m]=years_m
            
        return years
    
    
    def __getReportedScenariosByModel(self):
        sceModel = {}

        for m in self.modelsid:
            df = self.allData.loc[
                (self.allData["model"] == m) &
                (self.allData["time_resolution"] == "annual"),
                ["scenario_name", "scenario_variant"]
            ]
    
            combos = list(map(tuple, df.drop_duplicates().to_numpy()))
            sceModel[m] = combos
    
        return sceModel
    
    def __getReportedSceVariants(self):
        seen = set()
        union_list = []
        
        for pairs in self.sceModel.values():
            for combo in pairs:
                if combo not in seen:
                    seen.add(combo)
                    union_list.append(combo)
        return union_list
   


    def __checkSubcategories(self, subcats):
        """
        Create category rows by aggregating subcategories:
            value(varName, cat) = sum(value(varName, subcats))
    
        Rules:
          - If subcategories exist, rebuild `cat` from subcategories
            and replace any existing `cat` rows.
          - If subcategories do not exist, keep existing `cat` as-is.
          - If neither exists, do nothing.
        """
    
        df = self.allData.copy()
        new_rows = []
    
        base_keys = [
            "scenario_name",
            "scenario_variant",
            "model",
            "variable",
            "time_resolution",
            "timestamp",
        ]
    
        for v in subcats:
            varName = v["varName"]
    
            for resolution in v["time_resolution"]:
                suffix = "_typical_day" if resolution in ["typical-day", "hourly"] else ""
                var = varName + suffix
    
                for item in v["data"]:
                    cat = item["cat"]
                    sub_list = item["subcats"]
    
                    mask = (
                        (df["time_resolution"] == resolution)
                        & (df["variable"] == var)
                        & (df["use_technology_fuel"].isin(sub_list + [cat]))
                    )
    
                    d = df.loc[mask].copy()
                    if d.empty:
                        continue
    
                    sub_rows = d.loc[d["use_technology_fuel"].isin(sub_list)].copy()
    
                    # No subcats -> keep existing cat as-is
                    if sub_rows.empty:
                        continue
    
                    # Aggregate subcategories
                    sub_sum = (
                        sub_rows.groupby(base_keys, as_index=False)["value"]
                        .sum()
                    )
    
                    if sub_sum.empty:
                        continue
    
                    # Normalize timestamps so matching/removal is consistent
                    if resolution == "annual":
                        sub_sum["timestamp"] = pd.to_numeric(
                            sub_sum["timestamp"], errors="coerce"
                        ).astype("Int64")
    
                        df.loc[
                            (df["time_resolution"] == resolution) & (df["variable"] == var),
                            "timestamp"
                        ] = pd.to_numeric(
                            df.loc[
                                (df["time_resolution"] == resolution) & (df["variable"] == var),
                                "timestamp"
                            ],
                            errors="coerce"
                        ).astype("Int64")
    
                    else:
                        sub_sum["timestamp"] = pd.to_datetime(
                            sub_sum["timestamp"], dayfirst=True, errors="coerce"
                        ).dt.floor("min")
    
                        df.loc[
                            (df["time_resolution"] == resolution) & (df["variable"] == var),
                            "timestamp"
                        ] = pd.to_datetime(
                            df.loc[
                                (df["time_resolution"] == resolution) & (df["variable"] == var),
                                "timestamp"
                            ],
                            dayfirst=True,
                            errors="coerce"
                        ).dt.floor("min")
    
                    # Remove existing cat rows for the same keys that will be rebuilt
                    sub_sum_keys = sub_sum[base_keys].drop_duplicates()
                    existing_cat_mask = (
                        (df["time_resolution"] == resolution)
                        & (df["variable"] == var)
                        & (df["use_technology_fuel"] == cat)
                    )
    
                    existing_cat = df.loc[existing_cat_mask, base_keys].copy()
    
                    if not existing_cat.empty:
                        to_remove = existing_cat.merge(
                            sub_sum_keys,
                            on=base_keys,
                            how="inner"
                        )
    
                        if not to_remove.empty:
                            df = df.merge(
                                to_remove.assign(_drop=True),
                                on=base_keys,
                                how="left"
                            )
                            df = df.loc[
                                ~(
                                    (df["_drop"] == True)
                                    & (df["time_resolution"] == resolution)
                                    & (df["variable"] == var)
                                    & (df["use_technology_fuel"] == cat)
                                )
                            ].drop(columns="_drop")
    
                    # Add rebuilt cat rows
                    sub_sum["use_technology_fuel"] = cat
                    new_rows.append(sub_sum)
    
        if new_rows:
            add = pd.concat(new_rows, ignore_index=True)
            self.allData = pd.concat([df, add], ignore_index=True)
        else:
            self.allData = df

                               
    def __checkVariablesNoSub(self,variables):
        """ 
        Remove any text that was reported in use_technology_fuel for variables without subcategories 
        """ 
        # Create mask on the 'variable' index level
        mask = self.allData['variable'].isin(variables)
        
        # Set use_technology_fuel to '' where condition holds
        self.allData.loc[mask, 'use_technology_fuel'] = ''
        
        
                                
    def __calculateNets(self):
        """ 
        Calculate net imports, exports and storage for all the models, scenarios and timesteps
        """ 
        
        variables = [
            {'varSupply': 'electricity_supply','tech':['imports'],
             'varDemand': 'electricity_consumption','use':['exports'], 
             'netPositive':'net_imports',
             'netNegative':'net_exports',
             'time_resolution':['annual','typical-day']}, 
            {'varSupply': 'electricity_supply','tech':['battery_out','phs_out'],
             'varDemand': 'electricity_consumption','use':['battery_in','phs_in'],
             'netPositive':'net_storage_out',
             'netNegative':'net_storage_in',
            'time_resolution':['annual','typical-day']}, 
            
        ]
        
        out_rows = []
        keys = ["scenario_name", "scenario_variant", "model", "time_resolution", "timestamp"]
        
        base = self.allData.copy()
        
        for v in variables:
            for resolution in v['time_resolution']:
                suffix = "_typical_day" if resolution in ["typical-day", "hourly"] else ""
                var_supply = v["varSupply"] + suffix
                var_demand = v["varDemand"] + suffix
                
                # filter to the two variables + resolution of interest
                df = base.loc[
                       (base["time_resolution"] == resolution) &
                       (base["variable"].isin([var_supply, var_demand])),
                       :
                       ]
            
                if df.empty:
                    continue

                # Supply side: sum over tech list
                supply = (
                    df.loc[
                        (df["variable"] == var_supply) &
                        (df["use_technology_fuel"].isin(v["tech"])),
                        keys + ["value"]
                    ]
                    .groupby(keys, as_index=False)["value"]
                    .sum()
                    .rename(columns={"value": "supply_sum"})
                )
                
                # Demand side: sum over use list
                demand = (
                    df.loc[
                        (df["variable"] == var_demand) &
                        (df["use_technology_fuel"].isin(v["use"])),
                        keys + ["value"]
                    ]
                    .groupby(keys, as_index=False)["value"]
                    .sum()
                    .rename(columns={"value": "demand_sum"})
                )
                
                
                # Combine (outer so missing tech/use becomes 0)
                netdf = supply.merge(demand, on=keys, how="outer")
                netdf["supply_sum"] = netdf["supply_sum"].fillna(0.0)
                netdf["demand_sum"] = netdf["demand_sum"].fillna(0.0)
                netdf["net"] = netdf["supply_sum"] - netdf["demand_sum"]
                
                if netdf.empty:
                    continue

                # Build two outputs:
                #  - on supply variable: netPositive = max(net,0)
                #  - on demand variable: netNegative = max(-net,0)
                pos = netdf[keys].copy()
                pos["variable"] = var_supply
                pos["use_technology_fuel"] = v["netPositive"]
                pos["value"] = netdf["net"].clip(lower=0.0)
    
                neg = netdf[keys].copy()
                neg["variable"] = var_demand
                neg["use_technology_fuel"] = v["netNegative"]
                neg["value"] = (-netdf["net"]).clip(lower=0.0)
    
                out_rows.append(pos)
                out_rows.append(neg)
        
        if not out_rows:
            return

        new_rows = pd.concat(out_rows, ignore_index=True)
    
        self.allData = pd.concat([self.allData, new_rows], ignore_index=True)
        
        
                   
    def __calculateTotalSupply(self,varList_supply):
        """ 
        Calculate Net supply = sum(varList_supply)
        """ 
        df = self.allData.copy()
        # --- restrict to annual electricity supply & selected fuels ---
        d = df.loc[
            (df["time_resolution"] == "annual") &
            (df["variable"] == "electricity_supply") &
            (df["use_technology_fuel"].isin(varList_supply)),
            :
        ]
        if d.empty:
            return
        
        # --- sum across supply technologies ---
        keys = ["scenario_name", "scenario_variant", "model", "time_resolution", "timestamp"]
        total = (
            d.groupby(keys, as_index=False)["value"]
             .sum(min_count=1)  # keeps NaN if all components are NaN
        )
        # --- build output rows ---
        total["variable"] = "electricity_supply"
        total["use_technology_fuel"] = "total"
        
        self.allData = pd.concat([self.allData, total], ignore_index=True)
           
    
    
    def __extractPositiveNegative(self,positive_variables,negative_variables):
        
        positive_labels = [d['name'] for d in positive_variables]
        negative_labels=[d['name'] for d in negative_variables]
        
        timesteps = self.hourlyData['summer'].index.get_level_values(level=2).unique()
        
        for season in self.seasons:
            allData_h = self.hourlyData[season].copy()
            
            posNegData=pd.DataFrame(index=pd.MultiIndex.from_product([self.sce,positive_labels+negative_labels,timesteps] ,names=('scenario','index','timestep')),columns=self.models)
            posNegData.sort_index(inplace=True)
            posNegData.loc[(slice(None),slice(None),slice(None)),:] = 0
            
            for v in positive_variables:
                for s in self.sce:
                    for t in timesteps:
                        for subv in v['data']:
                            try:
                                posNegData.loc[(s,v['name'],t),:] += allData_h.loc[(s,subv.lower(),t),:]
                            except KeyError:
                                posNegData.loc[(s,v['name'],t),:] = posNegData.loc[(s,v['name'],t),:] 
            for v in negative_variables:
                for s in self.sce:
                    for t in timesteps:
                        for subv in v['data']:
                            try:
                                posNegData.loc[(s,v['name'],t),:] -= allData_h.loc[(s,subv.lower(),t),:]
                            except KeyError:
                                posNegData.loc[(s,v['name'],t),:] = posNegData.loc[(s,v['name'],t),:] 
            
            posNegData = posNegData.reset_index().melt(id_vars=["scenario",'index','timestep'])
            posNegData.rename(columns={'variable':'model','value':'Electricity (GW)'},inplace=True)
            self.posNegData[season] = posNegData.set_index(["scenario",'index','timestep','model'])
            
     
    def plotLineByScenario(
        self,
        listModelsid,
        map_sce_xaxis,
        varName,
        use_technology_fuel,
        year,
        scale,
        xlabel,
        ylabel,
        fileName,
        width,
        height,
        ylim=None,
        extra_values=None, 
        ncols=1,
        subplot_titles=None, 
        show_point_labels=True
    ):
        """
        Line plot of a variable by scenario/variant, with custom x-positions.
    
        Parameters
        ----------
        listModelsid : list[str]
            Model IDs to plot (keys in self.models).
    
        map_sce_xaxis : dict[(str, str), (str, float)]
            Mapping from (scenario_id, variant) -> (line_id, x_value).
            line_id    : arbitrary string used to group points into lines
                         (e.g. 'resnuc', 'res', or '5% WACC', '10% WACC').
            x_value    : numeric value for the x-axis (e.g. OCC).
    
            Example:
                map_sce_xaxis = {
                    ('abroad-resnuc-high','reference'):   ('resnuc', 12000),
                    ('abroad-resnuc-medium','reference'): ('resnuc', 8000),
                    ('abroad-resnuc-low','reference'):    ('resnuc', 5000),
                    ('abroad-res-high','reference'):      ('res',    12000),
                    ('abroad-res-medium','reference'):    ('res',    8000),
                    ('abroad-res-low','reference'):       ('res',    5000),
                }
    
        varName : str
            Variable name in the data template.
    
        use_technology_fuel : str
            Name of the use / technology / fuel.
    
        year : int
            Year for the plot.
    
        scale : float
            Factor dividing the raw value (e.g. PJ → TWh).
    
        xlabel, ylabel : str
            Axis labels.
    
        fileName : str
            Base name for saved figure files.
    
        width, height : float
            Figure size in centimeters.
            
        ylim : (float, float) or None, optional
            If not None, fixed y-axis limits (ymin, ymax).
        
        """
        
        # ---- Styling ----
        sb.reset_defaults()
        matplotlib.rcParams["font.family"] = "sans-serif"
        matplotlib.rcParams["font.sans-serif"] = "Arial"
    
        # Collect all line_ids (e.g. 'resnuc', 'res', ...)
        line_ids = sorted({v[0] for v in map_sce_xaxis.values()})
    
        # Container: values[model_id][line_id] = list of (x,y)
        values = {
            m: {line_id: [] for line_id in line_ids}
            for m in listModelsid
        }
    
                        
         # ---- Read data ----
        for (sce_id, variant), (line_id, x_val) in map_sce_xaxis.items():
            for m in listModelsid:
                # 1) try to read from self.annualData
                try:
                    val = self.annualData.loc[
                        (sce_id, variant, m, varName, use_technology_fuel, "annual", year),
                        "value",
                    ]
                except KeyError:
                    val = np.nan
    
                # 2) if missing, try extra_values
                if (np.isnan(val) or val is None) and extra_values is not None:
                    key = (sce_id, variant, m)
                    if key in extra_values:
                        val = extra_values[key]
    
                # 3) if still NaN, skip
                if not np.isnan(val):
                    y_val = val / scale
                    values[m][line_id].append((x_val, y_val))
    
        # ---- Figure ----
        cm = 1 / 2.54
        fig, axes = plt.subplots(
            1,
            ncols,
            figsize=(width * cm, height * cm),
            sharey=True
        )
        
        # Make sure axes is always iterable
        if ncols == 1:
            axes = [axes]
    
        # Simple color mapping for models
        # If you already have self.modelColors, you can replace this.
        color_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]
        model_colors = {}
        for i, m in enumerate(listModelsid):
            if hasattr(self, "modelColors") and m in self.modelColors:
                model_colors[m] = self.modelColors[m]
            else:
                model_colors[m] = color_cycle[i % len(color_cycle)]
    
        # Some markers for different line_ids so they are distinguishable
        marker_cycle = ["o", "s", "^", "D", "v", "P", "X"]
        line_styles = ["-", "--", "-.", ":"]
    
        # For legend management
        model_handles = {}
        line_handles  = {}
    
        # ---- Plot each model & line ----
        for col, ax in enumerate(axes):
        
            # split line_ids across subplots
            lines_for_this_subplot = line_ids[col::ncols]
        
            for im, m in enumerate(listModelsid):
                for il, line_id in enumerate(lines_for_this_subplot):
                    pts = values[m][line_id]
                    if not pts:
                        continue
        
                    # sort by x
                    pts = sorted(pts, key=lambda t: t[0])
                    xs = [p[0] for p in pts]
                    ys = [p[1] for p in pts]
        
                    color = model_colors[m]
                    marker = marker_cycle[il % len(marker_cycle)]
                    ls = line_styles[il % len(line_styles)]
        
                    # line + markers
                    h = ax.plot(
                        xs,
                        ys,
                        linestyle=ls,
                        marker=marker,
                        color=color,
                        label=self.models.get(m, m),
                    )[0]
        
                    # store handles for potential legends
                    model_handles.setdefault(m, h)
                    line_handles.setdefault(line_id, h)
        
                    # annotate each point: "x: y GW"
                    if show_point_labels:
                        for x_val, y_val in zip(xs, ys):
                            text = f"{int(x_val)}: {y_val:.1f} GW"
                            ax.text(
                                x_val,
                                y_val,
                                text,
                                fontsize=8,
                                va="bottom",
                                ha="center",
                                bbox=dict(
                                    boxstyle="round,pad=0.2",
                                    edgecolor=color,
                                    facecolor="white",
                                    linewidth=1,
                                ),
                            )
    
        # ---- Axes, grid, labels ----
        for i, ax in enumerate(axes):
            ax.set_xlabel(xlabel)
            ax.grid(True, linestyle="--", alpha=0.5)
            # ---- Titles ----
            if subplot_titles is not None:
                if i < len(subplot_titles):
                    ax.set_title(subplot_titles[i], fontsize=11, pad=8)
        
        axes[0].set_ylabel(ylabel)
    
    
        # Optional: small padding around x
        all_x = [x for m_dict in values.values() for line_pts in m_dict.values() for (x, _) in line_pts]
        if all_x:
            xmin, xmax = min(all_x), max(all_x)
            span = xmax - xmin if xmax > xmin else 1.0
            ax.set_xlim(xmin - 0.05 * span, xmax + 0.05 * span)
            
        # <<< Optional fixed y-limits
        if ylim is not None:
            ax.set_ylim(ylim)
    
        # ---- Legends ----
        from matplotlib.lines import Line2D

        # ---- Build final legend with custom handles ----
        combined_handles = []
        combined_labels  = []
        
        # 1. Model entries  (colored lines, NO markers)
        for m in listModelsid:
            if m in model_handles:
                # get color from the actual plotted handle
                color = model_handles[m].get_color()
                h = Line2D(
                    [], [], 
                    linestyle='-',
                    color=color,
                    marker='None',
                    linewidth=2,
                )
                combined_handles.append(h)
                combined_labels.append(self.models.get(m, m))
        
        # ---- Draw combined legend ----
        ax.legend(
            combined_handles,
            combined_labels,
            loc="upper right",
            frameon=True,
        )



    
        plt.tight_layout()
        plt.savefig(self.folder_plots + "/" + fileName+ ".pdf", bbox_inches="tight")
        plt.savefig(
            self.folder_plots + "/" + fileName + ".png",
            bbox_inches="tight",
            dpi=300,
        )
        plt.show()



    def plotTechDist(self,listModelsid,varName,varList,year,order,ylabel,ymax,fileName,legend):
        """ 
        Plots the distribution by technology
        Parameters:
        ----------
        listModelsid: list of models id to plot
        varName: str, variable name in the data template
        varList: list of dictionaries with 
            name: name of the technology or group of technologies,
            data: list with the technologies that correspond to this category
            color: color to use for this category
        year: year for the plot
        order: list with the technology order 
        ylabel: str, label for y-axis
        ymax: int, maximum level y-axis
        fileName: str, file name for the plot
        legend: True if legend has to be displayed
        """
    
        variables =[v['name'] for v in varList]
        dataNew =pd.DataFrame (index=pd.MultiIndex.from_product([self.sce,variables] ,names=('scenario','index')), columns=listModelsid)

        for v in varList:
            var =  v['name']
            for s in self.sce:
                for m in listModelsid:
                    dataNew.loc[(s,var),m] = np.nan
                    for subv in v['data']:
                        datasubv = np.nan
                        try:
                            datasubv = self.annualData.loc[(s,m,varName,subv,'annual',year),'value']
                        except:
                            datasubv = np.nan
                        if not np.isnan(datasubv):
                            if not np.isnan(dataNew.loc[(s,var),m]):    
                                dataNew.loc[(s,var),m] = dataNew.loc[(s,var),m] + datasubv
                            else:
                                dataNew.loc[(s,var),m] = datasubv

        dataNew=dataNew.dropna(how='all')
        # Remove scenarios not existent
        dataNew.reset_index(inplace=True)

        dataNew=dataNew.melt(id_vars=["scenario", "index"], 
                var_name="Model", 
                value_name="value")

        # Rename the models using the name instead of the modelid
        dataNew=dataNew.replace({'Model': self.models})
        
        # Remove  non-existent scenarios
        dataNew_unmelted = dataNew.pivot(index=['scenario','Model'], columns='index')
        dataNew_unmelted=dataNew_unmelted.loc[(dataNew_unmelted!=0).any(axis=1)]
        dataNew_unmelted.columns= dataNew_unmelted.columns.droplevel()

        dataNew_unmelted.reset_index(inplace=True)
        
        
        dataPlot=dataNew_unmelted.melt(id_vars=["scenario", "Model"], 
                    var_name="index", 
                    value_name="value")

        sb.set_style("whitegrid")

        PROPS = {
            'boxprops':{'facecolor':'none', 'edgecolor':'grey'},
            'medianprops':{'color':'grey'},
            'whiskerprops':{'color':'grey'},
            'capprops':{'color':'grey'}
        }
        
        #Get the color of the models in the list
        colors = [ self.model_colors[self.  modelsid.index(m)] for m in listModelsid ]
        #Get the names from the ids
        listModels = [self.models[x] for x in listModelsid]

        g1 = sb.catplot(x="index", y="value",hue='Model',hue_order=listModels,palette=sb.color_palette(colors), alpha=.8, data=dataPlot, 
                             order=order);
        if legend==False:
            g1._legend.remove()
        
        g1.set(xlabel='', ylabel=ylabel )
        g1.set(ylim=(0, ymax))
        
        g2 = sb.boxplot(x="index", y="value", data=dataPlot, order=order,
                        showfliers=False,
                        linewidth=0.75,
                        **PROPS);
        g2.set(xlabel='', ylabel=ylabel )
        g2.set(ylim=(0, ymax))
        
        plt.savefig(self.folder_plots+'/'+fileName,bbox_inches='tight')
        plt.savefig(self.folder_plots+'/'+fileName+'.png',bbox_inches='tight', dpi=300)
        plt.show()
    
        

    def _resolve_scenarios(self, listSce):
        if listSce is None:
            sce_names = self.sceVariants
            sce_labels = sce_names[:]
        elif isinstance(listSce, dict):
            sce_names = list(listSce.keys())
            sce_labels = list(listSce.values())
        else:
            sce_names = list(listSce)
            sce_labels = sce_names[:]
        return sce_names, sce_labels
    
    def _group_layout(self, listModelsid, sce_names, sce_labels, group_by):
        nmodels = len(listModelsid)
        nscen   = len(sce_names)
        listModels = [self.models[k] for k in listModelsid if k in self.models]
    
        if group_by == "model":
            nGroups, nWithin = nmodels, nscen
            group_labels  = listModels
            within_labels = sce_labels
    
            def flatten(mat):         # [model, scen] -> model-major
                return mat.reshape(-1)
    
            def slice_group(mat, g):  # values for group g (length nWithin)
                return mat[g, :]
    
        elif group_by == "scenario":
            nGroups, nWithin = nscen, nmodels
            group_labels  = sce_labels
            within_labels = listModels
    
            def flatten(mat):         # scenario-major
                return mat.T.reshape(-1)
    
            def slice_group(mat, g):
                return mat[:, g]
        else:
            raise ValueError("group_by must be 'model' or 'scenario'")
    
        return nGroups, nWithin, group_labels, within_labels, flatten, slice_group
    
    def _positions_single_axis(self,nGroups, nWithin, orientation):
        pos_grid, pos_cols, pos_bar = [], [], []
        for g in range(nGroups):
            ini = nGroups * nWithin / 2 - g * nWithin * 0.5 + 0.5 * (nGroups - g)
            pos_grid.append(ini)
            pos_cols.append(ini - nWithin / 4 - 0.25)
            for w in range(nWithin):
                if orientation == "vertical":
                    pos = ini - (nWithin - 1 - w) * 0.5 - 0.5
                else:  # horizontal (matches your old order)
                    pos = ini - w * 0.5 - 0.5
                pos_bar.append(pos)
    
        pos_bar = np.array(pos_bar)
    
        # keep your vertical "flip so first group on left"
        if orientation == "vertical":
            max_grid = pos_grid[0]
            pos_grid = [max_grid - x for x in pos_grid]
            pos_cols = [max_grid - x for x in pos_cols]
            pos_bar  = max_grid - pos_bar
        else:
            max_grid = pos_grid[0]
    
        return pos_bar, pos_grid, pos_cols, max_grid
    
    def _positions_within_only(self,nWithin, orientation):
        ini = 1 * nWithin / 2 - 0 * nWithin * 0.5 + 0.5 * (1 - 0)
        pos_grid = [ini]
        pos_cols = [ini - nWithin / 4 - 0.25]
        pos_bar = []
        for w in range(nWithin):
            if orientation == "vertical":
                pos = ini - (nWithin - 1 - w) * 0.5 - 0.5
            else:
                pos = ini - w * 0.5 - 0.5
            pos_bar.append(pos)
        return np.array(pos_bar), pos_grid, pos_cols, pos_grid[0]
    
    def _compute_matrices_mi(self, listModelsid, sce_names, year, scale, varName, components, signed):
        """
        Uses annual data only (time_resolution='annual', timestamp=year).
        """
        nmodels = len(listModelsid)
        nscen   = len(sce_names)
    
        names, colors, mats = [], {}, {}
    
        for comp in components:
            name = comp["name"]
            names.append(name)
            colors[name] = comp["color"]
            mat = np.zeros((nmodels, nscen))
    
            if signed:
                vname = comp["varName"]
                techs = comp["techs"]
                sgn   = float(comp.get("sign", 1.0))
            else:
                vname = varName
                techs = comp["data"]
                sgn   = 1.0
    
            for im, m in enumerate(listModelsid):
                for isce, sce in enumerate(sce_names):
                    total = 0.0
                    for tech in techs:
                        try:
                            val = self.allData.loc[
                                (sce[0], sce[1], m, vname, tech, "annual", year),
                                "value"
                            ]
                        except KeyError:
                            val = 0.0
    
                        # val might be scalar or Series if duplicates exist
                        if hasattr(val, "sum"):
                            val = float(val.sum())
                        if not np.isnan(val):
                            total += val
    
                    mat[im, isce] = sgn * (total / scale)
    
            mats[name] = mat
    
        return names, colors, mats
    
    def _draw_stacks(self,ax, orientation, pos_bar, names, colors, mats, vec_getter, signed, bar_width=0.3):
        if orientation == "vertical":
            barfunc = ax.bar
            stack_key = "bottom"
        else:
            barfunc = ax.barh
            stack_key = "left"
    
        n = len(pos_bar)
    
        if not signed:
            offset = np.zeros(n)
            for nm in names:
                vals = vec_getter(nm)
                barfunc(pos_bar, vals, bar_width, color=colors[nm], edgecolor="none",
                        zorder=1, label=nm, **{stack_key: offset})
                offset += vals
            return
    
        off_pos = np.zeros(n)
        off_neg = np.zeros(n)
        for nm in names:
            vals = vec_getter(nm)
            pos_vals = np.clip(vals, 0, None)
            neg_vals = np.clip(vals, None, 0)
    
            barfunc(pos_bar, pos_vals, bar_width, color=colors[nm], edgecolor="none",
                    zorder=1, label=nm, **{stack_key: off_pos})
            barfunc(pos_bar, neg_vals, bar_width, color=colors[nm], edgecolor="none",
                    zorder=1, **{stack_key: off_neg})
    
            off_pos += pos_vals
            off_neg += neg_vals
    
    def _plot_stacked_engine_mi(
            self,
            *,
            orientation,          # "vertical" / "horizontal"
            listModelsid,
            listSce,
            year,
            scale,
            label,
            figmax,
            fileName,
            invert,
            legend,
            pos_legend,
            width,
            height,
            group_by,
            multi,
            signed,
            varName=None,         # unsigned
            varList=None,         # unsigned
            signedVarList=None,   # signed
            ):
        # Require sorted MultiIndex for fastest/most reliable .loc
        # (safe even if already sorted)
        if not self.allData.index.is_monotonic_increasing:
            self.allData = self.allData.sort_index()
    
        sce_names, sce_labels = self._resolve_scenarios(listSce)
        nGroups, nWithin, group_labels, within_labels, flatten, slice_group = self._group_layout(
            listModelsid, sce_names, sce_labels, group_by
        )
    
        components = signedVarList if signed else varList
        names, colors, mats = self._compute_matrices_mi(
            listModelsid, sce_names, year, scale, varName, components, signed
        )
    
        cm = 1 / 2.54
    
        # ---------------- single axis ----------------
        if not multi:
            fig, ax = plt.subplots(1, figsize=(width * cm, height * cm))
            pos_bar, pos_grid, pos_cols, max_grid = self._positions_single_axis(nGroups, nWithin, orientation)
    
            def vec_getter(nm):
                return flatten(mats[nm])
    
            self._draw_stacks(ax, orientation, pos_bar, names, colors, mats, vec_getter, signed=signed)
    
            if orientation == "vertical":
                if signed:
                    ax.set_ylim(-figmax, figmax)
                    ax.axhline(0, color="black", linewidth=1)
                else:
                    ax.set_ylim(0, figmax)
                    if invert:
                        ax.invert_yaxis()
                        ax.set_ylim(figmax, 0)
    
                # within labels
                within_flat = []
                if group_by == "model":
                    for _ in range(len(listModelsid)):
                        within_flat.extend(within_labels)
                else:
                    for _ in range(len(sce_names)):
                        within_flat.extend(within_labels)
    
                ax.set_xticks(pos_bar)
                ax.set_xticklabels(within_flat, rotation=90)
                ax.set_xlim(0, max_grid)
                ax.set_ylabel(label)
                ax.tick_params(axis="y", which="major", length=0)
    
                # ---- Group labels (fixed position in axes coords) ----
                y_axes = 1.02      # always above plot
                va = "bottom"
                
                for x, group_label in zip(pos_cols, group_labels):
                    ax.text(
                        x,
                        y_axes,
                        group_label,
                        ha="center",
                        va=va,
                        transform=ax.get_xaxis_transform(),  # x in data, y in axes
                    )
                
                ax.xaxis.set_minor_locator(ticker.FixedLocator(pos_grid))
                ax.xaxis.grid(color="gray", linestyle="dashed", which="minor")
                ax.yaxis.grid(color="gray", linestyle="dashed")
                ax.spines["right"].set_visible(False)
                ax.spines["top"].set_visible(False if not invert else True)
    
            else:  # horizontal
                if signed:
                    ax.set_xlim(-figmax, figmax)
                    ax.axvline(0, color="black", linewidth=1)
                else:
                    ax.set_xlim(0, figmax)
                    if invert:
                        ax.invert_xaxis()
                        ax.set_xlim(figmax, 0)
    
                within_flat = []
                if group_by == "model":
                    for _ in range(len(listModelsid)):
                        within_flat.extend(within_labels)
                else:
                    for _ in range(len(sce_names)):
                        within_flat.extend(within_labels)
    
                ax.set_yticks(pos_bar)
                ax.set_yticklabels(within_flat)
                ax.set_ylim(0, pos_grid[0])
                ax.set_xlabel(label)
                ax.tick_params(axis="x", which="major", length=0)
    
                x_axes = 1.02
                ha = "left"
                
                for y, group_label in zip(pos_cols, group_labels):
                    ax.text(
                        x_axes,
                        y,
                        group_label,
                        va="center",
                        ha=ha,
                        transform=ax.get_yaxis_transform(),  # y in data, x in axes
                    )
    
                ax.yaxis.set_minor_locator(ticker.FixedLocator(pos_grid))
                ax.yaxis.grid(color="gray", linestyle="dashed", which="minor")
                ax.xaxis.grid(color="gray", linestyle="dashed")
                ax.spines["right"].set_visible(False)
                ax.spines["top"].set_visible(False)
    
            if legend:
                proxies = [Patch(facecolor=colors[nm], edgecolor="none") for nm in names]
                if isinstance(pos_legend, dict):
                    ax.legend(proxies, names, **pos_legend)
                else:
                    ax.legend(proxies, names, loc=pos_legend, ncol=1)
    
            plt.savefig(self.folder_plots + "/" + fileName + ".pdf", bbox_inches="tight")
            plt.savefig(self.folder_plots + "/" + fileName + ".png", bbox_inches="tight", dpi=300)
            plt.show()
            return
    
        # ---------------- multi: one subplot per group ----------------
        fig, axes = plt.subplots(
            1, nGroups,
            figsize=(width * cm, height * cm),
            sharey=(orientation == "vertical"),
            sharex=(orientation == "horizontal"),
        )
        if nGroups == 1:
            axes = [axes]
    
        local_pos_bar, local_pos_grid, _, local_max = self._positions_within_only(nWithin, orientation)
    
        for g in range(nGroups):
            ax = axes[g]
    
            def vec_getter(nm):
                return slice_group(mats[nm], g)
    
            self._draw_stacks(ax, orientation, local_pos_bar, names, colors, mats, vec_getter, signed=signed)
    
            if orientation == "vertical":
                if signed:
                    ax.set_ylim(-figmax, figmax)
                    ax.axhline(0, linewidth=1)
                else:
                    ax.set_ylim(0, figmax)
                    if invert:
                        ax.invert_yaxis()
                        ax.set_ylim(figmax, 0)
    
                ax.set_xlim(0, local_max)
                ax.set_xticks(local_pos_bar)
                ax.set_xticklabels(within_labels, rotation=90)
                ax.yaxis.grid(color="gray", linestyle="dashed")
                ax.set_title(group_labels[g])
    
                if g == 0:
                    ax.set_ylabel(label)
                else:
                    ax.set_ylabel("")
                    ax.tick_params(axis="y", labelleft=False)
    
                ax.spines["right"].set_visible(False)
                ax.spines["top"].set_visible(False)
    
            else:  # horizontal
                if signed:
                    ax.set_xlim(-figmax, figmax)
                    ax.axvline(0, linewidth=1)
                else:
                    ax.set_xlim(0, figmax)
                    if invert:
                        ax.invert_xaxis()
                        ax.set_xlim(figmax, 0)
    
                ax.set_ylim(0, local_pos_grid[0])
                ax.set_yticks(local_pos_bar)
                ax.set_yticklabels(within_labels)
                ax.xaxis.grid(color="gray", linestyle="dashed")
                ax.set_title(group_labels[g])
                ax.set_xlabel(label)
    
                if g != 0:
                    ax.set_yticklabels([])
                    ax.tick_params(axis="y", which="major", length=0)
    
                ax.spines["right"].set_visible(False)
                ax.spines["top"].set_visible(False)
    
        if legend:
            proxies = [Patch(facecolor=colors[nm], edgecolor="none") for nm in names]
        
            if isinstance(pos_legend, dict):
                fig.legend(proxies, names, **pos_legend)
            else:
                fig.legend(proxies, names, loc=pos_legend, ncol=1)

    
        fig.tight_layout()
        plt.savefig(self.folder_plots + "/" + fileName + ".pdf", bbox_inches="tight")
        plt.savefig(self.folder_plots + "/" + fileName + ".png", bbox_inches="tight", dpi=300)
        plt.show()

    def plotBarVertical(self, listModelsid, listSce, varName, varList, year, scale, label, figmax,
                        fileName, invert, legend, pos_legend, width, height,
                        group_by="model", multi=False):
        return self._plot_stacked_engine_mi(
            orientation="vertical",
            listModelsid=listModelsid,
            listSce=listSce,
            year=year,
            scale=scale,
            label=label,
            figmax=figmax,
            fileName=fileName,
            invert=invert,
            legend=legend,
            pos_legend=pos_legend,
            width=width,
            height=height,
            group_by=group_by,
            multi=multi,
            signed=False,
            varName=varName,
            varList=varList,
        )
    
    def plotBarHorizontal(self, listModelsid, listSce, varName, varList, year, scale, label, figmax,
                          fileName, invert, legend, pos_legend, width, height,
                          group_by="model", multi=False):
        return self._plot_stacked_engine_mi(
            orientation="horizontal",
            listModelsid=listModelsid,
            listSce=listSce,
            year=year,
            scale=scale,
            label=label,
            figmax=figmax,
            fileName=fileName,
            invert=invert,
            legend=legend,
            pos_legend=pos_legend,
            width=width,
            height=height,
            group_by=group_by,
            multi=multi,
            signed=False,
            varName=varName,
            varList=varList,
        )
    
    def plotBarVerticalSigned(self, listModelsid, listSce, signedVarList, year, scale, label, figmax,
                              fileName, invert=False, legend=True, pos_legend="upper right",
                              width=12, height=5, group_by="model", multi=False):
        return self._plot_stacked_engine_mi(
            orientation="vertical",
            listModelsid=listModelsid,
            listSce=listSce,
            year=year,
            scale=scale,
            label=label,
            figmax=figmax,
            fileName=fileName,
            invert=invert,
            legend=legend,
            pos_legend=pos_legend,
            width=width,
            height=height,
            group_by=group_by,
            multi=multi,
            signed=True,
            signedVarList=signedVarList,
        )
    
    def plotBarHorizontalSigned(self, listModelsid, listSce, signedVarList, year, scale, label, figmax,
                                fileName, invert=False, legend=True, pos_legend="upper right",
                                width=12, height=5, group_by="model", multi=False):
        return self._plot_stacked_engine_mi(
            orientation="horizontal",
            listModelsid=listModelsid,
            listSce=listSce,
            year=year,
            scale=scale,
            label=label,
            figmax=figmax,
            fileName=fileName,
            invert=invert,
            legend=legend,
            pos_legend=pos_legend,
            width=width,
            height=height,
            group_by=group_by,
            multi=multi,
            signed=True,
            signedVarList=signedVarList,
        )


    def plotScatter(
        self,
        listModelsid,
        listSce,
        varName,
        use_technology_fuel,
        year,
        scale,
        label,
        figmax,
        fileName,
        width,
        height,
        orientation="horizontal",   # 'horizontal' or 'vertical'
        group_by="model",           # 'model' or 'scenario'
    ):
        # ensure MI sorted for reliable lookup speed
        if not self.allData.index.is_monotonic_increasing:
            self.allData = self.allData.sort_index()
    
        is_horizontal = (orientation == "horizontal")
    
        # 1) scenarios + grouping (reused)
        sce_names, sce_labels = self._resolve_scenarios(listSce)
        nGroups, nWithin, group_labels, within_labels, flatten, slice_group = self._group_layout(
            listModelsid, sce_names, sce_labels, group_by
        )
    
        # 2) positions (same as bars, single-axis geometry)
        orient = "horizontal" if is_horizontal else "vertical"
        pos_bar, pos_grid, pos_cols, max_grid = self._positions_single_axis(nGroups, nWithin, orient)
    
        # 3) figure/axis
        cm = 1 / 2.54
        fig, ax = plt.subplots(1, figsize=(width * cm, height * cm))
    
        # 4) plotting (loop through bars in the same order as bar plots)
        k = 0
        tick_pos = []
        tick_lab = []
    
        for g in range(nGroups):
            for w in range(nWithin):
                # map (g,w) -> (model_idx, scenario_idx) consistent with group_by
                if group_by == "model":
                    im, isce = g, w
                else:
                    im, isce = w, g
    
                m = listModelsid[im]
                sce = sce_names[isce]
                cat_pos = pos_bar[k]
                k += 1
    
                # MultiIndex lookup
                try:
                    val = self.allData.loc[
                        (sce[0], sce[1], m, varName, use_technology_fuel, "annual", year),
                        "value",
                    ]
                except KeyError:
                    val = np.nan
    
                if hasattr(val, "sum"):
                    val = float(val.sum())
                if not np.isnan(val):
                    val = val / scale
                    if is_horizontal:
                        ax.scatter(val, cat_pos, s=20, zorder=2)
                    else:
                        ax.scatter(cat_pos, val, s=20, zorder=2)
    
                tick_pos.append(cat_pos)
                tick_lab.append(within_labels[w])
    
        # 5) axes, ticks, grids
        if is_horizontal:
            ax.set_xlim(0, figmax)
            ax.set_ylim(0, max_grid)
            ax.yaxis.set_major_locator(ticker.FixedLocator(tick_pos))
            ax.set_yticklabels(tick_lab)
            ax.set_xlabel(label)
    
            # group labels outside (axes coords so it doesn't move)
            for y, lab in zip(pos_cols, group_labels):
                ax.text(1.01, y, lab, transform=ax.get_yaxis_transform(),
                        va="center", ha="left")
            ax.yaxis.set_minor_locator(ticker.FixedLocator(pos_grid))
            ax.yaxis.grid(color="gray", linestyle="dashed", which="minor")
            ax.xaxis.grid(color="gray", linestyle="dashed")
    
            ax.spines["left"].set_visible(False)
    
        else:
            ax.set_ylim(0, figmax)
            ax.set_xlim(0, max_grid)
            ax.xaxis.set_major_locator(ticker.FixedLocator(tick_pos))
            ax.set_xticklabels(tick_lab, rotation=90)
            ax.set_ylabel(label)
    
            # group labels outside (axes coords so it doesn't move)
            for x, lab in zip(pos_cols, group_labels):
                ax.text(x, 1.02, lab, transform=ax.get_xaxis_transform(),
                        va="bottom", ha="center")
            ax.xaxis.set_minor_locator(ticker.FixedLocator(pos_grid))
            ax.xaxis.grid(color="gray", linestyle="dashed", which="minor")
            ax.yaxis.grid(color="gray", linestyle="dashed")
    
            ax.spines["bottom"].set_visible(False)
    
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    
        plt.savefig(self.folder_plots + "/" + fileName + ".pdf", bbox_inches="tight")
        plt.savefig(self.folder_plots + "/" + fileName + ".png", bbox_inches="tight", dpi=300)
        plt.show()



    def plotHourlySignedProfile(
        self,
        *,
        listModelsid,
        listSce,
        signedVarList,
        day_by_model,              # dict: {model_id: "dd.mm.yyyy"} or pd.Timestamp/date-like
        time_resolution="typical-day",  # or "hourly"
        scale=1.0,
        ylabel="Electricity (GW)",
        fileName="hourly_signed",
        width=18,
        height=5,
        ymin=None,                 # e.g. -60
        ymax=None,                 # e.g. 100
        legend=True,
        pos_legend=None,           # dict or string (like your other plots)
    ):
        """
        One subplot per model. X axis = hour 0..23. Signed stacked bars (positive/negative).
    
        signedVarList entries:
          {"name": "...", "varName": "...", "techs": [...], "sign": +1/-1, "color": "..."}
        """
    
        # --- scenario selection (same convention as your bar funcs) ---
        if listSce is None:
            sce_names = self.sceVariants
            sce_labels = sce_names[:]
        elif isinstance(listSce, dict):
            sce_names = list(listSce.keys())
            sce_labels = list(listSce.values())
        else:
            sce_names = list(listSce)
            sce_labels = sce_names[:]
    
        if len(sce_names) != 1:
            raise ValueError("Hourly profile plot expects exactly ONE scenario/variant (pass one tuple in listSce).")
        sce = sce_names[0]  # (scenario_name, scenario_variant)
    
        # --- prepare figure ---
        cm = 1 / 2.54
        n = len(listModelsid)
        fig, axes = plt.subplots(1, n, figsize=(width * cm, height * cm), sharey=True)
        if n == 1:
            axes = [axes]
    
        # proxy legend (always correct)
        names = [v["name"] for v in signedVarList]
        colors = {v["name"]: v["color"] for v in signedVarList}
        proxies = [Patch(facecolor=colors[nm], edgecolor="none") for nm in names]
    
        for ax, m in zip(axes, listModelsid):
            day_val = day_by_model.get(m, None)
            if day_val is None:
                raise ValueError(f"Missing day_by_model entry for model '{m}'")
    
            day = pd.to_datetime(day_val, dayfirst=True)
            ts = pd.date_range(day.normalize(), periods=24, freq="H")
    
            # collect series per component
            comp_vals = {}
            for comp in signedVarList:
                vname = comp["varName"]
                techs = comp["techs"]
                sgn = float(comp.get("sign", 1.0))
    
                arr = np.zeros(24, dtype=float)
                for i, t in enumerate(ts):
                    s = 0.0
                    for tech in techs:
                        try:
                            val = self.allData.loc[(sce[0], sce[1], m, vname, tech, time_resolution, t), "value"]
                        except KeyError:
                            val = 0.0
    
                        if hasattr(val, "sum"):
                            val = float(val.sum())
                        s += 0.0 if np.isnan(val) else float(val)
    
                    arr[i] = sgn * (s / scale)
    
                comp_vals[comp["name"]] = arr
    
            # --- signed stacked bars ---
            x = np.arange(24)
            width_bar = 0.9
            pos_base = np.zeros(24)
            neg_base = np.zeros(24)
    
            for comp in signedVarList:
                nm = comp["name"]
                vals = comp_vals[nm]
                pos = np.clip(vals, 0, None)
                neg = np.clip(vals, None, 0)
    
                ax.bar(x, pos, width=width_bar, bottom=pos_base, color=colors[nm], edgecolor="none")
                ax.bar(x, neg, width=width_bar, bottom=neg_base, color=colors[nm], edgecolor="none")
    
                pos_base += pos
                neg_base += neg
    
            # --- cosmetics: black axes + black zero line ---
            ax.axhline(0, color="black", linewidth=1.0)
            for spine in ["left", "bottom"]:
                ax.spines[spine].set_color("black")
                ax.spines[spine].set_linewidth(1.0)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.tick_params(colors="black")
    
            ax.set_xticks([0, 6, 12, 18, 23])
            ax.set_xlim(-0.5, 23.5)
            ax.set_title(self.models.get(m, m), fontsize=10)
            ax.grid(axis="y", linestyle="dashed", color="gray", alpha=0.6)
    
        # y-limits (asymmetric supported)
        if ymin is None or ymax is None:
            # autoscale from data if not provided
            all_max = max(ax.get_ylim()[1] for ax in axes)
            all_min = min(ax.get_ylim()[0] for ax in axes)
            ymin = all_min if ymin is None else ymin
            ymax = all_max if ymax is None else ymax
    
        for ax in axes:
            ax.set_ylim(ymin, ymax)
    
        axes[0].set_ylabel(ylabel)
    
        # legend (figure-level, outside if you want)
        if legend:
            if pos_legend is None:
                # decent default: outside bottom
                pos_legend = {"loc": "lower center", "bbox_to_anchor": (0.5, -0.10), "ncol": min(len(names), 6)}
            if isinstance(pos_legend, dict):
                fig.legend(proxies, names, **pos_legend)
            else:
                fig.legend(proxies, names, loc=pos_legend, ncol=1)
    
        fig.tight_layout()
        plt.savefig(self.folder_plots + "/" + fileName + ".pdf", bbox_inches="tight")
        plt.savefig(self.folder_plots + "/" + fileName + ".png", bbox_inches="tight", dpi=300)
        plt.show()
        


    def plotBarVerticalSignedFuels(
        self,
        *,
        scenario,            # tuple: (scenario_name, scenario_variant)
        listModelsid,
        signedVarByFuel,     # dict: fuel -> list[component dicts]
        year,
        scale,
        label,
        ylim=None,           # e.g. (-60, 100). If None: symmetric (+/- figmax)
        figmax=100,          # used if ylim is None
        fileName="signed_fuels",
        group_by="fuel",     # "fuel" or "model"
        multi=False,
        legend=True,
        pos_legend="upper right",  # or dict for outside
        width=12,
        height=5,
        invert=False,        # optional (kept for API consistency)
    ):
        """
        Signed vertical bars for one scenario, with fuels as the "scenario dimension".
        group_by:
          - "fuel": groups are fuels, within are models
          - "model": groups are models, within are fuels
        """
    
        # Ensure sorted index for stable .loc performance
        if not self.allData.index.is_monotonic_increasing:
            self.allData = self.allData.sort_index()
    
        sce_name, sce_var = scenario
        fuels = list(signedVarByFuel.keys())
        nfuels = len(fuels)
        nmodels = len(listModelsid)
        model_labels = [self.models.get(m, m) for m in listModelsid]
    
        # Component names + colors (use first fuel as reference)
        ref = signedVarByFuel[fuels[0]]
        comp_names = [c["name"] for c in ref]
        colors = {c["name"]: c["color"] for c in ref}
    
        # Build matrices: comp_name -> (nmodels, nfuels)
        mats = {nm: np.zeros((nmodels, nfuels)) for nm in comp_names}
    
        for jf, fuel in enumerate(fuels):
            comps = {c["name"]: c for c in signedVarByFuel[fuel]}
            for im, m in enumerate(listModelsid):
                for nm in comp_names:
                    c = comps[nm]
                    total = 0.0
                    for tech in c["techs"]:
                        try:
                            val = self.allData.loc[
                                (sce_name, sce_var, m, c["varName"], tech, "annual", year),
                                "value"
                            ]
                        except KeyError:
                            val = 0.0
                        if hasattr(val, "sum"):
                            val = float(val.sum())
                        if not np.isnan(val):
                            total += val
                    mats[nm][im, jf] = float(c.get("sign", 1.0)) * (total / scale)
    
        # Grouping layout (fuels/models)
        if group_by == "fuel":
            nGroups, nWithin = nfuels, nmodels
            group_labels = fuels
            within_labels = model_labels
    
            def flatten(mat):      # (nmodels,nfuels) -> scenario-major equivalent (fuels major)
                return mat.T.reshape(-1)
    
            def slice_group(mat, g):
                return mat[:, g]   # models within this fuel
    
        elif group_by == "model":
            nGroups, nWithin = nmodels, nfuels
            group_labels = model_labels
            within_labels = fuels
    
            def flatten(mat):
                return mat.reshape(-1)
    
            def slice_group(mat, g):
                return mat[g, :]   # fuels within this model
        else:
            raise ValueError("group_by must be 'fuel' or 'model'")
    
        # Positions (same as your vertical bar)
        def _positions_single_axis(nGroups, nWithin):
            pos_grid, pos_cols, pos_bar = [], [], []
            for g in range(nGroups):
                ini = nGroups * nWithin / 2 - g * nWithin * 0.5 + 0.5 * (nGroups - g)
                pos_grid.append(ini)
                pos_cols.append(ini - nWithin / 4 - 0.25)
                for w in range(nWithin):
                    pos = ini - (nWithin - 1 - w) * 0.5 - 0.5
                    pos_bar.append(pos)
            pos_bar = np.array(pos_bar)
    
            # flip so first group is left
            max_grid = pos_grid[0]
            pos_grid = [max_grid - x for x in pos_grid]
            pos_cols = [max_grid - x for x in pos_cols]
            pos_bar  = max_grid - pos_bar
            return pos_bar, pos_grid, pos_cols, max_grid
    
        def _positions_within_only(nWithin):
            ini = 1 * nWithin / 2 + 0.5
            pos_bar = []
            for w in range(nWithin):
                pos_bar.append(ini - (nWithin - 1 - w) * 0.5 - 0.5)
            return np.array(pos_bar), ini
    
        cm = 1 / 2.54
    
        # ---------- SINGLE AXIS ----------
        if not multi:
            fig, ax = plt.subplots(1, figsize=(width * cm, height * cm))
            pos_bar, pos_grid, pos_cols, max_grid = _positions_single_axis(nGroups, nWithin)
    
            # signed stacking
            off_pos = np.zeros(len(pos_bar))
            off_neg = np.zeros(len(pos_bar))
    
            for nm in comp_names:
                vals = flatten(mats[nm])
                pos_vals = np.clip(vals, 0, None)
                neg_vals = np.clip(vals, None, 0)
    
                ax.bar(pos_bar, pos_vals, 0.3, bottom=off_pos, color=colors[nm], edgecolor="none", zorder=1)
                ax.bar(pos_bar, neg_vals, 0.3, bottom=off_neg, color=colors[nm], edgecolor="none", zorder=1)
    
                off_pos += pos_vals
                off_neg += neg_vals
    
            # y-limits
            if ylim is not None:
                ax.set_ylim(ylim[0], ylim[1])
            else:
                ax.set_ylim(-figmax, figmax)
    
            ax.axhline(0, color="black", linewidth=1)  # black axis line
    
            # ticks
            within_flat = []
            for _ in range(nGroups):
                within_flat.extend(within_labels)
            ax.set_xticks(pos_bar)
            ax.set_xticklabels(within_flat, rotation=90)
    
            # group labels pinned to axes top (won’t move with invert)
            for x, glab in zip(pos_cols, group_labels):
                ax.text(x, 1.02, glab, ha="center", va="bottom", transform=ax.get_xaxis_transform())
    
            ax.set_xlim(0, max_grid)
            ax.xaxis.set_minor_locator(ticker.FixedLocator(pos_grid))
            ax.xaxis.grid(color="gray", linestyle="dashed", which="minor")
            ax.yaxis.grid(color="gray", linestyle="dashed")
            ax.set_ylabel(label)
    
            # legend (proxy patches; correct for signed)
            if legend:
                proxies = [Patch(facecolor=colors[nm], edgecolor="none") for nm in comp_names]
                if isinstance(pos_legend, dict):
                    ax.legend(proxies, comp_names, **pos_legend)
                else:
                    ax.legend(proxies, comp_names, loc=pos_legend, ncol=1)
    
            plt.savefig(self.folder_plots + "/" + fileName + ".pdf", bbox_inches="tight")
            plt.savefig(self.folder_plots + "/" + fileName + ".png", bbox_inches="tight", dpi=300)
            plt.show()
            return
    
        # ---------- MULTI: one subplot per group ----------
        fig, axes = plt.subplots(1, nGroups, figsize=(width * cm, height * cm), sharey=True)
        if nGroups == 1:
            axes = [axes]
    
        local_pos_bar, local_max = _positions_within_only(nWithin)
    
        for g in range(nGroups):
            ax = axes[g]
            off_pos = np.zeros(nWithin)
            off_neg = np.zeros(nWithin)
    
            for nm in comp_names:
                vals = slice_group(mats[nm], g)
                pos_vals = np.clip(vals, 0, None)
                neg_vals = np.clip(vals, None, 0)
    
                ax.bar(local_pos_bar, pos_vals, 0.3, bottom=off_pos, color=colors[nm], edgecolor="none", zorder=1)
                ax.bar(local_pos_bar, neg_vals, 0.3, bottom=off_neg, color=colors[nm], edgecolor="none", zorder=1)
    
                off_pos += pos_vals
                off_neg += neg_vals
    
            if ylim is not None:
                ax.set_ylim(ylim[0], ylim[1])
            else:
                ax.set_ylim(-figmax, figmax)
    
            ax.axhline(0, color="black", linewidth=1)
            ax.set_xlim(0, local_max)
            ax.set_xticks(local_pos_bar)
            ax.set_xticklabels(within_labels, rotation=90)
            ax.set_title(group_labels[g])
            ax.yaxis.grid(color="gray", linestyle="dashed")
    
            if g == 0:
                ax.set_ylabel(label)
            else:
                ax.tick_params(axis="y", labelleft=False)
    
        if legend:
            proxies = [Patch(facecolor=colors[nm], edgecolor="none") for nm in comp_names]
            if isinstance(pos_legend, dict):
                fig.legend(proxies, comp_names, **pos_legend)
            else:
                fig.legend(proxies, comp_names, loc=pos_legend, ncol=1)
    
        fig.tight_layout()
        plt.savefig(self.folder_plots + "/" + fileName + ".pdf", bbox_inches="tight")
        plt.savefig(self.folder_plots + "/" + fileName + ".png", bbox_inches="tight", dpi=300)
        plt.show()

