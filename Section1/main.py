num1 = input("enter the first number")
num2 = input("enter the second number")
try:
    print(f"addition of {num1} and  {num2}  is {str(int(num1) + int(num2))}")
    print(f"multiplication of  {num1}  and   {num2}  is + {str(int(num1) * int(num2))}")
    print(f"subtraction of  {num1} and {num2} is {str(int(num1) - int(num2))}")
    print(f"division of  {num1} and { num2 } is{str(int(num1) / int(num2))}")
except Exception as e:
    print(e)




name = input("enter your name")
age = input("enter your age")
print(f"my name is {name}")
print(f"my age is {age}")
print([22, 33, 44, 55, 66, 77, 88, 99])
num2 = [22, 33, 44, 55, 66, 77, 88, 99]
print(f"the total number of list is {len(num2)}")
print(f"Hello, {name}!")
print(f"Hello, {name}! You are {age} years old.")

if age == None:
    print("You are not an adult.")
else:
    print("You are an adult.")

if age >= int('1'):
    print("You are an adult.")
else:
    print("You are not an adult.")

    if name == 'shubham':
        print('your name is shubham')
    elif name == 'shubhama':
        print('your name is not shubham')
    else:
        print('your name is not shubham')

name =input('Enter you name')
age =input('Enter your age')
isadult_ =input('are you an adult?')

if __name__ == '__main__':
    print(f"Hello, {name}!")
    print(f"Hello, {name}! You are {age} years old.")
    if isadult_ == 'yes':
        print("You are an adult.")
    else:
        print("You are not an adult.")