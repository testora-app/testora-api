import random
import string

   

def create_school_code():
    letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(3))
    numbers = ''.join(random.choice(string.digits) for _ in range(3))
    return letters + numbers 
