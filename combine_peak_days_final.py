#!/usr/bin/env python3

import os
from datetime import datetime

main_folder = os.path.dirname(os.path.abspath(__file__))
peak_folder = os.path.join(main_folder, "peak_files")
output_folder = os.path.join(main_folder, "big_peak_files")

frequencies = ["2500", "3330", "4996"]
channels = [1, 2, 3, 4]

if not os.path.isdir(peak_folder):
    print("Cannot find:", peak_folder)
    raise SystemExit

os.makedirs(output_folder, exist_ok=True)
file_names = os.listdir(peak_folder)

# Get each date from the last 8 digits before .dat.
dates = []
for name in file_names:
    if name.startswith("peak_") and name.endswith(".dat"):
        date_number = name[-12:-4]
        if date_number not in dates:
            dates.append(date_number)

dates.sort()

# Make one large file for each frequency and channel.
for frequency in frequencies:
    for channel in channels:
        output_name = f"all_peak_{frequency}_ch{channel}.dat"
        output_path = os.path.join(output_folder, output_name)
        outfile = open(output_path, "w")
        outfile.write("# date day_of_year time_UT signal_power\n")

        for date_number in dates:
            input_name = f"peak_{frequency}_ch{channel}_{date_number}.dat"
            input_path = os.path.join(peak_folder, input_name)

            # 900 positions: one for every minute from 01:01 to 16:00.
            powers = [float("nan")] * 900

            if os.path.exists(input_path):
                infile = open(input_path, "r")

                for line in infile:
                    parts = line.split()
                    if len(parts) < 2:
                        continue

                    try:
                        time = float(parts[0])
                        power = float(parts[1])
                    except ValueError:
                        continue

                    # Round each input time to the nearest minute.
                    position = round(time * 60) - 61
                    if 0 <= position < 900:
                        powers[position] = power

                infile.close()

            date = datetime.strptime(date_number, "%Y%m%d")
            normal_date = date.strftime("%d-%m-%Y")
            day_of_year = date.timetuple().tm_yday

            for position in range(900):
                time = 1.0 + (position + 1) / 60.0
                power = powers[position]
                outfile.write(
                    f"{normal_date} {day_of_year}.0 {time:.6f} {power}\n"
                )

            outfile.write("\n")

        outfile.close()
        print("Created:", output_path)
