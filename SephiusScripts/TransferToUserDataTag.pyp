import c4d # type: ignore
from c4d import plugins, utils, bitmaps  # type: ignore
import os

PLUGIN_ID = 2242905

class TransferToUserDataTag(plugins.CommandData):
    def Execute(self, doc):
        # Get the selected objects
        selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)

        # Check if any objects are selected
        if not selected_objects:
            c4d.gui.MessageDialog('Please select objects with user data')
            return False

        # Iterate over each selected object and update the 'SETTINGS' tag
        for obj in selected_objects:
            update_user_data_tag(obj)

        # Update the Cinema 4D document
        c4d.EventAdd()
        return True
    
    def GetState(self, doc):
        # Retorna o estado do comando
        return c4d.CMD_ENABLED  
      
def get_imageresult_description(result_code):
    # Dicionário que mapeia os códigos de resultado para descrições
    descriptions = {
    c4d.IMAGERESULT_OK: "Success",
    c4d.IMAGERESULT_NOTEXISTING: "File does not exist",
    c4d.IMAGERESULT_WRONGTYPE: "Wrong type",
    c4d.IMAGERESULT_OUTOFMEMORY: "Out of memory",
    c4d.IMAGERESULT_FILEERROR: "File error",
    c4d.IMAGERESULT_FILESTRUCTURE: "Corrupt file structure",
    c4d.IMAGERESULT_MISC_ERROR: "Miscellaneous error"
    }

    # Retorna a descrição correspondente ao código, ou uma string padrão se o código não for conhecido
    return descriptions.get(result_code, "Unknown error code")

# Função para carregar o ícone do plugin
def load_icon():
    # Obtém o diretório do script atual
    dir_path = os.path.dirname(__file__)
    icon_path = os.path.join(dir_path, "TransferToUserDataTag.tif")
    bmp = bitmaps.BaseBitmap()
    result = bmp.InitWith(icon_path)
    if result[0] != c4d.IMAGERESULT_OK:
        error_message = get_imageresult_description(result[0])
        c4d.gui.MessageDialog("Falha ao carregar o ícone:" + error_message)  # Isso vai imprimir o código de erro
        return None
    return bmp

def update_user_data_tag(obj):
        # Get the user data container from the object
        userDataContainer = obj.GetUserDataContainer()

        # Check if the object has any user data
        if not userDataContainer:
            return

        # Find the 'SETTINGS' tag
        userDataTag = None
        for tag in obj.GetTags():
            if tag.GetName() == "SETTINGS" and tag.GetType() == c4d.Tuserdata:
                userDataTag = tag
                break

        if userDataTag is None:
            print("No SETTINGS tag found for object", obj.GetName())           
            return

        # Copy user data from the object to the tag, matching by name
        for id, bc in userDataContainer:
            # Get the name of the user data
            name = bc[c4d.DESC_NAME]
            print("name: ", name)
            # Get the user data value
            value = obj[id]
            print("value: ", value)
            # Find the corresponding parameter in the tag
            tagUserDataContainer = userDataTag.GetUserDataContainer()

            if tagUserDataContainer is None:
                c4d.gui.MessageDialog("No user data found in 'SETTINGS' tag")
                return
            
            for tagId, tagBc in tagUserDataContainer:
                print("tagId[1].dtype: ", tagId[1].dtype, "dtypes: ",c4d.DTYPE_GROUP, c4d.DTYPE_SUBCONTAINER)
                if tagId[1].dtype not in [c4d.DTYPE_GROUP, c4d.DTYPE_SUBCONTAINER]:
                    if tagBc[c4d.DESC_NAME] == name and tagId[1].dtype:
                        # Update the tag user data value
                        print("Updating the tag user data value: ", name, value)
                        userDataTag[tagId] = value
                        break
                else:
                    print("User data", name, "is a group or subcontainer.  Ignoring")
                    continue

            print("User data", name, "don't exist in Settings Tag. Ignoring")

    
if __name__ == "__main__":
    icon = load_icon()
    plugins.RegisterCommandPlugin(
        id=PLUGIN_ID,
        str="Sephius Transfer To User Data Tag",
        info=0,
        icon=icon,
        help="Transfer the user data parameters of an object to an user data tag named 'SETTINGS' for selected objects",
        dat=TransferToUserDataTag()
    )
