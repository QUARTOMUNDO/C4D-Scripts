import c4d
from c4d import plugins, bitmaps # type: ignore
import os

PLUGIN_ID = 2242904

class UserDataParamNameChager(plugins.CommandData):
    def Execute(self, doc):
        # Coloque aqui o código que seu script deve executar
        main()
        # c4d.gui.MessageDialog("Exportador de Níveis XML Sephius Executado")
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
    icon_path = os.path.join(dir_path, "UserDataParamNameChager.tif")
    bmp = bitmaps.BaseBitmap()
    result = bmp.InitWith(icon_path)
    if result[0] != c4d.IMAGERESULT_OK:
        error_message = get_imageresult_description(result[0])
        c4d.gui.MessageDialog("Falha ao carregar o ícone:" + error_message)  # Isso vai imprimir o código de erro
        return None
    return bmp

# Esta função é chamada quando o plugin é carregado
if __name__ == "__main__":
    icon = load_icon()
    # Registra o plugin no Cinema 4D
    c4d.plugins.RegisterCommandPlugin(id=PLUGIN_ID, str="Sephius User Data Param Name Chager",
                                      info=0, icon=icon, help="Change the name of a User Data",
                                      dat=UserDataParamNameChager())
 
doc = c4d.documents.GetActiveDocument()
def update_doc():
    global doc
    doc = c4d.documents.GetActiveDocument()

def main():
    global doc 
    update_doc()

    # Get the active selection in the scene
    selection = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)

    if not selection:
        c4d.gui.MessageDialog("[UserDataParamNameChager] No objects selected.")
        return

    # Name of the User Data Parameter you want to change
    parameter_name = c4d.gui.InputDialog("Enter the name of the User Data Parameter you want to change:")

    # New name for the User Data Parameter
    new_parameter_name = c4d.gui.InputDialog("Enter the new name for the User Data Parameter:")
    
    print("parameter_name: ", parameter_name, "new_parameter_name: ", new_parameter_name)

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
