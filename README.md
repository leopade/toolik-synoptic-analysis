# Toolik Synoptic Radio Analysis

Python tools for processing and analyzing Toolik synoptic HF radio data for a Space Physics research project.

## Project Overview

This project processes long-duration Toolik radio observations in order to study the behavior of signals near three HF frequencies:

- 2.500 MHz
- 3.330 MHz
- 4.996 MHz

The data contain four receiver channels.

The main goal is to turn the original large SYN data files into much smaller time series containing the strongest signal near each of the three frequencies. These daily peak files can then be combined across many days and compared with geomagnetic activity using the Kp index.

The general workflow is:

```text
Raw SYN data
     |
     v
Fortran processing
     |
     v
Frequency/power output for four channels
     |
     v
Combine the 01, 06, and 11 UT sections
     |
     v
15-hour daily channel files
     |
     v
Peak extraction
     |
     v
Daily peak files
     |
     v
Combine daily peak files across many dates
     |
     v
Multi-day peak files
     |
     +--------------------+
     |                    |
     v                    v
Radio peak data       Daily Kp sums
     |                    |
     +---------+----------+
               |
               v
          Make plots
```

---

# Raw Data Organization

Each date is represented by three SYN files covering consecutive 5-hour periods.

The filenames have the form:

```text
YYYYMMDD-010001-TLK-SYN.data
YYYYMMDD-060001-TLK-SYN.data
YYYYMMDD-110001-TLK-SYN.data
```

For example:

```text
20200927-010001-TLK-SYN.data
20200927-060001-TLK-SYN.data
20200927-110001-TLK-SYN.data
```

The three files are processed chronologically in the order:

```text
01 -> 06 -> 11
```

Together they cover 01–16 UT.

The input files are compressed:

```text
.data.gz
```

The Python programs looks for compressed files, however it can also process already uncompressed files.

---

# Fortran Processing

The Python programs call an already-compiled Fortran executable:

```text
a.out
```

The Python programs do not compile the Fortran code.

Before running `a.out`, Python creates a small text file called:

```text
filename
```

The raw SYN filename is written into this file twice because that is the input format expected by the Fortran program.

For each SYN file, the Fortran program is expected to create four main channel outputs:

```text
gnudata-11
gnudata-22
gnudata-33
gnudata-44
```

These correspond to the four receiver channels.

The Fortran program also creates large temporary files:

```text
2500-data
3330-data
4996-data
```

The current Python programs remove these after processing because they are not needed for the final peak analysis.

---

# Current Programs

At the moment, the repository contains three production-processing programs.

## `run_synoptic_final_with_dates.py`

This is the main full-day processing program.

It processes all three 5-hour SYN files for each requested date.

The intended order is:

```text
010001
   |
   v
060001
   |
   v
110001
```

Only after these three sections are processed should a complete daily result be available.

### What the program does

For each date, the program:

1. Checks that the `010001`, `060001`, and `110001` input files exist.
2. Creates a results directory for the date.
3. Processes the `010001` file with the Fortran program.
4. Processes the `060001` file.
5. Processes the `110001` file.
6. Appends the four channel outputs in chronological order.
7. Produces one combined 15-hour file for each channel.
8. Extracts the strongest signal near 2.500, 3.330, and 4.996 MHz.
9. Writes the daily peak files.
10. Creates a `DONE` file when the complete date finishes.

### Run the program

```bash
python3 run_synoptic_final_with_dates.py START_DATE END_DATE
```

Dates must use the format:

```text
YYYYMMDD
```

### Work directory

Temporary files are placed in:

```text
synoptic_work/
```

### Results directory

Finished results are placed in:

```text
synoptic_results/
```

with one folder for each date.

Example:

```text
synoptic_results/
└── 20200927/
```

### Combined channel files

A successfully completed date produces:

```text
20200927-0100-1600-ch1.dat
20200927-0100-1600-ch2.dat
20200927-0100-1600-ch3.dat
20200927-0100-1600-ch4.dat
```

