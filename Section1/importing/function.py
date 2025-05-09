def square(x):
    return x * x
def main():
    for i in range(10):
       # print("{} squared is {}".format(i, square(i)))
        #using f string
        print(f"{i} squared is {square(i)}")
if __name__ == "__main__":
    main()
