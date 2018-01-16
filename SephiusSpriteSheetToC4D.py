import c4d
import os
from c4d import gui
from c4d import storage
from c4d import utils
from xml.etree import ElementTree
 
#Welcome to the world of Python
 
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

def SetPolygon(ParentName, CObject, UVWTag, Polygon, TextureNode, AtlasWidth, AtlasHeight):
    #print "Getting Atlas Sizes: ", AtlasWidth, AtlasHeight
    #AtlasWidth =  float(TextureNode.attrib.get("width"))
    AtlasHalfWidth = AtlasWidth * 0.5
    #AtlasHeight = float(TextureNode.attrib.get("height"))
    AtlasHalfHeight = AtlasHeight * 0.5

    CHalfWidth = float(TextureNode.attrib.get("width")) * 0.5
    CHalfHeight = float(TextureNode.attrib.get("height")) * 0.5
    
    HasFrmeInfo = bool(TextureNode.attrib.get("frameX"))
    if HasFrmeInfo:
        CDIFFX = -float(TextureNode.attrib.get("frameX")) - (float(TextureNode.attrib.get("frameWidth"))  - float(TextureNode.attrib.get("width")))
        CDIFFY = float(TextureNode.attrib.get("frameY")) + (float(TextureNode.attrib.get("frameHeight")) - float(TextureNode.attrib.get("height")))
        diff = c4d.Vector(CDIFFX * 0.5, CDIFFY * 0.5, 0)
        CoDiff = c4d.Vector(0, 0, 0)
    else:
        diff = c4d.Vector(0, 0, 0)
        CoDiff = c4d.Vector(0, 0, 0)
    
    CX = float(TextureNode.attrib.get("x")) - AtlasHalfWidth + CHalfWidth
    CY = -float(TextureNode.attrib.get("y")) + AtlasHalfHeight - CHalfHeight
    CPX = -float(TextureNode.attrib.get("width")) * 0.5
    CPY = float(TextureNode.attrib.get("height")) * 0.5
    CPW = float(TextureNode.attrib.get("width")) * 0.5
    CPH = -float(TextureNode.attrib.get("height")) * 0.5
    
    pX = CPX
    pY = CPY
    hX = CPW
    hY = CPH
    
    PSs = []
    PSs.append(c4d.Vector(pX, pY, 0) + diff)
    PSs.append(c4d.Vector(hX, pY, 0) + diff)
    PSs.append(c4d.Vector(hX, hY, 0) + diff)
    PSs.append(c4d.Vector(pX, hY, 0) + diff)           
    
    if not Polygon:
        Polygon = c4d.CPolygon(0, 1, 2, 3)
        Polygon.__init__(0, 1, 2, 3)
        CObject.ResizeObject(4, 1)
        CObject.SetPolygon(0, Polygon)
   
    pcount = CObject.GetPointCount()
    point = CObject.GetAllPoints()
    for i in xrange(pcount):
        CObject.SetPoint(i, PSs[i])
        
    #Update object. Need to update bound box for selection and etc.
    CObject.Message (c4d.MSG_UPDATE)
    
    #print "UV Coord px: ", float(TextureNode.attrib.get("x")), float(TextureNode.attrib.get("y")), float(TextureNode.attrib.get("width")), float(TextureNode.attrib.get("height"))
    CoX = float(TextureNode.attrib.get("x")) / AtlasWidth
    CoY = float(TextureNode.attrib.get("y")) / AtlasHeight
    CoHX = (float(TextureNode.attrib.get("x")) + float(TextureNode.attrib.get("width"))) / AtlasWidth
    CoHY = (float(TextureNode.attrib.get("y")) + float(TextureNode.attrib.get("height"))) / AtlasHeight
    
    #print "Atlas: ", AtlasWidth, AtlasHeight
    #print "UVW: ", CoX, CoY, CoHX, CoHY
    
    PCSs = []
    PCSs.append(c4d.Vector(CoX, CoY, 0) + CoDiff)
    PCSs.append(c4d.Vector(CoHX, CoY, 0) + CoDiff)
    PCSs.append(c4d.Vector(CoHX, CoHY, 0) + CoDiff)
    PCSs.append(c4d.Vector(CoX, CoHY, 0) + CoDiff) 
              
    if not UVWTag:
        UVWTag = CObject.MakeVariableTag(c4d.Tuvw, 1)
        UVWTag[c4d.ID_BASELIST_NAME] = "SampleUVW"
        
    UVWTag.SetSlow(0, PCSs[0], PCSs[1], PCSs[2], PCSs[3])
    
    if CObject.GetUp().GetName() == ParentName:
        CObject[c4d.ID_BASEOBJECT_REL_POSITION] = CObject[c4d.ID_BASEOBJECT_REL_POSITION] - diff 

    