Each file contains the processed data for one receiver channel over the full approximately 15-hour period.

### Peak files

For every channel, the program produces a peak file for each of the three frequencies.

For example:

```text
peak_2500_ch1_20200927.dat
peak_2500_ch2_20200927.dat
peak_2500_ch3_20200927.dat
peak_2500_ch4_20200927.dat

peak_3330_ch1_20200927.dat
peak_3330_ch2_20200927.dat
peak_3330_ch3_20200927.dat
peak_3330_ch4_20200927.dat

peak_4996_ch1_20200927.dat
peak_4996_ch2_20200927.dat
peak_4996_ch3_20200927.dat
peak_4996_ch4_20200927.dat
```

### Peak file columns

Each peak file contains three columns:

```text
time   maximum_power   frequency_of_maximum_power
```

### DONE file

When all processing and peak extraction for a date completes, the program creates:

```text
DONE
```

If the program is run again and a date already contains `DONE`, that date is skipped.

---

# Peak Extraction Method

The peak extraction is performed separately for every receiver channel.

The processed data are read in groups of:

```text
315 rows
```

Each group is divided into:

```text
rows   1–105     -> 2.500 MHz region
rows 106–210     -> 3.330 MHz region
rows 211–315     -> 4.996 MHz region
```

For each region, the program starts with the first point and then checks every other point in that region.

Whenever a larger power value is found, it saves:

```text
new maximum power
new corresponding frequency
```

At the end of the region, one peak point is written to the appropriate output file.

The result is therefore not simply the power at exactly 2.500, 3.330, or 4.996 MHz. Instead, it is the highest-power frequency bin within the search region around that nominal frequency. This allows small frequency shifts in the observed signal to be retained.

---

# `combine_peak_days_final.py`

This program combines many daily peak files into larger multi-day files for plotting and comparison.

It is intended to be used after the daily peak files have already been created.

## Input folder

The program expects a folder called:

```text
peak_files/
```

in the same directory as the Python program.

The daily peak files inside this folder must contain the date in the filename.

Example filenames:

```text
peak_2500_ch1_20200927.dat
peak_3330_ch2_20200927.dat
peak_4996_ch4_20200927.dat
```

The last 8 digits before `.dat` are interpreted as the date in:

```text
YYYYMMDD
```

format.

The program finds all available dates automatically and sorts them chronologically.

## Frequencies and channels

The program processes the three frequencies:

```text
2500
3330
4996
```

and all four receiver channels:

```text
1
2
3
4
```

This produces 12 combined output files.

## Output folder

The program creates:

```text
big_peak_files/
```

if it does not already exist.

The output files are named:

```text
all_peak_2500_ch1.dat
all_peak_2500_ch2.dat
all_peak_2500_ch3.dat
all_peak_2500_ch4.dat

all_peak_3330_ch1.dat
all_peak_3330_ch2.dat
all_peak_3330_ch3.dat
all_peak_3330_ch4.dat

all_peak_4996_ch1.dat
all_peak_4996_ch2.dat
all_peak_4996_ch3.dat
all_peak_4996_ch4.dat
```

Each file contains one frequency and one receiver channel across all available dates.

For example:

```text
all_peak_3330_ch2.dat
```

contains the 3.330 MHz peak-power data from channel 2 for every date found in `peak_files/`.

## Daily time grid

For every date, the program creates exactly:

```text
900 time positions
```

corresponding to one-minute steps from approximately:

```text
01:01 UT -> 16:00 UT
```

Each day is first filled with:

```text
nan
```

values.

The daily peak file is then read and the measured power values are placed into the appropriate one-minute positions.

If a minute does not contain a valid measurement, the value remains:

```text
nan
```

This keeps all dates aligned to the same time grid.

## Daily peak-file columns

The program reads:

```text
column 1 = time
column 2 = signal power
```

