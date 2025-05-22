#count-down-timer
import time
user_input = input("Enter the time in seconds: ")
t = int(user_input)

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        time_format = '{:02d} : {:02d}'.format(mins, secs)
        print(time_format, end='\r')
        time.sleep(1)
        t -= 1

    print('Fire in the hole!')

countdown(t)