#introduction to inheritance
class Person():
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def getName(self):



    return self.age + 1

class Student(Person):
    def __init__(self, name, age, grade):
        super().__init__(name, age)
        self.grade = grade  #this is a new attribute


class Animal():
    def speak(self):
        return ("I am an animal")

class Dog(Animal):
    def speak(self):
        return ("I am a dog")

class Cat(Animal):
    def speak(self):
        return ("I am a cat")

dog = Dog()
cat = Cat()
print(dog.speak())
print(cat.speak())
#