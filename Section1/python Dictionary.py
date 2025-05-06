#python dictionary

thisdict = {
    "brand": "Ford",
    "model": "Mustang",
    "year": 1964
}
print(thisdict)
print(thisdict["brand"])
print(thisdict["model"])
print(thisdict["year"])
Dict = {
    'Tim':18,
    'Tina':17,
    'Tolu':21
}
print(Dict)
print(Dict['Tim'])
print(Dict['Tina'])
print(Dict['Tolu'])

ages = {
    'blessing':30,
    'bode':25
}
print("Print the keys using their values")
for key, value in ages.items():
    print(f"{value} is {key}")

print("Print all keys")
for key in ages.keys():
    print(key)
print(ages)
print(ages['blessing'])
print(ages.items())
print(ages['bode'])

Dict = {'Tim': 18, 'Charlie': 22, 'Tiffany': 22, 'Robert': 25}
print(Dict['Charlie'])
print((Dict['Tiffany']))

mydict = {'StuName': 'Ajeet', 'StuAge': 30, 'StuCity' : 'Arga'}
print(mydict)
print("student Age before update", mydict['StuAge'])
print("student City before update", mydict['StuCity'])
mydict['StuAge'] = 31
mydict['StuCity'] = 'Noida'
print("student Age after update", mydict['StuAge'])
print("student City after update", mydict['StuCity'])
mydict={'StuName': 'Steve', 'StuAge': 4, 'StuCity' : 'Arga'}
del mydict['StuCity'];
mydict.clear();
del mydict;

Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25}
Boys = {'Tim': 18,'Charlie':12,'Robert':25}
Girls = {'Tiffany':22}
studentX=Boys.copy()
studentY=Girls.copy()
print(studentX)
print(studentY)

Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25}
Dict.update({"Sarah":9})

print(Dict)

Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25}
del Dict ['Charlie']
print(Dict)

Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25}
print("Students Name: %s" % list(Dict.items()))

Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25}
Boys = {'Tim': 18,'Charlie':12,'Robert':25}
Girls = {'Tiffany':22}
for key in list(Boys.keys()):
 if key in list(Dict.keys()):
    print(True)
 else:
    print(False)


student = {'name': 'james', 'city': 'calabar', 'age' : 200}
print(f"before delete",student)
del student['city']
print(f"after delete",student)
student.clear();
print(student)
del student

Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25}
Boys = {'Tim': 18,'Charlie':12,'Robert':25}
Girls = {'Tiffany':22}
Students = list(Dict.keys())
Students.sort()

Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25}
print("Length : %d" % len (Dict))

Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25}
print("variable Type: %s" %type (Dict))


###classwork
fancy_line = "<----------------(❁´◡`❁)------------------>"
print(fancy_line)
ProgrammingLanguages = {
    'Python': 'Guido van Rossum',
    'Ruby': 'Yukihiro Matsumoto',
    'Java': 'James Gosling',
    'C++': 'Bjarne Stroustrup',
    'C': 'Dennis Ritchie'
}
for key, value in ProgrammingLanguages.items():
    print(f"{key} was created by {value}")
print(fancy_line)
#second
GoodProgrammingLanguages = {'Ruby': 'Yukihiro Matsumoto', 'Java': 'James Gosling','C++': 'Bjarne Stroustrup','Html': 'Tim Berners-Lee', 'Css': 'Tim Berners-Lee'}
print("before update",GoodProgrammingLanguages)
GoodProgrammingLanguages.update({'sky': 'Ayo'})
print("after update",GoodProgrammingLanguages)
GoodProgrammingLanguages.clear()
print(GoodProgrammingLanguages)
del GoodProgrammingLanguages

#length
Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25}
print("Length : %d" % len (Dict))

#string
Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25}
print("printable string:%s" % str (Dict))

#type
Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25}
print("variable Type: %s" %type (Dict))

#cmp
Dict = {'Tim': 18,'Charlie':12,'Tiffany':22,'Robert':25}



my_dict1 = {"username": "XYZ", "email": "xyz@gmail.com", "location":"Mumbai"}

my_dict2 = {"firstName" : "Nick", "lastName": "Price"}


my_dict1 = {"username": "XYZ", "email": "xyz@gmail.com", "location":"Mumbai"}
my_dict2 = {"firstName" : "Nick", "lastName": "Price"}
my_dict1.update(my_dict2)
print(my_dict1)
#or
my_dict = {**my_dict1, **my_dict2}
print(my_dict)



