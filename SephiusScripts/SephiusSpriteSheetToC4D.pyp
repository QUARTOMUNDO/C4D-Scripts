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
FileName = ""
folderPath = ""
AtlasWidth = 0
AtlasHeight = 0
AtlasHalfWidth = 0
AtlasHalfHeight = 0
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

def SetPolygon(ParentName, CObject, UVWTag, Polygon, TextureNode, AtlasWidth, AtlasHeight):

    #print("Getting Atlas Sizes: ", AtlasWidth, AtlasHeight)
    #AtlasWidth =  float(TextureNode.attrib.get("width")) * ScaleRatio
    AtlasHalfWidth = AtlasWidth * 0.5
    #AtlasHeight = float(TextureNode.attrib.get("height")) * ScaleRatio
    AtlasHalfHeight = AtlasHeight * 0.5

    CHalfWidth = float(TextureNode.attrib.get("width")) * 0.5
    CHalfHeight = float(TextureNode.attrib.get("height")) * 0.5

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
        
    #print("UV Coord px: ", float(TextureNode.attrib.get("x")), float(TextureNode.attrib.get("y")), float(TextureNode.attrib.get("width")), float(TextureNode.attrib.get("height")))
    CoX = float(TextureNode.attrib.get("x")) * ScaleRatio / AtlasWidth
    CoY = float(TextureNode.attrib.get("y"))  * ScaleRatio/ AtlasHeight
    CoHX = (float(TextureNode.attrib.get("x")) + float(TextureNode.attrib.get("width"))) * ScaleRatio / AtlasWidth
    CoHY = (float(TextureNode.attrib.get("y")) + float(TextureNode.attrib.get("height"))) * ScaleRatio / AtlasHeight

    PCSs = []
    PCSs.append(c4d.Vector(CoX, CoY, 0))
    PCSs.append(c4d.Vector(CoHX, CoY, 0))
    PCSs.append(c4d.Vector(CoHX, CoHY, 0))
    PCSs.append(c4d.Vector(CoX, CoHY, 0))

    #Update object. Need to update bound box for selection and etc.
    #CObject.Message (c4d.MSG_UPDATE)

    #print("Atlas: ", AtlasWidth, AtlasHeight)
    #print("UVW: ", CoX, CoY, CoHX, CoHY)

    if not Polygon:
        Polygon = c4d.CPolygon(0, 1, 2, 3)
        Polygon.__init__(0, 1, 2, 3)
        CObject.ResizeObject(4, 1)
        CObject.SetPolygon(0, Polygon)

    if not UVWTag:
        UVWTag = CObject.MakeVariableTag(c4d.Tuvw, 1)
        UVWTag[c4d.ID_BASELIST_NAME] = "SampleUVW"
        CObject.InsertTag(UVWTag)

    pcount = CObject.GetPointCount()
    point = CObject.GetAllPoints()
    #print(pcount)
    for i in range(pcount):
        CObject.SetPoint(i, PSs[i])

    UVWTag.SetSlow(0, PCSs[0], PCSs[1], PCSs[2], PCSs[3])

    
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

#nulls = get_all_objects(doc.GetFirstObject(), lambda x: x.CheckType(c4d.Onull), [])
def get_all_objects(op, filter, output):
    while op:
        if filter(op):
            output.append(op)
        get_all_objects(op.GetDown(), filter, output)
        op = op.GetNext()
    return output

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

#Return true if object has a user data name and value is equal to desired
def GetUserData(CObject, UDName):
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

