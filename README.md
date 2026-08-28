# toolik-synoptic-analysis
Python programs for processing Toolik synoptic radio data

## Project Overview

The goal of this project is to process Toolik synoptic radio data and study signal power near three frequencies:

- 2.500 MHz
- 3.330 MHz
- 4.996 MHz

The data contain four receiver channels.

Each date is divided into three 5-hour SYN files:

- `YYYYMMDD-010001-TLK-SYN.data`
- `YYYYMMDD-060001-TLK-SYN.data`
- `YYYYMMDD-110001-TLK-SYN.data`

Together, these cover approximately 01–16 UT.

The normal chronological order is:

`01 -> 06 -> 11`

---

# Programs

## `run_synoptic_final.py`

This is the main full-day processing program.

For every date in a selected date range, it looks for all three SYN files:

- `010001`
- `060001`
- `110001`

The program processes them in the order:

`01 -> 06 -> 11`

For each 5-hour file, the Python program:

1. Finds the `.data` or `.data.gz` input file.
2. Decompresses the file if necessary.
3. Creates the text file called `filename` required by the Fortran program.
4. Runs the precompiled Fortran program `a.out`.
5. Collects the four Fortran outputs:
   - `gnudata-11`
   - `gnudata-22`
   - `gnudata-33`
   - `gnudata-44`
6. Adds the output from each 5-hour section to a daily file for each channel.
7. After all three sections are processed, extracts the maximum-power point near:
   - 2.500 MHz
   - 3.330 MHz
   - 4.996 MHz

### Run

```bash
python3 run_synoptic_final.py START_DATE END_DATE
```

Example:

```bash
python3 run_synoptic_final.py 20200927 20201026
```

Dates must be written as:

`YYYYMMDD`

### Main output directory

The program creates:

```text
synoptic_results/
```

with a separate folder for each date.

Example:

```text
synoptic_results/
    20200927/
```

### Combined channel files

A complete date produces four combined 15-hour channel files:

```text
20200927-0100-1600-ch1.dat
20200927-0100-1600-ch2.dat
20200927-0100-1600-ch3.dat
20200927-0100-1600-ch4.dat
```

### Peak files

The program produces one peak file for each frequency and channel.

Example:

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

Each peak file contains three columns:

```text
time   maximum_power   frequency_of_maximum_power
```

When a date finishes successfully, the program also creates a file called:

```text
DONE
```

---

## `run_synoptic_06_only.py`

This program processes only the 5-hour SYN files beginning at 06 UT:

```text
YYYYMMDD-060001-TLK-SYN.data
```

It was created so that the 06 files can be processed independently and in parallel with other processing.

### Run

```bash
python3 run_synoptic_06_only.py START_DATE END_DATE
```

Example:

```bash
python3 run_synoptic_06_only.py 20200927 20201026
```

### Work directory

```text
synoptic_work_06/
```

### Results directory

```text
synoptic_results_06/
```

Each date gets its own folder.

Example output:

```text
synoptic_results_06/
    20200927/
        20200927-060001-ch1.dat
        20200927-060001-ch2.dat
        20200927-060001-ch3.dat
        20200927-060001-ch4.dat
```

These are intermediate 5-hour channel files. They are not final daily peak files.

---

## `run_synoptic_11_only.py`

This program processes only the 5-hour SYN files beginning at 11 UT:

```text
YYYYMMDD-110001-TLK-SYN.data
```

It works in the same way as the 06-only program.

### Run

```bash
python3 run_synoptic_11_only.py START_DATE END_DATE
```

Example:

```bash
python3 run_synoptic_11_only.py 20200927 20201026
```

### Work directory

```text
synoptic_work_11/
```

### Results directory

```text
synoptic_results_11/
```

Example output:

```text
synoptic_results_11/
    20200927/
        20200927-110001-ch1.dat
        20200927-110001-ch2.dat
        20200927-110001-ch3.dat
        20200927-110001-ch4.dat
```

These are also intermediate 5-hour channel files.

---

# Required Files

The Python programs expect the precompiled Fortran executable:

```text
a.out
```

to be located in the directory where the Python program is started.

The SYN input files should also be available from that directory.

The programs accept either:

```text
.data
```

or compressed:

```text
.data.gz
```

files.

---

# Fortran Outputs

For each SYN file, the Fortran program is expected to create:

```text
gnudata-11
gnudata-22
gnudata-33
gnudata-44
```

These correspond to the four receiver channels.

The Python programs also remove the large temporary outputs:

```text
2500-data
3330-data
4996-data
```

after processing.

---

# Parallel Processing Workflow

Because processing each 5-hour SYN file takes a long time, the three time sections can be processed separately.

For one date:

```text
01 section
+
06 section
+
11 section
```

The 06-only and 11-only programs use separate work directories, allowing them to run independently from the main processing job.

Once all three sections for a date are available, they should be combined in chronological order:

```text
01 -> 06 -> 11
```

The resulting 15-hour channel files can then be used for peak extraction.

---

# Peak Extraction

For every minute of data, the program searches three frequency regions:

```text
2.500 MHz
3.330 MHz
4.996 MHz
```

For each region, it selects the frequency bin with the highest power.

The output contains:

```text
time   maximum_power   frequency_of_maximum_power
```

This is done separately for all four channels.

---

# Current Processing Workflow

The current workflow is:

```text
Raw SYN files
      |
      v
Fortran processing
      |
      v
Four channel outputs
      |
      v
Combine 01 + 06 + 11
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
Multi-day analysis and plotting
```

---

# Known Issue With the Main Full-Day Program

The current full-day program is intended to process:

```text
01 -> 06 -> 11
```

before moving to the next date.

However, if the Fortran program fails or one of the expected `gnudata` files is missing, the current version returns from that date and the outer date loop can continue to the next date.

This can make the processing appear to run:

```text
date 1 - 01
date 2 - 01
date 3 - 01
```

instead of completing all three sections of each date.

When running the program, check the terminal output for messages such as:

```text
Fortran failed.
```

or:

```text
Missing: gnudata-XX
```

This behavior should be considered when restarting or troubleshooting long processing runs.

---

# Current Research Period

Initial detailed analysis was performed for:

```text
September 21–25, 2020
```

Additional processing is being performed beginning around:

```text
September 27, 2020
```

with the goal of building approximately 30 continuous days of data for multi-day analysis.

September 26 can be processed separately to connect the two periods.

---
