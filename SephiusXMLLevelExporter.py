import c4d
import xml.etree.ElementTree as ET
import math

def indxTrans(j):
    #  <p>The indices of the vertices are arranged like this:</p>
    #  Question is how is the right order... Cinema order points differently.
    #  <pre>
    #  0 - 1
    #  | / |
    #  2 - 3
    #  </pre>
    indxArray = [0,1,3,2]
    #return [0,1,2,3]
    #return [1,0,2,3]
    #return [2,3,1,0]
    #return [3,2,1,0]

    return indxArray[j]

def indxTransUV(j):
    indxArray = [3,2,1,0]
    
    return indxArray[j]

def MaxAndMinCoord(coordinates):
    # Define a list to store the x and y coordinates of each vector
    #coordinates = [vector1, vector2, vector3, vector4]
    
    # Initialize the minimum and maximum height and width values
    min_height = math.inf
    max_height = -math.inf
    min_width = math.inf
    max_width = -math.inf
    
    # Loop through each coordinate and update the minimum and maximum values
    for coordinate in coordinates:
        x = coordinate.x
        y = coordinate.y
        
        if y < min_height:
            min_height = y
        if y > max_height:
            max_height = y
        if x < min_width:
            min_width = x
        if x > max_width:
            max_width = x
    
    # Print the minimum and maximum height and width values
    #print("Minimum height:", min_height)
    #print("Maximum height:", max_height)
    #print("Minimum width:", min_width)
    #print("Maximum width:", max_width)
    return [min_width, max_width, min_height, max_height]

def SetPolygonVertexData(PolygonObject, node, SampleReference):
    if PolygonObject is not None and type(PolygonObject) is c4d.PolygonObject:
        # Get the point count and list of points
        point_count = PolygonObject.GetPointCount()
        #points = PolygonObject.GetAllPoints()

        # Get the polygon count and list of polygons
        polygon_count = PolygonObject.GetPolygonCount()
        polygons = PolygonObject.GetAllPolygons()

        # Get the UV tag and UV count
        sampleReference = GetUserData(PolygonObject, "Sample Reference")
        uv_tag = PolygonObject.GetTag(c4d.Tuvw)
        Refuv_tag = sampleReference.GetTag(c4d.Tuvw)

        node.set('PolyCount', str(polygon_count))

        # Loop through each polygon and get the UV coordinates for its vertices
        for i in range(polygon_count):
            vertex_positions = ""
            vertex_uvs = ""

            #  <p>The indices of the vertices are arranged like this:</p>
            #
            #  <pre>
            #  0 - 1
            #  | / |
            #  2 - 3
            #  </pre>
            # Loop through each vertex of the polygon and get its UV coordinates
             # Get the polygon's UVW coordinates
            poly = PolygonObject.GetPolygon(i)
            uvw = uv_tag.GetSlow(i)

            # Get the indices of the points for the current polygon. Note that the order is different from Cinema to Sephius Engine
            pointsIndx = [poly.b, poly.a, poly.c, poly.d]
            uvPoints = [uvw["b"], uvw["a"], uvw["c"], uvw["d"]]
            
            # Get the U and V components of the vertex's UV coordinates for ref sample
            uvwRef = Refuv_tag.GetSlow(0)
            REFuvPoints = [uvwRef["b"], uvwRef["a"], uvwRef["c"], uvwRef["d"]]
            Range = MaxAndMinCoord(REFuvPoints)
            
            uMin = Range[0]
            uMax = Range[1]
            vMin = Range[2]
            vMax = Range[3]
            
            print ('REPoints ', REFuvPoints)
            print ('uvPoints ', uvPoints)
            
            for j in range(4):
                # Get the vertex index for the current vertex of the polygon
                point = PolygonObject.GetPoint(pointsIndx[j])
                x = point.x
                y = -point.y

                # Get the U and V components of the vertex's UV coordinates
                UVpoint = uvPoints[j]
                u = UVpoint.x
                v = UVpoint.y

                #remap uv to be proportional to reference sample. In SephiusEngine, we acess the sub texture which has values from 0 to 1.
                u = remap(u, uMin, uMax)
                v = remap(v, vMin, vMax)

                # Add the U and V components to the vertex UV coordinates string
                vertex_uvs += "{},{},".format(u, v)
                vertex_positions += "{},{},".format(x, y)

            # Remove the last comma from the strings

            vertex_uvs = vertex_uvs[:-1]
            #vertex_uvs = "0,0,1,0,0,1,1,1"
            #vertex_uvs = "1,1,0,1,1,0,0,0"
            vertex_positions = vertex_positions[:-1]

            # Print the UV coordinates
            print(vertex_uvs)

            #print("vertex_positions" + str(vertex_positions))

            node.text = '\n' + ' ' * (12)
            VertexNode = ET.SubElement(node, 'PolygonData')

            if (i == polygon_count - 1):
                VertexNode.tail = '\n' + ' ' * (8)
            else:
                VertexNode.tail = '\n' + ' ' * (12)

            VertexNode.set('PolygonID', str(i))
            VertexNode.set('PointCount', str(4))
            VertexNode.set('Positions', vertex_positions)
            VertexNode.set('Coords', vertex_uvs)

    else:
       raise ValueError("Provided object is not a polygon object ", PolygonObject)

