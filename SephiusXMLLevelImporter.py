import c4d
import os
import random
import copy
from random import randint
from c4d import gui
from c4d import storage
from c4d import utils
from xml.etree import ElementTree

XMLpath = ""
FileName = ""
folderPath = ""

objectTypesCounts = {}

global CurrentSite
global CurrentArea
global CurrentAreaLayer
global CurrentBackground
global CurrentGroup

def CreateLayer(layername, layercolor, layerParent):
    doc = c4d.documents.GetActiveDocument()
    root = doc.GetLayerObjectRoot() #Gets the layer manager
    
    if not layerParent:
        LayersList = root.GetChildren() #Get Layer list
    else:
        LayersList = layerParent.GetChildren() #Get Layer list
        
    # check if layer already exist
    layerexist = False
    for layers in LayersList:
        name = layers.GetName()
        if name == layername:
            layerexist = True
            NewLayer = layers
        
    #print "layerexist: ", layerexist
    if not layerexist:
        c4d.CallCommand(100004738) # New Layer
        c4d.EventAdd()
        
        #rename new layer
        LayersList = root.GetChildren() #redo getchildren, because a new one was added.
            
        for layers in LayersList:
            name = layers.GetName()
            if name == "Layer":
                NewLayer = layers
                layers.SetName(layername)
                #layers.SetBit(c4d.BIT_ACTIVE) # set layer active
                if layercolor:
                    layers[c4d.ID_LAYER_COLOR] = layercolor
                c4d.EventAdd()
                
    if layerParent:            
        # Insert the layer under the parent
        NewLayer.InsertUnder(layerParent)
        
    print LayersList
    return NewLayer # end createlayer

def GetLayer(layername):
    doc = c4d.documents.GetActiveDocument()
    root = doc.GetLayerObjectRoot() #Gets the layer manager
    LayersList = root.GetChildren()
    
    for layers in LayersList:
        name = layers.GetName()
        if (name == layername):
            return layers
        
    #gui.MessageDialog ("Layer does not exist: " + layername)
    return None #end GetLayer

def GetNullStyle(tag):
    return { "TYPE":3, "RADIUS":300, "ASPECTRATIO":1, "ORIENTATION":1 }

def GetElementColor(tag):
    if tag == "Spawner":
        return c4d.Vector(1, 0, 0)
    elif tag == "MessageCollider":
        return c4d.Vector(0, 0, 1)
    elif tag == "ReagentCollider":
        return c4d.Vector(0, .5, 1)
    elif tag == "Reward":
        return c4d.Vector(1, 1, 0)
    elif tag == " GameSprite":
        return c4d.Vector(1, 0, 0)
    elif tag == "Base" or tag == "Bases":
        return c4d.Vector(1, 1, 1)
    elif tag == "LevelCollision":
        return c4d.Vector(.3, 1, 1)
    else:
        return c4d.Vector(0, 1, 0)

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
    
    if parent:
        nextObject = parent.GetDown()
    else:
        nextObject = parent

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
        #print bc[c4d.DESC_NAME], UDName
        if bc[c4d.DESC_NAME] == UDName:
            return id
        
    return None

def setUserDataFromNode(cObject, node):
    for attribute in node.attrib.keys():
        userDataGroup = None
        GroupName = None
        NumOfCollums = 1
        
        if attribute == "x" or attribute == "y" or attribute == "offsetX" or attribute == "offsetY" or attribute == "skewX" or attribute == "skewY" or attribute == "scaleX" or attribute == "scaleY":
            GroupName = "Transform"
            NumOfCollums = 8
        elif attribute == "matrixA" or attribute == "matrixB" or attribute == "matrixC" or attribute == "matrixD" or attribute == "matrixTx" or attribute == "matrixTy":
            GroupName = "Matrix"
            NumOfCollums = 6
        elif attribute == "useAuroraEffect" or attribute == "useFlyingObjectsEffects" or attribute == "useFogEffect" or attribute == "useRainEffect" or attribute == "useSunEffec":
            GroupName = "Level Effects"
            NumOfCollums = 5
        elif attribute == "scaleOffsetX" or attribute == "scaleOffsetY":
            GroupName = "Offsets"
            NumOfCollums = 2
        elif attribute == "localId" or attribute == "globalId" or attribute == "site":
            GroupName = "IDs"
            NumOfCollums = 3
        elif attribute == "VertexData0" or attribute == "VertexData1" or attribute == "VertexData2" or attribute == "VertexData3":
            GroupName = "Vertex Data"
        elif attribute == "objectCount" or attribute == "spritesContainersCount" or attribute == "spriteCount" or attribute == "shapeCount" or attribute == "pointCount" or attribute == "containersCount":
            GroupName = "Statistics"
            NumOfCollums = 6
        else:
            GroupName = "Other Properties"
            
        if GroupName:
            userDataGroup = GetUserData(cObject, GroupName)
            
            if not userDataGroup:
                #print "Creating User Data Group"
                Cbc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP) # Create Group
                Cbc[c4d.DESC_NAME] = GroupName
                Cbc[c4d.DESC_COLUMNS] = NumOfCollums
                Celement = cObject.AddUserData(Cbc)
                cObject[Celement] = GroupName
                userDataGroup = Celement

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
        #print "Has Group ? ", userDataGroup
        if userDataGroup:
            Cbc[c4d.DESC_PARENTGROUP] = userDataGroup
        Celement = cObject.AddUserData(Cbc)
        cObject[Celement] = FinalValue
     

    
