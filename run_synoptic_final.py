#!/usr/bin/env python3

import os
import sys
import gzip
import shutil
import subprocess
from datetime import datetime, timedelta

START_TIMES = ["010001", "060001", "110001"]
GNU_NAMES = ["gnudata-11", "gnudata-22", "gnudata-33", "gnudata-44"]


def raw_name(date, start):
    return date + "-" + start + "-TLK-SYN.data"


def find_input(folder, date, start):
    raw = os.path.join(folder, raw_name(date, start))

    if os.path.exists(raw + ".gz"):
        return raw + ".gz"
    if os.path.exists(raw):
        return raw

    return None


def prepare_raw(source, work_dir):
    name = os.path.basename(source)

    if name.endswith(".gz"):
        name = name[:-3]

    work_raw = os.path.join(work_dir, name)

    if os.path.lexists(work_raw):
        os.remove(work_raw)

    if source.endswith(".gz"):
        print("Decompressing:", source)
        infile = gzip.open(source, "rb")
        outfile = open(work_raw, "wb")
        shutil.copyfileobj(infile, outfile)
        infile.close()
        outfile.close()
    else:
        print("Linking:", source)
        os.symlink(os.path.abspath(source), work_raw)

    return work_raw


def clean_work(work_dir):
    names = [
        "filename",
        "gnudata-11", "gnudata-22", "gnudata-33", "gnudata-44",
        "2500-data", "3330-data", "4996-data"
    ]

    for name in names:
        path = os.path.join(work_dir, name)
        if os.path.lexists(path):
            os.remove(path)


def append_file(source, destination):
    infile = open(source, "rb")
    outfile = open(destination, "ab")
    shutil.copyfileobj(infile, outfile)
    infile.close()
    outfile.close()


def extract_peaks(input_file, day_dir, channel):
    file = open(input_file, "r")
    lines = file.readlines()
    file.close()

    out2500 = open(
        os.path.join(day_dir, "peak_2500_ch" + str(channel) + ".dat"),
        "w"
    )
    out3330 = open(
        os.path.join(day_dir, "peak_3330_ch" + str(channel) + ".dat"),
        "w"
    )
    out4996 = open(
        os.path.join(day_dir, "peak_4996_ch" + str(channel) + ".dat"),
        "w"
    )

    # Go through the file one minute at a time
    for start in range(0, len(lines), 315):

        # Stop if there are not enough lines left for a complete minute
        if start + 314 >= len(lines):
            break

        # 2.5 MHz band

        first = lines[start].split()

        time = float(first[0])
        max_frequency = float(first[1])
        max_power = float(first[2])

        for i in range(start, start + 105):

            parts = lines[i].split()

            frequency = float(parts[1])
            power = float(parts[2])

            if power > max_power:
                max_power = power
                max_frequency = frequency

        out2500.write(str(time) + " " +
                      str(max_power) + " " +
                      str(max_frequency) + "\n")

        # 3.33 MHz band

        first = lines[start + 105].split()

        time = float(first[0])
        max_frequency = float(first[1])
        max_power = float(first[2])

        for i in range(start + 105, start + 210):

            parts = lines[i].split()

            frequency = float(parts[1])
            power = float(parts[2])

            if power > max_power:
                max_power = power
                max_frequency = frequency

        out3330.write(str(time) + " " +
                      str(max_power) + " " +
                      str(max_frequency) + "\n")

        # 4.996 MHz band

        first = lines[start + 210].split()

        time = float(first[0])
        max_frequency = float(first[1])
        max_power = float(first[2])

        for i in range(start + 210, start + 315):

            parts = lines[i].split()

            frequency = float(parts[1])
            power = float(parts[2])

            if power > max_power:
                max_power = power
                max_frequency = frequency

        out4996.write(str(time) + " " +
                      str(max_power) + " " +
                      str(max_frequency) + "\n")

    out2500.close()
    out3330.close()
    out4996.close()

def process_day(date, archive_dir, work_dir, results_dir, executable):
    print()
    print("==========", date, "==========")

    day_dir = os.path.join(results_dir, date)
    os.makedirs(day_dir, exist_ok=True)

    done_file = os.path.join(day_dir, "DONE")

    if os.path.exists(done_file):
        print("Already finished. Skipping.")
        return

    # Find the three input files
    inputs = []

    for start in START_TIMES:
        source = find_input(archive_dir, date, start)

        if source is None:
            print("Missing:", raw_name(date, start))
            return

        inputs.append(source)

    # Create four empty daily files
    combined = []

    for channel in range(1, 5):
        path = os.path.join(
            day_dir,
            date + "-0100-1600-ch" + str(channel) + ".dat"
        )

        file = open(path, "wb")
        file.close()
        combined.append(path)

    # Run the three 5-hour files
    for n in range(3):
        clean_work(work_dir)

        work_raw = prepare_raw(inputs[n], work_dir)

        # Fortran needs the raw filename twice in "filename"
        file = open(os.path.join(work_dir, "filename"), "w")
        file.write(os.path.basename(work_raw) + "\n")
        file.write(os.path.basename(work_raw) + "\n")
        file.close()

        print("Running Fortran:", date, START_TIMES[n])

        result = subprocess.run([executable], cwd=work_dir)

        # Remove only the temporary link/file
        if os.path.lexists(work_raw):
            os.remove(work_raw)

        if result.returncode != 0:
            print("Fortran failed.")
            return

        # Add the four Fortran outputs to the daily files
        for channel in range(4):
            gnu = os.path.join(work_dir, GNU_NAMES[channel])

            if not os.path.exists(gnu):
                print("Missing:", GNU_NAMES[channel])
                return

            append_file(gnu, combined[channel])
            os.remove(gnu)

        # Delete huge extra outputs
        for name in ["2500-data", "3330-data", "4996-data"]:
            path = os.path.join(work_dir, name)
            if os.path.exists(path):
                os.remove(path)

    # Extract peaks after all three files are combined
    print("Extracting peaks...")

    for channel in range(1, 5):
        extract_peaks(combined[channel - 1], day_dir, channel)

    # Marker saying this date finished successfully
    file = open(done_file, "w")
    file.write("finished\n")
    file.close()

    print("Finished:", date)


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 run_synoptic_simple_v2.py START_DATE END_DATE")
        sys.exit(1)

    try:
        current = datetime.strptime(sys.argv[1], "%Y%m%d")
        end = datetime.strptime(sys.argv[2], "%Y%m%d")
    except ValueError:
        print("Dates must be YYYYMMDD")
        sys.exit(1)

    archive_dir = os.getcwd()
    work_dir = os.path.join(archive_dir, "synoptic_work")
    results_dir = os.path.join(archive_dir, "synoptic_results")
    executable = os.path.join(archive_dir, "a.out")

    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    if not os.path.exists(executable):
        print("Cannot find:", executable)
        sys.exit(1)

    while current <= end:
        date = current.strftime("%Y%m%d")

        process_day(
            date,
            archive_dir,
            work_dir,
            results_dir,
            executable
        )

        current = current + timedelta(days=1)


main()
