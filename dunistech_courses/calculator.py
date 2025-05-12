import math

#function calculator
def add(x,y):
    return x + y
def subtract(x,y):
    return x - y
def multiply(x,y):
    return x * y
def divide(x,y):
   if y == 0:
       return "Null pointer exception"
   if x == 0:
       return "Null pointer exception"
   else:
       return x / y
def exponent(x,y):
    return x ** y
def modulus(x,y):
    return x % y
def square_root(x):
    return math.sqrt(x)

# print(f"The sum of {x} and {y} is {add(x,y)}")
# print(f"The difference of {x} and {y} is {subtract(x,y)}")
# print(f"The product of {x} and {y} is {multiply(x,y)}")
# print(f"The quotient of {x} and {y} is {divide(x,y)}")
# print(f"The exponent of {x} and {y} is {exponent(x,y)}")
# print(f"The modulus of {x} and {y} is {modulus(x,y)}")
# print(f"The square root of {x} is {square_root(x)}")

def calculator():
    print("select operation")
    print("1.Add")
    print("2.Subtract")
    print("3.Multiply")
    print("4.Divide")
    print("5.Exponent")
    print("6.Modulus")
    print("7.Square Root")
    choice = input("Enter choice(1/2/3/4/5/6/7): ")
    num1 = int(input("Enter first number: "))
    num2 = int(input("Enter second number: "))
    if choice == '1':
        print(num1,"+",num2,"=",add(num1,num2))
    elif choice == '2':
        print(num1,"-",num2,"=",subtract(num1,num2))
    elif choice == '3':
        print(num1,"*",num2,"=",multiply(num1,num2))
    elif choice == '4':
        print(num1,"/",num2,"=",divide(num1,num2))
    elif choice == '5':
        print(num1,"**",num2,"=",exponent(num1,num2))
    elif choice == '6':
        print(num1,"%",num2,"=",modulus(num1,num2))
    elif choice == '7':
        print("The square root of",num1,"is",square_root(num1))
    else:
        print("Invalid input")

__name__ = "__main__"
calculator()