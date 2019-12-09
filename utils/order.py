
a = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]

new_list = []

counter = 0

while counter < len(a):
    new_list.append(a[counter])
    counter += 1
    new_list.append(a[counter])
    counter += 1
    new_list.append(a[counter])
    counter += 1
    new_list.append(a[counter])
    counter += 5

    new_list.append(a[counter])
    counter += 1
    new_list.append(a[counter])
    counter += 1
    new_list.append(a[counter])
    counter += 1
    new_list.append(a[counter])
    counter -= 7

    new_list.append(a[counter])
    counter += 1
    new_list.append(a[counter])
    counter += 1
    new_list.append(a[counter])
    counter += 1
    new_list.append(a[counter])
    counter += 5

    new_list.append(a[counter])
    counter += 1
    new_list.append(a[counter])
    counter += 1
    new_list.append(a[counter])
    counter += 1
    new_list.append(a[counter])
    counter += 1

print new_list


