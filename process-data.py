import pandas as pd
import numpy as np

location_df=pd.read_csv('data-raw/uscities.csv')
loc_df= location_df[location_df['population']>10000][['city','state_name','lat','lng']]
loc_df['city_state']=loc_df['city']+', '+loc_df['state_name']
loc_df.set_index('city_state', inplace=True)
loc_df.drop(['city','state_name'], axis=1, inplace=True)
loc_df.to_csv('data/cities.csv')

