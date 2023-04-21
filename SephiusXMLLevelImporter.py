import c4d
import os
import random
import copy
import math
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

#return the position in Z depending on the group object is related to
def getLocalSpacing(groupID):
    switcher = {
        0: 0,
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        10: 0,
        11: -0.05,
        12: 0,
        13: 0,
    }
    #print("group: ", int(groupID), " ",  switcher.get(int(groupID), 0.0))
    return switcher.get(int(groupID), 0.0)

#return the position in Z depending on the group object is related to
def getGroupZPos(groupID):
    switcher = {
        0: 200000,
        1: 95000,
        2: 95000,
        3: 37000,
        4: 25500,
        5: 7600,
        6: 192,
        7: 99,
        8: 48,
        9: 0,
        10: 0,
        11: -180,
        12: -5,
        13: -10,
    }
    #print("group: ", int(groupID), " ",  switcher.get(int(groupID), 0.0))
    return switcher.get(int(groupID), 0.0)

#return the position in Z depending on the group object is related to
def getScaleByGroup(groupID):
    switcher = {
        0: 0.01,
        1: 0.02,
        2: 0.02,
        3: 0.05,
        4: 0.07,
        5: 0.2,
        6: 1,
        7: 1,
        8: 1,
        9: 1,
        10: 1,
        11: 1,
        12: 1,
        13: 1,
    }
    return 1/switcher.get(float(groupID), 1.0)

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

    #print("layerexist: ", layerexist)
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

    #print(LayersList)
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
    elif tag == "LightSprite":
        return c4d.Vector(1, 1, 0.3)
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
    elif tag == "BreakableObject":
        return c4d.Vector(1, .5, 0)
    elif tag == "Pool":
        return c4d.Vector(0, 1, 1)
    elif tag == "Pyra":
        return c4d.Vector(1, 0, .5)
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
        if nextObject:
            PChildren.append(nextObject)

    return PChildren

#Return True if object has a user data name and value is equal to desired
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

#Return True if object has a user data name and value is equal to desired
def GetUserData(CObject, UDName):
    #print(CObject, UDName)
    for id, bc in CObject.GetUserDataContainer():
        #print(bc[c4d.DESC_NAME], UDName)
        if bc[c4d.DESC_NAME] == UDName:
            return id

    return None

def setUserDataFromNode(cObject, node, isRef):
    ObjectExportGroup = GetUserData(cObject, "OBJECT EXPORT INFO")

    if not ObjectExportGroup:
        Cbc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        Cbc[c4d.DESC_NAME] = "OBJECT EXPORT INFO"
        Cbc[c4d.DESC_SHORT_NAME] = "OBJECT EXPORT INFO"
        Cbc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
        Cbc[c4d.DESC_DEFAULT] = True
        Cbc[c4d.DESC_TITLEBAR] = True
        Cbc[c4d.DESC_COLUMNS] = 1
        ObjectExportGroup = cObject.AddUserData(Cbc)
        cObject[ObjectExportGroup] = "OBJECT EXPORT INFO"

    for attribute in node.attrib.keys():
        if attribute == "name" or attribute == "alpha":
            continue

        userDataGroup = None
        GroupName = None
        NumOfCollums = 1

        if attribute == "x" or attribute == "y" or attribute == "offsetX" or attribute == "offsetY" or attribute == "skewX" or attribute == "skewY" or attribute == "scaleX" or attribute == "scaleY" or attribute == "rotation":
            GroupName = "Transform"
            NumOfCollums = 2
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
        elif attribute == "parentAreaID" or attribute == "group":
            GroupName = "Level Relation"
            NumOfCollums = 3
        elif attribute == "VertexData0" or attribute == "VertexData1" or attribute == "VertexData2" or attribute == "VertexData3":
            GroupName = "Vertex Data"
        elif attribute == "objectCount" or attribute == "spritesContainersCount" or attribute == "spriteCount" or attribute == "shapeCount" or attribute == "pointCount" or attribute == "containersCount":
            GroupName = "Statistics"
            NumOfCollums = 6
        else:
            GroupName = "GAME PROPERTIES"

        if (attribute == "globalID" or attribute == "scaleOffsetX" or attribute == "scaleOffsetY" or attribute == "matrixA" or attribute == "matrixB" or attribute == "matrixC" or attribute == "matrixD" or attribute == "matrixTx" or attribute == "matrixTy" or attribute == "x" or attribute == "y" or attribute == "offsetX" or attribute == "offsetY" or attribute == "skewX" or attribute == "skewY" or attribute == "scaleX" or attribute == "scaleY" or attribute == "rotation" or attribute == "parentAreaID" or attribute == "group"):
            if(isRef):
                continue

        if GroupName:
            #print("group", cObject, GroupName)
            userDataGroup = GetUserData(cObject, GroupName)

            if not userDataGroup:
                #print("Creating User Data Group")
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
                FinalValue = False
            elif node.attrib.get(attribute) == "true":
                dataType = c4d.DTYPE_BOOL
                FinalValue = True
            else:
                dataType = c4d.DTYPE_STRING
                FinalValue = str(node.attrib.get(attribute))

        #Add UserData storing
        Cbc = c4d.GetCustomDataTypeDefault(dataType) # Create Group
        Cbc[c4d.DESC_NAME] = attribute
        Cbc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
        #print("Has Group ? ", userDataGroup)
        if userDataGroup:
            Cbc[c4d.DESC_PARENTGROUP] = userDataGroup
        Celement = cObject.AddUserData(Cbc)
        cObject[Celement] = FinalValue

    GamePropertiesGroup = userDataGroup = GetUserData(cObject, "GAME PROPERTIES")

    if node.get("className") is None:
        Cbc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING) # Create Group
        Cbc[c4d.DESC_NAME] = "className"
        Cbc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
        Cbc[c4d.DESC_PARENTGROUP] = GamePropertiesGroup
        Celement = cObject.AddUserData(Cbc)
        cObject[Celement] = node.tag

    if node.tag == "Image" or node.tag == "LightSprite" or node.tag == "EffectArt":
        Cbc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL) # Create Group
        Cbc[c4d.DESC_NAME] = "IsSpriteSheetSample"
        Cbc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
        Cbc[c4d.DESC_PARENTGROUP] = ObjectExportGroup
        Celement = cObject.AddUserData(Cbc)
        cObject[Celement] = True

        SampleContainer = SamplesContainer = doc.SearchObject(str(node.get("atlas")) + " Samples")
        SampleReference = getChild(SampleContainer, str(node.get("texture")) + "_Sample")

        Cbc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BASELISTLINK) # Create Group
        Cbc[c4d.DESC_NAME] = "Sample Reference"
        Cbc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
        Cbc[c4d.DESC_PARENTGROUP] = ObjectExportGroup
        Celement = cObject.AddUserData(Cbc)
        cObject[Celement] = SampleReference

        #if node.tag == "LightSprite":
            #CreateBounds(cObject, node)
    elif node.tag not in ["GameSprite", "Container", "BoxCollisions", "RawShape", "RawCollision", "BoxShape", "LevelCollision", "LevelArea", "LevelSite", "LevelBackground", "Bases", "Base", "LumaMap", "AreaMap", "LANDS OF OBLIVION", "LevelRegion"]:
        Cbc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL) # Create Group
        Cbc[c4d.DESC_NAME] = "IsGameObject"
        Cbc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
        Cbc[c4d.DESC_PARENTGROUP] = ObjectExportGroup
        Celement = cObject.AddUserData(Cbc)
        cObject[Celement] = True

