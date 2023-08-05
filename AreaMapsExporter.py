from typing import Optional
import c4d
import xml.etree.ElementTree as ET
import xml.dom.minidom

doc: c4d.documents.BaseDocument  # The active document
op: Optional[c4d.BaseObject]  # The active object, None if unselected

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
    
    OblivionLandsBox = SiteMapsContainer.GetDown()
    print(OblivionLandsBox.GetName())
    
    OblivionLandsBoxNode = ET.SubElement(SiteMapsRoot, "MapLocation")
    OblivionLandsBoxNode.attrib = {
        "TextureName": OblivionLandsBox.GetName(),
        "scaleX": str(OblivionLandsBox[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X]),
        "scaleY": str(OblivionLandsBox[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y]),
        "positionX": str(OblivionLandsBox[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X]),
        "positionY": str(-OblivionLandsBox[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y]),
        "className": "MapLocation"
    }

    CurrentMapPiece = OblivionLandsBox.GetNext()
    while CurrentMapPiece:
        #process_children(child)
        if CurrentMapPiece:
            print(CurrentMapPiece.GetName())
    
            SiteMapLocationNode = ET.SubElement(SiteMapsRoot, "MapLocation")
            SiteMapLocationNode.attrib = {
                "siteName": CurrentMapPiece.GetName().split("_")[1],
                "scaleX": str(CurrentMapPiece[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X]),
                "scaleY": str(CurrentMapPiece[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y]),
                "positionX": str(CurrentMapPiece[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X]),
                "positionY": str(-CurrentMapPiece[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y]),
                "className": "SiteMap"
            }

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

"""
def state():
    # Defines the state of the command in a menu. Similar to CommandData.GetState.
    return c4d.CMD_ENABLED
"""

if __name__ == '__main__':
    main()