def remap(value, old_min, old_max):
    
    """
    Remap a value from the old range [old_min, old_max] to the new range [new_min, new_max].
    """
    remapRange = old_max - old_min
    minSize = value - old_min
    
    remapValue = minSize / remapRange
    print('old_min', old_min, '   /    old_max', old_max,  '   /  remapRange',   remapRange )
    print('value', value, '   /    remapValue', remapValue,  '   /  minSize',   minSize )
    
    return remapValue

def GetPolygonPointsCoords(PolygonObject):
    if PolygonObject is not None and type(PolygonObject) is c4d.PolygonObject:
        # Get the point count and list of points
        point_count = PolygonObject.GetPointCount()
        points = PolygonObject.GetAllPoints()

        # Get the polygon count and list of polygons
        polygon_count = PolygonObject.GetPolygonCount()
        polygons = PolygonObject.GetAllPolygons()

        # Loop through each polygon and get the UV coordinates for its vertices
        for i in range(polygon_count):
            # Get the polygon's UVW coordinates
            uvw = PolygonObject.GetPolygonUV(i)

            # Loop through each vertex of the polygon and get its UV coordinates
            for j in range(3):
                # Get the vertex index for the current vertex of the polygon
                vertex_index = polygons[i].a+j

                # Get the U and V components of the vertex's UV coordinates
                u = uvw[j].x
                v = uvw[j].y

                # Add the U and V components to the vertex UV coordinates string
                vertex_uvs += "{},{},".format(u, v)

        return vertex_uvs
    else:
       raise ValueError("Provided object is not a spline ", SplineObject)

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

def getChildCount(obj):
    # Loop through all the child objects of the parent object
    child = obj.GetDown()
    child_count = 0
    while child is not None:
        # Increment the child count
        child_count += 1
        # Get the next child object
        child = child.GetNext()

    return child_count

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
    Bound = obj.GetRad()
    print(Bound)
    #Get matrix information, inclusind skewing
    node.set('matrixA', str(worldMatrix.v1.x))
    node.set('matrixB', str(-worldMatrix.v1.y))
    node.set('matrixC', str(-worldMatrix.v2.x))
    node.set('matrixD', str(worldMatrix.v2.y))
    #node.set('matrixTx', str(obj[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X] + (Bound.x /2)))
    #node.set('matrixTy', str(-obj[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] + (Bound.y /2)))

    node.set('matrixTx', str(obj.GetRelPos().x))
    node.set('matrixTy', str(-obj.GetRelPos().y))

#Return value for a user data by name
def GetUserData(obj, UDName, stopIfNone=True):
    #print(obj)

    for id, bc in obj.GetUserDataContainer():
        #print(bc[c4d.DESC_NAME], UDName)
        obID = obj[id]
        if bc[c4d.DESC_NAME] == UDName:
            return obj[id]

    if(stopIfNone == True):
        if(obj is None):
            raise ValueError("Object is None")
        raise ValueError(UDName, "is None")

    return "None"

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

def PreLevelCollision(obj, obj_node):
    ObjectName = obj.GetName().split('.')[0]

    obj_node.set('name', obj.GetName())
    obj_node.set('parentAreaID', ToIntStr(GetUserData(obj, "parentAreaID")))

    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))

    obj_node.set('physichScale', ToIntStr(GetUserData(obj, "physichScale")))

    print("==============")
    print("LEVEL COLLISION PROCESSED")
    print("==============")

def PreDefineContainer(obj, obj_node):
    ObjectName = obj.GetName().split('.')[1]

    obj_node.set('name', ObjectName)
    obj_node.set('className', (GetUserData(obj, "className")))
    obj_node.set('group', ToIntStr(GetUserData(obj, "group")))
    obj_node.set('atlas', (GetUserData(obj, "atlas")))
    obj_node.set('atlas', (GetUserData(obj, "blendMode")))
    obj_node.set('spriteCount', ToIntStr(getChildCount(obj)))

    print("==============")
    print("Container PROCESSED")
    print("==============")

