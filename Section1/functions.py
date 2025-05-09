#functions
def func1(name):
    print(f"i am learning python {name}")
func1(name="ww")
#return statement
def greet(name):
    return print(f"Hello, {name}!")

greetings = greet("bola")
print(greetings)

def square(x):
    return x * x

result = square(5)
print(result)
def square(x):
    return (x * x)
print(square(8))

def multiply(x, y):
    print(x*y)
multiply(2,8)

def multiply(x, y=0):
    print("value of x =",x)
    print("value of y =",y)
    return x * y
print(multiply(y=2,x=4))

def dunis1(*args):
    print(args)
dunis1(1,2,3,4,5)

def dunis():
    print("learning python is fun")
    print("still on functions")
dunis()

def square(x):
    return x * x
print(square(5))

def multiply(x, y=10):
    print("value of x =",x)
    print("value of y =",y)
    return x * y
print(multiply(y=2,x=4))


