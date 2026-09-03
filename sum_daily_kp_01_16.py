from datetime import datetime


input_file = "Kp_ap_20200829_20201023.dat"
output_file = "daily_kp_sum_01_16.dat"


f = open(input_file, "r")
lines = f.readlines()
f.close()


out = open(output_file, "w")
out.write("# Date DOY Kp_sum_01_16\n")


current_date = ""

sum_01_16 = 0.0
count_01_16 = 0


for line in lines:

    parts = line.split()

    if len(parts) < 8:
        continue

    if not parts[0].isdigit():
        continue


    year = parts[0]
    month = parts[1]
    day = parts[2]

    start_hour = float(parts[3])
    kp = float(parts[7])

    date = year + "-" + month + "-" + day


    if current_date == "":
        current_date = date


    if date != current_date:

        # Find day of year
        d = datetime.strptime(current_date, "%Y-%m-%d")
        doy = d.timetuple().tm_yday


        if count_01_16 == 6:

            out.write(
                current_date + " "
                + str(doy) + " "
                + str(round(sum_01_16, 3))
                + "\n"
            )

        else:

            print(
                "WARNING:",
                current_date,
                "has",
                count_01_16,
                "selected Kp values instead of 6"
            )


        current_date = date
        sum_01_16 = 0.0
        count_01_16 = 0


    # Kp bins overlapping the 01-16 UT radio period:
    # 00-03
    # 03-06
    # 06-09
    # 09-12
    # 12-15
    # 15-18
    if start_hour >= 0.0 and start_hour <= 15.0:

        sum_01_16 = sum_01_16 + kp
        count_01_16 = count_01_16 + 1


# Write final day
if current_date != "":

    d = datetime.strptime(current_date, "%Y-%m-%d")
    doy = d.timetuple().tm_yday


    if count_01_16 == 6:

        out.write(
            current_date + " "
            + str(doy) + " "
            + str(round(sum_01_16, 3))
            + "\n"
        )

    else:

        print(
            "WARNING:",
            current_date,
            "has",
            count_01_16,
            "selected Kp values instead of 6"
        )


out.close()


print()
print("Done.")
print("Created:", output_file)
