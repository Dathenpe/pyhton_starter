students = []


def add_student(name, course):
    students.append({"name": name,"course":course})

def get_students():
    return students

def get_student(index):
    return students[index]