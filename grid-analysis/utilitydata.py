import pandas as pd

utilities = pd.read_csv('utilities.csv')
substations = pd.read_csv('substations.csv')
lines = pd.read_csv('lines.csv')


# attach region info to each line, using its source substation's region
lines_with_region = lines.merge(
    substations[['Substation ID', 'Region']],
    left_on='Source Substation ID',
    right_on='Substation ID',
    how='left'
)

# count lines per utility, per region
footprint = lines_with_region.groupby(['Utility ID', 'Region'])['Line ID'].count().reset_index()
footprint = footprint.rename(columns={'Line ID': 'Line Count'})

# bring in utility names instead of just IDs
footprint = footprint.merge(utilities[['Utility ID', 'Name']], on='Utility ID', how='left')

print(footprint.sort_values('Line Count', ascending=False))