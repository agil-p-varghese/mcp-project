
import pandas as pd

df = pd.read_csv("datasets/SuperKart.csv")

# Exclude allocated area
df = df.drop(columns=["Product_Allocated_Area"])

print("Dataset Shape:", df.shape)

print("\nColumn Names:")
print(df.columns.tolist())

print("\nMissing Values:")
print(df.isnull().sum())

print("\nDistinct Store IDs:")
print(df["Store_Id"].unique())

print("\nProduct Categories:")
print(df["Product_Type"].unique())

print("\nData Types:")
print(df.dtypes)
