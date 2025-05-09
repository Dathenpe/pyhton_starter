class DemoClass:
    num = 101

    def __init__(self):
        self.num


    def read_number(self):
        print(self.num)

obj = DemoClass()

obj.read_number()

class DemoClass2:
    # parameterized constructor
    def __init__(self, data):
        self.num = data

    # a method
    def read_number(self):
        print(self.num)

# creating object of the class
# this will invoke parameterized constructor
obj = DemoClass2(55)

# calling the instance method using the object obj
obj.read_number()

# creating another object of the class
obj2 = DemoClass2(66)

# calling the instance method using the object obj
obj2.read_number()