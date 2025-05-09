# class multiply():
#     def add(a,b):
#         return a + b
#
#     def subtract(a,b):
#         return a - b
#
#     def divide(a,b):
#         return a / b
#
#     def multiply(a,b):
#         return a * b
#
#
# # multiply = multiply()
# # print(multiply.add(2,3))
# # print(multiply.subtract(2,3))
# # print(multiply.divide(2,3))
# # print(multiply.multiply(2,3))
#
# class myClass():
#     def method1(self):
#         print(" WELCOME")
#
#     def method2(self, someString):
#         print("Software Development:" + someString)
#
# class Person():
#     def setName(self, name):
#         self.name = name.title()

#     def getName(self):
#         return self.name
#
#     def setDesc(self, desc):
#         self.desc = desc.capitalize()
#
#     def getDesc(self):
#         return self.desc
#
# # end of class definition
#
# # program starts here
# person1 = Person() #this is an instance of class Person
# person1.setName('Mr. Smith') #set name
# print(person1.getName()) # to get name
# person1.setDesc('A software developer') #set description
#
# MrChris= Person()
# MrChris.setName('Mr. Chris')
# MrChris.setDesc('A software developer')
#
# print(person1.getDesc())
# print(MrChris.getDesc())
#
#
# print(MrChris.getName())
# print(MrChris.getDesc())

class Login():
    def setUsername(self, username):
        self.username = username

    def setPassword(self, password):
        self.password = password

    def getUsername(self):
        return self.username

    def getPassword(self):
        return self.password

Admin = Login()
Admin.setUsername(input("Enter your username: "))
Admin.setPassword(input("Enter your password: "))

if Admin.getPassword() == '1234':
    print(f'login successful {Admin.getUsername()}')
else:
    print(f'login failed {Admin.getUsername()} please try again')

print(Admin.getPassword())
print(Admin.getUsername())

class myClass():
 def method1(self):
    print("WELDONE")
 def method2(self,someString):
        print("Software Testing:" + someString)
def main():

 # exercise the class methods
 c = myClass()
 c.method1()
 c.method2(" Testing is fun")


class Person:

    def setName(self, name):
        self.name = name.title()

    def getName(self):
        return self.name

    def setDesc(self, desc):
        self.desc = desc.capitalize()

    def getDesc(self):
        return self.desc


person3 = Person()
person3.setName('Mr. Smith')
print(person3.getName())
person3.setDesc('A software developer')
print(person3.getDesc())

character_sheet = f"""
Name: {person3.getName()},\n
Description: {person3.getDesc()},\n
"""
print(character_sheet)
