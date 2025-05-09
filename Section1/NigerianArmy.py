username = input("Enter your username: ")
age = input("Enter your age: ")
height = input("Enter your height: ")

if type(age) == int and type(height) == int:
    entries_dict = {username: age }
    entries_dictb = {"height": height}

    if entries_dict[username] < 18:
        if entries_dictb["height"] < 150:
            print("You are not allowed to join the army")
    else:
        print("You are allowed to join the army")
else:
    print("input intgers oooooooooooooooooooooooo!!!!!!!!!!!!!!!!!!!!!!!!!! ahan")


# Program 1: Populate Dictionary with Entries


def main():
    applicants = {

        "bode": {"age": 20, "height": 180},
        "blessing": {"age": 18, "height": 160},
        "dapo": {"age": 21, "height": 170},
        "kola": {"age": 19, "height": 165},
        "sarah": {"age": 20, "height": 160},
        "james": {"age": 19, "height": 165},
        "joe": {"age": 21, "height": 175},
    }

    def add_applicant():
     name = input("Enter the name of the applicant: ")
     age = int(input("Enter the age of the applicant: "))
     height = int(input("Enter the height of the applicant: "))
     applicants[name] = {"age": age, "height": height}
     print("Applicant added successfully!")

     def view_applicants():
        print("List of Applicants:")
        for name, details in applicants.items():
            print(f"Name: {name}, Age: {details['age']}, Height: {details['height']}")

     def delete_applicant():
        name = input("Enter the name of the applicant to delete: ")
        if name in applicants:
            del applicants[name]
            print("Applicant deleted successfully!")
        else:
            print("Applicant not found in the database.")

    def check_eligibility():
        name = input("Enter the name of the applicant to check eligibility: ")
        if name in applicants:
            age = applicants[name]["age"]
            height = applicants[name]["height"]
            if age >= 18 and height >= 160:
                print(f"{name} is eligible for the Nigerian Army.")
            else:
                print(f"{name} is not eligible for the Nigerian Army.")
        else:
            print("Applicant not found in the database.")

    while True:
        print("\nMenu:")
        print("1. Add Applicant")
        print("2. Check Eligibility")
        print("3. Exit")

        choice = input("Enter your choice: ")
        if choice == "1":
            add_applicant()
        elif choice == "2":
            check_eligibility()
        elif choice == "3":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
