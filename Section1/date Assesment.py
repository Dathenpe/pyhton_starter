#create a class that represents a date and include different methods that present date in different formats
from datetime import date

class DateTime:
    def __init__(self):
        self.today = date.today()

    def get_format_a(self):
        return self.today.strftime("%d/%m/%Y")

    def get_format_b(self):
        return self.today.strftime("%B %d, %Y")

    def get_format_c(self):
        return self.today.strftime("%m/%d/%y")

    def get_format_d(self):
        return self.today.strftime("%b-%d-%Y")



my_datetime = DateTime()
print("Format A:", my_datetime.get_format_a())
print("Format B:", my_datetime.get_format_b())
print("Format C:", my_datetime.get_format_c())
print("Format D:", my_datetime.get_format_d())