import c4d # type: ignore
import os
from c4d import gui # type: ignore
from c4d import storage # type: ignore
from c4d import utils # type: ignore
from xml.etree import ElementTree
import math 
from c4d import plugins, bitmaps # type: ignore
import os
PLUGIN_ID = 2242903

class SephiusSpriteSheetToC4D(plugins.CommandData):
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
    icon_path = os.path.join(dir_path, "SephiusSpriteSheetToC4D.tif")
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
    c4d.plugins.RegisterCommandPlugin(id=PLUGIN_ID, str="Sephius Sprite Sheet To C4D",
                                      info=0, icon=icon, help="Import sprite sheet in XML format to Cinema 4D as planes with UVW and Materials.",
                                      dat=SephiusSpriteSheetToC4D())

XMLpath = ""
PNGpath = ""
#FileName = ""
folderPath = ""
TextureSizeRatio = 1
TextureBiggerSize = 1024

Csample = ""
SamplesContainer = ""

global ScaleRatio
ScaleRatio = 1

#Define the pivot center of a sprite when it has transparent pixels cropped during pack process and that made center offset
def setPivotDiff(TextureNode):
    # Check if frame information is present
    frameX = TextureNode.attrib.get("frameX")
    frameY = TextureNode.attrib.get("frameY")

    if frameX is not None and frameY is not None:
        frameX = float(frameX)
        frameY = float(frameY)
        frameWidth = float(TextureNode.attrib.get("frameWidth"))
        frameHeight = float(TextureNode.attrib.get("frameHeight"))

        # Check for rotation
        rotated = TextureNode.attrib.get("rotated") == "true"

        if rotated:
            # Swap width and height if rotated
            width = float(TextureNode.attrib.get("height"))
            height = float(TextureNode.attrib.get("width"))
        else:
            width = float(TextureNode.attrib.get("width"))
            height = float(TextureNode.attrib.get("height"))

        # Calculate the center of the original rectangle (assuming it starts at 0,0)
        originalCenterX = width / 2
        originalCenterY = height / 2

        # Calculate the center of the frame
        frameCenterX = frameX + frameWidth / 2
        frameCenterY = frameY + frameHeight / 2

        if rotated:   
            # Calculate the difference in centers, scaled
            CDIFFY = (originalCenterX - frameCenterX) * ScaleRatio
            CDIFFX = (originalCenterY - frameCenterY) * ScaleRatio
            pivotDiff = c4d.Vector(-CDIFFX, -CDIFFY, 0)
        else:
            CDIFFX = (originalCenterX - frameCenterX) * ScaleRatio
            CDIFFY = (originalCenterY - frameCenterY) * ScaleRatio
            pivotDiff = c4d.Vector(CDIFFX, -CDIFFY, 0)
    else:
        pivotDiff = c4d.Vector(0, 0, 0)

    return pivotDiff

#Return true if object has a user data name and value is equal to desired
def HasUserData(CObject, UDName):
    for id, bc in CObject.GetUserDataContainer():
        if bc[c4d.DESC_NAME] == UDName:
            return True
    return False

#Return true if object has a user data name and value is equal to desired
def UserDataCheck(CObject, UDName, Value):
    for id, bc in CObject.GetUserDataContainer():
        #print(bc[c4d.DESC_NAME], UDName)
        if bc[c4d.DESC_NAME] == UDName:
            #print(CObject[id], Value)
            if CObject[id] == Value:
                return True
    return False

def UserDataAndTextureNameCheck(CObject, TexName, UserDataNAme, Value):
    UserDataCconslusion = False
    TexNameCconslusion = False

    if UserDataCheck(CObject, UserDataNAme, Value):
        UserDataCconslusion = True

    if UserDataCheck(CObject, "texture", TexName):
        TexNameCconslusion = True

    if c4d.InstanceObject == type(CObject):
        #if have a reference to a sample
        SampleRef = CObject[c4d.INSTANCEOBJECT_LINK]
        if SampleRef:
            if UserDataCheck(CObject[c4d.INSTANCEOBJECT_LINK], "texture", TexName):
                TexNameCconslusion = True

    #print ("TexNameCconslusion: ", TexNameCconslusion, " TexNameCconslusion: ", UserDataCconslusion)
    return TexNameCconslusion and UserDataCconslusion

def UserDataAndNameCheck(CObject, OName, UDName, Value):
    #print(CObject.GetName(), OName, UserDataCheck(CObject, UDName, Value), CObject.GetName().split(".")[0] == OName)
    #atlasName = GetUserData(CObject, "Atlas")

    #if not CObject.GetUp():
        #return False
    #if not atlasName:
        #return False
    #if CObject.GetUp().GetName() != CObject[atlasName] + " Samples":
        #return False
    #print(UserDataCheck(CObject, UDName, Value), UDName, Value)
    if not UserDataCheck(CObject, UDName, Value):
        return False
    if not CObject.GetName().split(".")[0] == OName:
        return False
    return True

def get_all_objects(container, filter_function=lambda x: True):
    """
    Itera recursivamente pelos objetos filhos de um Container no Cinema 4D,
    processando subcontainers e seus descendentes.

    Args:
        container (c4d.BaseObject): O objeto inicial cujos filhos serão processados.
        filter_function (function): Uma função lambda que retorna True para objetos que devem ser incluídos.
                                    Por padrão, todos os objetos são incluídos.

    Returns:
        list: Uma lista de objetos filhos que atendem ao critério do filtro.
    """
    if not container:
        return []

    filtered_objects = []

    # Obter o primeiro filho do container
    child = container.GetDown()

    # Iterar pelos filhos
    while child:
        # Aplica o filtro; se for True, adiciona o objeto à lista
        if filter_function(child):
            filtered_objects.append(child)

        # Recursivamente processar os filhos do objeto atual (subcontainers e seus descendentes)
        filtered_objects.extend(get_all_objects(child, filter_function))

        # Ir para o próximo objeto no mesmo nível (entre os filhos do container)
        child = child.GetNext()

    return filtered_objects

def getChildrenWithPrefix(parent, childPrefix):
    PChildren = []
    nextObject = parent.GetDown()

    if nextObject:
        if nextObject[c4d.ID_BASELIST_NAME].find(childPrefix) != -1:
            PChildren.append(nextObject)

    while nextObject:
        nextObject = nextObject.GetNext()
        if nextObject:
            if nextObject[c4d.ID_BASELIST_NAME].find(childPrefix) != -1:
               PChildren.append(nextObject)

    return PChildren

def hasChild(parent, childName):
    PChildren = []
    nextObject = parent.GetDown()

    if nextObject[c4d.ID_BASELIST_NAME] == childName:
        return True

    while nextObject:
        nextObject = nextObject.GetNext()
        if nextObject:
            if nextObject[c4d.ID_BASELIST_NAME] == childName:
                return True

    return False

def getChild(parent, childName):
    if not parent:
        print("Parent is NONE: ", parent, " childName: ", childName)
        return None
     
    PChildren = []
    nextObject = parent.GetDown()

    if nextObject:
        if nextObject[c4d.ID_BASELIST_NAME] == childName:
            return nextObject

    while nextObject:
        nextObject = nextObject.GetNext()
        if nextObject:
            if nextObject[c4d.ID_BASELIST_NAME] == childName:
                return nextObject

    return None

def IsUserDataSupported(CObject):
    """
    Verifica se o objeto suporta User Data Container.

    Args:
        CObject (c4d.BaseObject): O objeto a ser verificado.

    Returns:
        bool: True se o objeto suporta User Data, False caso contrário.
    """

    if not IsValidObject(CObject):
        return False

    # Verifica se o método GetUserDataContainer existe no objeto
    if not hasattr(CObject, 'GetUserDataContainer'):
        return False

    return True