#Return true if object has a user data name and value is equal to desired
def UserDataCheck(CObject, UDName, Value):
    for id, bc in CObject.GetUserDataContainer():
        #print bc[c4d.DESC_NAME], UDName
        if bc[c4d.DESC_NAME] == UDName:
            #print CObject[id], Value
            if CObject[id] == Value:
                return True
    return False

def UserDataAndNameCheck(CObject, OName, UDName, Value):
    #print CObject.GetName(), OName, UserDataCheck(CObject, UDName, Value), CObject.GetName().split(".")[0] == OName
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

def main():
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
     
    print "-------- XMLpath:"
    print XMLpath
     
    #Verify if the file is valid
    if not XMLpath:
        return
    elif XMLpath == "":
        return
    elif not isXML:
        print gui.MessageDialog("File path is not for XML or is null")
        return
     
    #Open and parse the file creating a ElementTree with all info inside
    with open(XMLpath.decode("utf-8"), 'rt') as f:
        tree = ElementTree.parse(f)
     
    #Verify if the XML has "TextureAtlas" node. If has set info about the TextureAtlas
    hasTextureAtlas = 0;
    for node in tree.iter("TextureAtlas"): 
        hasTextureAtlas = 1;   
        AtlasWidth =  float(node.attrib.get("width"))
        AtlasHalfWidth = AtlasWidth * 0.5
        AtlasHeight = float(node.attrib.get("height"))
        AtlasHalfHeight = AtlasHeight * 0.5
        PNGpath = folderPath + node.attrib.get("imagePath")
        #print "Setting Atlas Sizes: ", AtlasWidth, AtlasHeight

        if AtlasWidth >= AtlasHeight:
            TextureBiggerSize = AtlasHeight
        else:
            TextureBiggerSize = AtlasWidth
            
        TextureSizeRatio = 1024 / AtlasWidth

        
    #Stop ant show a error if XML does not have "TextureAtlas" node
    if not hasTextureAtlas:
        print gui.MessageDialog("XML does not have TextureAtlas information")
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
        SamplesContainer[Celement] = "Atlas Information"
     
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
        SamplesContainer[C2element] = "Resolution"
         
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
    print AtlasMaterial
    if not AtlasMaterial:
        # create material
        AtlasMaterial = c4d.BaseMaterial(c4d.Mmaterial)
        AtlasMaterial.SetName( FileName + " Material" )
     
    MShaderD = c4d.BaseList2D(c4d.Xbitmap)
    MShaderD[c4d.BITMAPSHADER_FILENAME]  = folderPath + FileName + ".png"
    AtlasMaterial.InsertShader( MShaderD )
    AtlasMaterial[c4d.MATERIAL_COLOR_SHADER]  = MShaderD
     
    # Create Material or Update the Existing one
    AtlasMaterial[c4d.MATERIAL_USE_ALPHA] = True
    AtlasMaterial[c4d.MATERIAL_USE_REFLECTION] = False
    AtlasMaterial[c4d.MATERIAL_PREVIEWSIZE] = 13
    AtlasMaterial[c4d.MATERIAL_USE_TRANSPARENCY] = True
    AtlasMaterial[c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS] = 0
    
    MShaderA = c4d.BaseList2D(c4d.Xbitmap)
    MShaderA[c4d.BITMAPSHADER_FILENAME]  = folderPath + FileName + ".png"
    
    LayerSet = c4d.LayerSet()
    LayerSet.SetMode(c4d.LAYERSETMODE_LAYERALPHA)
    MShaderA[c4d.BITMAPSHADER_LAYERSET] = LayerSet
    MShaderA[c4d.BITMAPSHADER_BLACKPOINT] = 1
    MShaderA[c4d.BITMAPSHADER_WHITEPOINT] = 0

    AtlasMaterial.InsertShader( MShaderA )
    AtlasMaterial[c4d.MATERIAL_TRANSPARENCY_SHADER] = MShaderA
    
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
        
    #print "Sample List USer Data: ", SamplesContainer[c4d.ID_USERDATA,4]     
    AtlasSamplesList = (SamplesContainer[c4d.ID_USERDATA,4]).split(",")
    AtlasSamplesList.pop()
    #print "Sample List: ", AtlasSamplesList
    SamplesContainer[c4d.ID_USERDATA,4] = ""
     
    #Create the Samples
    for node in tree.iter("SubTexture"):
        currenName = node.attrib.get("name")
        CHalfWidth = float(node.attrib.get("width")) * 0.5
        CHalfHeight = float(node.attrib.get("height")) * 0.5
        
        HasFrameInfo = bool(node.attrib.get("frameX"))
        if HasFrameInfo:
            CDIFFX = -float(node.attrib.get("frameX")) - (float(node.attrib.get("frameWidth"))  - float(node.attrib.get("width")))
            CDIFFY = float(node.attrib.get("frameY")) + (float(node.attrib.get("frameHeight")) - float(node.attrib.get("height")))
            diff = c4d.Vector(CDIFFX * 0.5, CDIFFY * 0.5, 0)
        else:
            diff = c4d.Vector(0, 0, 0)

        Csample = False
        
        hasExistingSamples = False
        #Updating Actual Samples:...
        for Csample in get_all_objects(doc.GetFirstObject(), lambda x:UserDataAndNameCheck(x, currenName + "_Sample", "IsSpriteSheetSample", True), []):
            hasExistingSamples = True
            print "hasExistingSamples: ", hasExistingSamples, currenName, Csample.GetName()
            
            SParent = Csample.GetUp()
            
            XTag = None
            for XTag in Csample.GetTags():
               if XTag[c4d.ID_BASELIST_NAME] == "SampleUVW":
                   CTag = XTag

            SetPolygon(FileName + " Samples", Csample, CTag, Csample.GetPolygon(0), node, AtlasWidth, AtlasHeight)
            
            CTag = Csample.GetTag(c4d.Ttexture)
            CTag.SetMaterial(AtlasMaterial)

            oldDiff = Csample[c4d.ID_USERDATA,2]
            Csample[c4d.ID_BASEOBJECT_REL_POSITION] = Csample[c4d.ID_BASEOBJECT_REL_POSITION] + oldDiff
            
            if SParent == SamplesContainer:
                Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) - AtlasHalfWidth + CHalfWidth
                Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) + AtlasHalfHeight - CHalfHeight
                Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
                Csample.InsertUnder(SamplesContainer)
            
            Csample[c4d.ID_BASEOBJECT_REL_POSITION] = Csample[c4d.ID_BASEOBJECT_REL_POSITION] - diff
            
        #Create and set object parameters
        CInstance = getChild(InstancesContainer, currenName + "_Instance")
        
        #Verify if sample is on sample list
        if (currenName + "_Sample") in AtlasSamplesList:
            #print "Sample is listed"
            SampleListIndex = AtlasSamplesList.index(currenName + "_Sample")
            AtlasSamplesList.pop(SampleListIndex)
             
        SamplesContainer[c4d.ID_USERDATA,4] = SamplesContainer[c4d.ID_USERDATA,4] + currenName + "_Sample,"
         
        if not hasExistingSamples:
            #print "Don´t have Existing Samples: ", hasExistingSamples, currenName
            #Set the Sample
            Csample = c4d.BaseObject(c4d.Opolygon)
            Csample.SetName(currenName + "_Sample")
            
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) - AtlasHalfWidth + CHalfWidth
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) + AtlasHalfHeight - CHalfHeight
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
           
            Csample.InsertUnder(SamplesContainer)
            
            SetPolygon(FileName + " Samples", Csample, None, None, node, AtlasWidth, AtlasHeight)
            
            CTag = c4d.VertexColorTag(4)
            CTag.__init__(4)
            Csample.InsertTag(CTag)
            VCdata = CTag.GetDataAddressW()
            white = c4d.Vector(1.0, 1.0, 1.0)
            
            pointCount = Csample.GetPointCount()
            for idx in xrange(pointCount):
              CTag.SetColor(VCdata, None, None, idx, white)
              CTag.SetAlpha(VCdata, None, None, idx, 1)
              
            c4d.EventAdd()
            
            CTag.SetPerPointMode(False) 
   
            CTag = Csample.MakeTag(c4d.Ttexture)
            CTag[c4d.TEXTURETAG_PROJECTION] = 6
            CTag.SetMaterial(AtlasMaterial)
            Csample.InsertTag(CTag, Csample.GetTag(c4d.Tvertexmap))
            
         
            if not MVCTag:
                MVCTag = CTag
            
            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL)
            bc[c4d.DESC_NAME] = "IsSpriteSheetSample"
            bc[c4d.DESC_EDITABLE] = False
            element = Csample.AddUserData(bc)
            Csample[element] = True
            
            bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_VECTOR) 
            bc[c4d.DESC_NAME] = "Offset"
            bc[c4d.DESC_EDITABLE] = False
            element = Csample.AddUserData(bc)
            Csample[element] = diff

            CHalfWidth = float(node.attrib.get("width")) * 0.5
            CHalfHeight = float(node.attrib.get("height")) * 0.5
        
            CInstance = c4d.BaseObject(c4d.Oinstance)
            CInstance.SetName(currenName + "_Instance")
            CInstance[c4d.INSTANCEOBJECT_LINK] = Csample
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) - AtlasHalfWidth + CHalfWidth
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) + AtlasHalfHeight - CHalfHeight
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
            CInstance.InsertUnder(InstancesContainer)
           
            #Refresh the managers to show the new object    
            c4d.EventAdd()
               
            #Fix sample pivot to match the original sample. If SubTexture have no frame info, it was not trimed so there is no need to adjust pivot.
            if bool(node.attrib.get("frameX")):
                CInstance[c4d.ID_BASEOBJECT_REL_POSITION] = Csample[c4d.ID_BASEOBJECT_REL_POSITION]
            
            #Create undo for this operation
            doc.AddUndo(c4d.UNDOTYPE_NEW, Csample)
            #print node.tag, currenName, Csample2
        else:
            if CInstance.GetUp() == InstancesContainer:
                CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) - AtlasHalfWidth + CHalfWidth
                CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) + AtlasHalfHeight - CHalfHeight
                CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
                CInstance[c4d.ID_BASEOBJECT_REL_POSITION] = CInstance[c4d.ID_BASEOBJECT_REL_POSITION] - diff
                
            doc.AddUndo(c4d.UNDOTYPE_NEW, Csample)
     
    #Some samples could be missing from the new atlas, is this happen, mark them as missing samples by giving a red texture and fixed size
    if len(AtlasSamplesList) > 0:
        gui.MessageDialog("Some sprites are missing from this spritesheet. They will be turned red. Delete the sprites if not needed or reimport a spritesheet containing all sprites from last import")
    
    for missingName in AtlasSamplesList:
        # Udate samples which are missing on the new sprite sheet
        for Csample in get_all_objects(doc.GetFirstObject(), lambda x:UserDataAndNameCheck(x, missingName, "IsSpriteSheetSample", True), []):
            Csample.KillTag(c4d.Ttexture)
            
            CTag = Csample.MakeTag(c4d.Ttexture)
            CTag[c4d.TEXTURETAG_PROJECTION] = 6
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
        for i in xrange(pcount):
            CAtlas.SetPoint(i, PSs[i])

        PCSs = []
        PCSs.append(c4d.Vector(0, 1, 0))
        PCSs.append(c4d.Vector(1, 1, 0))
        PCSs.append(c4d.Vector(1, 0, 0))
        PCSs.append(c4d.Vector(0, 0, 0))
        
        CTag = c4d.VertexColorTag(4)
        CTag.__init__(4)
        CAtlas.InsertTag(CTag)
        VCdata = CTag.GetDataAddressW()
        white = c4d.Vector(1.0, 1.0, 1.0)
        
        pointCount = CAtlas.GetPointCount()
        for idx in xrange(pointCount):
          CTag.SetColor(VCdata, None, None, idx, white)
          CTag.SetAlpha(VCdata, None, None, idx, 1)
          
        c4d.EventAdd()
        
        CTag.SetPerPointMode(False) 
 
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
        for i in xrange(pcount):
            CAtlas.SetPoint(i, PSs[i])


    #Add plane to the Atlas Container
    CAtlas.InsertUnder(SamplesContainer)
    doc.AddUndo(c4d.UNDOTYPE_NEW, CAtlas)
        
    MShaderT = c4d.BaseList2D(c4d.Xvertexmap)
    MShaderT[c4d.SLA_DIRTY_VMAP_OBJECT] = MVCTag
    AtlasMaterial.InsertShader( MShaderT )
    AtlasMaterial[c4d.MATERIAL_ALPHA_SHADER] = MShaderT
    AtlasMaterial.Message( c4d.MSG_UPDATE )
    AtlasMaterial.Update( True, True )

    CAtlas[c4d.PRIM_PLANE_WIDTH] = float(AtlasWidth)
    CAtlas[c4d.PRIM_PLANE_HEIGHT] = float(AtlasHeight)
    
    doc.EndUndo()
    c4d.EventAdd()
     
    return
     
if __name__=='__main__':
    main()