def CreateElementContainer(node, keys, name, parent):
    #print "------------------------------------------------------"
    #print "Processing: ", node, keys, name, parent
    #print "------------------------------------------------------"
    
    FinalContainer = ""
    
    if node.tag == "LevelRegion":
        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 2
        CContainer[c4d.NULLOBJECT_RADIUS] = 600
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 0
        FinalContainer = CContainer
        
    elif node.tag == "Bases":
        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 4
        CContainer[c4d.NULLOBJECT_RADIUS] = 100
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
        CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = -2
        CContainer[c4d.ID_BASEOBJECT_USECOLOR] = 2
        CContainer[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
        CContainer[c4d.NULLOBJECT_ICONCOL] = True

        for node2 in node.iter("Base"): 
            CSubContainer = c4d.BaseObject(c4d.Onull)
            CSubContainer.SetName("Base." + node2.get("globalID"))
            CSubContainer[c4d.NULLOBJECT_DISPLAY] = 4
            CSubContainer[c4d.NULLOBJECT_RADIUS] = 250
            CSubContainer[c4d.NULLOBJECT_ORIENTATION] = 1
            CSubContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
            CSubContainer[c4d.ID_BASEOBJECT_USECOLOR] = 2
            CSubContainer[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
            CSubContainer[c4d.NULLOBJECT_ICONCOL] = True

            CSubContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node2.get("x"))
            CSubContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node2.get("y"))
    
            setUserDataFromNode(CSubContainer, node2)
            
            CSubContainer.InsertUnder(CContainer)
            
        FinalContainer = CContainer
    
    elif node.tag.find("Map") != -1:
        CContainer = c4d.BaseObject(c4d.Oplane)
        CContainer[c4d.PRIM_AXIS] = 0

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
            
            #print len(AreasIDsList)
            
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
        
        #print CTag.GetDataCount(), FinalContainer.GetPolygonCount(), len(valuesFloat)
        
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
        MapMaterial[c4d.MATERIAL_USE_ALPHA] = True
        
        if name.split("_")[0] == "AreaMap":
            MapMaterial[c4d.MATERIAL_LUMINANCE_COLOR] = c4d.Vector(0, 0.12, 1)
        else:
            MapMaterial[c4d.MATERIAL_LUMINANCE_COLOR] = c4d.Vector(0, 0.9, 1)
            
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
        MapMaterial[c4d.MATERIAL_LUMINANCE_TEXTUREMIXING] = 2
        
        MShaderD = c4d.BaseList2D(c4d.Xcolor)
        MShaderD[c4d.COLORSHADER_COLOR] = c4d.Vector(0.33, 0.33, 0.33)
        MapMaterial.InsertShader( MShaderD )
        MapMaterial[c4d.MATERIAL_ALPHA_SHADER]  = MShaderD

        MapMaterial.Message( c4d.MSG_UPDATE )
        MapMaterial.Update( True, True )
        
        CTag.SetPerPointMode(False)
        CTag[c4d.ID_VERTEXCOLOR_ALPHAMODE] = True
            
        c4d.EventAdd()
        
    elif node.tag == "LevelSite":
        global CurrentSite 
        CurrentSite = node.get('name')
        
        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 12
        CContainer[c4d.NULLOBJECT_RADIUS] = 50
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
        
        for node2 in node.iter("LevelArea"):
            CreateElementContainer(node2, node2.attrib.keys(), node2.tag + "." + node2.get("globalId"), CContainer)
             
        FinalContainer = CContainer
    
    elif node.tag == "LevelBackground":
        global CurrentBackground 
        CurrentBackground = node.get('name')
        
        global CurrentAreaLayer 
        CurrentAreaLayer = CreateLayer("BGs" + "." + name, None, CreateLayer("BGs", None, None))

        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 3
        CContainer[c4d.NULLOBJECT_RADIUS] = 200
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 1

        #print node.tag
        BBGName = node.tag + "s"
        BBGGroupContainer = getChild(parent, BBGName)

        if not BBGGroupContainer:
            BBGGroupContainer = c4d.BaseObject(c4d.Onull)
        
            BBGGroupContainer.SetName(BBGName)
            BBGGroupContainer[c4d.NULLOBJECT_DISPLAY] = 3
            BBGGroupContainer[c4d.NULLOBJECT_RADIUS] = 100
            BBGGroupContainer[c4d.NULLOBJECT_ORIENTATION] = 1
            BBGGroupContainer.InsertUnder(parent)
        
        CContainer.InsertUnder(BBGGroupContainer)

        for subNode in node:
            SubNomeName = subNode.get('name')
            if not SubNomeName:
                SubNomeName = ""
            else:
                SubNomeName = "." + SubNomeName
                
            CContainer.SetName(name)
            #print ">>>>>>>>>>>>>>>>>>>>>>>>", name
            CreateElementContainer(subNode, subNode.attrib.keys(), subNode.tag, CContainer)

        FinalContainer = CContainer

    elif node.tag == "LevelArea":
        global CurrentArea
        CurrentArea = name
        
        global CurrentAreaLayer 
        CurrentAreaLayer = CreateLayer(CurrentSite + "." + name, None, CreateLayer(CurrentSite, None, CreateLayer("Sites", None, None)))
        
        #Get Area Bound from string coming as: "(x=A, y=B, w=C, h=D)"
        boundsStrX = float(node.get("bounds")[1:-1].split(",")[0].split("=")[1])
        boundsStrY = float(node.get("bounds")[1:-1].split(",")[1].split("=")[1])
        boundsStrW = float(node.get("bounds")[1:-1].split(",")[2].split("=")[1])
        boundsStrH = float(node.get("bounds")[1:-1].split(",")[3].split("=")[1])
        boundRatio =  boundsStrW / boundsStrH
        
        #print "Bounds: ", boundsStrX, boundsStrX, boundsStrW, boundsStrH 
        
        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 3
        CContainer[c4d.NULLOBJECT_RADIUS] = 300
        CContainer[c4d.NULLOBJECT_ASPECTRATIO] = 1
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
        CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.get("x"))
        CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.get("y"))
        CContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer
    
        CBounds = c4d.BaseObject(c4d.Osplinerectangle)
        CBounds.SetName("Bounds." + name)
        CBounds[c4d.PRIM_RECTANGLE_WIDTH] = boundsStrW
        CBounds[c4d.PRIM_RECTANGLE_HEIGHT] = boundsStrH
        CBounds[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = boundsStrX + (boundsStrW * .5) - float(node.get("x"))
        CBounds[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -boundsStrY - (boundsStrH * .5) + float(node.get("y"))
        CBounds[c4d.ID_LAYER_LINK] = CurrentAreaLayer
        
        CBounds.InsertUnder(CContainer)  
        
        for subNode in node:
            SubNomeName = subNode.get('name')
            if not SubNomeName:
                SubNomeName = ""
            else:
                SubNomeName = "." + SubNomeName
                
            CContainer.SetName(name)
            CreateElementContainer(subNode, subNode.attrib.keys(), subNode.tag + SubNomeName, CContainer)
        
        FinalContainer = CContainer
        
    elif parent.GetName().split(".")[0] == "LevelArea" or parent.GetName().split(".")[0] == "LevelBackground":#Game Objects
        CContainer = c4d.BaseObject(c4d.Onull)
        Styke = GetNullStyle(node.tag)["RADIUS"]
        #print "[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[", Styke

        CContainer[c4d.NULLOBJECT_DISPLAY] = 3
        CContainer[c4d.NULLOBJECT_RADIUS] = 50
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
        CContainer[c4d.ID_BASEOBJECT_USECOLOR] = 2
        CContainer[c4d.NULLOBJECT_ICONCOL] = True
        CContainer[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
        CContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer
        
        GObjectType = node.tag
        #print "<<<<<<<<<<<<<<<<<<<<<<<<<<<<",  parent.GetName()
        if GObjectType in objectTypesCounts.keys():
            objectTypesCounts[GObjectType] = objectTypesCounts[GObjectType] + 1
        else:
             objectTypesCounts[GObjectType] = 1
             
        #print GObjectType, objectTypesCounts[GObjectType]
        
        GObjectName = GObjectType + "." + str(objectTypesCounts[GObjectType])
        CContainer.SetName(GObjectName)

        for viewNode in node.iter("View"):
            for attiName in viewNode.attrib.keys():
                node.set(attiName, viewNode.get(attiName))
                    
        #Some objects was stored with it´s properties inside a sub element. We need to joint thoses properties with the object node itself
        for paramsNode in node.iter("CustomParams"):
            for attiName in paramsNode.attrib.keys():
                node.set(attiName, paramsNode.get(attiName))
                
        if node.tag == "Spawner" or node.tag == "MessageCollider" or node.tag == "ReagentCollider":
            boundsStrW = float(node.get("width"))
            boundsStrH = float(node.get("height"))
            
            #print "Bounds: ", boundsStrW, boundsStrW
            
            CBounds = c4d.BaseObject(c4d.Osplinerectangle)
            CBounds.SetName("Bounds." + GObjectName)
            CBounds[c4d.PRIM_RECTANGLE_WIDTH] = boundsStrW
            CBounds[c4d.PRIM_RECTANGLE_HEIGHT] = boundsStrH
            CBounds[c4d.ID_BASEOBJECT_USECOLOR] = 2
            CBounds[c4d.NULLOBJECT_ICONCOL] = True
            CBounds[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
            CBounds[c4d.ID_LAYER_LINK] = CurrentAreaLayer
            #CBounds[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = boundsStrX + (boundsStrW * .5) - float(node.get("x"))
            #CBounds[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -boundsStrY - (boundsStrH * .5) + float(node.get("y"))
            
            CBounds.InsertUnder(CContainer)  

        if node.get("group"):
            CGName = "Group" + "." + node.get("group")
            global CurrentGroup 
            CurrentGroup = CGName
            CGroupContainer = getChild(parent, CGName)
       
            if not CGroupContainer:
                CGroupContainer = c4d.BaseObject(c4d.Onull)
                
                CGroupContainer.SetName(CGName)
                CGroupContainer[c4d.NULLOBJECT_DISPLAY] = 3
                CGroupContainer[c4d.NULLOBJECT_RADIUS] = 100
                CGroupContainer[c4d.NULLOBJECT_ORIENTATION] = 1
                CGroupContainer.InsertUnder(parent)
                CGroupContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer
                
            if node.tag != "GameSprite":   
                #print node.tag
                OGName = node.tag + "s"
                OGroupContainer = getChild(CGroupContainer, OGName)
   
                if not OGroupContainer:
                    OGroupContainer = c4d.BaseObject(c4d.Onull)
            
                    OGroupContainer.SetName(OGName)
                    OGroupContainer[c4d.NULLOBJECT_DISPLAY] = 3
                    OGroupContainer[c4d.NULLOBJECT_RADIUS] = 100
                    OGroupContainer[c4d.NULLOBJECT_ORIENTATION] = 1
                    OGroupContainer[c4d.ID_BASEOBJECT_USECOLOR] = 2
                    OGroupContainer[c4d.NULLOBJECT_ICONCOL] = True
                    OGroupContainer[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
                    OGroupContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer
                    OGroupContainer.InsertUnder(CGroupContainer)
            
                CContainer.InsertUnder(OGroupContainer)
            else:
                CContainer.InsertUnder(CGroupContainer)
                
        for viewNode in node.iter("View"):
            for containerNode in viewNode:
                CreateElementContainer(containerNode, containerNode.attrib.keys(), containerNode.get('name'), CContainer)
        
        if(node.tag != "LevelCollision" and node.tag != "Spikes"):
            CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.get("x"))
            CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.get("y"))
            
        elif (node.tag == "LevelCollision" or node.tag != "Spikes"):
            CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.get("x")) - parent[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X]
            CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.get("y")) - parent[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y]
            
        FinalContainer = CContainer
        
    elif parent.GetName().split(".")[0] == "GameSprite":#Sprite Containers
        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 3
        CContainer[c4d.NULLOBJECT_RADIUS] = 200
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
        CContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer
        
        for ImageNode in node.iter("Image"):
            CreateElementContainer(ImageNode, ImageNode.attrib.keys(), ImageNode.get('texture'), CContainer)
        
        FinalContainer = CContainer
    
    elif node.tag == "Image":#Sprite Containers
        CContainer = c4d.BaseObject(c4d.Opolygon)
        #CContainer[c4d.NULLOBJECT_DISPLAY] = 1
        #CContainer[c4d.NULLOBJECT_RADIUS] = 20
        #CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
        
        SetPolygon(node, CContainer, None, None, None)
        
        #print node.get("atlas") + " Material"
        AtlasMaterial = doc.SearchMaterial(node.get("atlas") + " Material")
        
        CTag = CContainer.MakeTag(c4d.Ttexture)
        CTag[c4d.TEXTURETAG_PROJECTION] = 6
        CTag.SetMaterial(AtlasMaterial)
        CContainer.InsertTag(CTag)
        
        #bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL)
        #bc[c4d.DESC_NAME] = "IsSpriteSheetSample"
        #bc[c4d.DESC_EDITABLE] = False
        #element = Csample.AddUserData(bc)
        #Csample[element] = True

        #CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.get("x"))
        #CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.get("y"))
        #CContainer[c4d.PRIM_PLANE_WIDTH] = 20
        #CContainer[c4d.PRIM_PLANE_HEIGHT] = 20
        #CContainer[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X] = float(node.get("scaleX"))
        #CContainer[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y] = float(node.get("scaleY"))
        #CContainer[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Z] = 1
        #CContainer[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = float(node.get("rotation"))
        #CContainer[c4d.PRIM_AXIS] = 5
        #CContainer[c4d.PRIM_PLANE_SUBW] = 1
        #CContainer[c4d.PRIM_PLANE_SUBH] = 1 
        
        CContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer
        FinalContainer = CContainer

    else:
        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 3
        CContainer[c4d.NULLOBJECT_RADIUS] = 200
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
        CContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer
        FinalContainer = CContainer
        
    #if parent != None:
       #print parent  
         
    setUserDataFromNode(FinalContainer, node)
    
    if parent != None:
        if parent.GetName().split(".")[0] != "LevelArea" and parent.GetName().split(".")[0] != "LevelBackground":
            FinalContainer.SetName(name)
        #Inser the Container to the doccument
        if not FinalContainer.GetUp():
            #print FinalContainer[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X], parent
            FinalContainer.InsertUnder(parent)  
            doc.AddUndo(c4d.UNDOTYPE_NEW, FinalContainer) 
    return FinalContainer

def SetPolygon(SampleNode, CObject, UVWTag, VertexColorTag, Polygon):
    AtlasName = SampleNode.get("atlas")
    TextureName = SampleNode.get("texture")
    
    HasDistortion = False
    if float(SampleNode.get("skewX")) != 0 or float(SampleNode.get("skewY")) != 0:
        HasDistortion = True
    
    SampleContainer = SamplesContainer = doc.SearchObject(AtlasName + " Samples")
    SampleReference = getChild(SampleContainer, TextureName + "_Sample")
    
    data = {}
    PSs = []
    PCSs = []
    #print "SampleContainer", AtlasName + " Samples", SampleContainer, "SampleReference", TextureName + "_Sample", SampleReference
    Offset = SampleReference[GetUserData(SampleReference, "Offset")]
    
    if not Polygon:
        Polygon = c4d.CPolygon(0, 1, 2, 3)
        Polygon.__init__(0, 1, 2, 3)
        CObject.ResizeObject(4, 1)
        CObject.SetPolygon(0, Polygon)
    
    if not UVWTag:
        UVWTag = CObject.MakeVariableTag(c4d.Tuvw, 1)
        UVWTag[c4d.ID_BASELIST_NAME] = "SampleUVW"
        CObject.InsertTag(UVWTag)
    
    if not VertexColorTag:
        VertexColorTag = c4d.VertexColorTag(4)
        VertexColorTag.__init__(4)
        CObject.InsertTag(VertexColorTag)
        VertexColorTag.SetPerPointMode(False)
        
    VCdata = VertexColorTag.GetDataAddressW()
    
    for i in xrange(4):
        VertexData = {}
        
        CurrentVertexDataList = SampleNode.get("VertexData" + str(i)).split(",")
        
        #print CurrentVertexDataList
        
        for CPair in CurrentVertexDataList:
            VertexData[CPair.split(":")[0]] = float(CPair.split(":")[1])
        
        data["VertexPosition" + str(i)] = SampleReference[GetUserData(SampleReference, "Vertex " + str(i) + " Position")]
        
        #print "HasDistortion: ", HasDistortion SampleReference[GetUserData(SampleReference, "Vertex " + str(i) + " Position")]
        #print "data: ", data
        #print "VertexPosition" + str(i), data["VertexPosition" + str(i)]
        
        print SampleReference
        textureHight = SampleReference[GetUserData(SampleReference, "Texture Height")]
        
        if HasDistortion:
            if i == 0 or i == 2:
                data["VertexDistortion" + str(i)] = c4d.Vector(0, -float(SampleNode.get("skewY")) * textureHight, 0)
            else:
                data["VertexDistortion" + str(i)] = c4d.Vector(0, float(SampleNode.get("skewY")) * textureHight, 0)
            #print VertexData["x"], VertexData["y"]
        else:
            data["VertexDistortion" + str(i)] = c4d.Vector(0, 0, 0)
            
        #data["VertexDistortion" + str(i)] = c4d.Vector(0, 0, 0)
        data["VertexAlpha" + str(i)] = VertexData["alpha"]
        data["VertexColor" + str(i)] = c4d.Vector(VertexData["colorR"], VertexData["colorG"], VertexData["colorB"])
        
        PSs.append(data["VertexPosition" + str(i)] + data["VertexDistortion" + str(i)] + Offset)
        CObject.SetPoint(i, PSs[i])
        
        data["Vertex" + str(i) + "UVW"] = SampleReference[GetUserData(SampleReference, "Vertex " + str(i) + " UVW")]

        PCSs.append(data["Vertex" + str(i) + "UVW"])
        
        VertexColorTag.SetColor(VCdata, None, None, i, data["VertexColor" + str(i)])
        VertexColorTag.SetAlpha(VCdata, None, None, i, float(data["VertexAlpha" + str(i)]))
    
    UVWTag.SetSlow(0, PCSs[0], PCSs[1], PCSs[2], PCSs[3])
    
    global ZOffset
    ZOffset = ZOffset - 0.2
    
    CObject[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X] = float(SampleNode.get("x"))
    CObject[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = -float(SampleNode.get("y"))
    CObject[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] = ZOffset
    CObject[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = float(SampleNode.get("rotation"))
    CObject[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X] = float(SampleNode.get("scaleX"))
    CObject[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y] = float(SampleNode.get("scaleY"))
    
    CObject[c4d.ID_BASEOBJECT_REL_POSITION] = CObject[c4d.ID_BASEOBJECT_REL_POSITION] - Offset 
    
    #Update object. Need to update bound box for selection and etc.
    CObject.Message (c4d.MSG_UPDATE)

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
        objectTypesCounts = {}
        LevelRegionContainer = CreateElementContainer(node, node.attrib.keys(), node.tag, None)
        LevelRegionContainer.SetName(node.get('name'))
        #Inser the Container to the doccument
        doc.InsertObject(LevelRegionContainer)  
        doc.AddUndo(c4d.UNDOTYPE_NEW, LevelRegionContainer) 

        print LevelRegionContainer
        
        for subNode in node: 
            SubNomeName = subNode.get('name')
            if not SubNomeName:
                SubNomeName = ""
            else:
                SubNomeName = "." + SubNomeName
                
            CreateElementContainer(subNode, subNode.attrib.keys(), subNode.tag + SubNomeName, LevelRegionContainer)
            
        #for child in root:
            #print child.tag, child.attrib
        #Luma and Area Maps could use vetex color
    doc.EndUndo()
    c4d.EventAdd()

                
if __name__=='__main__':
    global ZOffset
    ZOffset = 0
    main()
