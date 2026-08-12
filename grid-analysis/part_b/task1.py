import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV files
utilities = pd.read_csv('utilities.csv')
substations = pd.read_csv('substations.csv')
lines = pd.read_csv('lines.csv')

# Inspect the Utilities dataset
print("Utilities DataFrame Info:")
print(utilities.info(), "\n")

print("Utilities First 5 Rows:")
print(utilities.head(), "\n")

# Inspect the Substations dataset
print("Substations DataFrame Info:")
print(substations.info(), "\n")

print("Substations First 5 Rows:")
print(substations.head(), "\n")

# Inspect the Lines dataset
print("Lines DataFrame Info:")
print(lines.info(), "\n")

print("Lines First 5 Rows:")
print(lines.head(), "\n")


# task 2
# Check for missing values
print("Missing Values in Utilities:")
print(utilities.isnull().sum(), "\n")

print("Missing Values in Substations:")
print(substations.isnull().sum(), "\n")

print("Missing Values in Lines:")
print(lines.isnull().sum(), "\n")

# Convert columns to numeric data types
substations['Latitude'] = pd.to_numeric(substations['Latitude'], errors='coerce')
substations['Longitude'] = pd.to_numeric(substations['Longitude'], errors='coerce')
substations['Capacity (MVA)'] = pd.to_numeric(substations['Capacity (MVA)'], errors='coerce')
lines['Length (km)'] = pd.to_numeric(lines['Length (km)'], errors='coerce')

# Check for duplicate rows
print("Duplicate Rows in Utilities:", utilities.duplicated().sum())
print("Duplicate Rows in Substations:", substations.duplicated().sum())
print("Duplicate Rows in Lines:", lines.duplicated().sum())

# Remove duplicate rows
utilities = utilities.drop_duplicates()
substations = substations.drop_duplicates()
lines = lines.drop_duplicates()

# Verify the cleaned data
print("\nAfter Cleaning - Substations Info:")
print(substations.info(), "\n")


# task 3


# Distribution of substations by region
plt.figure(figsize=(10, 6))
substations['Region'].value_counts().head(10).plot(
    kind='bar',
    title='Top Regions by Number of Substations'
)
plt.xlabel('Region')
plt.ylabel('Number of Substations')
plt.tight_layout()
plt.savefig('eda_regions.png')
plt.show()


plt.figure(figsize=(10, 6))
lines['Source Substation'].value_counts().head(10).plot(
    kind='bar',
    title='Top 10 Source Substations by Number of Lines'
)
plt.xlabel('Substation')
plt.ylabel('Number of Lines')
plt.tight_layout()
plt.savefig('eda_top_substations.png')
plt.show()


print("Substations Numeric Summary:")
print(substations[
    ['Latitude', 'Longitude', 'Voltage (kV)', 'Capacity (MVA)']
].describe(), "\n")


print("Substation Status Count:")
print(substations['Status'].value_counts(), "\n")
