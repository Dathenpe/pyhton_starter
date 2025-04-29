print("Hello World")


#character description game
fancy_line = "<----------------(❁´◡`❁)------------------>"
name = input("enter your name")
print(fancy_line)
age = input("enter your age")
print(fancy_line)
bestFood = input("enter your best food")
print(fancy_line)
print(f"Your are welcome to python programming character game {name}")
footballTeam = input("enter your favorite football team")
if footballTeam is not None:
    print(f"your favorite football team is {footballTeam},they are losers")
print(fancy_line)
townOfBirth = input("enter your town of birth")
gender = input("enter your gender")
print(f"this is your character sheet your name is {name}\n you are {age} years old\n you are {gender}\n you were born in {townOfBirth}\n your best food is {bestFood}\n and you unfortunately support {footballTeam}")
print(fancy_line)
