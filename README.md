# Toolik Synoptic Radio Analysis

Python tools for processing and analyzing Toolik synoptic HF radio data for the LaBelle Space Physics research project.

## Project Overview

This project processes long-duration Toolik radio observations in order to study the behavior of signals near three HF frequencies:

- 2.500 MHz
- 3.330 MHz
- 4.996 MHz

The data contain four receiver channels.

The main goal is to turn the original large SYN data files into much smaller time series containing the strongest signal near each of the three frequencies. These daily peak files can then be combined across many days and compared with quantities such as auroral activity.

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
Multi-day plots and comparison with auroral activity
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

Together they cover approximately 01–16 UT.

The input files may either be uncompressed:

```text
.data
```

or compressed:

```text
.data.gz
```

The Python programs automatically look for both versions.

---

# Data Structure

A full 5-hour SYN file contains 4-channel radio data.

In the current processing setup:

- one SYN file covers 5 hours
- the raw data contain 4 interleaved channels
- the data are organized in 4-second blocks
- a complete 5-hour file contains 4,500 such blocks
- the Fortran processing averages groups of blocks before producing the frequency/power output

The Python peak-extraction method expects the processed channel files to be organized in repeating groups of 315 rows:

```text
105 rows near 2.500 MHz
105 rows near 3.330 MHz
105 rows near 4.996 MHz
```

Therefore:

```text
315 rows = one output time step
```

For each group, the Python program searches each 105-row frequency region and records the point with the highest power.

A normally completed 5-hour processed channel file is expected to contain approximately:

```text
94,500 rows
```

Three 5-hour sections combined into one full 15-hour day therefore contain approximately:

```text
283,500 rows per channel
```

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

## `run_synoptic_final.py`

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
python3 run_synoptic_final.py START_DATE END_DATE
```

Example:

```bash
python3 run_synoptic_final.py 20200927 20201026
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

The date is included in the filename so that files from multiple days can later be collected in the same folder without losing track of their dates.

### Peak file columns

Each peak file contains three columns:

```text
time   maximum_power   frequency_of_maximum_power
```

For example, for the 3.330 MHz file, each row represents one time step and contains:

1. time
2. highest power found in the 3.330 MHz search region
3. frequency at which that maximum power occurred

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

The result is therefore not simply the power at exactly 2.500, 3.330, or 4.996 MHz.

Instead, it is:

> the highest-power frequency bin within the search region around that nominal frequency.

This allows small frequency shifts in the observed signal to be retained.

---

# `run_synoptic_06_only.py`

This program processes only the 5-hour files beginning at 06 UT:

```text
YYYYMMDD-060001-TLK-SYN.data
```

It was created to allow the very long Fortran processing to be distributed across multiple computers.

Unlike the full-day program, it does not combine a complete day and does not perform the final daily peak extraction.

It saves the four Fortran channel outputs from the 06 UT section so they can later be combined with the corresponding 01 and 11 UT sections.

### Run

```bash
python3 run_synoptic_06_only.py START_DATE END_DATE
```

Example:

```bash
python3 run_synoptic_06_only.py 20200927 20201026
```

### Work directory

The program uses its own work directory:

```text
synoptic_work_06/
```

This is intentionally separate from the main program's:

```text
synoptic_work/
```

### Results directory

Results are stored in:

```text
synoptic_results_06/
```

Example:

```text
synoptic_results_06/
└── 20200927/
    ├── 20200927-060001-ch1.dat
    ├── 20200927-060001-ch2.dat
    ├── 20200927-060001-ch3.dat
    └── 20200927-060001-ch4.dat
```

These are intermediate 5-hour files, not final peak files.

### Restart behavior

Before processing a date, the program checks whether all four expected channel output files already exist.

If all four exist, it prints:

```text
Already finished. Skipping.
```

and moves to the next date.

If the Fortran program fails or an expected `gnudata` file is missing, this program stops so that the problem can be checked.

---

# `run_synoptic_11_only.py`

This program is the equivalent of the 06-only program for the final 5-hour section of each date.

It processes:

```text
YYYYMMDD-110001-TLK-SYN.data
```

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

Example:

```text
synoptic_results_11/
└── 20200927/
    ├── 20200927-110001-ch1.dat
    ├── 20200927-110001-ch2.dat
    ├── 20200927-110001-ch3.dat
    └── 20200927-110001-ch4.dat
```

As with the 06-only program, these are intermediate 5-hour channel outputs.

The program also skips dates whose four output files already exist and stops if the Fortran run fails or an expected channel output is missing.

---

# Parallel Processing

A single complete date requires three expensive Fortran calculations:

```text
01 UT section
06 UT section
11 UT section
```

Because the calculations take a long time, the processing was split so that different computers can work on different time sections.

For example:

```text
Computer 1
    |
    └── 01 processing / main processing

Computer 2
    |
    └── 06 processing
```

The first computer can later be switched to the 11-only program.

The separate programs use different work directories:

```text
synoptic_work/
synoptic_work_06/
synoptic_work_11/
```

and different results directories:

```text
synoptic_results/
synoptic_results_06/
synoptic_results_11/
```

This prevents the Python programs from deleting or overwriting each other's temporary files.

The purpose of the separate processing is only to create the individual 5-hour pieces more quickly.

A scientifically complete day still requires:

```text
01 + 06 + 11
```

---

# Combining Separately Processed Sections

When separate processing is used, a complete date will eventually have four channel files for each start time.

For channel 2, for example:

