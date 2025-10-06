"""
Used by GetData.sh to pull raw statcast data from pybaseball
"""
from pybaseball import statcast
import sys

if len(sys.argv) != 4:
    print("Usage: python3 ./GetData.py <start_date> <end_date> <file_path>")
    sys.exit(1)

start_date = sys.argv[1]
end_date = sys.argv[2]
file_path = sys.argv[3]

try:
    statcast(start_dt=start_date, end_dt=end_date).to_csv(file_path)
except Exception as e:
    print(e)
    print(f"Error: failed to pull data for {start_date} to {end_date}")
    sys.exit(1)




