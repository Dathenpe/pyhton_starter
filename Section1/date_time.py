from datetime import date
from datetime import time
from datetime import datetime

# now create an instance of the date object by declaring date objects in the main function
def main():
    ##DATE OBJECTS
    today = date.today()
    formatted_date_fstring = f"Today's date is: {today.strftime('%Y-%m-%d')}, Weekday (Mon=0): {today.weekday()}, Year: {today.year}, Month: {today.month}"
    print(formatted_date_fstring)

if __name__ == "__main__":
    main()

from datetime import date

today = date.today()

# dd/mm/YY
format1 = today.strftime("%d/%m/%Y")
print("Format1 =", format1)

# Textual month, day and year
format2 = today.strftime("%B %d, %Y")
print("Format2 =", format2)

# mm/dd/y
format3 = today.strftime("%m/%d/%y")
print("Format3 =", format3)

# Month abbreviation, day and year
format4 = today.strftime("%b-%d-%Y")
print("Format4 =", format4)

print(f"Today's week Day: {today.weekday()}")