from each daily peak file.

The third column of the daily peak files, which contains the frequency of the maximum-power point, is not used by this program.

## Output format

Each output file begins with:

```text
# date day_of_year time_UT signal_power
```

Each row then contains:

```text
date   day_of_year   time_UT   signal_power
```

Example:

```text
27-09-2020 271.0 1.016667 -102.4
27-09-2020 271.0 1.033333 -101.8
27-09-2020 271.0 1.050000 -100.9
```

A blank line is written between dates.

This makes the files convenient for multi-day plotting in Gnuplot.

## Run

```bash
python3 combine_peak_days_final.py
```

The program does not require start and end dates.

It automatically uses all valid dated peak files found in:

```text
peak_files/
```

# `sum_daily_kp_01_16.py`

This program prepares daily Kp-index values for comparison with the Toolik radio observations.

The radio data used in this project cover approximately:

```text
01:00–16:00 UT
```

Kp is reported in 3-hour intervals. Because the radio observing period does not line up exactly with the Kp intervals, the program uses the six Kp bins that overlap the 01–16 UT radio period:

```text
00–03 UT
03–06 UT
06–09 UT
09–12 UT
12–15 UT
15–18 UT
```

The program sums these six Kp values for each date.

This gives one daily geomagnetic-activity value that can be compared with the 01–16 UT radio data.

## Input file

The program expects:

```text
Kp_ap_20200829_20201023.dat
```
The Kp input data used for this project come from the **GFZ Helmholtz Centre for Geosciences Kp index service**:

- Kp website: https://kp.gfz.de/en/
- Data download page: https://kp.gfz.de/en/data

The input data must contain the date, the starting hour of the Kp interval, and the Kp value in the columns expected by the script.

## Output file

The program creates:

```text
daily_kp_sum_01_16.dat
```

The output begins with:

```text
# Date DOY Kp_sum_01_16
```

Each following row contains:

```text
date   day_of_year   summed_Kp
```

For example, the format is:

```text
2020-09-27 271 8.667
```

The exact value above is only an example of the file format.

A date is written only when all six selected 3-hour Kp values are present. If a date does not contain six selected Kp values, the program prints a warning.

## Run

```bash
python3 sum_daily_kp_01_16.py
```

# Plotting the Final Data

After running:

```text
combine_peak_days_final.py
```

the radio data are available in the 12 files:

```text
big_peak_files/all_peak_2500_ch1.dat
...
big_peak_files/all_peak_4996_ch4.dat
```

After running:

```text
sum_daily_kp_01_16.py
```

the daily geomagnetic activity is available in:

```text
daily_kp_sum_01_16.dat
```

These files can then be plotted with a plotting program.

Possible plots include:

- multi-day heat maps of signal power versus UT and day of year
- hidden-line or stacked daily plots
- comparisons among the four receiver channels
- comparisons among 2.500, 3.330, and 4.996 MHz
- radio peak-power plots with the daily 01–16 UT Kp sum shown underneath

The exact plotting style can be changed depending on which feature of the data is being investigated.

---

# Complete Analysis Workflow

The current analysis procedure is:

```text
1. Raw Toolik SYN files
        |
        v
2. run_synoptic_final_with_dates.py
        |
        +--> process 01, 06, and 11 UT SYN files
        +--> combine them into 01–16 UT channel files
        +--> extract peaks around 2.500, 3.330, and 4.996 MHz
        |
        v
3. Dated daily peak files
        |
        v
4. Place the required daily peak files in peak_files/
        |
        v
5. combine_peak_days_final.py
        |
        v
6. 12 multi-day all_peak_*.dat files

Separately:

7. Kp input data
        |
        v
8. sum_daily_kp_01_16.py
        |
        v
9. daily_kp_sum_01_16.dat

Finally:

10. Plot the radio data and Kp data
        |
        v
11. Compare frequency, channel, time-of-day, and geomagnetic behavior
```