def CreateElementLevelRegion(node, keys, name, parent):
    CContainer = c4d.BaseObject(c4d.Onull)
    CContainer[c4d.NULLOBJECT_DISPLAY] = 2
    CContainer[c4d.NULLOBJECT_RADIUS] = 600
    CContainer[c4d.NULLOBJECT_ORIENTATION] = 0
    FinalContainer = CContainer

    setUserDataFromNode(FinalContainer, node, False)

    return FinalContainer

def CreateElementContainer(node, keys, name, parent):
    #print("------------------------------------------------------")
    #print("Processing: ", node, keys, name, parent)
    #print("------------------------------------------------------")

    FinalContainer = ""

    if node.tag == "LevelRegion":
        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 2
        CContainer[c4d.NULLOBJECT_RADIUS] = 600
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 0

        AutoSetUserData = True
        FinalContainer = CContainer

        # Add a User Data parameter to the tag for the step value
        step_param = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
        step_param.SetString(c4d.DESC_NAME, "Global Sample Spacing")
        step_param.SetFloat(c4d.DESC_MIN, -100.0)
        step_param.SetFloat(c4d.DESC_MAX, 100.0)
        step_param.SetFloat(c4d.DESC_STEP, 0.1)
        step_param.SetFloat(c4d.DESC_DEFAULT, 0.1)
        CContainer.AddUserData(step_param)

        CContainer[c4d.ID_USERDATA,1] = 0.1

        # Add a User Data parameter to the tag for the step value
        step_param = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL)
        step_param.SetString(c4d.DESC_NAME, "Enable Spacing")
        step_param.SetFloat(c4d.DESC_DEFAULT, True)
        CContainer.AddUserData(step_param)

        CContainer[c4d.ID_USERDATA,2] = True

    elif node.tag == "Bases":
        CContainer = c4d.BaseObject(c4d.Onull)
        CContainer[c4d.NULLOBJECT_DISPLAY] = 4
        CContainer[c4d.NULLOBJECT_RADIUS] = 100
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
        CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = -2
        CContainer[c4d.ID_BASEOBJECT_USECOLOR] = 2
        CContainer[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
        CContainer[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1

        for node2 in node.iter("Base"):
            CSubContainer = c4d.BaseObject(c4d.Onull)
            CSubContainer.SetName("Base." + node2.get("globalID"))
            CSubContainer[c4d.NULLOBJECT_DISPLAY] = 4
            CSubContainer[c4d.NULLOBJECT_RADIUS] = 250
            CSubContainer[c4d.NULLOBJECT_ORIENTATION] = 1
            CSubContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
            CSubContainer[c4d.ID_BASEOBJECT_USECOLOR] = 2
            CSubContainer[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
            CSubContainer[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1

            CSubContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node2.get("x"))
            CSubContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node2.get("y"))

            setUserDataFromNode(CSubContainer, node2, False)

            CSubContainer.InsertUnder(CContainer)

        AutoSetUserData = True
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

        AutoSetUserData = True
        #Make Object Editable
        FinalContainer = c4d.utils.SendModelingCommand(command = c4d.MCOMMAND_MAKEEDITABLE, list = [CContainer], mode = c4d.MODELINGCOMMANDMODE_ALL, bc = c4d.BaseContainer(), doc = doc)[0]
        FinalContainer.Message(c4d.MSG_UPDATE)

        #Align Maps to Top Left
        pcount = FinalContainer.GetPointCount()
        point = FinalContainer.GetAllPoints()
        offsetX = float(node.get("mapWidth")) * 0.5
        offsetY = -float(node.get("mapHeight"))* 0.5
        pDiff = c4d.Vector(offsetX, offsetY, offsetX)
        for i in range(pcount):
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

            for strV in values:
                valuesFloat.append(float(strV) / 100)

            AreasIDListSorted = []
            while (len(AreasIDListSorted) - 1 < 100):
                AreasIDListSorted.append(99)

            #Swap colors to help visualization (more contras between adjacent areas)
            for idx in range(len(AreasIDsList)):
                AreasIDListSorted[randList[int(AreasIDsList[idx])]] = AreasIDsList[idx]

            print(AreasIDListSorted)

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

        # Obtains vertex colors data R/W addresses
        DataR = CTag.GetDataAddressW()
        DataW = CTag.GetDataAddressR()

        pointCount = CTag.GetDataCount()

        for idx in range(pointCount):
            if idx < len(valuesFloat):
                #if name.split("_")[0] == "AreaMap":
                    #valueDataFloat = float(randList[int(valuesFloat[idx] * 100)]) / 100
                #else:
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

        #CTag.SetPerPointMode(False)
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

        AutoSetUserData = True
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

        #print(node.tag)
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
            #print(">>>>>>>>>>>>>>>>>>>>>>>>", name)
            CreateElementContainer(subNode, subNode.attrib.keys(), subNode.tag, CContainer)

        AutoSetUserData = True
        FinalContainer = CContainer

    elif node.tag == "LevelArea":
        CurrentArea = name
        CurrentAreaLayer = CreateLayer(CurrentSite + "." + name, None, CreateLayer(CurrentSite, None, CreateLayer("Sites", None, None)))

        #Get Area Bound from string coming as: "(x=A, y=B, w=C, h=D)"
        boundsStrX = float(node.get("bounds")[1:-1].split(",")[0].split("=")[1])
        boundsStrY = float(node.get("bounds")[1:-1].split(",")[1].split("=")[1])
        boundsStrW = float(node.get("bounds")[1:-1].split(",")[2].split("=")[1])
        boundsStrH = float(node.get("bounds")[1:-1].split(",")[3].split("=")[1])
        boundRatio =  boundsStrW / boundsStrH

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

        AutoSetUserData = True
        FinalContainer = CContainer

    elif parent.GetName().split(".")[0] == "LevelArea" or parent.GetName().split(".")[0] == "LevelBackground":#Game Objects
        #Some objects was stored with it´s properties inside a sub element. We need to joint thoses properties with the object node itself
        for paramsNode in node.iter("CustomParams"):
            for attiName in paramsNode.attrib.keys():
                node.set(attiName, paramsNode.get(attiName))

        if node.tag == "Spawner" or node.tag == "MessageCollider" or node.tag == "ReagentCollider" or "Barrier" in node.tag or "BreakableObject" in node.tag or "Reward" in node.tag or "Pyra" in node.tag:
            useBound = True;
        else:
            useBound = False;

        PropertyName = node.get('properties')
        Type = node.get('type')
        nature = node.get('nature')
        rewardType = node.get('rewardType')

        if(PropertyName):
            GObjectType = node.tag + "." + PropertyName
        elif(Type):
            GObjectType = node.tag + "." + Type
        elif(nature):
            GObjectType = node.tag + "." + nature
        elif(rewardType):
            GObjectType = node.tag + "." + rewardType
        else:
            GObjectType = node.tag

        if GObjectType in objectTypesCounts.keys():
            objectTypesCounts[GObjectType] = objectTypesCounts[GObjectType] + 1
        else:
             objectTypesCounts[GObjectType] = 1

        GObjectName = GObjectType + "." + str(objectTypesCounts[GObjectType])

        if node.tag == "GameSprite":
            CContainer = c4d.BaseObject(c4d.Oconnector)
            CContainer[c4d.CONNECTOBJECT_WELD] = False
            CContainer[c4d.ID_BASEOBJECT_USECOLOR] = 0
            CContainer[c4d.ID_BASEOBJECT_GENERATOR_FLAG] = False

            # Set the Python code for the tag DONT REMOVE THE CODE BELLOW!!
            pythonCode = """

import c4d

global intCount
intCount = 0

def main():
    # Get the owner object
    owner = op.GetObject()

    global intCount
    intCount = 0

    recursive_iteration(owner)

    c4d.EventAdd()

def recursive_iteration(obj):
    # Set the step value for distributing the children using local spacing and user data that exist in the Level Region container (root container)

    organizeSamples = op[c4d.ID_USERDATA,2][c4d.ID_USERDATA,2]

    if organizeSamples == False:
        return

    step = op[c4d.ID_USERDATA,1] + op[c4d.ID_USERDATA,2][c4d.ID_USERDATA,1]
    global intCount
    # Update the current object's Z position
    obj[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] = intCount * step
    #print(obj.GetName(), intCount)

    # Iterate through the object's children and call the recursive function
    child = obj.GetDown()
    while child:

        intCount += 1
        recursive_iteration(child)
        child = child.GetNext()

if __name__ == '__main__':
    main()

        """
            # Add the tag to the selected object
            addPythonTagWithCode(CContainer, node, pythonCode)

            for viewNode in node.iter("View"):
                for attiName in viewNode.attrib.keys():
                    node.set(attiName, viewNode.get(attiName))
                for containerNode in viewNode:
                    CreateElementContainer(containerNode, containerNode.attrib.keys(), containerNode.get('name'), CContainer)

        elif (node.tag == "LevelCollision") or node.tag == "Spikes":
            CContainer = c4d.BaseObject(c4d.Onull)
            #GObjectName = node.get('name')
            CContainer[c4d.NULLOBJECT_DISPLAY] = 3
            CContainer[c4d.NULLOBJECT_RADIUS] = 70
            CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
            CContainer[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
            CContainer[c4d.ID_BASEOBJECT_USECOLOR] = 2

            #if node.tag != "Spikes":
            CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = - parent[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X]
            CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = - parent[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y]

            for rawNode in node.iter("RawCollision"):
                CreateElementContainer(rawNode, rawNode.attrib.keys(), "RawCollision", CContainer)

            for boxNode in node.iter("BoxCollisions"):
                CreateElementContainer(boxNode, boxNode.attrib.keys(), "BoxCollisions", CContainer)

            if node.tag == "Spikes":
                for rawNode in node.iter("ProcessedCollision"):
                    CreateElementContainer(rawNode, rawNode.attrib.keys(), "ProcessedCollision", CContainer)

        #General objects
        else:
            #Create Containter in the root to Store Game Objects Refs
            GameObjectsRefContainer = doc.SearchObject("LevelKitContainer")
            if(not GameObjectsRefContainer):
                GameObjectsRefContainer = c4d.BaseObject(c4d.Onull)
                GameObjectsRefContainer.SetName("LevelKitContainer")
                doc.InsertObject(GameObjectsRefContainer)

            #Create Game Objects Refs is don't exist. So avoid to keep recreating same object, copies of it will just be instances
            GameObjectReference = doc.SearchObject(GObjectType)
            if(not GameObjectReference):
                GameObjectReference = c4d.BaseObject(c4d.Onull)
                GameObjectReference.SetName(GObjectType)
                #GameObjectReference[c4d.NULLOBJECT_DISPLAY] = 3
                #GameObjectReference[c4d.NULLOBJECT_RADIUS] = 100
                GameObjectReference[c4d.NULLOBJECT_ORIENTATION] = 1
                print(GameObjectReference, node)
                CreateBounds(GameObjectReference, node)
                GameObjectReference.InsertUnder(GameObjectsRefContainer)
                setUserDataFromNode(GameObjectReference, node, True)

            CContainer = c4d.BaseObject(c4d.Oinstance)
            CContainer[c4d.INSTANCEOBJECT_RENDERINSTANCE_MODE] = 1
            CContainer[c4d.ID_BASEOBJECT_USECOLOR] = 2
            #print(GameObjectReference)
            CContainer[c4d.INSTANCEOBJECT_LINK] = GameObjectReference

        CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] + float(node.get("x"))
        CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] - float(node.get("y"))

        if useBound:
            CreateBounds(CContainer, node)

        #Inser Objects inside a container by group
        if node.get("group"):
            CGName = "Group" + "." + node.get("group")
            global CurrentGroup
            CurrentGroup = CGName
            CGroupContainer = getChild(parent, CGName)

            if not CGroupContainer:
                useNull = True
                if useNull:
                    CGroupContainer = c4d.BaseObject(c4d.Onull)
                    CGroupContainer[c4d.NULLOBJECT_DISPLAY] = 3
                    CGroupContainer[c4d.NULLOBJECT_RADIUS] = 100
                    CGroupContainer[c4d.NULLOBJECT_ORIENTATION] = 1
                else:
                    CGroupContainer = c4d.BaseObject(c4d.Oconnector)
                    CGroupContainer[c4d.CONNECTOBJECT_WELD] = False

                CGroupContainer.SetName(CGName)
                CGroupContainer.InsertUnder(parent)
                CGroupContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer

            #Move container to back/front depending on their group, this emulates the parallax effect from SephiusEngine
            CGroupContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = getGroupZPos(node.get("group"))

            if node.tag != "GameSprite":
                #print(node.tag)
                OGName = node.tag + "s"
                OGroupContainer = getChild(CGroupContainer, OGName)

                if not OGroupContainer:
                    OGroupContainer = c4d.BaseObject(c4d.Onull)

                    OGroupContainer.SetName(OGName)
                    OGroupContainer[c4d.NULLOBJECT_DISPLAY] = 3
                    OGroupContainer[c4d.NULLOBJECT_RADIUS] = 100
                    OGroupContainer[c4d.NULLOBJECT_ORIENTATION] = 1
                    OGroupContainer[c4d.ID_BASEOBJECT_USECOLOR] = 2
                    OGroupContainer[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
                    OGroupContainer[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
                    OGroupContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer
                    OGroupContainer.InsertUnder(CGroupContainer)

                CContainer.InsertUnder(OGroupContainer)
            else:
                CContainer.InsertUnder(CGroupContainer)
        else:
            print('object: ', node.tag, 'has no group property')

        #Put Object on a layer and with a specified collor
        CContainer[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
        CContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer
        CContainer.SetName(GObjectName)

        AutoSetUserData = True
        FinalContainer = CContainer

    elif node.tag == "Container":
        CContainer = c4d.BaseObject(c4d.Onull)

        name = node.tag + "." + name

        CContainer[c4d.NULLOBJECT_DISPLAY] = 3
        CContainer[c4d.NULLOBJECT_RADIUS] = 200
        CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
        CContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer

        #Move container to back/front depending on their group, this emulates the parallax effect from SephiusEngine
        #CContainer[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = getGroupZPos(node.get("group"))
        #Scales container depending on their group to make size depth independant, this emulates the parallax effect from SephiusEngine
        CContainer[c4d.ID_BASEOBJECT_REL_SCALE] = c4d.Vector(1, 1, 1) * getScaleByGroup(node.get("group"))

        for ImageNode in node.iter("Image"):
            CreateElementContainer(ImageNode, ImageNode.attrib.keys(), ImageNode.get('texture'), CContainer)

        for EffectArtNode in node.iter("EffectArt"):
            CreateElementContainer(EffectArtNode, EffectArtNode.attrib.keys(), EffectArtNode.get('texture'), CContainer)

        for LightNode in node.iter("LightSprite"):
            CreateElementContainer(LightNode, LightNode.attrib.keys(), LightNode.get('texture'), CContainer)

        AutoSetUserData = True
        FinalContainer = CContainer

    elif node.tag == "Image" or node.tag == "LightSprite":
        name = name + "_Sample"

        AtlasName = node.get("atlas")
        TextureName = node.get("texture")

        SampleContainer = doc.SearchObject(AtlasName + " Samples")
        SampleReference = getChild(SampleContainer, TextureName + "_Sample")

        HasDistortion = False
        if float(node.get("skewX")) != 0 or float(node.get("skewY")) != 0:
           HasDistortion = True

        if (HasDistortion):
            #Actual create the image.
            CContainer = c4d.BaseObject(c4d.Opolygon)
            SetPolygon(node, CContainer, None, None)
        else:
            #Create a instance of reference sample
            CContainer = c4d.BaseObject(c4d.Oinstance)
            CContainer[c4d.INSTANCEOBJECT_RENDERINSTANCE_MODE] = 0
            CContainer.SetName(name)
            CContainer[c4d.INSTANCEOBJECT_LINK] = SampleReference

            #Refresh the managers to show the new object
            c4d.EventAdd()

        global ZOffset
        ZOffset = ZOffset - 0.005

        CContainer[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X] = float(node.get("x"))
        CContainer[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = -float(node.get("y"))
        CContainer[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] = ZOffset
        CContainer[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = float(node.get("rotation"))
        CContainer[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X] = float(node.get("scaleX"))
        CContainer[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y] = float(node.get("scaleY"))

        #print(node.get("atlas") + " Material")
        AtlasMaterial = doc.SearchMaterial(node.get("atlas") + " Material")

        setColorTagWithData(CContainer, node)

        #Create texture tag/material and apply to the object
        MTag = CContainer.MakeTag(c4d.Ttexture)
        MTag[c4d.TEXTURETAG_PROJECTION] = 6
        MTag.SetMaterial(AtlasMaterial)
        AtlasMaterial
        CContainer.InsertTag(MTag)

        #Add object to a C4D Layer
        CContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer

        #if(node.tag == "LightSprite"):
            #CBounds = c4d.BaseObject(c4d.Osplinecircle)
            #CBounds[c4d.PRIM_CIRCLE_RADIUS] = float(node.get("radius"))
            #CBounds[c4d.PRIM_PLANE] = 0
            #CBounds[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
            #CBounds[c4d.SPLINEOBJECT_INTERPOLATION] = 1
            #CBounds[c4d.SPLINEOBJECT_SUB] = 2
            #CBounds.InsertUnder(CContainer)

        AutoSetUserData = True
        FinalContainer = CContainer

    elif node.tag == "EffectArt":
        name = name + "_Sample"

        CContainer = c4d.BaseObject(c4d.Oinstance)
        CContainer[c4d.INSTANCEOBJECT_RENDERINSTANCE_MODE] = 1
        CContainer[c4d.ID_BASEOBJECT_USECOLOR] = 2
        CContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer

        SampleReference = doc.SearchObject(name)
        print(SampleReference)
        CContainer[c4d.INSTANCEOBJECT_LINK] = SampleReference

        CContainer[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X] = float(node.get("x"))
        CContainer[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = -float(node.get("y"))
        CContainer[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = float(node.get("rotation"))
        CContainer[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X] = float(node.get("scaleX"))
        CContainer[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y] = float(node.get("scaleY"))

        setColorTagWithData(CContainer, node)

        AutoSetUserData = True
        FinalContainer = CContainer

    elif node.tag == "RawCollision" or node.tag == "BoxCollisions" or node.tag == "ProcessedCollision":
        CContainer = c4d.BaseObject(c4d.Onull)
        name = node.tag
        CContainer.SetName(node.tag)
        CContainer[c4d.ID_BASEOBJECT_USECOLOR] = 2
        CContainer[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
        CContainer[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
        CContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer

        AutoSetUserData = True
        FinalContainer = CContainer

        for shapeNode in node.iter("RawShape"):
            CreateElementContainer(shapeNode, shapeNode.attrib.keys(), shapeNode.get('type'), CContainer)

        for shapeNode in node.iter("BoxShape"):
            CreateElementContainer(shapeNode, shapeNode.attrib.keys(), shapeNode.get('type'), CContainer)

        for shapeNode in node.iter("ProcessedShape"):
            typeName = shapeNode.get('type')
            if not typeName:
                typeName = shapeNode.get('spikeType')
            CreateElementContainer(shapeNode, shapeNode.attrib.keys(), typeName, CContainer)

    elif node.tag == "RawShape" or node.tag == "ProcessedShape":
        CBounds = c4d.BaseObject(c4d.Ospline)
        CBounds.__init__(node.get("pointCount"), c4d.SPLINETYPE_LINEAR)
        name = node.tag
        rawPointList = node.get("points").split(",")
        idx = 0
        pointList = []
        while idx < len(rawPointList):
            pointList.append(c4d.Vector(float(rawPointList[idx]), -float(rawPointList[idx + 1]), 0))
            idx = idx + 2

        CBounds.ResizeObject(len(pointList))

        CBounds.SetAllPoints(pointList)
        CBounds.SetName("RawShape." + name)
        CBounds[c4d.ID_BASEOBJECT_USECOLOR] = 2
        CBounds[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
        CBounds[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
        CBounds[c4d.ID_LAYER_LINK] = CurrentAreaLayer
        CBounds[c4d.SPLINEOBJECT_CLOSED] = True
        CBounds.Message (c4d.MSG_UPDATE)

        if node.tag != "ProcessedShape":
            CBounds[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.get("x"))
            CBounds[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.get("y"))

        AutoSetUserData = True
        FinalContainer = CBounds

    elif node.tag == "BoxShape":
        CBounds = c4d.BaseObject(c4d.Osplinerectangle)
        name = "BoxShape"
        CBounds.SetName("BoxShape." + name)
        CBounds[c4d.ID_BASEOBJECT_USECOLOR] = 2
        CBounds[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
        CBounds[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
        CBounds[c4d.ID_LAYER_LINK] = CurrentAreaLayer

        cMatrix = Convert2DMatrixTo3DMatrix(node)
        CBounds.SetMg(cMatrix)

        CBounds[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = float(node.get("x"))
        CBounds[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = -float(node.get("y"))

        #print(float(node.get("rotation")))
        #CBounds[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = math.degrees(float(node.get("rotation")))

        CBounds[c4d.PRIM_RECTANGLE_WIDTH] = float(node.get("width"))
        CBounds[c4d.PRIM_RECTANGLE_HEIGHT] = float(node.get("height"))

        AutoSetUserData = True
        FinalContainer = CBounds

    else:
        AutoSetUserData = True
        FinalContainer = (CurrentAreaLayer)

    if(AutoSetUserData):
        setUserDataFromNode(FinalContainer, node, False)
    insertContainerToDocument(FinalContainer, parent, name)

    return FinalContainer

def addPythonTagWithCode(obj, node, texCode):
    # Create a new Python tag
    pythonTag = c4d.BaseTag(c4d.Tpython)

    # Add a User Data parameter to the tag for the step value
    step_param = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
    step_param.SetString(c4d.DESC_NAME, "Local Sample Spacing")
    step_param.SetFloat(c4d.DESC_MIN, -100.0)
    step_param.SetFloat(c4d.DESC_MAX, 100.0)
    step_param.SetFloat(c4d.DESC_STEP, 0.1)
    step_param.SetFloat(c4d.DESC_DEFAULT, 0)
    pythonTag.AddUserData(step_param)

    pythonTag[c4d.ID_USERDATA,1] = getLocalSpacing(node.get("group"))

    #Level Region container (root container)
    RootParam = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BASELISTLINK)
    RootParam.SetString(c4d.DESC_NAME, "Region Root")
    RootParam[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    Celement = pythonTag.AddUserData(RootParam)

    pythonTag[Celement] = doc.SearchObject(RegionName)

    # Set the Python code for the tag
    pythonTag[c4d.TPYTHON_CODE] = texCode

    # Add the tag to the selected object
    obj.InsertTag(pythonTag)

def setColorTagWithData(CContainer, data):
    #See if object has Transparency or Color
    cAlpha = float(data.get("alpha"))

    isPolygonObject = c4d.PolygonObject == type(CContainer)
    #Add the tag Vertex Color to match from ColorIDs Values

    CTag = CContainer.GetTag(c4d.Tvertexcolor)
    #print("Has Color Tag? ", CTag)

    if (isPolygonObject):
        #Create VertexColorTag using polygon points
        CTag = c4d.VertexColorTag(CContainer.GetPointCount())
        CTag.__init__(CContainer.GetPointCount())
    else:
        #Create color tag for undefined number of points
        CTag = c4d.BaseTag(c4d.Tvertexcolor)

    #Enable Color Tag Fields
    CTag[c4d.ID_VERTEXCOLOR_USEFIELDS] = True
    CContainer.InsertTag(CTag)

    # Create a new solid field layer
    field = c4d.BaseList2D(c4d.FLsolid)
    field.SetName("Alpha")

    # Set the color of the solid field to red
    field[c4d.FIELDLAYER_SOLID_COLOR] = c4d.Vector(1, 1, 1)

    # Set the opacity value
    field.SetStrength(cAlpha)

    fieldC = c4d.BaseList2D(c4d.FLcolorize)
    fieldC[c4d.FIELDLAYER_COLORIZE_MODE] = 1
    fieldC[c4d.FIELDLAYER_COLORIZE_COLORBASE] = c4d.Vector(1, 1, 1)
    fieldC[c4d.FIELDLAYER_COLORIZE_COLORTOP] = c4d.Vector(1, 1, 1)
    fieldC[c4d.FIELDLAYER_COLORIZE_COLORTOP_MODE] = 1
    fieldC[c4d.FIELDLAYER_COLORIZE_COLORTOP_DENSITY] = 1
    fieldC[c4d.FIELDLAYER_COLORIZE_CLIP] = True
    #fieldClamp[c4d.FIELDLAYER_CLAMP_MIN_VALUE] = 1
    fieldC.SetName("Color")

    # Add a new Field to the tag
    # Get the Vertex Color Field container
    CTag_field_container = CTag.GetParameter(c4d.ID_VERTEXCOLOR_FIELDS, 0)
    CTag_field_container.InsertLayer(field)
    CTag_field_container.InsertLayer(fieldC)
    CTag[c4d.ID_VERTEXCOLOR_FIELDS] = CTag_field_container

def createOtherGameObjects(CurrentAreaLayer):
    CContainer = c4d.BaseObject(c4d.Onull)
    CContainer[c4d.NULLOBJECT_DISPLAY] = 3
    CContainer[c4d.NULLOBJECT_RADIUS] = 200
    CContainer[c4d.NULLOBJECT_ORIENTATION] = 1
    CContainer[c4d.ID_LAYER_LINK] = CurrentAreaLayer
    return CContainer

def insertContainerToDocument(FinalContainer, parent, name):
    if parent != None:
        if parent.GetName().split(".")[0] != "LevelArea" and parent.GetName().split(".")[0] != "LevelBackground":
            FinalContainer.SetName(name)
        #Inser the Container to the doccument
        if not FinalContainer.GetUp():
            FinalContainer.InsertUnder(parent)
            doc.AddUndo(c4d.UNDOTYPE_NEW, FinalContainer)

def SetPolygon(SampleNode, CObject, UVWTag, Polygon):
    AtlasName = SampleNode.get("atlas")
    TextureName = SampleNode.get("texture")
    #print(SampleNode.get("texture"))

    SampleContainer = SamplesContainer = doc.SearchObject(AtlasName + " Samples")
    SampleReference = getChild(SampleContainer, TextureName + "_Sample")
    #print(SampleReference)
    data = {}
    PSs = []
    PCSs = []

    if not Polygon:
        Polygon = c4d.CPolygon(0, 1, 2, 3)
        Polygon.__init__(0, 1, 2, 3)
        CObject.ResizeObject(4, 1)
        CObject.SetPolygon(0, Polygon)

    if not UVWTag:
        UVWTag = CObject.MakeVariableTag(c4d.Tuvw, 1)
        UVWTag[c4d.ID_BASELIST_NAME] = "SampleUVW"
        CObject.InsertTag(UVWTag)

    #Form matrix from data
    o3dMatrix = Convert2DMatrixTo3DMatrix(SampleNode)

    #Create inverse trnsformation not taking into account skewing
    CObject[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = float(SampleNode.get("rotation"))
    CObject[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X] = float(SampleNode.get("scaleX"))
    CObject[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y] = float(SampleNode.get("scaleY"))
    invertMatrix = ~CObject.GetMg()

    for i in range(4):
        VertexData = {}

        CurrentVertexDataList = SampleNode.get("VertexData" + str(i)).split(",")

        for CPair in CurrentVertexDataList:
            VertexData[CPair.split(":")[0]] = float(CPair.split(":")[1])

        vertexPos = SampleReference[GetUserData(SampleReference, "Vertex " + str(i) + " Position")]
        vertexPos = vertexPos * o3dMatrix
        vertexPos = vertexPos * invertMatrix

        data["VertexPosition" + str(i)] = vertexPos

        textureHight = SampleReference[GetUserData(SampleReference, "Texture Height")]

        PSs.append(data["VertexPosition" + str(i)])
        CObject.SetPoint(i, PSs[i])

        data["Vertex" + str(i) + "UVW"] = SampleReference[GetUserData(SampleReference, "Vertex " + str(i) + " UVW")]

        PCSs.append(data["Vertex" + str(i) + "UVW"])

    UVWTag.SetSlow(0, PCSs[0], PCSs[1], PCSs[2], PCSs[3])

    PivotOffset = SampleReference[GetUserData(SampleReference, "Offset")]
    CObject[c4d.ID_BASEOBJECT_REL_POSITION] = CObject[c4d.ID_BASEOBJECT_REL_POSITION] - PivotOffset

    #Update object. Need to update bound box for selection and etc.
    CObject.Message (c4d.MSG_UPDATE)

def CreateBounds(ParentObject, node):
    if(node.get("radius")):
        boundsStrW = float(node.get("radius"))
        node.set("shapeType", "Circle")
    elif(node.get("width")):
        boundsStrW = float(node.get("width"))
        boundsStrH = float(node.get("height"))
    else:
        boundsStrW = 30
        boundsStrH = 30

    #print("Bounds: ", boundsStrW, boundsStrW)
    if node.get("shapeType") == "Circle":
        CBounds = c4d.BaseObject(c4d.Osplinecircle)
        CBounds[c4d.PRIM_CIRCLE_RADIUS] = boundsStrW
        CBounds[c4d.PRIM_PLANE] = 0
        CBounds[c4d.SPLINEOBJECT_INTERPOLATION] = 1
        CBounds[c4d.SPLINEOBJECT_SUB] = 2
    else:
        CBounds = c4d.BaseObject(c4d.Osplinerectangle)
        CBounds[c4d.PRIM_RECTANGLE_WIDTH] = boundsStrW
        CBounds[c4d.PRIM_RECTANGLE_HEIGHT] = boundsStrH

    CBounds.SetName("Bounds")
    CBounds[c4d.ID_BASEOBJECT_USECOLOR] = 2
    CBounds[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 1
    CBounds[c4d.ID_BASEOBJECT_COLOR] = GetElementColor(node.tag)
    CBounds[c4d.ID_LAYER_LINK] = ParentObject.GetLayerObject(doc)

    CBounds.InsertUnder(ParentObject)

#Challange here is to replicate Skew effect from 2D samples that existed. Since Cinema4D don't suppor skew and matrix operation is 3D and different
#This made conversion difficult. I'm trying to extract skew information to create a matrix just with that and apply that to vertex.
#Is not possible to apply a skewed matrix to a object cause Cinema4D will correct automaticly to Ortogonal matrix.
#So objects with skew will need to have this effect applyed on vertex itself
#i need to add support for custom vertex position in Sephius Engine later and abandon skew as a feature to deform samples.
def Convert2DMatrixTo3DMatrix(SampleNode):
    #Get matrix information, inclusind skewing
    matrixA = float(SampleNode.attrib.get("matrixA"))
    matrixB = float(SampleNode.attrib.get("matrixB"))
    matrixC = float(SampleNode.attrib.get("matrixC"))
    matrixD = float(SampleNode.attrib.get("matrixD"))
    matrixTx = float(SampleNode.attrib.get("matrixTx"))
    matrixTy = float(SampleNode.attrib.get("matrixTy"))

    #Form matrix from data
    o3dMatrix = c4d.Matrix(
        v1=c4d.Vector(matrixA, -matrixB, 0),
        v2=c4d.Vector(-matrixC, matrixD, 0),
        v3=c4d.Vector(0, 0, 1),
        off=c4d.Vector(0, 0, 0)
    )
    return o3dMatrix

def Convert3DMatrixTo2DMatrix(o3dMatrix, node):
    o3dMatrix.v1.x
    -o3dMatrix.v1.y
    -o3dMatrix.v2.x
    o3dMatrix.off.y
    -o3dMatrix.off.x

    #Get matrix information, inclusind skewing
    float(node.attrib.set(o3dMatrix.v1.x))
    float(node.attrib.set(-o3dMatrix.v1.y))
    float(node.attrib.set(-o3dMatrix.v2.x))
    float(node.attrib.set(o3dMatrix.v2.y))

    float(node.attrib.set(o3dMatrix.off.y))
    float(node.attrib.set(-o3dMatrix.off.x))

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
        print(f)
        tree = ElementTree.parse(f)
        print(tree)

    #Start Undo. This allow C4D to start to store actions in order to allow undo
    doc.StartUndo()

    for node in tree.iter("LevelRegion"):
        global RegionName
        RegionName = node.get('name')
        print("dsfdfsd", RegionName)

        objectTypesCounts = {}

        LevelRegionContainer = CreateElementContainer(node, node.attrib.keys(), RegionName, None)
        LevelRegionContainer.SetName(RegionName)

        #Inser the Container to the doccument
        doc.InsertObject(LevelRegionContainer)
        doc.AddUndo(c4d.UNDOTYPE_NEW, LevelRegionContainer)

        print(LevelRegionContainer)

        for subNode in node:
            SubNomeName = subNode.get('name')
            if not SubNomeName:
                SubNomeName = ""
            else:
                SubNomeName = "." + SubNomeName

            CreateElementContainer(subNode, subNode.attrib.keys(), subNode.tag + SubNomeName, LevelRegionContainer)

        #for child in root:
        #print(child.tag, child.attrib)
        #Luma and Area Maps could use vetex color
    doc.EndUndo()
    c4d.EventAdd()

if __name__=='__main__':
    global ZOffset
    ZOffset = 0
    main()