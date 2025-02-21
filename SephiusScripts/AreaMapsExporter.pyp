from typing import Optional
import c4d
import os
import random
import xml.etree.ElementTree as ET
import xml.dom.minidom
from c4d import plugins, bitmaps # type: ignoreround(
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

def generate_unique_colors(unique_values):
    """Gera um dicionário de cores RGB únicas para cada valor do mapa."""
    random.seed(42)  
    available_colors = set()

    def random_color():
        """Gera uma cor RGB aleatória que ainda não foi usada"""
        while True:
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            if color not in available_colors:
                available_colors.add(color)
                return color

    return {value: random_color() for value in unique_values}

def save_colored_texture(map_name, data, width, height, texture_directory):
    """Cria e salva a versão colorida do mapa onde cada valor recebe uma cor aleatória."""
    print(f"Generating colored texture for {map_name}...")

    # Identificar valores únicos no mapa
    unique_values = set(round(value * 100) for value in data)

    # Criar cores aleatórias para cada valor
    color_map = generate_unique_colors(unique_values)

    # Criar bitmap colorido
    bmp = bitmaps.BaseBitmap()
    bmp.Init(width, height)

    for i in range(height):
        for j in range(width):
            index = j + i * (width + 1)
            value = round(data[index] * 100)

            if value not in color_map:
                print(f"Valor não encontrado no color_map: {value}")
                continue  # Pule a iteração atual e evite o erro

            r, g, b = color_map[value]  # Obtém cor associada ao valor
            bmp.SetPixel(j, i, r, g, b)

    # Salvar PNG colorido
    png_filename = f"LoO{map_name}Colored.png"
    png_path = os.path.join(texture_directory, png_filename)
    result = bmp.Save(png_path, c4d.FILTER_PNG, None)
    
    if result == c4d.IMAGERESULT_OK:
        print(f"Saved {png_filename} at {png_path}")
    else:
        print(f"Failed to save {png_filename}")

    # Criar e salvar XML externo (somente referência ao PNG)
    xml_filename = f"LoO{map_name}Colored.xml"
    xml_path = os.path.join(texture_directory, xml_filename)

    xml_root = ET.Element("TextureAtlas", {
        "imagePath": png_filename,
        "width": str(width),
        "height": str(height)
    })
    ET.SubElement(xml_root, "SubTexture", {
        "name": f"{png_filename.replace('.png', '')}_default",
        "x": "0",
        "y": "0",
        "width": str(width),
        "height": str(height)
    })

    indent(xml_root)
    xml_tree = ET.ElementTree(xml_root)
    xml_tree.write(xml_path, encoding='utf-8', xml_declaration=True)
    print(f"Saved {xml_filename} at {xml_path}")


