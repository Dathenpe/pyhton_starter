#python lists

list = [22, 33, 44, 55, 66, 77, 88, 99]
print(list)
print(list[0])
print(list[1])
print(list[2])
print(list[3])
print(list[4])
print(list[5])
print(list[6])
print(list[7])
print(list[-1])
print(list[-2])
#mixed list
list = [22, 33, 44, 55, 66, 77, 88, 99, "hello", "world"]
print(list)
print(list[0])
print(list[1])
print(list[2])
print(list[3])
print(list[4])
print(list[5])
print(list[6])
print(list[7])
print(list[-1])
print(list[-2])

#change/updating lists
number = [22, 33, 44, 55, 66, 77, 88, 99]
print(number)
number[0] = 100
print(number)
number[1] = 200
print(number)
number[2] = 300
print(number)
number[3] = 400
print(number)
number[4] = 500
print(number)
number[5] = 600
print(number)
number[6] = 700
print(number)
number[7] = 800
print(number)
number[-1] = 900
print(number)

#looping through a list

#looping through a list
number = [22, 33, 44, 55, 66, 77, 88, 99,12.0]
#the for loop will iterate through each element in the list and print it out

# python
# for i in number:
#     print(i)
#   java
#     for(int i = 0; i < number.length; i++){
#         System.out.println(number[i]);
#     }

mix_list = [1.13,2,5,'beginner',100,'hello']
num_list =[11,22,9,9,78,34,12.0]
no_data=[]
print(mix_list[3])
print(mix_list[4])
print(mix_list[5])
print(num_list[-3])
print(num_list[-2])
#slicing
print(mix_list[0:3])
print(mix_list[:3])
print(mix_list[2:])
print(mix_list[-3:])
print(mix_list[-3:-1])
print(num_list[0:4])
#list methods
list = [22, 33, 44, 55, 66, 77, 88, 99]
print(list)
list.append(100)
print(list)
list.insert(0, 200)
list.insert(3,"onions")
print(list)
list.remove(200)
print(list)
list.pop()
print(list)
list.pop(0)
print(list)
list.clear()
print(list)
#extending a list
list1 = [1,2,3,4,5]
list2 = [6,7,8,9,10]
list1.extend(list2)
print(list1)
list1.extend("hello")
print(list1)
list2.extend(300,400,500)
print(list2)