def PreDefineGameSprite(obj, obj_node):
    ObjectName = obj.GetName()

    obj_node.set('name',  ObjectName)
    obj_node.set('group',  ToIntStr(GetUserData(obj, "group")))
    obj_node.set('parentAreaID',  ToIntStr(GetUserData(obj, "parentAreaID")))
    obj_node.set('alpha', str(GetUserData(obj, "alpha")))
    obj_node.set('blendMode',  str(GetUserData(obj, "blendMode")))

    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))

    obj_node.set('scaleOffsetX',  str(GetUserData(obj, "scaleOffsetX")))#Should be decided by game system
    obj_node.set('scaleOffsetY',  str(GetUserData(obj, "scaleOffsetY")))#Should be decided by game system

    obj_node.set('parallax',  str(GetUserData(obj, "parallax")))

    print("==============")
    print("GAME SPRITE PROCESSED")
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

def PreDefineImage(obj, obj_node):
    obj_node.tag = 'Image'
    ObjectName = 'Image'
    print(obj.GetName(), type(obj))
    obj_node.set('name', ObjectName)

    print (type(obj).__name__)

    SampleReference = GetUserData(obj, "Sample Reference")
    isSample = GetUserData(SampleReference, "IsSpriteSheetSample")
    SpriteName = GetUserData(SampleReference, "Sprite Name")
    Atlas = GetUserData(SampleReference, "Atlas")

    if (isSample == False):
        raise ValueError("Sample Reference is not a SpriteSheetSample", SampleReference)

    #We use the data from the original sample if this is a Instance
    if (type(obj).__name__ == "InstanceObject"):
        obj_node.set('type', "Instance")
    else:
        obj_node.set('type', "Polygon")

    obj_node.set('className', "Image")
    obj_node.set('texture', SpriteName)
    obj_node.set('atlas', Atlas)

    obj_node.set('transformMode', "normal")

    obj_node.set('x', str(obj.GetAbsPos().x))
    obj_node.set('y', str(-obj.GetAbsPos().y))
    obj_node.set('rotation', str(obj[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z]))
    obj_node.set('scaleX', str(obj[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X]))
    obj_node.set('scaleY', str(obj[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y]))

    # Get the vertex map tag by name
    vtag = obj.GetTag(c4d.Tvertexcolor)

    print('--------------------------------')
    print('Tag ', vtag)

    # Get the number of fields in the Vertex Color Tag
    fields = vtag[c4d.ID_VERTEXCOLOR_FIELDS]
    fieldsCount = fields.GetCount()
    fieldsRoot = fields.GetLayersRoot()
    ColorField = fieldsRoot.GetFirst()
    AlphaFiels = ColorField.GetNext()

    obj_node.set('alpha', str(AlphaFiels.GetStrength()))
    obj_node.set('color', str(ColorField[c4d.FIELDLAYER_COLORIZE_COLORTOP]))
    obj_node.set('blendMode', (GetUserData(obj, "blendMode", False)))
    #obj_node.set('group', ToIntStr(GetUserData(obj, "group")))

    obj_node.set('skewX', '0')#skew is not supported. we will use vertex offset
    obj_node.set('skewY', '0')#skew is not supported. we will use vertex offset

    if (type(obj).__name__ == "PolygonObject"):
        SetPolygonVertexData(obj, obj_node, SampleReference)

    Convert3DMatrixTo2DMatrix(obj, obj_node)

def BoundsString(x, y, w, h):
    BoundsStr = "(x=" + str(x) + ", " + "y=" + str(y) + ", " + "w=" + str(w) + ", " + "h=" + str(h) + ")"
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
    elif(ObjectID == "BoxShape"):
         return True
    elif(ObjectID == "RawShape"):
        return True
    elif(ObjectID == "Container"):
        return True
    elif((GetUserData(obj, "IsSpriteSheetSample", False)) == True):
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
    if(ObjectID == "LevelCollision"):
        PreLevelCollision(obj, obj_node)
    elif(ObjectID == "BoxShape"):
        PreDefineBoxCollision(obj, obj_node)
    elif(ObjectID == "RawShape"):
        PreDefineRawCollision(obj, obj_node)
    elif(ObjectID == "GameSprite"):
        PreDefineGameSprite(obj, obj_node)
    elif(ObjectID == "Container"):
        PreDefineContainer(obj, obj_node)

    #Images inside containers
    #elif(str(GetUserData(obj, "className", False)) == "Image"):
        #PreDefineImage(obj, obj_node)
    elif((GetUserData(obj, "IsSpriteSheetSample", False)) == True):
        PreDefineImage(obj, obj_node)

    #if(ObjectID == "Group"):
        #ProcessGroup(obj)
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

    #if(GenerateNode):
        #Post process the object
        #PostDefineObjectType(obj, PassNode)


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