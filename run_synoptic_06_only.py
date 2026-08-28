#!/usr/bin/env python3

import os
import sys
import gzip
import shutil
import subprocess
from datetime import datetime, timedelta

START_TIME = "060001"
GNU_NAMES = ["gnudata-11", "gnudata-22", "gnudata-33", "gnudata-44"]


def raw_name(date):
    return date + "-" + START_TIME + "-TLK-SYN.data"


def find_input(folder, date):
    raw = os.path.join(folder, raw_name(date))

    if os.path.exists(raw + ".gz"):
        return raw + ".gz"

    if os.path.exists(raw):
        return raw

    return None


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

        os.symlink(
            os.path.abspath(source),
            work_raw
        )

    return work_raw


def process_date(date, archive_dir, work_dir, results_dir, executable):
    print()
    print("==========", date, START_TIME, "==========")

    source = find_input(archive_dir, date)

    if source is None:
        print("Missing:", raw_name(date))
        return True

    day_dir = os.path.join(results_dir, date)
    os.makedirs(day_dir, exist_ok=True)

    # If all four outputs already exist, do not run this date again.
    all_done = True

    for channel in range(1, 5):
        output_name = (
            date + "-" + START_TIME +
            "-ch" + str(channel) + ".dat"
        )

        output_path = os.path.join(day_dir, output_name)

        if not os.path.exists(output_path):
            all_done = False

    if all_done:
        print("Already finished. Skipping.")
        return True

    clean_work(work_dir)

    work_raw = prepare_raw(source, work_dir)

    # Fortran needs the raw filename twice in "filename"
    file = open(os.path.join(work_dir, "filename"), "w")
    file.write(os.path.basename(work_raw) + "\n")
    file.write(os.path.basename(work_raw) + "\n")
    file.close()

    print("Running Fortran:", date, START_TIME)

    result = subprocess.run(
        [executable],
        cwd=work_dir
    )

    # Remove the temporary raw file/link
    if os.path.lexists(work_raw):
        os.remove(work_raw)

    if result.returncode != 0:
        print("Fortran failed.")
        return False

    # Save the four channel outputs with date and start time
    for channel in range(1, 5):
        gnu = os.path.join(
            work_dir,
            GNU_NAMES[channel - 1]
        )

        if not os.path.exists(gnu):
            print("Missing:", GNU_NAMES[channel - 1])
            return False

        output_name = (
            date + "-" + START_TIME +
            "-ch" + str(channel) + ".dat"
        )

        output_path = os.path.join(
            day_dir,
            output_name
        )

        shutil.copyfile(
            gnu,
            output_path
        )

    clean_work(work_dir)

    print("Finished:", date, START_TIME)
    return True


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python3 run_synoptic_06_only.py "
            "START_DATE END_DATE"
        )
        sys.exit(1)

    try:
        current = datetime.strptime(
            sys.argv[1],
            "%Y%m%d"
        )

        end = datetime.strptime(
            sys.argv[2],
            "%Y%m%d"
        )

    except ValueError:
        print("Dates must be YYYYMMDD")
        sys.exit(1)

    archive_dir = os.getcwd()

    # Separate work/results folders so this can run in parallel.
    work_dir = os.path.join(
        archive_dir,
        "synoptic_work_06"
    )

    results_dir = os.path.join(
        archive_dir,
        "synoptic_results_06"
    )

    executable = os.path.join(
        archive_dir,
        "a.out"
    )

    os.makedirs(
        work_dir,
        exist_ok=True
    )

    os.makedirs(
        results_dir,
        exist_ok=True
    )

    if not os.path.exists(executable):
        print("Cannot find:", executable)
        sys.exit(1)

    while current <= end:
        date = current.strftime("%Y%m%d")

        success = process_date(
            date,
            archive_dir,
            work_dir,
            results_dir,
            executable
        )

        if not success:
            print("Stopping so the problem can be checked.")
            sys.exit(1)

        current = current + timedelta(days=1)


main()
