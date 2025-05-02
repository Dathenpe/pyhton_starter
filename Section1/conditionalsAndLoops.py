coding = True
if coding:
    print("coding")
else:
    print("not coding")

num = 100
if num < 100:
    print("num is less than 200")

num = 22
if num % 2 == 0:
    print("num is even")
else:
    print("num is odd")

num = 1122
if 9 < num < 99:
    print("Two digit number")
elif 99 < num < 999:
    print("Three digit number")
elif 999 < num < 9999:
    print("Four digit number")

for i in range(10):
    print(i)
for i in range(1, 10):
    print(i)
for i in range(1, 10, 3):
    print(i)
for i in range(10, 0, -1):
    print(i)

list = ["flea", "dog", "cat", "mouse"]
for insect in list:
    print(insect)

#nested if else statements
num = -99
if num > 0:
    print("positive number")
else:
    print("negative number")
    #nested if
    if -99 <= num:
        print("two digit negative number")

for i in range(10):
    print(i)

list = ["Fleagle", "apple", "pineapple", "apple", "banana"]
for fruit in list:
    print(fruit)

# Program to print squares of all numbers present in a list

# List of integer numbers
numbers = [1, 2, 4, 6, 11, 20]

# iterating over the given list
for val in numbers:
    # calculating square of each number
    sq = val * val
    # displaying the squares
    print(sq)

# For loop with else block
numbers = [1, 2, 4, 6, 11, 20]
for val in numbers:
    sq = val * val
    print(sq)
else:
    print("Loop finished executing")

# Program to print the sum of first 5 natural numbers
sum_of_numbers = 0

for val in range(1, 6):
    sum_of_numbers += val

print(sum_of_numbers)

for val in range(5):
    print(val)
else:
    print("Loop finished executing")

for num1 in range(3):
    for num2 in range(3):
        print(num1, num2)

num = 1
# loop will repeat itself as long as num < 10 remains true
while num < 10:
    print(num)
    # incrementing the value of num
    num += 3
    print(num)

# enumerate function
list = ["Fleagle", "apple", "pineapple", "apple", "banana"]
for index, fruit in enumerate(list):
    print(index, fruit)

# break statement
for i in range(10):
    print(i)
    if i == 5:
        break

# continue statement
for i in range(10):
    if i == 5:
        continue
    print(i)

# pass statement
for i in range(10):
    pass

# while loop with else block
num = 10
while num > 6:
    print(num)
    num -= 1
else:
    print("Loop finished executing")

for num in [20, 11, 9, 66, 4, 89, 44]:
    # skipping the even numbers
    if num % 2 == 0:
        continue
    print(num)
#pass statement
for num in [20, 11, 9, 66, 4, 89, 44]:
    if num % 2 == 0:
        pass
    else:
        print(num)

num1 = int(input("enter a number to get its multiplication table"))
for i in range(1, 50):
    print(f"{num1} * {i} = {num1 * i}")

num1 = int(input("enter 30 numbers to get its ratio grid"))
for i in range(1, 31):
    print(f"{num1} / {i} = {num1 / i}")
