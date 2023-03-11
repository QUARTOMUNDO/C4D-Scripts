import c4d
import xml.etree.ElementTree as ET

def GetSplinePointsPositions(SplineObject):
    if SplineObject is not None and type(SplineObject) is c4d.SplineObject:
        # Get the number of points on the spline
        point_count = SplineObject.GetPointCount()

        PointsLocationsSrt = ""

        # Iterate over each point and get its location
        for i in range(point_count):
            point_location = SplineObject.GetPoint(i)
            
            if i < point_count - 1:
                Divisior = ','
            else:
                Divisior= ""
            
            PointsLocationsSrt += str(point_location.x) + ',' + str(-point_location.y) + Divisior

        print("Points", PointsLocationsSrt)
        return PointsLocationsSrt
    else:
       raise ValueError("Provided object is not a spline ", SplineObject)

def get_top_parent(obj):
    parent = obj.GetUp()
    if parent is None:
        # The current object has no parent, so it is the top-level parent
        return obj
    else:
        # Recursively get the parent of the current object
        return get_top_parent(parent)

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

def Convert3DMatrixTo2DMatrix(obj, node):
    worldMatrix = obj.GetMg()
    localMatrix = obj.GetMl()
    
    #Get matrix information, inclusind skewing
    node.set('matrixA', str(worldMatrix.v1.x))
    node.set('matrixB', str(-worldMatrix.v1.y))
    node.set('matrixC', str(worldMatrix.v2.x))
    node.set('matrixD', str(worldMatrix.v2.y))
    node.set('matrixTx', str(localMatrix.off.x))
    node.set('matrixTy', str(-localMatrix.off.y))

#Return value for a user data by name
def GetUserData(obj, UDName):
    for id, bc in obj.GetUserDataContainer():
        #print(bc[c4d.DESC_NAME], UDName)
        if bc[c4d.DESC_NAME] == UDName:
            return obj[id]

    raise ValueError(bc[c4d.DESC_NAME], UDName, "is None", obj[id])
    return None

def ToIntStr(value):
    return str(int(value))

def getChildByName(obj, name):
    """
    This function gets the child of the given object with the specified name.
    """
    child = obj.GetDown()
    while child is not None:
        if child.GetName() == name:
            return child
        child = child.GetNext()
    raise ValueError("Object Has no Child With The Name Provided", child.GetName())
    return None

def PreDefineLevelArea(obj, obj_node):
    ObjectName = obj.GetName().split('.')[0]

    obj_node.set('regionName', GetUserData(obj, "region").replace(" ", "_"))
    obj_node.set('globalId',  ToIntStr(GetUserData(obj, "globalId")))
    obj_node.set('localId',  ToIntStr(GetUserData(obj, "localId")))
    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))

    # Get the bounding box of the object
    BoundObject = getChildByName(obj, "Bounds." + obj.GetName())

    if(BoundObject is None):
        raise ValueError("No Bounds Found for ", obj.GetName())

    Bounds = BoundObject.GetRad()

    # Calculate the rectangle based on the bounding box
    x = BoundObject.GetMg().off.x - Bounds.x
    y = -(BoundObject.GetMg().off.y + Bounds.y)
    w = Bounds.x * 2
    h = Bounds.y * 2

    obj_node.set('bounds',   BoundsString(x, y, w, h))
    obj_node.set('objectCount', "0")
    obj_node.set('spritesContainersCount', "0")
    obj_node.set('spriteCount', "0")

    print("==============")
    print("AREA PROCESSED")
    print("==============")

def PreDefineRawCollision(obj, obj_node):
    ObjectName = obj.GetName().split('.')[0]

    obj_node.set('type', "RawPolygon")
    obj_node.set('oneWay',  str(GetUserData(obj, "oneWay")))
    obj_node.set('group',  ToIntStr(GetUserData(obj, "group")))
    obj_node.set('parallax',  str(GetUserData(obj, "parallax")))
    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))
    obj_node.set('points',  GetSplinePointsPositions(obj))

    print("==============")
    print("Raw COLLISION PROCESSED")
    print("==============")

def PreDefineBoxCollision(obj, obj_node):
    ObjectName = obj.GetName().split('.')[0]

    obj_node.set('type', "BoxPolygon")
    obj_node.set('oneWay',  str(GetUserData(obj, "oneWay")))
    obj_node.set('group',  ToIntStr(GetUserData(obj, "group")))
    obj_node.set('parallax',  str(GetUserData(obj, "parallax")))
    
    Convert3DMatrixTo2DMatrix(obj, obj_node)
    #print(obj_node, obj_node.get("matrixA"))
    
    obj_node.set('height',  str(GetUserData(obj, "height")))
    obj_node.set('width',  str(GetUserData(obj, "width")))

    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))
    obj_node.set('rotation',  str(GetUserData(obj, "rotation")))


    print("==============")
    print("BOX  COLLISION PROCESSED")
    print("==============")


def BoundsString(x, y, w, h):
    BoundsStr = "(x=" + str(x) + "," + "y=" + str(y) + "," + "w=" + str(w) + "," + "h=" + str(h) + ")"
    return BoundsStr

#Define if object should generate XML node with information othetwise it will be ignored (beside it's childen will be processes)
def ShouldGenerateNode(obj):
    ObjectID = obj.GetName().split('.')[0]

    if(ObjectID == "LevelArea"):
        return True
    elif(ObjectID == "GameSprite"):
        return True
    elif(ObjectID == "LevelCollision"):
        return True
    elif(ObjectID == "RawCollision"):
        return True
    elif(ObjectID == "BoxCollisions"):
        return True
    elif(ObjectID == "BoxShape" or ObjectID == "RawShape"):
        return True
    elif(ObjectID == "Container"):
        return True
    elif(ObjectID == "Image"):
        return True
    elif(ObjectID == "EffectArt"):
        return True
    elif(ObjectID == "LightSprite"):
        return True
    else:
        return False

