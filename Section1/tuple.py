#tuple
dunis =(23,99,"coding")
print(dunis[0])
#tuple of strings
tuple1 = ("apple", "banana", "cherry")
tuple2 = (1, 5, 7, 9, 3)
tuple3 = ("hello", "world", "python")

# empty tuple
dunis = ()

# tuple of strings
dunis_1 = ("hi", "hello", "bye")
print(dunis_1)

# tuple of int, float, string
dunis_2 = (1, 2.8, "Hello World")
print(dunis_2)

# tuple of string and list
dunis_3 = ("Book", [1, 2, 3])
print(dunis_3)

# tuples inside another tuple
# nested tuple
dunis_4 = ((2, 3, 4), (1, 2, "hi"))
print(dunis_4)

# a tuple with single data item
dunis1 = (99,)

# tuple of int, float, string
dunis_2 = (1, 2.8, "Hello World")
print(dunis_2)
print(dunis_2[0])
print(dunis_2[0])


dunis = (11, 22, 33, 44, 55, 66, 77, 88, 99)
print(dunis)

# elements from 3rd to 5th
# prints (33, 44, 55)
print(dunis[2:5])

# elements from start to 4th
# prints (11, 22, 33, 44)
print(dunis[:4])

# elements from 5th to end
# prints (55, 66, 77, 88, 99)
print(dunis[4:])

# elements from 5th to second last
# prints (55, 66, 77, 88)
print(dunis[4:-1])

# displaying entire tuple
print(dunis[:])

dunisClas = (1,[9,8,6],'hello')
print(dunisClas[0])
print(dunisClas[1])
print(dunisClas[2])
print(dunisClas[1][0])
print(dunisClas[1][1])
print(dunisClas[1][2])


print (22 in dunis)#true because 22 is in the tuple
print (2 in dunis)#false because 2 is not in the tuple
print(88 not in dunis)#false because 88 is in the tuple
print(101 not in dunis)#true because 101 is not in the tuple


#tuple of fruits
dunis_tuple = ("apple","orange","grape", "banana")

#iterating over tuple elements
for fruit in dunis_tuple:
    print(fruit)
