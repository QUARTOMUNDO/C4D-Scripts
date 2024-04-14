import c4d

def main():
    # Get the active selection in the scene
    selection = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)

    if not selection:
        c4d.gui.MessageDialog("No objects selected.")
        return

    # Name of the User Data Parameter you want to change
    parameter_name = "rewardName"

    # New name for the User Data Parameter
    new_parameter_name = "rewardID"
    
    print("selection: ", selection)
    
    # Iterate through the selected objects
    for obj in selection:
        print("obj: " + obj.GetName())
        
        # Get the User Data container
        user_data_container = obj.GetUserDataContainer()

        # Search for the parameter by name
        for param_id, param_data in user_data_container:
            #print("parameter_name: " + param_data[c4d.DESC_NAME] + " " + parameter_name)
            
            if param_data[c4d.DESC_NAME] == parameter_name:
                
                # Modify the copied description
                param_data.SetString(c4d.DESC_NAME, new_parameter_name)
                
                # Set the modified description back to the object
                obj.SetUserDataContainer(param_id, param_data) #Set the container changes  
                
                # Print the object name and parameter name for debugging
                print(f"Object: {obj.GetName()}, Parameter: {parameter_name}")
                
                # Print a message after renaming
                print(f"Renamed {parameter_name} to {new_parameter_name} in {obj.GetName()}")

    # Update the scene to reflect the changes
    c4d.EventAdd()


# Call the main function
if __name__ == '__main__':
    main()
