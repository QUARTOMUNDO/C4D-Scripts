import c4d
import os
import random
from random import randint
from c4d import gui
from c4d import storage
from c4d import utils
from xml.etree import ElementTree

XMLpath = ""
FileName = ""
folderPath = ""

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

def setUserDataFromNode(cObject, node):
    for attribute in node.attrib.keys():
        
        FinalValue = 0
        try :
            FinalValue = float(node.attrib.get(attribute))
            dataType = c4d.DTYPE_REAL
        except:
            if node.attrib.get(attribute) == "false":
                dataType = c4d.DTYPE_BOOL
                FinalValue = bool(node.attrib.get(attribute))
            elif node.attrib.get(attribute) == "true":
                dataType = c4d.DTYPE_BOOL
                FinalValue = bool(node.attrib.get(attribute))
            else:
                dataType = c4d.DTYPE_STRING
                FinalValue = str(node.attrib.get(attribute))
    
        #Add UserData storing Atlas Information to the Sample Container
        Cbc = c4d.GetCustomDataTypeDefault(dataType) # Create Group
        Cbc[c4d.DESC_NAME] = attribute
        Cbc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
        Celement = cObject.AddUserData(Cbc)
        cObject[Celement] = FinalValue
     

    
def CreateElementContainer(node, keys, name, parent):
    
    FinalContainer = ""
    
    if name == "LevelRegion":
        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 2
        CContainer[c4d.NULLOBJECT_RADIUS] = 600
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 0
        FinalContainer = CContainer
        
    elif name.split("_")[0] == "Bases":
        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 4
        CContainer[c4d.NULLOBJECT_RADIUS] = 100
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
        CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = -2
        
        for node2 in node.iter("Base"): 
            CSubContainer = c4d.BaseObject(c4d.Onull)
            CSubContainer.SetName("Base" + node2.get("globalID"))
            CSubContainer[c4d.NULLOBJECT_DISPLAY] = 4
            CSubContainer[c4d.NULLOBJECT_RADIUS] = 250
            CSubContainer[c4d.NULLOBJECT_ORIENTATION] = 1
            CSubContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
                
            CSubContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node2.get("x"))
            CSubContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node2.get("y"))
    
            setUserDataFromNode(CSubContainer, node2)
            
            CSubContainer.InsertUnder(CContainer)
            
        FinalContainer = CContainer
    
    elif name.find("Map") != -1:
        print "Map Index: ", name.find("Map")
        CContainer = c4d.BaseObject(c4d.Oplane)
        CContainer[c4d.PRIM_AXIS] = 0
        print node
        CContainer[c4d.PRIM_PLANE_HEIGHT] = float(node.get("mapWidth"))#Plane is rotated cause this way is easier to match vetex index ordr
        CContainer[c4d.PRIM_PLANE_WIDTH] = float(node.get("mapHeight"))
        CContainer[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_X] = -3.14 * 0.5
        CContainer[c4d.PRIM_PLANE_SUBH] = int(node.get("mapWidth")) - 1
        CContainer[c4d.PRIM_PLANE_SUBW] = int(node.get("mapHeight")) - 1
        CContainer[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y] = float(node.get("scaleX"))
        CContainer[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Z] = float(node.get("scaleY"))
        CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.get("positionX"))
        CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.get("positionY"))
        
        # Avoid to put both maps in same Z place
        if name.split("_")[0] == "LumaMap":
            CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 200
        else:
            CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 100   
        CContainer.InsertUnder(parent)  
        
        #Make Object Editable
        FinalContainer = c4d.utils.SendModelingCommand(command = c4d.MCOMMAND_MAKEEDITABLE, list = [CContainer], mode = c4d.MODELINGCOMMANDMODE_ALL, bc = c4d.BaseContainer(), doc = doc)[0]
        FinalContainer.Message(c4d.MSG_UPDATE)
        
        #Align Maps to Top Left
        pcount = FinalContainer.GetPointCount()
        point = FinalContainer.GetAllPoints()
        offsetX = float(node.get("mapWidth")) * 0.5
        offsetY = -float(node.get("mapHeight"))* 0.5
        pDiff = c4d.Vector(offsetX, offsetY, offsetX)
        for i in xrange(pcount):
            FinalContainer.SetPoint(i, point[i] + pDiff)
        
        #Fixed Random List
        randList = [48,84,5,65,87,14,89,17,6,72,69,34,15,21,76,64,8,59,0,29,71,32,88,39,62,30,16,26,73,18,50,36,78,81,47,77,68,82,37,86,24,98,13,31,95,33,35,55,85,9,2,79,3,1,70,20,49,99,93,83,7,61,80,40,52,28,54,44,94,53,58,41,96,60,51,38,67,27,56,46,74,90,12,19,11,63,42,22,66,97,92,23,4,75,25,57,43,45,10,91]
        
        #Get all colorsIDs in order
        values = []
        for colorNode in node.iter("MapValue"):
            values =  values + colorNode.get("values").split(",")
        
        #Convert values to float
        valuesFloat = []
        
        if name.split("_")[0] == "LumaMap":
            for strV in values:
                valuesFloat.append(int(strV))
        else:
            for colorNode in node.iter("AreasIDs"):
                AreasIDs = colorNode.get("values")
            
            AreasIDsList = AreasIDs.split(",")
            
            print len(AreasIDsList)
            
            for strV in values:
                valuesFloat.append(float(strV) / 100)
                
            AreasIDListSorted = []
            while (len(AreasIDListSorted) - 1 < 100):
                AreasIDListSorted.append(99)
            
            
            for idx in xrange(len(AreasIDsList)):
                AreasIDListSorted[randList[int(AreasIDsList[idx])]] = AreasIDsList[idx]
                       
            print AreasIDListSorted
            
            Cbc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING)
            Cbc[c4d.DESC_NAME] = "AreasIDs"
            Cbc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
            Celement = FinalContainer.AddUserData(Cbc)
            CContainer[Celement] = str(AreasIDListSorted)
            
        #Add the tag Vertex Color to match from ColorIDs Values
        CTag = c4d.VertexColorTag(FinalContainer.GetPointCount())
        #CTag = FinalContainer.MakeTag(c4d.Tvertexcolor)
        CTag.__init__(FinalContainer.GetPointCount())
        FinalContainer.InsertTag(CTag)
        
        # Tag is create with no data for some reason. This force Vertex Color Tag to initialize it´s data
        #CTag.SetPerPointMode(False)
        #CTag.SetPerPointMode(True)
        
        # Obtains vertex colors data R/W addresses   
        DataR = CTag.GetDataAddressW()
        DataW = CTag.GetDataAddressR()
        
        print CTag.GetDataCount(), FinalContainer.GetPolygonCount(), len(valuesFloat)
        
        pointCount = CTag.GetDataCount()
        
        for idx in xrange(pointCount):
            if idx < len(valuesFloat):
                if name.split("_")[0] == "AreaMap":
                    valueDataFloat = float(randList[int(valuesFloat[idx] * 100)]) / 100
                else:
                    valueDataFloat = valuesFloat[idx]
                
                areaColor = c4d.Vector4d(valueDataFloat, valueDataFloat, valueDataFloat, valueDataFloat)
            
                poly = {"a":areaColor, "b":areaColor, "c":areaColor, "d": areaColor}
           
                c4d.VertexColorTag.SetPoint(DataW, None, None, idx, areaColor)
        
        MapMaterial = doc.SearchMaterial(name)
        if MapMaterial:
            MapMaterial.Remove()

        MapMaterial = c4d.BaseMaterial(c4d.Mmaterial)
        MapMaterial.SetName(name)
         
        MapMaterial[c4d.MATERIAL_USE_REFLECTION] = False
        MapMaterial[c4d.MATERIAL_USE_COLOR] = False
        MapMaterial[c4d.MATERIAL_USE_LUMINANCE] = True
        MapMaterial.Message( c4d.MSG_UPDATE )
        MapMaterial.Update( True, True )
        doc.InsertMaterial(MapMaterial)
        
        MTag = c4d.TextureTag()
        MTag.__init__()
        MTag[c4d.TEXTURETAG_MATERIAL] = MapMaterial
        FinalContainer.InsertTag(MTag)
        
        MShaderD = c4d.BaseList2D(c4d.Xvertexmap)
        MShaderD[c4d.SLA_DIRTY_VMAP_OBJECT] = CTag
        MapMaterial.InsertShader( MShaderD )
        MapMaterial[c4d.MATERIAL_LUMINANCE_SHADER]  = MShaderD
        
        MapMaterial.Message( c4d.MSG_UPDATE )
        MapMaterial.Update( True, True )
        
        CTag.SetPerPointMode(False)
        CTag[c4d.ID_VERTEXCOLOR_ALPHAMODE] = True
            
        c4d.EventAdd()
        
    elif name.split("_")[0] == "LevelBackground":
        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 3
        CContainer[c4d.NULLOBJECT_RADIUS] = 200
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
        FinalContainer = CContainer
        
    elif name.split("_")[0] == "LevelSite":
        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 12
        CContainer[c4d.NULLOBJECT_RADIUS] = 50
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
        FinalContainer = CContainer
          
        
    FinalContainer.SetName(name)
    
    setUserDataFromNode(FinalContainer, node)
     
    #Inser the Container to the doccument
    if parent != None:
        #print FinalContainer[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X], parent
        FinalContainer.InsertUnder(parent)  
        doc.AddUndo(c4d.UNDOTYPE_NEW, FinalContainer) 
    return FinalContainer

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
        
    #Start Undo. This allow C4D to start to store actions in order to allow undo
    doc.StartUndo()

    for node in tree.iter("LevelRegion"): 
        LevelRegionContainer = CreateElementContainer(node, node.attrib.keys(), node.tag, None)
        #Inser the Container to the doccument
        doc.InsertObject(LevelRegionContainer)  
        doc.AddUndo(c4d.UNDOTYPE_NEW, LevelRegionContainer) 

        print LevelRegionContainer
        
        for subNode in node: 
            SubNomeName = subNode.get('name')
            if not SubNomeName:
                SubNomeName = ""
            else:
                SubNomeName = "_" + SubNomeName
                
            CreateElementContainer(subNode, subNode.attrib.keys(), subNode.tag + SubNomeName, LevelRegionContainer)
            
        #for child in root:
            #print child.tag, child.attrib
        #Luma and Area Maps could use vetex color
    doc.EndUndo()
    c4d.EventAdd()

                
if __name__=='__main__':
    main()
