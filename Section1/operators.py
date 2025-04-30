#all arithmetic operators
num1 =input("input a number")
num2 =int(input(" input another number"))
num1 = int(num1)
sum = num1 + num2
subtract = num1 - num2
divide = num1/num2
multiply = num1 * num2
modulus = num1 % num2
exponent = num1 ** num2

print(f"addition of {num1} and {num2} = {sum}")
print(f"subtraction of {num1} and {num2} = {subtract}")
print(f"division of {num1} and {num2} = {divide}")
print(f"multiplication of {num1} and {num2} = {multiply}")
print(f"modulus of {num1} and {num2} = {modulus}")
print(f"exponent of {num1} and {num2} = {exponent}")

#comparison operators
print(num1 > num2)
print(num1 < num2)
print(num1 == num2)
print(num1 != num2)
print(num1 >= num2)
print(num1 <= num2)

#relational operators
x = 5
y = 3
print(f"x > y is {x > y}")
print(f"x < y is {x < y}")
print(f"x >= y is {x >= y}")
print(f"x >= y is {x >= y}")
print(f"x == y is {x == y}")
print(f"x != y is {x != y}")
print()
#Compound assignment
x = 3
y = 2
# x = x + y
x += y
print(f"x = x + y is {x}")
# x = x - y
x -= y
print(f"x = x - y is {x}")
# x = x * y
x *= y
print(f"x = x * y is {x}")
# x = x / y
x /= y
print(f"x = x / y is {x}")
# x = x % y
x %= y
print(f"x = x % y is {x}")
# x = x ** y
x **= y
print(f"x = x ** y is {x}")

#logical operators
x = True
y = False
print(f"x and y is {x and y}")
print(f"x or y is {x or y}")
print(f"not x is {not x}")
print(f"not y is {not y}")


#membership operator
c = 3
e = 5
list =[1,2,3,4,5]
if c in list:
    print(f"{c} is in the list")
elif e not in list:
    print(f"{e} is not in the list")
else:
    print(f"{c} is not in the list")

#identity operators
x = 3
y = 3
print(f"x is y is {x is y}")
if x is y:
    print(f"x is y is {x is y}")
elif y is x:
    print(f"y is x is {y is x}")
else:print(f"x is not y is {x is not y}")

if x is not y:
    print(f"x is not y is {x is not y}")
else:
    print(f"x is not y is {x is not y}")

print(f"x is not y is {x is not y}")

#concatenation
a ='hello'
b = 500
print(a + " " +  str(b))

num = input("input any number to be multiplied")
print(f"{num} x 1 = "+(num * 1))
print(f"{num} x 2 = "+(num * 2))
print(f"{num} x 3 = "+(num * 3))
print(f"{num} x 4 = "+(num * 4))
print(f"{num} x 5 = "+(num * 5))
print(f"{num} x 6 = "+(num * 6))
print(f"{num} x 7 = "+(num * 7))
print(f"{num} x 8 = "+(num * 8))
print(f"{num} x 9 = "+(num * 9))
print(f"{num} x 10 = "+(num * 10))
print(f"{num} x 11 = "+(num * 11))
print(f"{num} x 12 = "+(num * 12))

#string methods
word = "elephant and eggs"
print(word[-1])

print(word[6])
print(word[1:5])
print(word[:6])
mrSlice = ["we","is","us","them","him","dead","nor","nu"]
print(word.upper())
print(word.lower())
print(word.capitalize())
print(word.join(reversed(word)))
word= word.replace("e","weres")
print(mrSlice[3])
print(":".join(mrSlice))
print(" ".join(mrSlice))
print(":".join(word))