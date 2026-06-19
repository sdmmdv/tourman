import subprocess
import pandas as pd

# Execute the print-table.py script and capture the output
output = subprocess.check_output(['./print-table.py', '-t', 'standings']).decode('utf-8')

# Process the output string to extract the table data
output_lines = output.strip().split('\n')
output_table = [line.strip().split('|')[1:-1] for line in output_lines[2:]]

# Convert the output table to a pandas DataFrame
df = pd.DataFrame(output_table, columns=['rank', 'name', 'matches', 't2', 't1', 'points'])

# Export the DataFrame to an Excel file
df.to_excel('output.xlsx', index=False)