def IsValidObject(obj):
    """
    Verifica se um objeto do Cinema 4D é válido para uso.
    
    Args:
        obj (c4d.BaseObject): O objeto a ser verificado.
        
    Returns:
        bool: True se o objeto for válido, False caso contrário.
    """
    # Verifica se o objeto é uma instância de BaseList2D (o que inclui objetos com User Data)
    if not isinstance(obj, c4d.BaseList2D):
        print(f"Objeto não é instancia de BaseList2D: {e}")
        return False
    
    try:
        # Verifica se o objeto não é None
        if obj is None:
            return False
                
        # Tenta acessar o nome para garantir que a referência está válida
        _ = obj.GetName()
        print("Trying to Validate: ", obj)
        return True
    except Exception as e:
        # Qualquer exceção capturada indica que o objeto é inválido
        print(f"Objeto inválido detectado: {e}")
        return False

#Return true if object has a user data name and value is equal to desired
def GetUserData(CObject, UDName):
    print("GetUserData OBJECT?: ", CObject)
    print("GetUserData: ", CObject.GetName(), UDName)
    if not IsUserDataSupported(CObject):  # Verifica se o objeto é válido
        print(f"Erro: Não é possível acessar o UserData '{UDName}'")
        return None

    for id, bc in CObject.GetUserDataContainer():
        #print(bc[c4d.DESC_NAME], UDName)
        if bc[c4d.DESC_NAME] == UDName:
            return id

    return None

def setColorTagWithData(CContainer):
    cAlpha = 1

    #CTag = c4d.BaseTag(c4d.Tvertexcolor)
    #CTag.SetName()

    #CTag.SetPerPointMode(False)
    #CTag.SetPerPointMode(True)
    #CTag.SetPerPointMode(False)

    #Enable Color Tag Fields
    CTag = c4d.VertexColorTag(CContainer.GetPointCount())
    CTag.__init__(CContainer.GetPointCount())
    CContainer.InsertTag(CTag)

    CTag[c4d.ID_VERTEXCOLOR_USEFIELDS] = True
    CTag[c4d.ID_VERTEXCOLOR_ALPHAMODE] = True

    # Create a new solid field layer
    FieldAlpha = c4d.BaseList2D(c4d.FLsolid)
    FieldAlpha.SetName("Alpha")

    # Set the color of the solid field to red
    FieldAlpha[c4d.FIELDLAYER_SOLID_COLOR] = c4d.Vector(1, 1, 1)

    # Set the opacity value
    FieldAlpha.SetStrength(cAlpha)

    FieldColor = c4d.BaseList2D(c4d.FLcolorize)
    FieldColor[c4d.FIELDLAYER_COLORIZE_MODE] = 1
    FieldColor[c4d.FIELDLAYER_COLORIZE_COLORBASE] = c4d.Vector(1, 1, 1)
    FieldColor[c4d.FIELDLAYER_COLORIZE_COLORTOP] = c4d.Vector(1, 1, 1)
    FieldColor[c4d.FIELDLAYER_COLORIZE_COLORTOP_MODE] = 1
    FieldColor[c4d.FIELDLAYER_COLORIZE_COLORTOP_DENSITY] = 1
    FieldColor[c4d.FIELDLAYER_COLORIZE_CLIP] = True
    #FieldColorlamp[c4d.FIELDLAYER_CLAMP_MIN_VALUE] = 1
    FieldColor.SetName("Color")

    # Add a new Field to the tag
    # Get the Vertex Color Field container
    CTag_field_container = CTag.GetParameter(c4d.ID_VERTEXCOLOR_FIELDS, 0)
    CTag_field_container.InsertLayer(FieldAlpha)
    CTag_field_container.InsertLayer(FieldColor)
    CTag[c4d.ID_VERTEXCOLOR_FIELDS] = CTag_field_container

