import json


banData = {"userID":{"type":"temp","release":17102343023,"ban_by":{"nick":"username","id":"userID"}}, "user2ID":{"type":"perm","ban_by":{"nick":"Scropts","id":"userIDhere"}}}

def ban(user):

    pass

def main():
    
    if not banData.get("userID"):
        print("Couldn't get that user. add em to the list")

    else:
        print(banData.get("userID"))

    if not banData.get("user3ID"):
        print("Couldn't find")

    print(banData.get("user2ID"))

    pass


if __name__ == "__main__":
    main()
