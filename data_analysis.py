import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_context("notebook", font_scale=1.5)
# Load the CSV file
df = pd.read_csv('PID Response2.csv')
# CORRECT WAY:
df.iloc[:, 2] = -1 * df.iloc[:, 2]

# Calculate how many rows to keep (first half)
half_rows = len(df) // 2

# Filter to keep only the second half of rows
# df = df.iloc[half_rows:]

# Create a lineplot using only the first and third columns
plt.figure(figsize=(10, 6))
sns.lineplot(x=df.iloc[:, 0], y=df.iloc[:, 2])

# Add labels and title
plt.xlabel("Time")
plt.ylabel("Position")
plt.title('PID Position Response Curve')

plt.axhline(y=-248, color='r', linestyle='--', label='y=320')

# print(df_half.iloc[:, 0].dtype)
# print(df_half.iloc[:, 1].dtype)

# print(df_half.iloc[:, 0].isna().sum())
# print(df_half.iloc[:, 1].isna().sum())

# print(df_half.iloc[:, 0].nunique())

# Show the plot
plt.tight_layout()
plt.show()