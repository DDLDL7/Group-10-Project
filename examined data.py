import pandas as pd
import numpy as np
 
utilities = pd.read_csv('utilities.csv')
substations = pd.read_csv('substations.csv')
lines = pd.read_csv('lines.csv')

print(utilities)
print(substations)
print(lines)

print(utilities.info())
print(substations.info())
print(lines.info())

print(substations.head())
print(lines.head())
"""
print("Duplicate rows in utilities:", utilities.duplicated().sum())
print("Duplicate rows in substations:", substations.duplicated().sum())
print("Duplicate rows in lines:", lines.duplicated().sum())
"""

"""valid_substation_ids = set(substations['Substation ID'])
valid_utility_ids = set(utilities['Utility ID'])

bad_source = lines[~lines['Source Substation ID'].isin(valid_substation_ids)]
bad_dest = lines[~lines['Destination Substation ID'].isin(valid_substation_ids)]
bad_utility = lines[~lines['Utility ID'].isin(valid_utility_ids)]

print("Lines with invalid source substation:", len(bad_source))
print("Lines with invalid destination substation:", len(bad_dest))
print("Lines with invalid utility:", len(bad_utility))"""
