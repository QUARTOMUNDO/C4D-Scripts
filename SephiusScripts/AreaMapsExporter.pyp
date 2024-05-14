from typing import Optional
import c4d
import xml.etree.ElementTree as ET
import xml.dom.minidom
from c4d import plugins, bitmaps
import os
PLUGIN_ID = 2242901

doc: c4d.documents.BaseDocument  # The active document
op: Optional[c4d.BaseObject]  # The active object, None if unselected

class AreaMapsExporter(plugins.CommandData):
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
    icon_path = os.path.join(dir_path, "AreaMapsExporter.tif")
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
    c4d.plugins.RegisterCommandPlugin(id=PLUGIN_ID, str="Area Maps Exporter",
                                      info=0, icon=icon, help="Export Area Maps to XML file",
                                      dat=AreaMapsExporter())

def color_to_value(color):
    rounded_value = round(color.x * 100)
    #print(rounded_value)
    return str(int(rounded_value))

def color_to_luma(color):
    #print(color.x)
    if(color.x > 0.5):
        return "1"
    else:
        return "0"

def indent(elem, level=0):
    """
    Recursive function to add indentation to XML elements.
    """
    indent_str = "  "  # Two spaces for each level of indentation
    i = "\n" + level * indent_str  # Indentation string for the current level

    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + indent_str
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def main() -> None:
    root = ET.Element("AreaMaps")
    root.attrib = {"regionName": "LANDS_OF_OBLIVION"}

    ##### AREA MAP  #####
    AreaMapRoot = ET.SubElement(root, "AreaMap")

    # Called when the plugin is selected by the user. Similar to CommandData.Execute.
    AreaMap = doc.SearchObject("AreaMap")

    # Create the root element of the XML structure

    AreaMapRoot.attrib = {
        "unkownAreaGlonalID": "99",
        "numberOfColors": "Unknown",
        "mapWidth": "128",
        "mapHeight": "64",
        "scaleX": str(AreaMap[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y]),
        "scaleY": str(AreaMap[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Z]),
        "positionX": str(AreaMap[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X]),
        "positionY": str(-AreaMap[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y])
    }

    vColorTag = AreaMap.GetTag(c4d.Tvertexcolor)
    if not vColorTag:
        print("No VertexColorTag found on the object")
        return

    # Get the bitmap from the VertexColorTag
    data = vColorTag.GetDataAddressR()

    # Iterate through points to get the color and convert it to a value
    for i in range(128):  # Assuming a height of 64
        AreaMapValueElement = ET.SubElement(AreaMapRoot, "MapValue")
        values = []

        for i2 in range(64):  # Assuming a width of 128
            value = c4d.VertexColorTag.GetPoint(data, None, None, i * 64 + i2)
            value = color_to_value(value)
            values.append(value)

        AreaMapValueElement.attrib = {"values": ",".join(values)}

    ##### AREA MAP  #####

    ##### LUMA MAP  #####
    LumaMapRoot = ET.SubElement(root, "LumaMap")

    # Called when the plugin is selected by the user. Similar to CommandData.Execute.
    LumaMap = doc.SearchObject("LumaMap")
    
    # Create the root element of the XML structure

    LumaMapRoot.attrib = {
        "unkownAreaGlonalID": "99",
        "numberOfColors": "0",
        "mapWidth": "256",
        "mapHeight": "128",
        "scaleX": str(LumaMap[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y]),
        "scaleY": str(LumaMap[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Z]),
        "positionX": str(LumaMap[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X]),
        "positionY": str(-LumaMap[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y])
    }

    vColorTag = LumaMap.GetTag(c4d.Tvertexcolor)
    if not vColorTag:
        print("No VertexColorTag found on the object")
        return

    # Get the bitmap from the VertexColorTag
    data = vColorTag.GetDataAddressR()

    # Iterate through points to get the color and convert it to a value
    for i in range(256):  # Assuming a height of 64
        LumaMapValueElement = ET.SubElement(LumaMapRoot, "MapValue")
        values = []

        for i2 in range(128):  # Assuming a width of 128
            value = c4d.VertexColorTag.GetPoint(data, None, None, i * 128 + i2)
            value = color_to_luma(value)
            values.append(value)

        LumaMapValueElement.attrib = {"values": ",".join(values)}

    ##### LUMA MAP  #####

    ##### SITE MAPS  #####
    SiteMapsRoot = ET.SubElement(root, "SiteMaps")
    SiteMapsContainer = doc.SearchObject("SiteMapPieces")

    CurrentMapPiece = SiteMapsContainer.GetDown()
    
    while CurrentMapPiece:
        #process_children(child)
        if CurrentMapPiece:
            print(CurrentMapPiece.GetName())

            mapType = CurrentMapPiece.GetName().split("_")[0]
            className = mapType

            SiteName = CurrentMapPiece.GetName().split("_")[1]

            if(len(CurrentMapPiece.GetName().split("_")) > 2):
                subID = CurrentMapPiece.GetName().split("_")[2]
            else:
                subID = ""

            SiteMapLocationNode = ET.SubElement(SiteMapsRoot, "MapLocation")
            SiteMapLocationNode.attrib = {
                "siteName": SiteName,
                "subID": subID,
                "scaleX": str(CurrentMapPiece[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X]),
                "scaleY": str(CurrentMapPiece[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y]),
                "positionX": str(CurrentMapPiece[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X]),
                "positionY": str(-CurrentMapPiece[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y]),
                "className": className
            }

            subMapPiece = CurrentMapPiece.GetDown()

            while subMapPiece:
                if(len(subMapPiece.GetName().split("_")) > 2):
                    pieceID = subMapPiece.GetName().split("_")[2]
                else:
                    pieceID = ""

                SiteMapPieceLocationNode = ET.SubElement(SiteMapLocationNode, "SiteMapPiece")
                SiteMapPieceLocationNode.attrib = {
                    "pieceID": pieceID,
                    "scaleX": str(subMapPiece[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X]),
                    "scaleY": str(subMapPiece[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y]),
                    "positionX": str(subMapPiece[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X]),
                    "positionY": str(-subMapPiece[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y]),
                }

                subMapPiece = subMapPiece.GetNext()   

        CurrentMapPiece = CurrentMapPiece.GetNext() 
        
    ##### SITE MAPS  #####

    XMLFileName = "LandsOfOblivion_Maps.xml"

    # Add indentation manually to the XML string
    indent(root)

    # Convert the XML structure to a string
    xmlString = ET.tostring(root, encoding="utf-8").decode()

    # Ask the user to choose where to save the file
    save_path = c4d.storage.SaveDialog(def_path=XMLFileName)

    print("Finished Parsing")

    # Write the XML tree to a file
    tree = ET.ElementTree(root)

    if save_path:
        tree.write(save_path, encoding='utf-8', xml_declaration=False)
        print("Done!!!!")
        c4d.gui.MessageDialog("Export successful! File saved to: " + save_path)

    print(xmlString)
