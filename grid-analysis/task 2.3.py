import sys
print(sys.executable)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

REFERENCE_YEAR = 2026   # ages computed "as of" 2026 — documented assumption

# 1. Load + sanity check
substations = pd.read_csv('substations.csv')
print(substations[['Name', 'Region', 'Commissioning Year']].head())
print(substations['Commissioning Year'].dtype)   # confirm it's int/float, not object

# 2. Derive age
substations['age'] = REFERENCE_YEAR - substations['Commissioning Year']
print(substations['age'].describe())   # sane range? no negatives?

# 3. Band it
bins   = [0, 20, 40, np.inf]
labels = ['Modern', 'Mature', 'Legacy']
substations['age_band'] = pd.cut(substations['age'], bins=bins, labels=labels)

# 4. Group by region
age_by_region = (substations
                 .groupby('Region')['age']
                 .agg(['mean', 'median', 'count'])
                 .sort_values('mean', ascending=False))
print(age_by_region)

# 5. Plot — mean age by region
age_by_region['mean'].plot(kind='bar', figsize=(10, 6),
                           title='Mean Substation Age by Region (as of 2026)')
plt.ylabel('Mean age (years)')
plt.tight_layout()
plt.savefig('age_by_region.png')
plt.show()