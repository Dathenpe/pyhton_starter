print("question 1\n")
fruits =["apple","banana","cherry"]
for i in fruits:
  i = i.upper()
  print(i)

print("question 2\n")
#number 2
num = int(input("Enter a number: "))
if num % 2 == 0 and num > 10:
    print("The number is even and greater than 10.")
else:
    print("The number is not even or not greater than 10.")
print("question 3\n")
#number 3
num = int(input("Enter a number to check if it is positive, negative, or zero: "))
#if number is positive
if num > 0:
    print("The number is positive.")
#if number is negative
elif num < 0:
    print("The number is negative.")
#else
elif num == 0:
    print("The number is zero.")
else:
    print("invalid input")
print("question 4\n")
#number 4
for i in range(1, 101):
    if i % 3 == 0 and i % 5 == 0:
       i = "fizz-buzz"
       print(i)
       continue
    elif i % 3 == 0:
        i = "fizz"
        print(i)
        continue
    elif i % 5 == 0:
        i = "buzz"
        print(i)
        continue
    else:
        print(i)