def PreDefineObjectType(obj, obj_node):
    ObjectID = obj.GetName().split('.')[0]

    if(ObjectID == "LevelArea"):
        PreDefineLevelArea(obj, obj_node)
    #if(ObjectID == "GameSprite"):
        #ProcessGameSprite(obj)
    #if(ObjectID == "LevelCollision"):
        #ProcesLevelCollision(obj)
    if(ObjectID == "BoxShape"):
        PreDefineBoxCollision(obj, obj_node)
    if(ObjectID == "RawShape"):
        PreDefineRawCollision(obj, obj_node)
    #if(ObjectID == "Group"):
        #ProcessGroup(obj)
    #if(ObjectID == "Container"):
        #ProcesContainer(obj)
    #if(ObjectID == "Image"):
        #ProcesImage(obj)
    #if(ObjectID == "EffectArt"):
        #ProcessEffectArt(obj)
    #if(ObjectID == "LightSprite"):
        #ProcessLightSprite(obj)

def PostDefineObjectType(obj, obj_node):
    ObjectID = obj.GetName().split('.')[0]

    #if(ObjectID == "GameSprite"):
        #ProcessGameSprite(obj)
    #if(ObjectID == "LevelCollision"):
        #ProcesLevelCollision(obj)
    #if(ObjectID == "BoxShape"):
        #PostDefineBoxCollision(obj, obj_node)
    #if(ObjectID == "RawPolygon"):
        #ProcessRawPolygon(obj)
    #if(ObjectID == "Group"):
        #ProcessGroup(obj)
    #if(ObjectID == "Container"):
        #ProcesContainer(obj)
    #if(ObjectID == "Image"):
        #ProcesImage(obj)
    #if(ObjectID == "EffectArt"):
        #ProcessEffectArt(obj)
    #if(ObjectID == "LightSprite"):
        #ProcessLightSprite(obj)

def parse_objects(obj, parent_node, GenerateNode, indent=0):
    """
    This function recursively parses through all children of the given object
    and creates an XML describing their position, rotation, scale, and any user data.
    """
    # Create a new XML node for the current object
    ObjectID = obj.GetName().split('.')[0]
    #print(obj.GetName())
    #ObjectName = obj.GetName().split('.')[1]

    if(GenerateNode):
        PassNode = ET.SubElement(parent_node, ObjectID)

        # Add line breaks and indentation to the XML string
        PassNode.tail = '\n' + ' ' * (indent + 2)

        #Process the object
        PreDefineObjectType(obj, PassNode)
    else:
        PassNode = parent_node;

    #obj_node.set('Name',ObjectName)
    #print(obj_node)


    # Add the object's position, rotation, and scale to the XML node
    #pos = obj.GetAbsPos()
    #rot = obj.GetAbsRot()
    #scale = obj.GetAbsScale()
    #obj_node.set('Position', f'{pos.x},{pos.y},{pos.z}')
    #obj_node.set('Rotation', f'{rot.x},{rot.y},{rot.z}')
    #obj_node.set('Scale', f'{scale.x},{scale.y},{scale.z}')

    # Check if the object has any user data
    #if obj.GetUserDataContainer():
        # Create an XML node for the user data
    #    userdata_node = ET.SubElement(obj_node, 'UserData')

        # Loop through all the user data parameters and add them to the XML node
   #     for id, bc in obj.GetUserDataContainer():
   #         param = bc[c4d.DESC_NAME]
   #         userdata_node.set(param, str(obj[id]))


    #print("Tail1")
    if(GenerateNode):
        NextIdent = indent+2
    else:
        NextIdent = indent

    # Invert the order of the children list
    children = obj.GetChildren()[::-1]
    # Recursively parse through all children of the current object
    for child in children:
        parse_objects(child, PassNode, ShouldGenerateNode(child), NextIdent)

    if(GenerateNode):
        #Post process the object
        PostDefineObjectType(obj, PassNode)


    #print("PArsed Sub Childs")

    if(GenerateNode):
        # Add line breaks and indentation to the closing XML string
        parent_node.text = '\n' + ' ' * indent
        PassNode.tail = '\n' + ' ' * indent

def main():
    # Get the active object in the scene
    obj = doc.GetActiveObject()

    #stop if root object is not a site
    if(obj.GetName().split('.')[0] != "LevelSite"):
        raise ValueError("OBJECT SELECTED ARE NOT A LEVEL SITE")

    Root = get_top_parent(obj)
    RegionName = Root.GetName().replace(" ", "")
    SiteName =  'Site' + obj.GetName().split('.')[1].replace(" ", "")

    XMLFileName = RegionName + '_' + SiteName + '.xml'
    print ('XML File Name' + XMLFileName)

    # Create a new XML tree and root node
    root = ET.Element('LevelAreas')
    root.set('regionName', GetUserData(obj, "region").replace(" ", "_"))
    root.set('siteName', obj.GetName().split('.')[1])
    root.set('siteID', str(int(GetUserData(obj,  "id"))))

    # Parse through all children of the active object
    parse_objects(obj, root, False, 2)
    print("Fnished Pa")
    # Write the XML tree to a file
    tree = ET.ElementTree(root)
    tree.write(XMLFileName, encoding='utf-8', xml_declaration=False)
    print("Done!!!!")

if __name__=='__main__':
    main()