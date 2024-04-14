from typing import Optional
import c4d
import random
import time
from datetime import datetime

#Return true if object has a user data name and value is equal to desired
def HasUserData(CObject, UDName):
    for id, bc in CObject.GetUserDataContainer():
        if bc[c4d.DESC_NAME] == UDName:
            return True
    return False

def createUserData(obj, paramName, dataType, userDataGroup, value):
    #Add UserData storing
    Cbc = c4d.GetCustomDataTypeDefault(dataType) # Create Group
    Cbc[c4d.DESC_NAME] = paramName
    Cbc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    #print("Has Group ? ", userDataGroup)
    if userDataGroup:
        Cbc[c4d.DESC_PARENTGROUP] = userDataGroup
    Celement = obj.AddUserData(Cbc)
    obj[Celement] = value

def get_selected_objects(doc):
    """Get a list of the selected objects in the document."""
    return doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_SELECTIONORDER)

#Return True if object has a user data name and value is equal to desired
def GetUserData(obj, UDName):
    #print(CObject, UDName)
    for id, bc in obj.GetUserDataContainer():
        #print(bc[c4d.DESC_NAME], UDName)
        if bc[c4d.DESC_NAME] == UDName:
            return id

    return None

def setUserData(obj, param_name, value):
    # Find the user data's ID
    dataID = None
    for descID, bc in obj.GetUserDataContainer():
        if bc[c4d.DESC_NAME] == param_name:
            dataID = descID
            break

    # Check if the user data was found
    if dataID is None:
        print(f"No user data found with name '{param_name}'")
        return

    # Get the user data value
    data = obj[dataID]

    # Check if the data is empty
    if not data:
        obj[dataID] = value
        print(f'{param_name}: {value}')

def generate_number(total_digits):
    total_digits = int(total_digits)

    # Get current date and time
    now = datetime.now()

    # Convert to a string with format: day + month + year + hour + minute + second
    timestamp_str = now.strftime("%d/%m/%Y-%H:%M:%S")  # This will be 14 characters long


    # Calculate how many random digits we need to add
    remaining_digits = total_digits - len(timestamp_str)

    # Generate a random number with the remaining number of digits
    random.seed()
    random_number = random.randint(0, 100000)

    # Combine the timestamp and random number to get a 20-digit number
    #final_number = int(timestamp_str + "-" + str(random_number))
    
    return timestamp_str + "-" + str(random_number)

def main():

    # Called when the tag is executed. It can be called multiple time per frame. Similar to TagData.Execute.
    # Write your code here
    selectedObjects = get_selected_objects(doc)
    for obj in selectedObjects:
        if HasUserData(obj, "globalID") is False:
            userDataGroup = GetUserData(obj, "GAME PROPERTIES")
            createUserData(obj, "globalID", c4d.DTYPE_STRING, userDataGroup, str(generate_number(10)))
        else:
            setUserData(obj, "globalID", str(generate_number(10)))

        print("update Global IDs")
        obj.Message(c4d.MSG_UPDATE)

if __name__ == '__main__':
    main()