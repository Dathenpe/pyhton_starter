import os
current_dir = os.getcwd()
print(current_dir)
print("current directory", os.listdir(current_dir))
os.mkdir("test_dir")
print("current directory", os.listdir(current_dir))
os.rmdir("test_dir")
print("current directory", os.listdir(current_dir))


