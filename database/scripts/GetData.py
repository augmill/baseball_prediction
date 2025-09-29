from pybaseball import statcast
import pandas as pd
from multipledispatch import dispatch
import sys

def main(start_date, end_date, file_path):
    # Fetch data from statcast
    data = statcast(start_dt=start_date, end_dt=end_date)
    # Save to CSV
    data.to_csv(file_path, index=False)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python GetData.py <start_date> <end_date> <file_path>")
        sys.exit(1)
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    file_path = sys.argv[3]
    main(start_date, end_date, file_path)