def SetRefPolygon(ParentName, CObject, UVWTag, Polygon, TextureNode):
    print("SetRefPolygon: ", ParentName, CObject.GetName(), UVWTag, Polygon, TextureNode)
    #AtlasWidth =  float(TextureNode.attrib.get("width")) * ScaleRatio
    #AtlasHeight = float(TextureNode.attrib.get("height")) * ScaleRatio

    pcount = CObject.GetPointCount()
    points = CObject.GetAllPoints()

    CHalfWidth = float(TextureNode.attrib.get("width")) * 0.5
    CHalfHeight = float(TextureNode.attrib.get("height")) * 0.5
    print("pcount1 ", pcount)
    pivotDiff = setPivotDiff(TextureNode)

    CX = float(TextureNode.attrib.get("x")) - AtlasHalfWidth + CHalfWidth
    CY = -float(TextureNode.attrib.get("y")) + AtlasHalfHeight - CHalfHeight
    CPX = -float(TextureNode.attrib.get("width")) * 0.5
    CPY = float(TextureNode.attrib.get("height")) * 0.5
    CPW = float(TextureNode.attrib.get("width")) * 0.5
    CPH = -float(TextureNode.attrib.get("height")) * 0.5

    #print(ScaleRatio)

    CX = CX * ScaleRatio
    CY = CY * ScaleRatio
    pX = CPX * ScaleRatio
    pY = CPY * ScaleRatio
    hX = CPW * ScaleRatio
    hY = CPH * ScaleRatio
    
    PSs = []
    PSs.append(c4d.Vector(pX, pY, 0) + pivotDiff)
    PSs.append(c4d.Vector(hX, pY, 0) + pivotDiff)
    PSs.append(c4d.Vector(hX, hY, 0) + pivotDiff)
    PSs.append(c4d.Vector(pX, hY, 0) + pivotDiff)
    
    rotated = TextureNode.attrib.get("rotated") == "true"
    
    if rotated:
        # create the rotation matrix for 90 degrees counterclockwise
        rotation_matrix = [[0, -1], [1, 0]]

        # apply the rotation to each point
        rotated_Pss = []
        for point in PSs:
            x = point.x
            y = point.y
            rotated_x = rotation_matrix[0][0]*x + rotation_matrix[0][1]*y
            rotated_y = rotation_matrix[1][0]*x + rotation_matrix[1][1]*y
            rotated_Pss.append(c4d.Vector(rotated_x, rotated_y, 0))

        PSs = rotated_Pss
    
        #re-rotate the object
        CObject[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = math.pi / 2

    if not Polygon or pcount == 0:
        print("Polygon is None or has no points")
        Polygon = c4d.CPolygon(0, 1, 2, 3)
        Polygon.__init__(0, 1, 2, 3)
        CObject.ResizeObject(4, 1)
        CObject.SetPolygon(0, Polygon)
        pcount = CObject.GetPointCount()

    print("pcount2 ", CObject.GetPointCount(), "polygon: ", Polygon, "points: ", PSs)
    for i in range(pcount):
        CObject.SetPoint(i, PSs[i])

    #print("UV Coord px: ", float(TextureNode.attrib.get("x")), float(TextureNode.attrib.get("y")), float(TextureNode.attrib.get("width")), float(TextureNode.attrib.get("height")))
    CoX = float(TextureNode.attrib.get("x")) * ScaleRatio / AtlasWidth
    CoY = float(TextureNode.attrib.get("y"))  * ScaleRatio / AtlasHeight
    CoHX = (float(TextureNode.attrib.get("x")) + float(TextureNode.attrib.get("width"))) * ScaleRatio / AtlasWidth
    CoHY = (float(TextureNode.attrib.get("y")) + float(TextureNode.attrib.get("height"))) * ScaleRatio / AtlasHeight

    PCSs = []
    PCSs.append(c4d.Vector(CoX, CoY, 0))
    PCSs.append(c4d.Vector(CoHX, CoY, 0))
    PCSs.append(c4d.Vector(CoHX, CoHY, 0))
    PCSs.append(c4d.Vector(CoX, CoHY, 0))

    if not UVWTag:
        UVWTag = CObject.MakeVariableTag(c4d.Tuvw, 1)
        UVWTag[c4d.ID_BASELIST_NAME] = "SampleUVW"
        CObject.InsertTag(UVWTag)

    UVWTag.SetSlow(0, PCSs[0], PCSs[1], PCSs[2], PCSs[3])

def UpdateScenePolygonUVs(ScenePolygonObject, SampleReference):
    """
    Atualiza os dados UV de um PolygonObject com base em um SampleReference e o atlas de textura,
    preservando as proporções relativas do mapeamento UV original.
    """
    print("UpdateScenePolygonUVs: ", ScenePolygonObject.GetName(), SampleReference.GetName())

    # Verifica se o objeto de referência é um PolygonObject
    isPolygon = isinstance(SampleReference, c4d.PolygonObject)
    if not isPolygon:
        print(f"Erro: SampleReference '{SampleReference.GetName()}' não é um PolygonObject.")
        return

    # Verificar tags UV
    uv_tag = ScenePolygonObject.GetTag(c4d.Tuvw)
    Refuv_tag = SampleReference.GetTag(c4d.Tuvw)
    if not uv_tag or not Refuv_tag:
        print(f"Erro: UVTag ausente em {ScenePolygonObject.GetName()} ou {SampleReference.GetName()}.")
        return

    # Coordenadas UV da referência
    uvwRef = Refuv_tag.GetSlow(0)
    REFuvPoints = [uvwRef["a"], uvwRef["b"], uvwRef["c"], uvwRef["d"]]

    # Determinar os limites UV da referência
    ref_uMin, ref_uMax = min(p.x for p in REFuvPoints), max(p.x for p in REFuvPoints)
    ref_vMin, ref_vMax = min(p.y for p in REFuvPoints), max(p.y for p in REFuvPoints)
    print(f"Limites UV da referência: u=[{ref_uMin}, {ref_uMax}], v=[{ref_vMin}, {ref_vMax}]")

    # Coordenadas UV do objeto da cena
    all_uv_points = []
    for i in range(ScenePolygonObject.GetPolygonCount()):
        uvw = uv_tag.GetSlow(i)
        all_uv_points.extend([uvw["a"], uvw["b"], uvw["c"], uvw["d"]])

    # Determinar os limites UV do objeto da cena
    obj_uMin, obj_uMax = min(p.x for p in all_uv_points), max(p.x for p in all_uv_points)
    obj_vMin, obj_vMax = min(p.y for p in all_uv_points), max(p.y for p in all_uv_points)
    print(f"Limites UV do objeto da cena: u=[{obj_uMin}, {obj_uMax}], v=[{obj_vMin}, {obj_vMax}]")

    # Atualizar as coordenadas UV para cada polígono
    for i in range(ScenePolygonObject.GetPolygonCount()):
        poly = ScenePolygonObject.GetPolygon(i)
        uvw = uv_tag.GetSlow(i)
        uvPoints = [uvw["a"], uvw["b"], uvw["c"], uvw["d"]]

        # Verifica e ajusta as coordenadas UV com base nos limites
        for j, vertexIndex in enumerate([poly.b, poly.a, poly.c, poly.d]):
            if vertexIndex == -1:  # Vértice inválido em triângulos
                continue

            UVpoint = uvPoints[j]
            u = UVpoint.x
            v = UVpoint.y

            # Ajusta a posição relativa dentro dos limites do objeto da cena
            relative_u = (u - obj_uMin) / (obj_uMax - obj_uMin) if obj_uMax != obj_uMin else 0
            relative_v = (v - obj_vMin) / (obj_vMax - obj_vMin) if obj_vMax != obj_vMin else 0

            # Remapeia para os limites da referência
            u = ref_uMin + (ref_uMax - ref_uMin) * relative_u
            v = ref_vMin + (ref_vMax - ref_vMin) * relative_v

            # Atualiza as coordenadas UV no UVWTag
            uvPoints[j] = c4d.Vector(u, v, 0)

        # Aplica as novas coordenadas UV ao polígono
        uv_tag.SetSlow(i, uvPoints[0], uvPoints[1], uvPoints[2], uvPoints[3])

    # Confirma as alterações no Cinema 4D
    c4d.EventAdd()
    print(f"UVs atualizados para o objeto '{ScenePolygonObject.GetName()}'.")


def remap(value, min_val, max_val):
    """
    Função utilitária para remapear um valor dentro de um intervalo.
    """
    return (value - min_val) / (max_val - min_val)

def PositionOriginalSample(Sample, node, pivotDiff):
    global AtlasHalfWidth
    global AtlasHalfHeight

    #print("pivotDiff: ", pivotDiff, " AtlasHalfWidth: ", AtlasHalfWidth, " AtlasHalfHeight: ", AtlasHalfHeight)
    #print("pivotDiff: ", pivotDiff, " AtlasWidth: ", AtlasWidth, " AtlasHeight: ", AtlasHeight)

    CHalfWidth = float(node.attrib.get("width")) * 0.5 * ScaleRatio
    CHalfHeight = float(node.attrib.get("height")) * 0.5 * ScaleRatio

    Sample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) * ScaleRatio - AtlasHalfWidth + CHalfWidth
    Sample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) * ScaleRatio + AtlasHalfHeight - CHalfHeight
    Sample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
    Sample[c4d.ID_BASEOBJECT_REL_POSITION] = Sample[c4d.ID_BASEOBJECT_REL_POSITION] - (pivotDiff)
    
    rotated = node.attrib.get("rotated")
    if rotated:
        Sample[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = math.pi / 2
    else:
        Sample[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = 0

def PositionOriginalInstance(Instance, node):
    global SamplesContainer

    SampleReference = Instance[c4d.INSTANCEOBJECT_LINK]
    if not SampleReference:
        SampleReference = getChild(SamplesContainer, node.attrib.get("name") + "_Sample")

    print("Positioing Instance Ref Name: ", node.attrib.get("name") + "_Sample", " SampleReference: ", SampleReference)
   
    #print("Instance Ref Object Name: ", SampleReference.GetName())
    if not SampleReference:
        print("Setting Instance Position but Sample Reference not found: ", node.attrib.get("name") + "_Sample")
        return
    
    Instance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = SampleReference[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X]
    Instance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = SampleReference[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y]
    Instance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = SampleReference[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z]
    Instance[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = SampleReference[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z]
    print("Instance Position Set", Instance[c4d.ID_BASEOBJECT_REL_POSITION], SampleReference[c4d.ID_BASEOBJECT_REL_POSITION])

def UpdateExistingSample(ExistingSample, node, pivotDiff, AtlasMaterial, isOriginalSample):
    isPolygonObject = isinstance(ExistingSample, c4d.PolygonObject)

    if not isPolygonObject:
        return
    
    #MVCTag = ExistingSample.GetTag(c4d.Tvertexmap)
    #CTag = ExistingSample.GetTag(c4d.Ttexture)
    #CTag.SetMaterial(AtlasMaterial)
    #ExistingSample.InsertTag(CTag, MVCTag)

    if isOriginalSample:
        #Is is a original sample inside SamplesContainer
        #print("Original Sample")
        PositionOriginalSample(ExistingSample, node, pivotDiff)

    UVWTag = ExistingSample.GetTag(c4d.Tuvw)
    VertexCoord = UVWTag.GetSlow(0)
    for i in range(4):
        if HasUserData(ExistingSample, "Vertex " + str(i) + " Position"):
            element = GetUserData(ExistingSample, "Vertex " + str(i) + " Position")
            ExistingSample[element] = ExistingSample.GetPoint(i)

        if HasUserData(ExistingSample, "Vertex " + str(i) + " UVW"):
            element = GetUserData(ExistingSample, "Vertex " + str(i) + " UVW")

            if i == 0:
                ExistingSample[element] = VertexCoord["a"]
            elif  i == 1:
                ExistingSample[element] = VertexCoord["b"]
            elif  i == 2:
                ExistingSample[element] = VertexCoord["c"]
            else:
                ExistingSample[element] = VertexCoord["d"]

    if HasUserData(ExistingSample, "Offset"):
        element = GetUserData(ExistingSample, "Offset")
        ExistingSample[element] = pivotDiff

    if HasUserData(ExistingSample, "Texture Width"):
        element = GetUserData(ExistingSample, "Texture Width")
        ExistingSample[element] = float(node.attrib.get("width")) * ScaleRatio

    if HasUserData(ExistingSample, "Texture Height"):
        element = GetUserData(ExistingSample, "Texture Height")
        ExistingSample[element] = float(node.attrib.get("height")) * ScaleRatio

    if HasUserData(ExistingSample, "Texture Frame X"):
        element = GetUserData(ExistingSample, "Texture Frame X")
        if(node.attrib.get("frameX")):
            ExistingSample[element] = float(node.attrib.get("frameX")) * ScaleRatio
        else:
            ExistingSample[element] = 0

    if HasUserData(ExistingSample, "Texture Frame Y"):
        element = GetUserData(ExistingSample, "Texture Frame Y")
        if(node.attrib.get("frameY")):
            ExistingSample[element] = float(node.attrib.get("frameY")) * ScaleRatio
        else:
            ExistingSample[element] = 0

    if HasUserData(ExistingSample, "Texture Frame Width"):
        element = GetUserData(ExistingSample, "Texture Frame Width")
        if(node.attrib.get("frameWidth")):
            ExistingSample[element] = float(node.attrib.get("frameWidth")) * ScaleRatio
        else:
            ExistingSample[element] = float(node.attrib.get("width")) * ScaleRatio

    if HasUserData(ExistingSample, "Texture Frame Height"):
        element = GetUserData(ExistingSample, "Texture Frame Height")
        if(node.attrib.get("frameHeight")):
            ExistingSample[element] = float(node.attrib.get("frameHeight")) * ScaleRatio
        else:
            ExistingSample[element] = float(node.attrib.get("height")) * ScaleRatio

    #Fix sample position if pivot has changes so sample continue in same position visually speaking
    #ExistingSample[c4d.ID_BASEOBJECT_REL_POSITION] = ExistingSample[c4d.ID_BASEOBJECT_REL_POSITION] - pivotDiff

def UpdateExistingInstance(ExistingInstance, node, isOriginalInstance):
    isInstanceObject = isinstance(ExistingInstance, c4d.InstanceObject)

    if not isInstanceObject:
        return
    
    global SamplesContainer

    SampleReference = ExistingInstance[c4d.INSTANCEOBJECT_LINK]
    if not SampleReference:
        SampleReference = getChild(SamplesContainer, node.attrib.get("name") + "_Sample")

    print("Existing Instance Ref Name: ", node.attrib.get("name") + "_Sample", SampleReference)

    #If is a original instance inside InstancesContainer, then update it's transform
    if isOriginalInstance:
        #print("Original Instance: ", ExistingInstance.GetName())
        PositionOriginalInstance(ExistingInstance, node)
    
    #Update the Instance Object to use new Sample Object
    ExistingInstance[c4d.INSTANCEOBJECT_LINK] = SampleReference

    #Update Instance Object's User Data to Point to the New Sample Object
    GetUserData(ExistingInstance, "Sample Reference")
    element = GetUserData(ExistingInstance, "Sample Reference")
    if element:
        ExistingInstance[element] = SampleReference
    else:
        CreateNewInstanceData(ExistingInstance, node, isOriginalInstance)

def CreateNewSampleData(NewSample, node, currentName, pivotDiff, AtlasMaterial):
    PositionOriginalSample(NewSample, node, pivotDiff)
    global FileName

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc[c4d.DESC_NAME] = "OBJECT EXPORT INFO"
    bc[c4d.DESC_SHORT_NAME] = "OBJECT EXPORT INFO"
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_DEFAULT] = True
    bc[c4d.DESC_TITLEBAR] = True
    bc[c4d.DESC_COLUMNS] = 1
    ObjectExportGroup = NewSample.AddUserData(bc)
    #NewSample[ObjectExportGroup] = "OBJECT EXPORT INFO"

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc[c4d.DESC_NAME] = "GAME PROPERTIES"
    bc[c4d.DESC_SHORT_NAME] = "GAME PROPERTIES"
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_DEFAULT] = True
    bc[c4d.DESC_TITLEBAR] = True
    bc[c4d.DESC_COLUMNS] = 1
    GamePropertiesGroup = NewSample.AddUserData(bc)
    #NewSample[GamePropertiesGroup] = "GAME PROPERTIES"

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL)
    bc[c4d.DESC_NAME] = "IsSpriteSheetSample"
    bc[c4d.DESC_SHORT_NAME] = "IsSpriteSheetSample"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = ObjectExportGroup
    element = NewSample.AddUserData(bc)
    NewSample[element] = True

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BASELISTLINK)
    bc[c4d.DESC_NAME] = "Sample Reference"
    bc[c4d.DESC_SHORT_NAME] = "Sample Reference"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = ObjectExportGroup
    element = NewSample.AddUserData(bc)
    NewSample[element] = NewSample

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING)
    bc[c4d.DESC_NAME] = "className"
    bc[c4d.DESC_SHORT_NAME] = "className"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = GamePropertiesGroup
    element = NewSample.AddUserData(bc)
    NewSample[element] = "Image"

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING)
    bc[c4d.DESC_NAME] = "texture"
    bc[c4d.DESC_SHORT_NAME] = "texture"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = GamePropertiesGroup
    element = NewSample.AddUserData(bc)
    NewSample[element] = currentName

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING)
    bc[c4d.DESC_NAME] = "Atlas"
    bc[c4d.DESC_SHORT_NAME] = "Atlas"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = GamePropertiesGroup
    element = NewSample.AddUserData(bc)
    NewSample[element] = FileName
    print("FileName inside CreateNewSampleData:", FileName)  # Debug

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING)
    bc[c4d.DESC_NAME] = "blendMode"
    bc[c4d.DESC_SHORT_NAME] = "blendMode"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = GamePropertiesGroup
    element = NewSample.AddUserData(bc)
    NewSample[element] = "normal"

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc[c4d.DESC_NAME] = "Vertex Position"
    bc[c4d.DESC_SHORT_NAME] = "Vertex Position"
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_COLUMNS] = 1
    #bc[c4d.DESC_PARENTGROUP] = C2element
    VertexPositionGroup = NewSample.AddUserData(bc)

    pcount = NewSample.GetPointCount()
    point = NewSample.GetAllPoints()
    for i in range(pcount):
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_VECTOR)
        bc[c4d.DESC_NAME] = "Vertex " + str(i) + " Position"
        bc[c4d.DESC_SHORT_NAME] = "Vertex " + str(i) + " Position"
        bc[c4d.DESC_EDITABLE] = False
        bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
        bc[c4d.DESC_PARENTGROUP] = VertexPositionGroup
        element = NewSample.AddUserData(bc)
        NewSample[element] = NewSample.GetPoint(i)

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_VECTOR)
    bc[c4d.DESC_NAME] = "Offset"
    bc[c4d.DESC_SHORT_NAME] = "Offset"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_TITLEBAR] = True
    bc[c4d.DESC_PARENTGROUP] = VertexPositionGroup
    element = NewSample.AddUserData(bc)
    NewSample[element] = pivotDiff

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc[c4d.DESC_NAME] = "Vertex UVW"
    bc[c4d.DESC_SHORT_NAME] = "Vertex UVW"
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_TITLEBAR] = True
    bc[c4d.DESC_COLUMNS] = 1
    #bc[c4d.DESC_PARENTGROUP] = C2element
    VertexUVWGroup = NewSample.AddUserData(bc)

    UVWTag = NewSample.GetTag(c4d.Tuvw)
    VertexCoord = UVWTag.GetSlow(0)
    for i in range(4):
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_VECTOR)
        bc[c4d.DESC_NAME] = "Vertex " + str(i) + " UVW"
        bc[c4d.DESC_SHORT_NAME] = "Vertex " + str(i) + " UVW"
        bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
        bc[c4d.DESC_PARENTGROUP] = VertexUVWGroup
        element = NewSample.AddUserData(bc)

        if i == 0:
            NewSample[element] = VertexCoord["a"]
        elif  i == 1:
            NewSample[element] = VertexCoord["b"]
        elif  i == 2:
            NewSample[element] = VertexCoord["c"]
        else:
            NewSample[element] = VertexCoord["d"]

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc[c4d.DESC_NAME] = "Texture Size"
    bc[c4d.DESC_SHORT_NAME] = "Texture Size"
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_TITLEBAR] = True
    bc[c4d.DESC_COLUMNS] = 2
    #bc[c4d.DESC_PARENTGROUP] = C2element
    TexSizeGroup = NewSample.AddUserData(bc)

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
    bc[c4d.DESC_NAME] = "Texture Width"
    bc[c4d.DESC_SHORT_NAME] = "Texture Width"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = TexSizeGroup
    element = NewSample.AddUserData(bc)
    NewSample[element] = float(node.attrib.get("width")) * ScaleRatio

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
    bc[c4d.DESC_NAME] = "Texture Height"
    bc[c4d.DESC_SHORT_NAME] = "Texture Height"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = TexSizeGroup
    element = NewSample.AddUserData(bc)
    NewSample[element] = float(node.attrib.get("height")) * ScaleRatio

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc[c4d.DESC_NAME] = "Texture Frame"
    bc[c4d.DESC_SHORT_NAME] = "Texture Frame"
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_TITLEBAR] = True
    bc[c4d.DESC_COLUMNS] = 4
    #bc[c4d.DESC_PARENTGROUP] = C2element
    TexFrameGroup = NewSample.AddUserData(bc)

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
    bc[c4d.DESC_NAME] = "Texture Frame X"
    bc[c4d.DESC_SHORT_NAME] = "Texture Frame X"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = TexFrameGroup
    element = NewSample.AddUserData(bc)
    if(node.attrib.get("frameX")):
        NewSample[element] = float(node.attrib.get("frameX")) * ScaleRatio
    else:
        NewSample[element] = 0

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
    bc[c4d.DESC_NAME] = "Texture Frame Y"
    bc[c4d.DESC_SHORT_NAME] = "Texture Frame Y"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = TexFrameGroup
    element = NewSample.AddUserData(bc)
    if(node.attrib.get("frameY")):
        NewSample[element] = float(node.attrib.get("frameY")) * ScaleRatio
    else:
        NewSample[element] = 0

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
    bc[c4d.DESC_NAME] = "Texture Frame Width"
    bc[c4d.DESC_SHORT_NAME] = "Texture Frame Width"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = TexFrameGroup
    element = NewSample.AddUserData(bc)
    if(node.attrib.get("frameY")):
        NewSample[element] = float(node.attrib.get("frameWidth")) * ScaleRatio
    else:
        NewSample[element] = float(node.attrib.get("width")) * ScaleRatio

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
    bc[c4d.DESC_NAME] = "Texture Frame Height"
    bc[c4d.DESC_SHORT_NAME] = "Texture Frame Height"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = TexFrameGroup
    element = NewSample.AddUserData(bc)
    if(node.attrib.get("frameY")):
        NewSample[element] = float(node.attrib.get("frameHeight")) * ScaleRatio
    else:
        NewSample[element] = float(node.attrib.get("height")) * ScaleRatio

    setColorTagWithData(NewSample)

    c4d.EventAdd()

    CTag = NewSample.MakeTag(c4d.Ttexture)
    CTag[c4d.TEXTURETAG_PROJECTION] = 6
    CTag.SetMaterial(AtlasMaterial)

    MVCTag = NewSample.GetTag(c4d.Tvertexmap)

    NewSample.InsertTag(CTag, MVCTag)