def save_texture_and_xml(map_name, map_object, map_cache, texture_directory, main_root):
    """Gera o mapa de texturas e o XML correspondente para uso externo"""
    if not map_object:
        print(f"{map_name} not found.")
        return

    global save_path

    map_width = map_object[c4d.PRIM_PLANE_SUBW]
    map_height = map_object[c4d.PRIM_PLANE_SUBH]
    bbox = map_object.GetRad()
    half_width = bbox.x
    half_height = bbox.y

    scale_x = map_object[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_X]
    scale_y = map_object[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_Y]
    position_x = map_cache.GetMg().off.x - (half_width * scale_x)
    position_y = -map_cache.GetMg().off.y - (half_height * scale_y)

    # Salvar PNG
    png_filename = f"LoO{map_name}.png"
    png_path = os.path.join(texture_directory, png_filename)
    bin_directory = os.path.abspath(os.path.join(os.path.dirname(save_path), "../.."))
    relative_png_path = os.path.relpath(png_path, bin_directory)

    # Criar nó dentro do XML principal
    map_root = ET.SubElement(main_root, map_name, {
        "numberOfColors": "256" if "Area" in map_name else "1",
        "dataName": str(f"LoO{map_name}"),
        "scaleX": str(scale_x),
        "scaleY": str(scale_y),
        "positionX": str(position_x),
        "positionY": str(position_y)
    })

    vmap_tag = map_cache.GetTag(c4d.Tvertexmap)
    if not vmap_tag:
        print(f"No Vertex Map Tag found on {map_name}")
        return

    data = vmap_tag.GetAllHighlevelData()
    bmp = bitmaps.BaseBitmap()
    bmp.Init(map_width, map_height)

    for i in range(map_height):
        #map_value_element = ET.SubElement(map_root, "MapValue")
        values = []
        for j in range(map_width):
            index = j + i * (map_width + 1)
            value = data[index]
            value_scaled = round(value * (255 if "Luma" in map_name else 100))  
            values.append(str((value if "Luma" in map_name else round(value * 100))))
            bmp.SetPixel(j, i, value_scaled, value_scaled, value_scaled)

        #map_value_element.attrib = {"values": ",".join(values)}

    result = bmp.Save(png_path, c4d.FILTER_PNG, None)
    if result == c4d.IMAGERESULT_OK:
        print(f"Saved {png_filename} at {png_path}")
    else:
        print(f"Failed to save {png_filename}")

    # Criar e salvar XML externo (somente referência ao PNG)
    xml_filename = f"LoO{map_name}.xml"
    xml_path = os.path.join(texture_directory, xml_filename)
    
    xml_root = ET.Element("TextureAtlas", {
        "imagePath": png_filename,
        "width": str(map_width),
        "height": str(map_height)
    })
    ET.SubElement(xml_root, "SubTexture", {
        "name": f"{png_filename.replace('.png', '')}_default",
        "x": "0",
        "y": "0",
        "width": str(map_width),
        "height": str(map_height)
    })

    indent(xml_root)
    xml_tree = ET.ElementTree(xml_root)
    xml_tree.write(xml_path, encoding='utf-8', xml_declaration=True)
    print(f"Saved {xml_filename} at {xml_path}")

    # Criar versão alternativa colorida para AreaMap
    if "Area" in map_name or "BG" in map_name:
        save_colored_texture(map_name, data, map_width, map_height, texture_directory)

def main(doc) -> None:
    XMLFileName = "LandsOfOblivion_Maps.xml"
    global save_path
    save_path = c4d.storage.SaveDialog(def_path=XMLFileName)

    if not save_path:
        return

    bin_directory = os.path.abspath(os.path.join(os.path.dirname(save_path), "../.."))
    texture_directory = os.path.join(bin_directory, "assets", "textures", "high", "gameplay")
    os.makedirs(texture_directory, exist_ok=True)

    root = ET.Element("AreaMaps")
    root.attrib = {"regionName": "LANDS_OF_OBLIVION"}

    # Gerar mapas de textura e XML para AreaMap e LumaMap
    area_map = doc.SearchObject("AreaMap")
    if area_map:
        area_map_cache = area_map.GetCache()
        save_texture_and_xml("AreaMap", area_map, area_map_cache, texture_directory, root)

    luma_map = doc.SearchObject("LumaMap")
    if luma_map:
        luma_map_cache = luma_map.GetCache()
        save_texture_and_xml("LumaMap", luma_map, luma_map_cache, texture_directory, root)
   
    bg_map = doc.SearchObject("BGMap")
    if bg_map:
        bg_map_cache = bg_map.GetCache()
        save_texture_and_xml("BGMap", bg_map, bg_map_cache, texture_directory, root)
   
    # **Adicionar Site Maps ao XML**
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
            ET.SubElement(site_map_location_node, "SiteMapPiece", {
                "pieceID": sub_map_piece.GetName().split("_")[2] if len(sub_map_piece.GetName().split("_")) > 2 else "",
                "scaleX": str(sub_map_piece[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_X]),
                "scaleY": str(sub_map_piece[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_Y]),
                "positionX": str(sub_map_piece[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X]),
                "positionY": str(-sub_map_piece[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y])
            })

            sub_map_piece = sub_map_piece.GetNext()

        current_map_piece = current_map_piece.GetNext()
        
    indent(root)
    tree = ET.ElementTree(root)
    tree.write(save_path, encoding='utf-8', xml_declaration=True)
    print(f"Export successful! File saved to: {save_path}")
    c4d.gui.MessageDialog("Export successful!")