age = int(input('Type your age: '))

if age < 18:
    print('Bye!')
else:
    print(age)


step = 1
max_step = 200


while step <= max_step:
    print(step)
    step += 1