def CreateNewInstanceData(NewInstance, node, isOriginalInstance):
    SampleReference = getChild(SamplesContainer, node.attrib.get("name") + "_Sample")

    if not SampleReference:
        print("Sample Reference not found: ", node.attrib.get("name") + "_Sample")
        return

    NewInstance[c4d.INSTANCEOBJECT_LINK] = SampleReference

    if isOriginalInstance:
        PositionOriginalInstance(NewInstance, node)
   
    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc[c4d.DESC_NAME] = "OBJECT EXPORT INFO"
    bc[c4d.DESC_SHORT_NAME] = "OBJECT EXPORT INFO"
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_DEFAULT] = True
    bc[c4d.DESC_TITLEBAR] = True
    bc[c4d.DESC_COLUMNS] = 1
    ObjectExportGroup = NewInstance.AddUserData(bc)

    #print("Instance", ObjectExportGroup)

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL)
    bc[c4d.DESC_NAME] = "IsSpriteSheetSample"
    bc[c4d.DESC_SHORT_NAME] = "IsSpriteSheetSample"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = ObjectExportGroup
    element = NewInstance.AddUserData(bc)
    NewInstance[element] = True

    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BASELISTLINK)
    bc[c4d.DESC_NAME] = "Sample Reference"
    bc[c4d.DESC_SHORT_NAME] = "Sample Reference"
    bc[c4d.DESC_EDITABLE] = False
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    bc[c4d.DESC_PARENTGROUP] = ObjectExportGroup
    element = NewInstance.AddUserData(bc)
    NewInstance[element] = SampleReference

