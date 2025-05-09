 #constructors
class DemoClass:
    # constructor
    def __init__(self):
        # initializing instance variable
        self.num = 100

    # a method
    def read_number(self):
        print(self.num)

obj = DemoClass()
obj.read_number()

class Demo:
    def __init__(self,number,name):
        self.number = number
        self.name = name

    def read_number(self):
        print(self.number)

    def read_name(self):
        print(self.name)

obj = Demo(100,"John")
obj.read_number()
obj.read_name()

class User(Demo):
    def __init__(self, password, number, name):
        self.name = name
        self.number = number
        self.password = password
        super().__init__(number=number, name=name)

    def sayHello(self):
        print(f"Welcome to DunisTech, {self.name}")

    def checkPassword(self):
        self.password =password
        print(f"Your password is {self.password}")


password = input("enter your password")
number = input("enter your number")
name = input("enter your name")

User1 = User(password, number, name)
User1.sayHello()
User1.read_number()
User1.read_name()
User1.checkPassword()

#what is a class in python and how to create one
#how do you create an object from a class in python with example
#define a class called book, that has the following attributes, tittle author and pages
#include a method called summary that returns a string with the book summary

#solution
print("definition of a python class\n a class is like a blueprint for creating objects and a collection of related attributes and methods\n")
print("how to create an object from a class in python with example\n to create an object from a class, you must create an instance of the class then assign values to its attributes")
class Book:
    def __init__(self, title, author, pages):
        self.title = title
        self.author = author
        self.pages = pages

    def summary(self):
        return f"{self.title} by {self.author}, {self.pages} pages"

book1 = Book("AYAMATANGA", "F. Scott CHRISTIE", 500)
print(book1.summary())
