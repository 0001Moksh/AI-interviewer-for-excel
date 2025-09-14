import pandas as pd

# Load Excel file
df = pd.read_excel("questions/interview_questions.xlsx")  # replace with your file path

# Total number of records (rows)
total_records = len(df)
print(f"Total records in Excel: {total_records}")

# Optional: count records per column if needed
for col in df.columns:
    non_empty = df[col].notna().sum()
    print(f"Column '{col}' has {non_empty} non-empty records")
