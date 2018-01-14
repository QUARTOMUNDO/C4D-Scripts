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

def get_all_objects(op, filter, output):
    while op:
        if filter(op):
            output.append(op)
        get_all_objects(op.GetDown(), filter, output)
        op = op.GetNext()
    return output

def getChildren(parent):
    PChildren = []
    nextObject = parent.GetDown()
    PChildren.append(nextObject)
    
    while nextObject:
        nextObject = nextObject.GetNext()
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
 
        #bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BUTTON) # Create Atlas Name Data
        #bc[c4d.DESC_NAME] = "Reload Atlas"
        #bc[c4d.DESC_PARENTGROUP] = Celement
        #bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_BUTTON
        #element = SamplesContainer.AddUserData(bc)
 
        Cbc2 = c4d.BaseContainer(c4d.DTYPE_GROUP) # Create Group
        Cbc2[c4d.DESC_NAME] = "Resolution"
        Cbc2[c4d.DESC_SHORT_NAME] = "Res"
        Cbc2[c4d.DESC_PARENTGROUP] = Celement
        #Cbc2[c4d.DESC_TITLEBAR] = False
        #Cbc2[c4d.DESC_LAYOUTGROUP] = True
        #Cbc2[c4d.DESC_LAYOUTVERSION] = 0
        Cbc2[c4d.DESC_COLUMNS] = 2
        #Cbc2[c4d.DESC_COLUMNSMATED] = 3
        #Cbc2[c4d.DESC_NOGUISWITCH] = False
        #Cbc2[c4d.DESC_GUIOPEN] = True
 
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
    InstancesContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = 0
    InstancesContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
 
    #Create Camera to be used for mapping texture
    cameraProject = doc.SearchObject(FileName + " CameraProject")
    if not cameraProject:
        cameraProject = c4d.BaseObject(c4d.Ocamera)
        cameraProject.SetName(FileName + " CameraProject")
        cameraProject[c4d.CAMERA_PROJECTION] = 4  #Caution, this index could change on future C4D versions. Option should be "Front"
        cameraProject.InsertUnder(SamplesContainer)
        doc.AddUndo(c4d.UNDOTYPE_NEW, cameraProject)
     
    cameraProject.SetZoom(TextureSizeRatio)
     
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
    MShaderA = c4d.BaseList2D(c4d.Xbitmap)
    MShaderA[c4d.BITMAPSHADER_FILENAME]  = folderPath + FileName + ".png"
    AtlasMaterial[c4d.MATERIAL_USE_ALPHA] = True
    AtlasMaterial[c4d.MATERIAL_USE_REFLECTION] = False
    AtlasMaterial[c4d.MATERIAL_PREVIEWSIZE] = 13
    AtlasMaterial.InsertShader( MShaderA )
    AtlasMaterial[c4d.MATERIAL_ALPHA_SHADER] = MShaderA
 
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
         
    AtlasSamplesList = (SamplesContainer[c4d.ID_USERDATA,4]).split(",")
    AtlasSamplesList.pop()
    print "Sample List: ", AtlasSamplesList
    SamplesContainer[c4d.ID_USERDATA,4] = ""
     
    #Create the Samples
    for node in tree.iter("SubTexture"):
        currenName = node.attrib.get("name")
        CHalfWidth = float(node.attrib.get("width")) * 0.5
        CHalfHeight = float(node.attrib.get("height")) * 0.5
         
        Csample = False
         
        #Create and set object parameters
        Csample = getChild(SamplesContainer, currenName + "_Sample")
        CInstance = getChild(InstancesContainer, currenName + "_Instance")
        #CInstanceSub = getChild(InstancesContainer, currenName + "_Object")
        
        #Verify if sample is on sample list
        #SampleListIndex = AtlasSamplesList.index(currenName + "_Sample")
        if (currenName + "_Sample") in AtlasSamplesList:
            #print "Sample is listed"
            SampleListIndex = AtlasSamplesList.index(currenName + "_Sample")
            AtlasSamplesList.pop(SampleListIndex)
             
        SamplesContainer[c4d.ID_USERDATA,4] = SamplesContainer[c4d.ID_USERDATA,4] + currenName + "_Sample,"
         
        if not Csample:
            #Set the Sample
            Csample = c4d.BaseObject(c4d.Oplane)
            Csample.SetName(currenName + "_Sample")
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) - AtlasHalfWidth + CHalfWidth
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) + AtlasHalfHeight - CHalfHeight
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
            Csample[c4d.PRIM_PLANE_WIDTH] = float(node.attrib.get("width"))
            Csample[c4d.PRIM_PLANE_HEIGHT] = float(node.attrib.get("height"))
            Csample[c4d.PRIM_PLANE_SUBW] = 1
            Csample[c4d.PRIM_PLANE_SUBH] = 1
            Csample[c4d.PRIM_AXIS] = 5  #Caution, this index could change on future C4D versions. Option should be -Z
            Csample.InsertUnder(SamplesContainer)
            
            #Set the Instance
            #CInstanceSub = c4d.BaseObject(c4d.Osds)
            #CInstanceSub.SetName(currenName + "_Object")
            #CInstanceSub[c4d.SDSOBJECT_SUBEDITOR_CM] = 0
            #CInstanceSub[c4d.SDSOBJECT_SUBRAY_CM] = 0
            #CInstanceSub[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) - AtlasHalfWidth + CHalfWidth
            #CInstanceSub[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) + AtlasHalfHeight - CHalfHeight
            #CInstanceSub[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
            #CInstanceSub.InsertUnder(InstancesContainer)
            
            #It seams there is no support to add modifers witch create polygons on real time using phyton script
            #Set the Corretion (for support Distortions)
            #CInstanceCorrect = c4d.BaseObject(1024542)#Can´t find Ocorrection ID from SDK documentation. "1024542" id the current ID shown for C4DR18
            #CInstanceCorrect.SetName(currenName + "_Correction")
            #CInstanceCorrect.InsertUnder(CInstanceSub)
            #CInstanceCorrect.Message(c4d.MSG_UPDATE)
            #c4d.EventAdd()
            
            CInstance = c4d.BaseObject(c4d.Oinstance)
            CInstance.SetName(currenName + "_Instance")
            CInstance[c4d.INSTANCEOBJECT_LINK] = Csample
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) - AtlasHalfWidth + CHalfWidth
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) + AtlasHalfHeight - CHalfHeight
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
            CInstance.InsertUnder(InstancesContainer)
           
            #Refresh the managers to show the new object    
            c4d.EventAdd()
             
            #Make Object Editable
            Csample2 = c4d.utils.SendModelingCommand(command = c4d.MCOMMAND_MAKEEDITABLE,list = [Csample], mode = c4d.MODELINGCOMMANDMODE_ALL, bc = c4d.BaseContainer(), doc = doc)[0]
            Csample2.InsertUnder(SamplesContainer)
            
            #Create a Texture Tag and use Camera Mapping to reproduce Atlas Subtexture coordinates
            CTag = Csample2.MakeTag(c4d.Ttexture)
            CTag[c4d.TEXTURETAG_PROJECTION] = 8 #Caution, this index could change on future C4D versions. Option should be "Camera Mapping"
            CTag[c4d.TEXTURETAG_CAMERA_FILMASPECT] = AtlasWidth/AtlasHeight
            CTag[c4d.TEXTURETAG_CAMERA] = cameraProject
            CTag[c4d.TEXTURETAG_MATERIAL] = AtlasMaterial
         
            #Create a UVW Tag with the created mapping from above. So object can be moved without have UVW mapping spoiled
            CTTag = c4d.utils.GenerateUVW(Csample2, Csample2.GetMg(), CTag, Csample2.GetMg())
         
            #Change the order of the Tags (Texture Tag uses the closest right tag)
            Csample2.InsertTag(CTTag)
            Csample2.InsertTag(CTag)
         
            #Turn texture projection back do UVW on the Texture Tag
            CTag[c4d.TEXTURETAG_PROJECTION] = 6 #Caution, this index could change on future C4D versions. Option should be "Camera Mapping"
               
            #Fix sample pivot to match the original sample. If SubTexture have no frame info, it was not trimed so there is no need to adjust pivot.
            if bool(node.attrib.get("frameX")):
                pcount = Csample2.GetPointCount()
                point = Csample2.GetAllPoints()
                diffX = -float(node.attrib.get("frameX")) - (float(node.attrib.get("frameWidth"))  - float(node.attrib.get("width")))
                diffY =  float(node.attrib.get("frameY")) + (float(node.attrib.get("frameHeight")) - float(node.attrib.get("height")))
                diff = c4d.Vector(diffX * 0.5, diffY * 0.5, 0)
                for i in xrange(pcount):
                     Csample2.SetPoint(i, point[i]+diff) 
                      
                #Update object. Need to update bound box for selection and etc.
                Csample2.Message (c4d.MSG_UPDATE)
                Csample2[c4d.ID_BASEOBJECT_REL_POSITION] = Csample2[c4d.ID_BASEOBJECT_REL_POSITION] - diff
                CInstance[c4d.ID_BASEOBJECT_REL_POSITION] = CInstance[c4d.ID_BASEOBJECT_REL_POSITION] - diff
                 
            #Create undo for this operation
            doc.AddUndo(c4d.UNDOTYPE_NEW, Csample2)
            #print node.tag, currenName, Csample2
        else:
            #print "Sample Alrady Exist", Csample
            #Update Code
            Csample.KillTag(c4d.Ttexture)
            Csample.KillTag(c4d.Tuvw)
             
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) - AtlasHalfWidth + CHalfWidth
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) + AtlasHalfHeight - CHalfHeight
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
             
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.attrib.get("x")) - AtlasHalfWidth + CHalfWidth
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.attrib.get("y")) + AtlasHalfHeight - CHalfHeight
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
           
            pX = -float(node.attrib.get("width")) * 0.5
            PY = float(node.attrib.get("height")) * 0.5
            hX = float(node.attrib.get("width")) * 0.5
            hY = -float(node.attrib.get("height")) * 0.5
             
            if bool(node.attrib.get("frameX")):
                diffX = -float(node.attrib.get("frameX")) - (float(node.attrib.get("frameWidth"))  - float(node.attrib.get("width")))
                diffY =  float(node.attrib.get("frameY")) + (float(node.attrib.get("frameHeight")) - float(node.attrib.get("height")))
                diff = c4d.Vector(diffX * 0.5, diffY * 0.5, 0)
            else:
                diffX = 0
                diffY = 0
                diff = c4d.Vector(0, 0, 0)
             
            PSs = []
            PSs.append(c4d.Vector(hX, PY, 0) + diff)
            PSs.append(c4d.Vector(pX, PY, 0) + diff)
            PSs.append(c4d.Vector(hX, hY, 0) + diff)           
            PSs.append(c4d.Vector(pX, hY, 0) + diff)
             
            pcount = Csample.GetPointCount()
            point = Csample.GetAllPoints()
            for i in xrange(pcount):
                Csample.SetPoint(i, PSs[i])
             
            Csample[c4d.ID_BASEOBJECT_REL_POSITION] = Csample[c4d.ID_BASEOBJECT_REL_POSITION] - diff   
            CInstance[c4d.ID_BASEOBJECT_REL_POSITION] = CInstance[c4d.ID_BASEOBJECT_REL_POSITION] - diff
             
            #Update object. Need to update bound box for selection and etc.
            Csample.Message (c4d.MSG_UPDATE) 
             
            #Create a Texture Tag and use Camera Mapping to reproduce Atlas Subtexture coordinates
            CTag = Csample.MakeTag(c4d.Ttexture)
            CTag[c4d.TEXTURETAG_PROJECTION] = 8 #Caution, this index could change on future C4D versions. Option should be "Camera Mapping"
            CTag[c4d.TEXTURETAG_CAMERA_FILMASPECT] = AtlasWidth/AtlasHeight
            CTag[c4d.TEXTURETAG_CAMERA] = cameraProject
            CTag[c4d.TEXTURETAG_MATERIAL] = AtlasMaterial
         
            #Create a UVW Tag with the created mapping from above. So object can be moved without have UVW mapping spoiled
            CTTag = c4d.utils.GenerateUVW(Csample, Csample.GetMg(), CTag, Csample.GetMg())
         
            #Change the order of the Tags (Texture Tag uses the closest right tag)
            Csample.InsertTag(CTTag)
            Csample.InsertTag(CTag)
         
            #Turn texture projection back do UVW on the Texture Tag
            CTag[c4d.TEXTURETAG_PROJECTION] = 6 #Caution, this index could change on future C4D versions. Option should be "Camera Mapping"
 
            Csample.InsertUnder(SamplesContainer)    
            #Create undo for this operation
            doc.AddUndo(c4d.UNDOTYPE_NEW, Csample)
     
    #Some samples could be missing from the new atlas, is this happen, mark them as missing samples by giving a red texture and fixed size
    for node in  AtlasSamplesList:
        Csample = getChild(SamplesContainer, node)
         
        CInstance = getChild(InstancesContainer, node[:-6] + "Instance")
        CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = 0
        CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = 0
        CInstance[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = -200
       
        SamplesContainer[c4d.ID_USERDATA,4] = SamplesContainer[c4d.ID_USERDATA,4] + node + ","
        
        if Csample:
            Csample.KillTag(c4d.Ttexture)
            #Csample.KillTag(c4d.Tuvw)
             
            PSs = []
            PSs.append(c4d.Vector(15, 15, 0))
            PSs.append(c4d.Vector(-15, 15, 0))
            PSs.append(c4d.Vector(15, -15, 0))           
            PSs.append(c4d.Vector(-15, -15, 0))
 
            pcount = Csample.GetPointCount()
            point = Csample.GetAllPoints()
            for i in xrange(pcount):
                Csample.SetPoint(i, PSs[i])
              
            #Update object. Need to update bound box for selection and etc.
            Csample.Message (c4d.MSG_UPDATE)
             
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = 0
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = 0
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = -200
 
            CTag = Csample.MakeTag(c4d.Ttexture)
            CTag[c4d.TEXTURETAG_MATERIAL] = MissingMaterial
 
        else:
            Csample = c4d.BaseObject(c4d.Oplane)
            Csample.SetName(node)
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = 0
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = 0
            Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = -200
            Csample[c4d.PRIM_PLANE_WIDTH] = 30
            Csample[c4d.PRIM_PLANE_HEIGHT] = 30
            Csample[c4d.PRIM_PLANE_SUBW] = 1
            Csample[c4d.PRIM_PLANE_SUBH] = 1
            Csample[c4d.PRIM_AXIS] = 5  #Caution, this index could change on future C4D versions. Option should be -Z
             
            CTag = Csample.MakeTag(c4d.Ttexture)
            CTag[c4d.TEXTURETAG_MATERIAL] = MissingMaterial
 
            #Make Object Editable
            Csample2 = c4d.utils.SendModelingCommand(command = c4d.MCOMMAND_MAKEEDITABLE,list = [Csample], mode = c4d.MODELINGCOMMANDMODE_ALL, bc = c4d.BaseContainer(), doc = doc)[0]
            Csample2.InsertUnder(SamplesContainer)
 
            CTag = Csample2.MakeTag(c4d.Ttexture)
            CTag[c4d.TEXTURETAG_MATERIAL] = MissingMaterial
     
    #Create a plane representing the Atlas Texture as a hole. Objects and this plane should show exacly same texture on them own position. Use this to verify if all goes right
    Csample = doc.SearchObject(FileName + " TextureAtlas")
    if not Csample:
        Csample = c4d.BaseObject(c4d.Oplane)
        Csample.SetName(FileName + " TextureAtlas")
        Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = 0
        Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = 0
        Csample[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 10
        Csample[c4d.PRIM_PLANE_SUBW] = 1
        Csample[c4d.PRIM_PLANE_SUBH] = 1
        Csample[c4d.PRIM_AXIS] = 5
        Csample[c4d.ID_BASEOBJECT_USECOLOR] = True
        Csample[c4d.ID_BASEOBJECT_COLOR] = c4d.Vector(255, 255, 255)
         
        #Add texture tag to this plane
        CTag = Csample.MakeTag(c4d.Ttexture)
        CTag[c4d.TEXTURETAG_PROJECTION] = 8 #Caution, this index could change on future C4D versions. Option should be "Camera Mapping"
        CTag[c4d.TEXTURETAG_CAMERA] = cameraProject
        CTag[c4d.TEXTURETAG_MATERIAL] = AtlasMaterial
    else:
        CTag = Csample.GetTag(c4d.Ttexture)
         
    CTag[c4d.TEXTURETAG_CAMERA_FILMASPECT] = AtlasWidth/AtlasHeight
     
    #Add plane to the Atlas Container
    Csample.InsertUnder(SamplesContainer)
    doc.AddUndo(c4d.UNDOTYPE_NEW, Csample)
     
    Csample[c4d.PRIM_PLANE_WIDTH] = float(AtlasWidth)
    Csample[c4d.PRIM_PLANE_HEIGHT] = float(AtlasHeight)
     
    #Put Camera on top of the hierarky
    cameraProject.InsertUnder(SamplesContainer)
    doc.AddUndo(c4d.UNDOTYPE_NEW, cameraProject)
    
    doc.EndUndo()
    c4d.EventAdd()
     
    return
     
if __name__=='__main__':
    main()