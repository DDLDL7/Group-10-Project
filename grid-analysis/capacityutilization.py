import pandas as pd

substations = pd.read_csv('substations.csv')

active = substations[substations['Status'] == 'Active'].copy()

total_capacity = active['Capacity (MVA)'].sum()
active['national_share_%'] = active['Capacity (MVA)'] / total_capacity * 100

top_national = (active
                .sort_values('Capacity (MVA)', ascending=False)
                [['Name', 'Region', 'Capacity (MVA)', 'national_share_%']]
                .head(10))
print("Top 10 substations by national capacity share:")
print(top_national.round(2), "\n")

region_totals = active.groupby('Region')['Capacity (MVA)'].transform('sum')
active['regional_share_%'] = active['Capacity (MVA)'] / region_totals * 100

top_regional = (active
                .sort_values('regional_share_%', ascending=False)
                [['Name', 'Region', 'Capacity (MVA)', 'regional_share_%']]
                .head(10))
print("Top 10 substations by share of their own region's capacity:")
print(top_regional.round(2), "\n")

active['concentration_risk'] = active['regional_share_%'] >= 50
print("Substations carrying 50%+ of their region's capacity (single-point risk):")
print(active[active['concentration_risk']]
      [['Name', 'Region', 'Capacity (MVA)', 'regional_share_%']].round(2))