def main(doc):
    global ScaleRatio
    #Ask the XML to import
    XMLpath = storage.LoadDialog()
    #See if is a XML file
    isXML = (XMLpath.find(".xml") +  XMLpath.find(".XML")) > 0

    #Convert path string to a array to remove file name and so get the folder name
    pathStruct = XMLpath.split("\\")
    #Get the file name without the extention
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
        #print("Setting Atlas Sizes: ", AtlasWidth, AtlasHeight)

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

    # Verify if Material already Exist
    AtlasMaterial = doc.SearchMaterial(FileName + " Material")
    print(AtlasMaterial)
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
    AtlasSamplesList = (SamplesContainer[c4d.ID_USERDATA,4]).split(",\n")
    AtlasSamplesList.pop()
    #print("Sample List: ", AtlasSamplesList)
    SamplesContainer[c4d.ID_USERDATA,4] = ""

    #Create the Samples
    for node in tree.iter("SubTexture"):
        currenName = node.attrib.get("name")
        rotated = node.attrib.get("rotated")
        
        print(currenName, len(currenName.split("_")))

        #if len(currenName.split("_")) > 2:
            #return gui.MessageDialog("Sub textues (samples) name patern is wrong. Should be like 'Atlas_TexName', have just one '_' divisor. This sample " + currenName + " have more.")

        CHalfWidth = float(node.attrib.get("width")) * 0.5 * ScaleRatio
        CHalfHeight = float(node.attrib.get("height")) * 0.5 * ScaleRatio

        pivotDiff = setPivotDiff(node)

        Csample = False

        hasExistingSamples = False
        #Updating Actual Samples:...
        for Csample in get_all_objects(doc.GetFirstObject(), lambda x:UserDataAndNameCheck(x, currenName + "_Sample", "IsSpriteSheetSample", True), []):
            if not Csample.GetUp():
                hasExistingSamples = False
            elif Csample.GetUp().GetName() == FileName + " Samples":
                hasExistingSamples = True

            #see if is a polygon object, if not should not update as existing sample
            isPolygonObject = c4d.PolygonObject == type(Csample)

            #print("hasExistingSamples: ", hasExistingSamples, currenName, Csample.GetName())

            SParent = Csample.GetUp()

            XTag = None
            for XTag in Csample.GetTags():
               if XTag[c4d.ID_BASELIST_NAME] == "SampleUVW":
                   CTag = XTag

            if (isPolygonObject):
                SetPolygon(FileName + " Samples", Csample, CTag, Csample.GetPolygon(0), node, AtlasWidth, AtlasHeight)

                MVCTag = Csample.GetTag(c4d.Tvertexmap)
                CTag = Csample.GetTag(c4d.Ttexture)
                CTag.SetMaterial(AtlasMaterial)
                Csample.InsertTag(CTag, MVCTag)

                #oldPivotDiff = Csample[c4d.ID_USERDATA,2]
                #print("oldPivotDiff", Csample, oldPivotDiff)
                Csample[c4d.ID_BASEOBJECT_REL_POSITION] = Csample[c4d.ID_BASEOBJECT_REL_POSITION] + 0

                if SParent == SamplesContainer:
                    Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) * ScaleRatio - AtlasHalfWidth + CHalfWidth
                    Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) * ScaleRatio + AtlasHalfHeight - CHalfHeight
                    Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
                    Csample.InsertUnder(SamplesContainer)

                    UVWTag = Csample.GetTag(c4d.Tuvw)
                    VertexCoord = UVWTag.GetSlow(0)
                    for i in range(4):
                        element = GetUserData(Csample, "Vertex " + str(i) + " Position")
                        Csample[element] = Csample.GetPoint(i)

                        element = GetUserData(Csample, "Vertex " + str(i) + " UVW")
                        if i == 0:
                            Csample[element] = VertexCoord["a"]
                        elif  i == 1:
                            Csample[element] = VertexCoord["b"]
                        elif  i == 2:
                            Csample[element] = VertexCoord["c"]
                        else:
                            Csample[element] = VertexCoord["d"]

                    element = GetUserData(Csample, "Offset")
                    Csample[element] = pivotDiff

                    element = GetUserData(Csample, "Texture Width")
                    Csample[element] = float(node.attrib.get("width")) * ScaleRatio

                    element = GetUserData(Csample, "Texture Height")
                    Csample[element] = float(node.attrib.get("height")) * ScaleRatio

                    element = GetUserData(Csample, "Texture Frame X")
                    if(node.attrib.get("frameX")):
                        Csample[element] = float(node.attrib.get("frameX")) * ScaleRatio
                    else:
                        Csample[element] = 0

                    element = GetUserData(Csample, "Texture Frame Y")
                    if(node.attrib.get("frameY")):
                        Csample[element] = float(node.attrib.get("frameY")) * ScaleRatio
                    else:
                        Csample[element] = 0

                    element = GetUserData(Csample, "Texture Frame Width")
                    if(node.attrib.get("frameWidth")):
                        Csample[element] = float(node.attrib.get("frameWidth")) * ScaleRatio
                    else:
                        Csample[element] = float(node.attrib.get("width")) * ScaleRatio

                    element = GetUserData(Csample, "Texture Frame Height")
                    if(node.attrib.get("frameHeight")):
                        Csample[element] = float(node.attrib.get("frameHeight")) * ScaleRatio
                    else:
                        Csample[element] = float(node.attrib.get("height")) * ScaleRatio

                Csample[c4d.ID_BASEOBJECT_REL_POSITION] = Csample[c4d.ID_BASEOBJECT_REL_POSITION] - pivotDiff

        #Create and set object parameters
        CInstance = getChild(InstancesContainer, currenName + "_Instance")

        #Verify if sample is on sample list
        if (currenName + "_Sample") in AtlasSamplesList:
            #print("Sample is listed")
            SampleListIndex = AtlasSamplesList.index(currenName + "_Sample")
            AtlasSamplesList.pop(SampleListIndex)

        SamplesContainer[c4d.ID_USERDATA,4] = SamplesContainer[c4d.ID_USERDATA,4] + currenName + "_Sample,\n"

        if not hasExistingSamples:
            #print("Don´t have Existing Samples: ", hasExistingSamples, currenName)
            #Create a quad polygon by creating a plane then set it as editable
            #QuadPolygon = c4d.BaseObject(c4d.Oplane)
            #QuadPolygon[c4d.PRIM_PLANE_SUBW] = 1
            #QuadPolygon[c4d.PRIM_PLANE_SUBH] = 1
            #QuadPolygon[c4d.PRIM_AXIS] = c4d.PRIM_AXIS_ZN

            #Csample = c4d.utils.SendModelingCommand(command = c4d.MCOMMAND_MAKEEDITABLE, list = [QuadPolygon], mode = c4d.MODELINGCOMMANDMODE_ALL, bc = c4d.BaseContainer(), doc = doc)[0]
            #Csample.Message(c4d.MSG_UPDATE)

            Csample = c4d.BaseObject(c4d.Opolygon)

            # If the editable object exists, insert it into the document
            #QuadPolygon.Remove()

            Csample.SetName(currenName + "_Sample")

            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) * ScaleRatio - AtlasHalfWidth + CHalfWidth
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) * ScaleRatio + AtlasHalfHeight - CHalfHeight
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
            #print(pivotDiff)
            Csample[c4d.ID_BASEOBJECT_REL_POSITION] = Csample[c4d.ID_BASEOBJECT_REL_POSITION] - (pivotDiff * 1)

            Csample.InsertUnder(SamplesContainer)

            SetPolygon(FileName + " Samples", Csample, None, None, node, AtlasWidth, AtlasHeight)

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
            bc[c4d.DESC_NAME] = "OBJECT EXPORT INFO"
            bc[c4d.DESC_SHORT_NAME] = "OBJECT EXPORT INFO"
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_DEFAULT] = True
            bc[c4d.DESC_TITLEBAR] = True
            bc[c4d.DESC_COLUMNS] = 1
            ObjectExportGroup = Csample.AddUserData(bc)
            #Csample[ObjectExportGroup] = "OBJECT EXPORT INFO"

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
            bc[c4d.DESC_NAME] = "GAME PROPERTIES"
            bc[c4d.DESC_SHORT_NAME] = "GAME PROPERTIES"
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_DEFAULT] = True
            bc[c4d.DESC_TITLEBAR] = True
            bc[c4d.DESC_COLUMNS] = 1
            GamePropertiesGroup = Csample.AddUserData(bc)
            #Csample[GamePropertiesGroup] = "GAME PROPERTIES"

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL)
            bc[c4d.DESC_NAME] = "IsSpriteSheetSample"
            bc[c4d.DESC_SHORT_NAME] = "IsSpriteSheetSample"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = ObjectExportGroup
            element = Csample.AddUserData(bc)
            Csample[element] = True

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BASELISTLINK)
            bc[c4d.DESC_NAME] = "Sample Reference"
            bc[c4d.DESC_SHORT_NAME] = "Sample Reference"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = ObjectExportGroup
            element = Csample.AddUserData(bc)
            Csample[element] = Csample

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING)
            bc[c4d.DESC_NAME] = "className"
            bc[c4d.DESC_SHORT_NAME] = "className"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = GamePropertiesGroup
            element = Csample.AddUserData(bc)
            Csample[element] = "Image"

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING)
            bc[c4d.DESC_NAME] = "texture"
            bc[c4d.DESC_SHORT_NAME] = "texture"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = GamePropertiesGroup
            element = Csample.AddUserData(bc)
            Csample[element] = currenName

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING)
            bc[c4d.DESC_NAME] = "Atlas"
            bc[c4d.DESC_SHORT_NAME] = "Atlas"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = GamePropertiesGroup
            element = Csample.AddUserData(bc)
            Csample[element] = FileName

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING)
            bc[c4d.DESC_NAME] = "blendMode"
            bc[c4d.DESC_SHORT_NAME] = "blendMode"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = GamePropertiesGroup
            element = Csample.AddUserData(bc)
            Csample[element] = "normal"

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
            bc[c4d.DESC_NAME] = "Vertex Position"
            bc[c4d.DESC_SHORT_NAME] = "Vertex Position"
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_COLUMNS] = 1
            #bc[c4d.DESC_PARENTGROUP] = C2element
            VertexPositionGroup = Csample.AddUserData(bc)

            pcount = Csample.GetPointCount()
            point = Csample.GetAllPoints()
            for i in range(pcount):
                bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_VECTOR)
                bc[c4d.DESC_NAME] = "Vertex " + str(i) + " Position"
                bc[c4d.DESC_SHORT_NAME] = "Vertex " + str(i) + " Position"
                bc[c4d.DESC_EDITABLE] = False
                bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
                bc[c4d.DESC_PARENTGROUP] = VertexPositionGroup
                element = Csample.AddUserData(bc)
                Csample[element] = Csample.GetPoint(i)

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_VECTOR)
            bc[c4d.DESC_NAME] = "Offset"
            bc[c4d.DESC_SHORT_NAME] = "Offset"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_TITLEBAR] = True
            bc[c4d.DESC_PARENTGROUP] = VertexPositionGroup
            element = Csample.AddUserData(bc)
            Csample[element] = pivotDiff

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
            bc[c4d.DESC_NAME] = "Vertex UVW"
            bc[c4d.DESC_SHORT_NAME] = "Vertex UVW"
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_TITLEBAR] = True
            bc[c4d.DESC_COLUMNS] = 1
            #bc[c4d.DESC_PARENTGROUP] = C2element
            VertexUVWGroup = Csample.AddUserData(bc)

            UVWTag = Csample.GetTag(c4d.Tuvw)
            VertexCoord = UVWTag.GetSlow(0)
            for i in range(4):
                bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_VECTOR)
                bc[c4d.DESC_NAME] = "Vertex " + str(i) + " UVW"
                bc[c4d.DESC_SHORT_NAME] = "Vertex " + str(i) + " UVW"
                bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
                bc[c4d.DESC_PARENTGROUP] = VertexUVWGroup
                element = Csample.AddUserData(bc)

                if i == 0:
                    Csample[element] = VertexCoord["a"]
                elif  i == 1:
                    Csample[element] = VertexCoord["b"]
                elif  i == 2:
                    Csample[element] = VertexCoord["c"]
                else:
                    Csample[element] = VertexCoord["d"]

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
            bc[c4d.DESC_NAME] = "Texture Size"
            bc[c4d.DESC_SHORT_NAME] = "Texture Size"
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_TITLEBAR] = True
            bc[c4d.DESC_COLUMNS] = 2
            #bc[c4d.DESC_PARENTGROUP] = C2element
            TexSizeGroup = Csample.AddUserData(bc)

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
            bc[c4d.DESC_NAME] = "Texture Width"
            bc[c4d.DESC_SHORT_NAME] = "Texture Width"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = TexSizeGroup
            element = Csample.AddUserData(bc)
            Csample[element] = float(node.attrib.get("width")) * ScaleRatio

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
            bc[c4d.DESC_NAME] = "Texture Height"
            bc[c4d.DESC_SHORT_NAME] = "Texture Height"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = TexSizeGroup
            element = Csample.AddUserData(bc)
            Csample[element] = float(node.attrib.get("height")) * ScaleRatio

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
            bc[c4d.DESC_NAME] = "Texture Frame"
            bc[c4d.DESC_SHORT_NAME] = "Texture Frame"
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_TITLEBAR] = True
            bc[c4d.DESC_COLUMNS] = 4
            #bc[c4d.DESC_PARENTGROUP] = C2element
            TexFrameGroup = Csample.AddUserData(bc)

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
            bc[c4d.DESC_NAME] = "Texture Frame X"
            bc[c4d.DESC_SHORT_NAME] = "Texture Frame X"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = TexFrameGroup
            element = Csample.AddUserData(bc)
            if(node.attrib.get("frameX")):
                Csample[element] = float(node.attrib.get("frameX")) * ScaleRatio
            else:
                Csample[element] = 0

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
            bc[c4d.DESC_NAME] = "Texture Frame Y"
            bc[c4d.DESC_SHORT_NAME] = "Texture Frame Y"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = TexFrameGroup
            element = Csample.AddUserData(bc)
            if(node.attrib.get("frameY")):
                Csample[element] = float(node.attrib.get("frameY")) * ScaleRatio
            else:
                Csample[element] = 0

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
            bc[c4d.DESC_NAME] = "Texture Frame Width"
            bc[c4d.DESC_SHORT_NAME] = "Texture Frame Width"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = TexFrameGroup
            element = Csample.AddUserData(bc)
            if(node.attrib.get("frameY")):
                Csample[element] = float(node.attrib.get("frameWidth")) * ScaleRatio
            else:
                Csample[element] = float(node.attrib.get("width")) * ScaleRatio

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
            bc[c4d.DESC_NAME] = "Texture Frame Height"
            bc[c4d.DESC_SHORT_NAME] = "Texture Frame Height"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = TexFrameGroup
            element = Csample.AddUserData(bc)
            if(node.attrib.get("frameY")):
                Csample[element] = float(node.attrib.get("frameHeight")) * ScaleRatio
            else:
                Csample[element] = float(node.attrib.get("height")) * ScaleRatio

            setColorTagWithData(Csample)

            #MVCTag = c4d.VertexColorTag(4)
            #MVCTag.__init__(4)
            #Csample.InsertTag(MVCTag)
            #VCdata = MVCTag.GetDataAddressW()
            #white = c4d.Vector(1.0, 1.0, 1.0)

            #pointCount = Csample.GetPointCount()
            #for idx in range(pointCount):
              #MVCTag.SetColor(VCdata, None, None, idx, white)
              #MVCTag.SetAlpha(VCdata, None, None, idx, 1)

            c4d.EventAdd()

            #MVCTag.SetPerPointMode(False)

            CTag = Csample.MakeTag(c4d.Ttexture)
            CTag[c4d.TEXTURETAG_PROJECTION] = 6
            CTag.SetMaterial(AtlasMaterial)
            Csample.InsertTag(CTag, MVCTag)

            if not MVCTag:
                MVCTag = Csample.GetTag(c4d.Tvertexmap)

            CHalfWidth = float(node.attrib.get("width")) * 0.5 * ScaleRatio
            CHalfHeight = float(node.attrib.get("height")) * 0.5 * ScaleRatio

            CInstance = c4d.BaseObject(c4d.Oinstance)
            CInstance.SetName(currenName + "_Instance")
            CInstance[c4d.INSTANCEOBJECT_LINK] = Csample
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) * ScaleRatio - AtlasHalfWidth + CHalfWidth
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) * ScaleRatio + AtlasHalfHeight - CHalfHeight
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
            
            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
            bc[c4d.DESC_NAME] = "OBJECT EXPORT INFO"
            bc[c4d.DESC_SHORT_NAME] = "OBJECT EXPORT INFO"
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_DEFAULT] = True
            bc[c4d.DESC_TITLEBAR] = True
            bc[c4d.DESC_COLUMNS] = 1
            ObjectExportGroup = CInstance.AddUserData(bc)
            #CInstance[ObjectExportGroup] = "OBJECT EXPORT INFO"

            print("Instance", ObjectExportGroup)

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL)
            bc[c4d.DESC_NAME] = "IsSpriteSheetSample"
            bc[c4d.DESC_SHORT_NAME] = "IsSpriteSheetSample"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = ObjectExportGroup
            element = CInstance.AddUserData(bc)
            CInstance[element] = True

            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BASELISTLINK)
            bc[c4d.DESC_NAME] = "Sample Reference"
            bc[c4d.DESC_SHORT_NAME] = "Sample Reference"
            bc[c4d.DESC_EDITABLE] = False
            bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            bc[c4d.DESC_PARENTGROUP] = ObjectExportGroup
            element = CInstance.AddUserData(bc)
            CInstance[element] = Csample

            rotated = node.attrib.get("rotated") == "true"            
            if rotated:
                #re-rotate the object
                CInstance[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = math.pi / 2
        
            CInstance.InsertUnder(InstancesContainer)

            #Refresh the managers to show the new object
            c4d.EventAdd()

            #Fix sample pivot to match the original sample. If SubTexture have no frame info, it was not trimed so there is no need to adjust pivot.
            if bool(node.attrib.get("frameX")):
                CInstance[c4d.ID_BASEOBJECT_REL_POSITION] = Csample[c4d.ID_BASEOBJECT_REL_POSITION]

            #Create undo for this operation
            doc.AddUndo(c4d.UNDOTYPE_NEW, Csample)
            #print(node.tag, currenName, Csample2)
        else:
            if CInstance and CInstance.GetUp() == InstancesContainer:
                CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) * ScaleRatio - AtlasHalfWidth + CHalfWidth
                CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) * ScaleRatio + AtlasHalfHeight - CHalfHeight
                CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
                CInstance[c4d.ID_BASEOBJECT_REL_POSITION] = CInstance[c4d.ID_BASEOBJECT_REL_POSITION] - pivotDiff

            doc.AddUndo(c4d.UNDOTYPE_NEW, Csample)

    #Some samples could be missing from the new atlas, is this happen, mark them as missing samples by giving a red texture and fixed size
    if len(AtlasSamplesList) > 0:
        gui.MessageDialog("Some sprites are missing from this spritesheet. They will be turned red. Delete the sprites if not needed or reimport a spritesheet containing all sprites from last import")

    for missingName in AtlasSamplesList:
        # Udate samples which are missing on the new sprite sheet
        for Csample in get_all_objects(doc.GetFirstObject(), lambda x:UserDataAndNameCheck(x, missingName, "IsSpriteSheetSample", True), []):
            #Csample.KillTag(c4d.Ttexture)
            CTag = Csample.GetTag(c4d.Ttexture)
            #CTag = Csample.MakeTag(c4d.Ttexture)
            #CTag[c4d.TEXTURETAG_PROJECTION] = 6
            CTag.SetMaterial(MissingMaterial)
            Csample.InsertTag(CTag, Csample.GetTag(c4d.Tvertexmap))

            if SParent == SamplesContainer:
                Csample.InsertUnder(SamplesContainer)

    #Create a plane representing the Atlas Texture as a hole. Objects and this plane should show exacly same texture on them own position. Use this to verify if all goes right
    CAtlas = doc.SearchObject(FileName + " TextureAtlas")
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
        CTag = Csample.GetTag(c4d.Ttexture)
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
    print('TVertexcolor', TVertexcolor, CAtlas)
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