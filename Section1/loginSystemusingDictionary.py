#login system using python dictionary
users = {
    'blessing': 'password',
    'bode': 'ow',
    'blessing': 'password',
    'bode': 'password'
}
username = input("Enter your username: ")
password = input("Enter your password: ")



if username in users and users[username] == password:
    print("Login successful!")
else:
    print("Invalid username or password.")
