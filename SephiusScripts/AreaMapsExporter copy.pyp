from typing import Optional
import c4d
import os
import random
import xml.etree.ElementTree as ET
import xml.dom.minidom
from c4d import plugins, bitmaps # type: ignore
import os
PLUGIN_ID = 2242901

doc: c4d.documents.BaseDocument  # The active document
op: Optional[c4d.BaseObject]  # The active object, None if unselected

class AreaMapsExporter(plugins.CommandData):
    def Execute(self, doc):
        # Coloque aqui o código que seu script deve executar
        main(doc)
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
    c4d.plugins.RegisterCommandPlugin(id=PLUGIN_ID, str="Sephius Area Maps Exporter",
                                      info=0, icon=icon, help="Export Area Maps to XML file",
                                      dat=AreaMapsExporter())

def color_to_value(color):
    rounded_value = round(color.x * 100)
    #print(rounded_value)
    return str(int(rounded_value))

def indent(elem, level=0):
    """Recursive function to add indentation to XML elements."""
    indent_str = "  "  
    i = "\n" + level * indent_str  

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

def save_texture_and_xml(map_name, map_object, map_cache, texture_directory):
    """Gera o mapa de texturas e o arquivo XML correspondente"""
    if not map_object:
        print(f"{map_name} not found.")
        return

    map_width = map_object[c4d.PRIM_PLANE_SUBW]
    map_height = map_object[c4d.PRIM_PLANE_SUBH]
    bbox = map_object.GetRad()
    half_width = bbox.x
    half_height = bbox.y

    scale_x = map_object[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_X]
    scale_y = map_object[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_Y]
    position_x = map_cache.GetMg().off.x - (half_width * scale_x)
    position_y = -map_cache.GetMg().off.y - (half_height * scale_y)

    map_root = ET.Element(map_name)
    map_root.attrib = {
        "unkownAreaGlobalID": "99",
        "numberOfColors": "256" if "Area" in map_name else "1",
        "mapWidth": str(map_width),
        "mapHeight": str(map_height),
        "scaleX": str(scale_x),
        "scaleY": str(scale_y),
        "positionX": str(position_x),
        "positionY": str(position_y)
    }

    vmap_tag = map_cache.GetTag(c4d.Tvertexmap)
    if not vmap_tag:
        print(f"No Vertex Map Tag found on {map_name}")
        return

    data = vmap_tag.GetAllHighlevelData()
    bmp = bitmaps.BaseBitmap()
    bmp.Init(map_width, map_height)

    for i in range(map_height):
        map_value_element = ET.SubElement(map_root, "MapValue")
        values = []
        for j in range(map_width):
            index = j + i * (map_width + 1)
            value = data[index]
            value_scaled = int(value * (255 if "Luma" in map_name else 100))  
            values.append(str(value_scaled))
            bmp.SetPixel(j, i, value_scaled, value_scaled, value_scaled)

        map_value_element.attrib = {"values": ",".join(values)}

    # Salvar PNG
    png_filename = f"LoO{map_name}.png"
    png_path = os.path.join(texture_directory, png_filename)
    result = bmp.Save(png_path, c4d.FILTER_PNG, None)
    if result == c4d.IMAGERESULT_OK:
        print(f"Saved {png_filename} at {png_path}")
    else:
        print(f"Failed to save {png_filename}")

    # Salvar XML
    xml_filename = f"LoO{map_name}.xml"
    xml_path = os.path.join(texture_directory, xml_filename)
    indent(map_root)
    tree = ET.ElementTree(map_root)
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)
    print(f"Saved {xml_filename} at {xml_path}")

def main(doc) -> None:
    XMLFileName = "LandsOfOblivion_Maps.xml"
    save_path = c4d.storage.SaveDialog(def_path=XMLFileName)

    if not save_path:
        return

    # Definir caminho final para assets/textures/high/debug
    bin_directory = os.path.abspath(os.path.join(os.path.dirname(save_path), ".."))    
    texture_directory = os.path.join(bin_directory, "assets", "textures", "high", "debug")
    os.makedirs(texture_directory, exist_ok=True)

    root = ET.Element("AreaMaps")
    root.attrib = {"regionName": "LANDS_OF_OBLIVION"}

    # Gerar mapas de textura e XML para AreaMap e LumaMap
    area_map = doc.SearchObject("AreaMap")
    if area_map:
        area_map_cache = area_map.GetCache()
        save_texture_and_xml("AreaMap", area_map, area_map_cache, texture_directory)

    luma_map = doc.SearchObject("LumaMap")
    if luma_map:
        luma_map_cache = luma_map.GetCache()
        save_texture_and_xml("LumaMap", luma_map, luma_map_cache, texture_directory)

    # Adicionar estrutura de SiteMaps
    site_maps_root = ET.SubElement(root, "SiteMaps")
    site_maps_container = doc.SearchObject("SiteMapPieces")
    current_map_piece = site_maps_container.GetDown() if site_maps_container else None

    while current_map_piece:
        map_type = current_map_piece.GetName().split("_")[0]
        site_name = current_map_piece.GetName().split("_")[1]
        sub_id = current_map_piece.GetName().split("_")[2] if len(current_map_piece.GetName().split("_")) > 2 else ""

        site_map_location_node = ET.SubElement(site_maps_root, "MapLocation", {
            "siteName": site_name,
            "subID": sub_id,
            "scaleX": str(current_map_piece[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_X]),
            "scaleY": str(current_map_piece[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_Y]),
            "positionX": str(current_map_piece[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X]),
            "positionY": str(-current_map_piece[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y]),
            "className": map_type
        })

        sub_map_piece = current_map_piece.GetDown()
        while sub_map_piece:
            piece_id = sub_map_piece.GetName().split("_")[2] if len(sub_map_piece.GetName().split("_")) > 2 else ""

            ET.SubElement(site_map_location_node, "SiteMapPiece", {
                "pieceID": piece_id,
                "scaleX": str(sub_map_piece[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_X]),
                "scaleY": str(sub_map_piece[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_Y]),
                "positionX": str(sub_map_piece[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X]),
                "positionY": str(-sub_map_piece[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y])
            })

            sub_map_piece = sub_map_piece.GetNext()

        current_map_piece = current_map_piece.GetNext()

    indent(root)
    xml_path = save_path
    tree = ET.ElementTree(root)
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)
    print(f"Export successful! File saved to: {xml_path}")
    c4d.gui.MessageDialog("Export successful!")