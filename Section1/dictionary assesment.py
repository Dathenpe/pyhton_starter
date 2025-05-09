fancy_line = "<----------------(❁´◡`❁)------------------>"
python_dictionary="this is a data storage thats stores its values in key value pairs so each item has its key and value"
print(fancy_line)
print("number 1")
print(python_dictionary)
print(fancy_line)

print("number 2")
items = ['apple', 'banana', 'apple', 'orange', 'banana', 'apple']
count = {}
for i in items:
    if i not in count:
        count[i] = 1
    else:
        count[i] += 1
formatted_count = {k: str(v) for k, v in count.items()}
print(formatted_count)

print(fancy_line)
print("number 3")
keys =['name','age','city']
values =['Edem','20','lekki']
person = {keys[0]:values[0],keys[1]:values[1],keys[2]:values[2]}
print(person)
print(fancy_line)