```text
01 section
20200927-010001-ch2.dat

06 section
20200927-060001-ch2.dat

11 section
20200927-110001-ch2.dat
```

The files must be combined in exactly this order:

```text
01 -> 06 -> 11
```

The same operation is performed independently for channels 1, 2, 3, and 4.

The resulting complete files should represent approximately 01–16 UT.

A separate combining program is currently being developed and tested.

It will be added to this repository after the workflow has been verified with real output data.

---

# Directory Layout

A typical working directory may look like:

```text
data_directory/
│
├── a.out
│
├── run_synoptic_final.py
├── run_synoptic_06_only.py
├── run_synoptic_11_only.py
│
├── 20200927-010001-TLK-SYN.data.gz
├── 20200927-060001-TLK-SYN.data.gz
├── 20200927-110001-TLK-SYN.data.gz
│
├── synoptic_work/
├── synoptic_work_06/
├── synoptic_work_11/
│
├── synoptic_results/
├── synoptic_results_06/
└── synoptic_results_11/
```

The large original SYN files and processed data files are not intended to be stored in this GitHub repository.

GitHub is being used primarily to preserve:

- source code
- documentation
- processing instructions
- small sample outputs
- example plots

---

# Important Error Messages

## `Cannot find: a.out`

The Python program cannot find the compiled Fortran program.

Make sure:

```text
a.out
```

is in the directory from which the Python program is being run.

---

## `Missing: YYYYMMDD-...-TLK-SYN.data`

The expected raw input file cannot be found.

The programs check for both:

```text
.data
```

and:

```text
.data.gz
```

versions.

---

## `Fortran failed.`

The `a.out` process returned a nonzero exit status.

This indicates that the Fortran program did not terminate normally.

---

## `Missing: gnudata-XX`

The Fortran process ended, but one of the four expected channel outputs could not be found.

The expected outputs are:

```text
gnudata-11
gnudata-22
gnudata-33
gnudata-44
```

---

# Known Behavior of the Full-Day Program

The current full-day program is intended to process each date as:

```text
01 -> 06 -> 11
```

before moving to the next date.

However, the current version has an important behavior to keep in mind.

After a Fortran run, it checks:

1. whether the Fortran program returned successfully
2. whether each expected `gnudata` file exists

If one of those checks fails, the function processing the current date returns.

The outer date loop can then continue to the next date.

Because each new date starts at 01 UT, repeated failures after the first section can create an apparent sequence such as:

```text
Date 1 -> 01
Date 2 -> 01
Date 3 -> 01
```

This does not mean that the program was intentionally written to process all 01 files first.

It means the previous date may have been abandoned after its 01 section.

When diagnosing this behavior, check the terminal output immediately after a run for:

```text
Fortran failed.
```

or:

```text
Missing: gnudata-XX
```

The 06-only and 11-only programs were written to stop rather than continue through dates after these types of processing failures.

---

# Important Note About Full-Day Output Filenames

The full-day program creates its combined channel files at the beginning of processing a date.

For example:

```text
20200927-0100-1600-ch2.dat
```

The filename describes the intended complete daily product.

However, if processing stops after only the 01 section, that file may exist even though it does not yet contain the complete 01–16 UT day.

Therefore:

> The existence of a `YYYYMMDD-0100-1600-chX.dat` file by itself does not prove that the full day finished.

The `DONE` file is the stronger indication that the original full-day workflow completed successfully.

When working with files from an interrupted run, file size or line count should also be checked before treating them as complete daily files.

---

# Expected Output Sizes

For the current processing setup, useful approximate checks are:

```text
one 5-hour channel output:
~94,500 rows

three sections combined:
~283,500 rows

daily peak output:
~900 time points per frequency/channel
```

These checks are useful when verifying whether an output represents one 5-hour section or a complete 15-hour day.

---

# Current Scientific Analysis

The initial detailed analysis focused on five consecutive dates:

```text
September 21–25, 2020
```

The analysis examined the behavior of the three HF frequencies across the day and compared changes between frequencies.

Additional processing is being performed beginning with:

```text
September 27, 2020
```

with the goal of creating a longer multi-day dataset.

September 26 can be processed separately to connect the two periods continuously.

The longer-term goal is to obtain approximately 30 consecutive days that can be compared systematically.

---

# Planned Multi-Day Analysis

Once complete daily peak files are available, the next analysis stage is to combine many dates.

Planned visualizations include:

- multi-day heat maps
- hidden-line plots
- comparison of 2.500, 3.330, and 4.996 MHz
- comparison between receiver channels
- examination of recurring signal features
- comparison with auroral activity

Auroral activity will eventually be plotted alongside the radio observations to investigate whether radio propagation or signal-power changes correspond to changes in geomagnetic activity.

---

# Current Development Status

## Working / currently in use

- `run_synoptic_final.py`
- `run_synoptic_06_only.py`
- `run_synoptic_11_only.py`
- Fortran processing with the precompiled `a.out`
- daily peak extraction in the full-day program
- dated final peak filenames

## Currently being developed or tested

- combining independently processed 01, 06, and 11 sections
- automatic peak extraction after separate-section combination
- combining peak files across many days
- multi-day heat maps
- hidden-line plots
- auroral-activity comparison

These programs should only be added to the repository once they have been tested with real processing output.

---

# Repository Purpose

This repository is intended to document the processing workflow so that the project can be resumed later by the current researchers or continued by someone new to the project.

The repository should contain:

```text
Python source programs
README and documentation
small sample outputs
example plots
```

Large raw SYN files and large intermediate processing files should remain outside the repository.
