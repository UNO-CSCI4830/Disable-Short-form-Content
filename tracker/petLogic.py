'''
Goals with this "class"

done! 1. take daily average points, return a score value based on changes to the daily average points. If a user reduces their
overall use of the substance/technology day between day, then they will be awarded a point. if the user increases their
use day to day, the points will decrease, to a minimum of zero.
done! 2. take in an average of a week's changes, if between 2 weeks there is an overall increase or decrease then there will
be more points added.
done! 3. store the position of multiple pet images and push that information through the function so that one can request the
individual image through the functions on the views page
done! 4. on the actual view, make a spot where someone would be able to input the date that they submitted the information in
so that we can test additional things and allow for retroactive tracking

'''
def daily_point_change(today, yesterday, points):
    if not yesterday:
        return points
    if today > yesterday:
        if points == 0:
            return 0
        else:
            points -= 1
    elif today < yesterday:
        if points == 100:
            return 100
        else:
            points +=1
    return points

def weekly_point_change(this_week, last_week, points):
    if not last_week:
        return points
    if this_week > last_week:
        if points < 10:
            return points - points
        else:
            points -= 10
    elif this_week < last_week:
        if points > 90:
            points_left = 100 - points
            return points + points_left
        else:
            points += 10
    return points

def safe_image(img): #if an image doesn't exist, it returns dragon egg
    if os.path.exists(img):
        return img
    return "assets/dragon_pet_egg.png"

def return_pet_info(pet, points): #takes in pet and points, returns image path
    loader = [None, None, None] #image path, stage name, progress
    if pet == 1: #dragon
        if 0 < points <= 10:
            loader[0] = safe_image("assets/dragon_pet_egg.png")
            loader[1] = "Baby Dragon 🐣"
            loader[2] = round((points / 10) * 100, 2)
            return loader
        elif 10 < points <= 30:
            loader[0] = safe_image("assets/dragon_pet_baby.png")
            loader[1] = "Baby Dragon 🐣"
            loader[2] = round(((points - 10) / 20) * 100, 2)
            return loader
        elif 30 < points <= 60:
            loader[0] = safe_image("assets/dragon_pet_teen.png")
            loader[1] = "Baby Dragon 🐣"
            loader[2] = round(((points - 30) / 30) * 100, 2)
            return loader
        elif 60 < points <= 100:
            loader[0] = safe_image("assets/dragon_pet_adult.png") #does not exist at the moment
            loader[1] = "Baby Dragon 🐣"
            loader[2] = 100
            return loader
        else:
            print("points not within range")
    elif pet == 2:#phoenix
        if 0 < points <= 10:
            return loader
        elif 10 < points <= 30:
            return loader
        elif 30 < points <= 60:
            return loader
        elif 60 < points <= 100:
            return loader
        else:
            print("points not within range")
    elif pet == 3:#tbd
        if 0 < points <= 10:
            return loader
        elif 10 < points <= 30:
            return loader
        elif 30 < points <= 60:
            return loader
        elif 60 < points <= 100:
            return loader
        else:
            print("points not within range")
    return loader