def setAsMissingMaterial(doc, ObjectWithMissingSample, SampleParent):
    isPolygonObject = c4d.PolygonObject == type(ObjectWithMissingSample)
    
    MissingMaterial = doc.SearchMaterial("Missing Sample Material")
    if not MissingMaterial:
        # create MissingMaterial
        MissingMaterial = c4d.BaseMaterial(c4d.Mmaterial)
        MissingMaterial.SetName( "Missing Sample Material" )
        MissingMaterial[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(255, 0, 0)
        MissingMaterial[c4d.MATERIAL_USE_REFLECTION] = False
        MissingMaterial.Message( c4d.MSG_UPDATE )
        MissingMaterial.Update( True, True )
        doc.InsertMaterial(MissingMaterial)

    print("Setting Missing Material to: ", ObjectWithMissingSample.GetName(), "MissingMaterial ", MissingMaterial.GetName())

    if isPolygonObject:
        CTag = ObjectWithMissingSample.GetTag(c4d.Ttexture)
        CTag.SetMaterial(MissingMaterial)
        ObjectWithMissingSample.InsertTag(CTag, ObjectWithMissingSample.GetTag(c4d.Tvertexmap))

        if SampleParent == SamplesContainer:
            ObjectWithMissingSample.InsertUnder(SamplesContainer)

InstancesContainer = None
SamplesContainer = None
AtlasHalfWidth = 0
AtlasHalfHeight = 0
AtlasWidth = 0
AtlasHeight = 0

def main(doc):
    global ScaleRatio
    global SamplesContainer
    global InstancesContainer
    global AtlasHalfWidth
    global AtlasHeight
    global AtlasWidth
    global AtlasHalfHeight

    #Ask the XML to import
    XMLpath = storage.LoadDialog()
    #See if is a XML file
    isXML = (XMLpath.find(".xml") +  XMLpath.find(".XML")) > 0

    #Convert path string to a array to remove file name and so get the folder name
    pathStruct = XMLpath.split("\\")
    #Get the file name without the extention
    global FileName
    FileName = pathStruct.pop()[:-4]
    
    pathStruct2 = []

    #Joint the string again without the file name
    for pPart in pathStruct:
        pathStruct2.append(pPart + "\\")

    #Define the folder path
    folderPath = "".join(pathStruct2)

    print("-------- XMLpath:")
    print(XMLpath)

    #Verify if the file is valid
    if not XMLpath:
        return
    elif XMLpath == "":
        return
    elif not isXML:
        print(gui.MessageDialog("File path is not for XML or is null"))
        return

    #Open and parse the file creating a ElementTree with all info inside
    with open(XMLpath, 'rt') as f:
        tree = ElementTree.parse(f)

    #Verify if the XML has "TextureAtlas" node. If has set info about the TextureAtlas
    hasTextureAtlas = 0;
    for node in tree.iter("TextureAtlas"):
        if node.attrib.get("ScaleRatio"):
            ScaleRatio = float(node.attrib.get("ScaleRatio"))

        hasTextureAtlas = 1;
        AtlasWidth =  float(node.attrib.get("width")) * ScaleRatio
        AtlasHalfWidth = AtlasWidth * 0.5
        AtlasHeight = float(node.attrib.get("height")) * ScaleRatio
        AtlasHalfHeight = AtlasHeight * 0.5
        PNGpath = folderPath + node.attrib.get("imagePath")
        print("Setting Atlas Sizes: ", AtlasWidth, AtlasHeight, AtlasHalfWidth, AtlasHalfHeight)

        if AtlasWidth >= AtlasHeight:
            TextureBiggerSize = AtlasHeight
        else:
            TextureBiggerSize = AtlasWidth

        TextureSizeRatio = 1024 / AtlasWidth

    #Stop ant show a error if XML does not have "TextureAtlas" node
    if not hasTextureAtlas:
        print(gui.MessageDialog("XML does not have TextureAtlas information"))
        return

    #Start Undo. This allow C4D to start to store actions in order to allow undo
    doc.StartUndo()
    #Create a Sample Container to collect all our samples. It it alrearyExist Just use the actual one.
    SamplesContainer = doc.SearchObject(FileName + " Samples")
    if not SamplesContainer:
        SamplesContainer = c4d.BaseObject(c4d.Onull)
        SamplesContainer.SetName(FileName + " Samples")
        #Add UserData storing Atlas Information to the Sample Container
        Cbc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP) # Create Group
        Cbc[c4d.DESC_NAME] = "Atlas Information"
        Celement = SamplesContainer.AddUserData(Cbc)
        #SamplesContainer[Celement] = "Atlas Information"

        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING) # Create Atlas Name Data
        bc[c4d.DESC_NAME] = "Atlas Name"
        bc[c4d.DESC_PARENTGROUP] = Celement
        bc[c4d.DESC_EDITABLE] = False
        element = SamplesContainer.AddUserData(bc)
        SamplesContainer[element] = FileName

        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_FILENAME) # Create Atlas Name Data
        bc[c4d.DESC_NAME] = "Atlas Path"
        bc[c4d.DESC_PARENTGROUP] = Celement
        bc[c4d.DESC_EDITABLE] = False
        element = SamplesContainer.AddUserData(bc)
        SamplesContainer[element] = folderPath

        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING) # Create Atlas Name Data
        bc[c4d.DESC_NAME] = "Atlas Samples"
        bc[c4d.DESC_PARENTGROUP] = Celement
        bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_STRINGMULTI
        element = SamplesContainer.AddUserData(bc)
        SamplesContainer[element] = ""

        Cbc2 = c4d.BaseContainer(c4d.DTYPE_GROUP) # Create Group
        Cbc2[c4d.DESC_NAME] = "Resolution"
        Cbc2[c4d.DESC_SHORT_NAME] = "Res"
        Cbc2[c4d.DESC_PARENTGROUP] = Celement
        Cbc2[c4d.DESC_COLUMNS] = 2

        C2element = SamplesContainer.AddUserData(Cbc2)
        #SamplesContainer[C2element] = "Resolution"

        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_LONG) # Create Atlas Width Data
        bc[c4d.DESC_NAME] = "Atlas Width"
        bc[c4d.DESC_PARENTGROUP] = C2element
        bc[c4d.DESC_EDITABLE] = False
        element = SamplesContainer.AddUserData(bc)
        SamplesContainer[element] = int(AtlasWidth)

        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_LONG) # Create Atlas Height Data
        bc[c4d.DESC_NAME] = "Atlas Height"
        bc[c4d.DESC_PARENTGROUP] = C2element
        bc[c4d.DESC_EDITABLE] = False
        element = SamplesContainer.AddUserData(bc)
        SamplesContainer[element] = int(AtlasHeight)

        #Inser the Container to the doccument
        doc.InsertObject(SamplesContainer)
        doc.AddUndo(c4d.UNDOTYPE_NEW, SamplesContainer)

    else:
        SamplesContainer[c4d.ID_USERDATA,2] = FileName
        SamplesContainer[c4d.ID_USERDATA,3] = folderPath
        SamplesContainer[c4d.ID_USERDATA,6] = int(AtlasWidth)
        SamplesContainer[c4d.ID_USERDATA,7] = int(AtlasHeight)

    InstancesContainer = doc.SearchObject(FileName + " Instances")
    if not InstancesContainer:
        InstancesContainer = c4d.BaseObject(c4d.Onull)
        InstancesContainer.SetName(FileName + " Instances")

        #Inser the Instance Container to the doccument
        doc.InsertObject(InstancesContainer)
        doc.AddUndo(c4d.UNDOTYPE_NEW, InstancesContainer)

    InstancesContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = AtlasHalfWidth * 2 + 200

    SceneContainer = doc.SearchObject("LANDS OF OBLIVION")

    # Verify if Material already Exist
    AtlasMaterial = doc.SearchMaterial(FileName + " Material")
    #print(AtlasMaterial)
    if not AtlasMaterial:
        # create material
        AtlasMaterial = c4d.BaseMaterial(c4d.Mmaterial)
        AtlasMaterial.SetName( FileName + " Material" )

    TextureShaderDifuse = c4d.BaseList2D(c4d.Xbitmap)
    TextureShaderDifuse[c4d.BITMAPSHADER_FILENAME]  = FileName + ".png"

    TextureShaderAlpha = c4d.BaseList2D(c4d.Xbitmap)
    TextureShaderAlpha[c4d.BITMAPSHADER_FILENAME]  = FileName + ".png"

    FusionShaderDifuse = c4d.BaseList2D(c4d.Xfusion)
    FusionShaderDifuse[c4d.SLA_FUSION_BASE_CHANNEL]  = TextureShaderDifuse
    FusionShaderDifuse[c4d.SLA_FUSION_MODE] = c4d.SLA_FUSION_MODE_MULTIPLY

    FusionShaderAlpha = c4d.BaseList2D(c4d.Xfusion)
    FusionShaderAlpha[c4d.SLA_FUSION_BASE_CHANNEL]  = TextureShaderAlpha
    FusionShaderAlpha[c4d.SLA_FUSION_MODE] = c4d.SLA_FUSION_MODE_MULTIPLY

    # Create Material or Update the Existing one
    AtlasMaterial[c4d.MATERIAL_USE_ALPHA] = True
    AtlasMaterial[c4d.MATERIAL_USE_REFLECTION] = False
    AtlasMaterial[c4d.MATERIAL_PREVIEWSIZE] = 13
    AtlasMaterial[c4d.MATERIAL_USE_TRANSPARENCY] = False
    AtlasMaterial[c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS] = 0

    #Configure Texture shader for use alpha channel
    LayerSet = c4d.LayerSet()
    LayerSet.SetMode(c4d.LAYERSETMODE_LAYERALPHA)
    TextureShaderAlpha[c4d.BITMAPSHADER_LAYERSET] = LayerSet

    AtlasMaterial.InsertShader( TextureShaderAlpha )
    AtlasMaterial.InsertShader( TextureShaderDifuse )
    AtlasMaterial.InsertShader( FusionShaderDifuse )
    AtlasMaterial.InsertShader( FusionShaderAlpha )
    AtlasMaterial[c4d.MATERIAL_COLOR_SHADER]  = FusionShaderDifuse
    AtlasMaterial[c4d.MATERIAL_ALPHA_SHADER] = FusionShaderAlpha

    MVCTag = None

    AtlasMaterial.Message( c4d.MSG_UPDATE )
    AtlasMaterial.Update( True, True )
    doc.InsertMaterial(AtlasMaterial)

    MissingMaterial = doc.SearchMaterial("Missing Sample Material")
    if not MissingMaterial:
        # create MissingMaterial
        MissingMaterial = c4d.BaseMaterial(c4d.Mmaterial)
        MissingMaterial.SetName( "Missing Sample Material" )
        MissingMaterial[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(255, 0, 0)
        MissingMaterial[c4d.MATERIAL_USE_REFLECTION] = False
        MissingMaterial.Message( c4d.MSG_UPDATE )
        MissingMaterial.Update( True, True )
        doc.InsertMaterial(MissingMaterial)

    #print("Sample List USer Data: ", SamplesContainer[c4d.ID_USERDATA,4])
    #Temporary Store Sample Container Samples List
    AtlasSamplesList = (SamplesContainer[c4d.ID_USERDATA,4]).split("_Sample,\n")
    if len(AtlasSamplesList) <= 1:
        print("No Samples in the Scene using ',' as separator")
        AtlasSamplesList = (SamplesContainer[c4d.ID_USERDATA,4]).split(",\n")

    print("Sample List: ", len(AtlasSamplesList))

    #Remove empty last element
    AtlasSamplesList.pop()

    #Clear the Sample Container Sample List to make a new one
    SamplesContainer[c4d.ID_USERDATA,4] = ""

    #Create the Samples
    for node in tree.iter("SubTexture"):
        currentName = node.attrib.get("name")
        rotated = node.attrib.get("rotated")
        
        print(currentName, " Name Parts:", len(currentName.split("_")))

        if len(currentName.split("_")) > 2:
           print("Sub textues (samples) name patern maybe is wrong. Should be like 'Atlas_TexName', have just one '_' divisor. This sample " + currentName + " have more. It's an animation?")

        #Find the difference between the original sample pivot and the updated sample pivot
        pivotDiff = setPivotDiff(node)

        #Verify if current sample data is on current sample list in the scene
        print("Current Sample: ", currentName)
        if (currentName) in AtlasSamplesList:
            print("Sample is listed")
            SampleListIndex = AtlasSamplesList.index(currentName)
            #Remove the sample from the this temporary list as they are being processed
            AtlasSamplesList.pop(SampleListIndex)

        #Add sample to the Sample Container Samples List
        SamplesContainer[c4d.ID_USERDATA,4] = SamplesContainer[c4d.ID_USERDATA,4] + currentName + ",\n"

        Csample = None
        sampleAlradyExist = False

        #print("----------------------------Updating ExistingSample -------")
        ExistingSample = getChild(SamplesContainer, currentName + "_Sample")

        #Updating Actual Samples in SampleContainer
        if(ExistingSample):
            print("Updating Existing Sample: ", currentName)

            sampleAlradyExist = True
            
            #see if is a polygon object, if not should not update
            isPolygonObject = c4d.PolygonObject == type(ExistingSample)

            if isPolygonObject:
                XTag = None
                for XTag in ExistingSample.GetTags():
                    if XTag[c4d.ID_BASELIST_NAME] == "SampleUVW":
                        CTag = XTag

                SetRefPolygon(FileName + " Samples", ExistingSample, CTag, ExistingSample.GetPolygon(0), node)
                UpdateExistingSample(ExistingSample, node, pivotDiff, AtlasMaterial, True)
            #Create undo for this operation
            doc.AddUndo(c4d.UNDOTYPE_NEW, ExistingSample)
        
        #print("----------------------------------Finished ExistingSample-------")     
        #print("----------------------------Creating New Samples-------")
        #Create a new sample if not exist
        if not sampleAlradyExist:
            print("Sample is completly new: ", sampleAlradyExist, currentName)

            Csample = c4d.BaseObject(c4d.Opolygon)
            Csample.SetName(currentName + "_Sample")
            Csample.InsertUnder(SamplesContainer)

            SetRefPolygon(FileName + " Samples", Csample, None, None, node)
            CreateNewSampleData(Csample, node, currentName, pivotDiff, AtlasMaterial)
            
            #Refresh the managers to show the new object
            c4d.EventAdd()

            #Create undo for this operation
            doc.AddUndo(c4d.UNDOTYPE_NEW, Csample)
            #print(node.tag, currenName, Csample2)
        #print("----------------------------------Creating New Samples-------")

        #Updating Actual Instances in InstanceContainer
        #print("----------------------------Updating Existing Instances-------")
        ExistingInstance = getChild(InstancesContainer, currentName + "_Instance")
        if ExistingInstance:
            print("Updating Existing Instance: ", currentName, ExistingInstance, InstancesContainer.GetName())

            #see if is a instance object, if not should not update
            isInstanceObject = c4d.InstanceObject == type(ExistingInstance)
            print("isInstanceObject: ", isInstanceObject, type(ExistingInstance), ExistingInstance.GetName())

            if isInstanceObject:
                UpdateExistingInstance(ExistingInstance, node, True)
        else:
            print("Creating Missing Instance: ", currentName, InstancesContainer.GetName())
            ExistingInstance = c4d.BaseObject(c4d.Oinstance)
            ExistingInstance.SetName(currentName + "_Instance")
            ExistingInstance.InsertUnder(InstancesContainer)
            CreateNewInstanceData(ExistingInstance, node, True)


        #Create undo for this operation
            #print("----------------------------------Finished Existing Instances-------")

        #print("----------------------------Updating SceneSamples-------")
        #Updating Actual Objects in the scene including the Sample/Instance container. Also see if sample already exist
        for SceneSample in get_all_objects(SceneContainer, lambda x:UserDataAndTextureNameCheck(x, currentName, "IsSpriteSheetSample", True)):            
            print("Updating Scene Objects: ", currentName, SceneSample.GetName(), " SceneContainer ", SceneContainer.GetName())

            #see if is a polygon object or instance object, if not should not update
            isPolygonObject = c4d.PolygonObject == type(SceneSample)
            isinstanceObject = c4d.InstanceObject == type(SceneSample)

            if isPolygonObject:
                XTag = None
                for XTag in SceneSample.GetTags():
                    if XTag[c4d.ID_BASELIST_NAME] == "SampleUVW":
                        CTag = XTag

                print("Updating Polygon Scene Objects: ", currentName)

                SampleReference = getChild(SamplesContainer, currentName + "_Sample")

                if not SampleReference:
                    print("Sample Reference not found: ", currentName + "_Sample")
                    return
                
                UpdateScenePolygonUVs(SceneSample, SampleReference)
                #SetRefPolygon(FileName + " Samples", SceneSample, CTag, SceneSample.GetPolygon(0), node)
                UpdateExistingSample(SceneSample, node, pivotDiff, AtlasMaterial, False)

            if isinstanceObject:
                UpdateExistingInstance(SceneSample, node, False)

            #Create undo for this operation
            doc.AddUndo(c4d.UNDOTYPE_NEW, SceneSample)
        #print("----------------------------------Finished SceneSamples-------")


    #Some samples could be missing from the new atlas, is this happen, mark them as missing samples by giving a red texture and fixed size
    print("AtlasSamplesList", len(AtlasSamplesList))
    if len(AtlasSamplesList) > 0:
        gui.MessageDialog("Some sprites are missing from this spritesheet. They will be turned red. Delete the sprites if not needed or reimport a spritesheet containing all sprites from last import")

    for missingName in AtlasSamplesList:
        print("----------------------------Updating Missing Samples-------")
        print("Missing Sample: ", missingName)

        # Udate objects, samples and instances  which are missing on the new sprite sheet

        ExistingInstance = getChild(InstancesContainer, missingName + "_Instance")
        ExistingSample = getChild(SamplesContainer, missingName + "_Sample")
        
        if ExistingInstance:
            print("Missing Existing Instance: ", ExistingInstance)
            SampleParent = ExistingInstance.GetUp()
            ExistingInstance[c4d.INSTANCEOBJECT_LINK] = getChild(SamplesContainer, missingName + "_Sample")
            ExistingInstance.InsertUnder(InstancesContainer)
        
        if ExistingSample:
            print("Missing Existing Sample: ", ExistingSample)
            SampleParent = ExistingInstance.GetUp()
            setAsMissingMaterial(doc, ExistingSample, SampleParent)
        
        for ObjectWithMissingSample in get_all_objects(SceneContainer, lambda x:UserDataAndNameCheck(x, missingName, "IsSpriteSheetSample", True)):
            print("Missing Scene Object: ", ObjectWithMissingSample)
            SampleParent = ObjectWithMissingSample.GetUp()

            #see if is a polygon object or instance object, if not should not update
            isPolygonObject = c4d.PolygonObject == type(ObjectWithMissingSample)
            isinstanceObject = c4d.InstanceObject == type(ObjectWithMissingSample)

            if isPolygonObject:
                setAsMissingMaterial(doc, ObjectWithMissingSample, SampleParent)      

            if isinstanceObject:
                ObjectWithMissingSample[c4d.INSTANCEOBJECT_LINK] = getChild(SamplesContainer, missingName + "_Sample")
                ObjectWithMissingSample.InsertUnder(InstancesContainer)

        #print("----------------------------Finished Missing Samples-------")

    #Create a plane representing the Atlas Texture as a hole. Objects and this plane should show exacly same texture on them own position. Use this to verify if all goes right
    CAtlas = doc.SearchObject(FileName + " TextureAtlas")
    #print("CAtlas", CAtlas)
    if not CAtlas:
        CAtlas = c4d.BaseObject(c4d.Opolygon)
        Polygon = c4d.CPolygon(0, 1, 2, 3)
        Polygon.__init__(0, 1, 2, 3)
        CAtlas.ResizeObject(4, 1)
        CAtlas.SetPolygon(0, Polygon)

        PSs = []
        PSs.append(c4d.Vector(-AtlasHalfWidth, -AtlasHalfHeight, 0))
        PSs.append(c4d.Vector(AtlasHalfWidth, -AtlasHalfHeight, 0))
        PSs.append(c4d.Vector(AtlasHalfWidth, AtlasHalfHeight, 0))
        PSs.append(c4d.Vector(-AtlasHalfWidth, AtlasHalfHeight, 0))

        pcount = CAtlas.GetPointCount()
        point = CAtlas.GetAllPoints()
        for i in range(pcount):
            CAtlas.SetPoint(i, PSs[i])

        PCSs = []
        PCSs.append(c4d.Vector(0, 1, 0))
        PCSs.append(c4d.Vector(1, 1, 0))
        PCSs.append(c4d.Vector(1, 0, 0))
        PCSs.append(c4d.Vector(0, 0, 0))

        setColorTagWithData(CAtlas)

        #MVCTag = c4d.VertexColorTag(4)
        #MVCTag.__init__(4)
        #CAtlas.InsertTag(MVCTag)
        #VCdata = MVCTag.GetDataAddressW()
        #white = c4d.Vector(1.0, 1.0, 1.0)

        #pointCount = CAtlas.GetPointCount()
        #for idx in range(pointCount):
          #MVCTag.SetColor(VCdata, None, None, idx, white)
          #MVCTag.SetAlpha(VCdata, None, None, idx, 1)

        c4d.EventAdd()

        #MVCTag.SetPerPointMode(False)

        UVWTag = CAtlas.MakeVariableTag(c4d.Tuvw, 1)
        UVWTag[c4d.ID_BASELIST_NAME] = "SampleUVW"
        UVWTag.SetSlow(0, PCSs[0], PCSs[1], PCSs[2], PCSs[3])

        CAtlas.SetName(FileName + " TextureAtlas")
        CAtlas[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = 0
        CAtlas[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = 0
        CAtlas[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 10
        #CAtlas[c4d.PRIM_PLANE_SUBW] = 1
        #CAtlas[c4d.PRIM_PLANE_SUBH] = 1
        #CAtlas[c4d.PRIM_AXIS] = 5
        CAtlas[c4d.ID_BASEOBJECT_USECOLOR] = True
        CAtlas[c4d.ID_BASEOBJECT_COLOR] = c4d.Vector(255, 255, 255)

        #Add texture tag to this plane
        CTag = CAtlas.MakeTag(c4d.Ttexture)
        CTag[c4d.TEXTURETAG_PROJECTION] = 6
        CTag[c4d.TEXTURETAG_MATERIAL] = AtlasMaterial
    else:
        CTag = CAtlas.GetTag(c4d.Ttexture)
        PSs = []
        PSs.append(c4d.Vector(-AtlasHalfWidth, -AtlasHalfHeight, 0))
        PSs.append(c4d.Vector(AtlasHalfWidth, -AtlasHalfHeight, 0))
        PSs.append(c4d.Vector(AtlasHalfWidth, AtlasHalfHeight, 0))
        PSs.append(c4d.Vector(-AtlasHalfWidth, AtlasHalfHeight, 0))

        pcount = CAtlas.GetPointCount()
        point = CAtlas.GetAllPoints()
        for i in range(pcount):
            CAtlas.SetPoint(i, PSs[i])

    #Add plane to the Atlas Container
    CAtlas.InsertUnder(SamplesContainer)
    doc.AddUndo(c4d.UNDOTYPE_NEW, CAtlas)

    VertexShaderDifuse = c4d.BaseList2D(c4d.Xvertexmap)
    VertexShaderAlpha = c4d.BaseList2D(c4d.Xvertexmap)
    AtlasMaterial.InsertShader( VertexShaderDifuse )
    AtlasMaterial.InsertShader( VertexShaderAlpha )

    FusionShaderDifuse[c4d.SLA_FUSION_BLEND_CHANNEL]  = VertexShaderDifuse
    FusionShaderAlpha[c4d.SLA_FUSION_BLEND_CHANNEL]  = VertexShaderAlpha

    TVertexcolor = CAtlas.GetTag(c4d.Tvertexcolor)
    #print('TVertexcolor', TVertexcolor, CAtlas)
    VertexShaderDifuse[c4d.SLA_DIRTY_VMAP_OBJECT]  = TVertexcolor
    VertexShaderAlpha[c4d.SLA_DIRTY_VMAP_OBJECT]  = TVertexcolor

    AtlasMaterial.Message( c4d.MSG_UPDATE )
    AtlasMaterial.Update( True, True )

    CAtlas[c4d.PRIM_PLANE_WIDTH] = float(AtlasWidth)
    CAtlas[c4d.PRIM_PLANE_HEIGHT] = float(AtlasHeight)
    CAtlas[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = c4d.OBJECT_OFF

    doc.EndUndo()
    c4d.EventAdd()

    return