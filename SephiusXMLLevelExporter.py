import c4d
import xml.etree.ElementTree as ET
import math
from c4d import DescID, Vector, Matrix, utils
from datetime import datetime

def search_for_object(name, obj):
    """
    Search for a child object with a specific name.
    :param name: the name of the object to search for.
    :param obj: the current object in the hierarchy.
    :return: the object if found, else None.
    """
    while obj:
        if obj.GetName() == name:
            return obj

        result = search_for_object(name, obj.GetDown())
        if result:
            return result

        obj = obj.GetNext()

    return None

def update_user_data(obj, param_name, value):
    """
    Update the value of a specific user data parameter.
    :param obj: the object which has the user data.
    :param param_name: the name of the user data parameter.
    :param value: the new value to set.
    :return: True if successful, False otherwise.
    """
    data = obj.GetUserDataContainer()
    print('updating user data')
    for id, bc in data:
        if bc[c4d.DESC_NAME] == param_name:
            print(bc[c4d.DESC_NAME], param_name, value)
            obj[id] = value
            return True

    return False

#Return true if object has a user data name and value is equal to desired
def HasUserData(CObject, UDName):
    for id, bc in CObject.GetUserDataContainer():
        if bc[c4d.DESC_NAME] == UDName:
            return True
    return False

def get_parameter_type(obj, parameter_id):
    parameter_data = obj.GetParameter(parameter_id, c4d.DESCFLAGS_GET_0)

    print('parameter_data', parameter_data)

    if parameter_data is None:
        return None

    value, dtype = parameter_data

    if dtype == c4d.DTYPE_BOOL:
        return 'bool'
    elif dtype == c4d.DTYPE_LONG:
        return 'int'
    elif dtype == c4d.DTYPE_REAL:
        return 'float'
    elif dtype == c4d.DTYPE_VECTOR:
        return 'c4d.Vector'
    elif dtype == c4d.DTYPE_STRING:
        return 'str'
    elif dtype == c4d.DTYPE_FILENAME:
        return 'c4d.storage.Filename'
    elif dtype == c4d.DTYPE_COLOR:
        return 'c4d.Color'
    else:
        return 'unknown'


def get_userdata_values(obj, group_name):
    user_data_dict = {}
    #print('1', group_name)
    if not obj:
        return user_data_dict

    # Get the object's user data container
    ud_container = obj.GetUserDataContainer()

    for id, bc in ud_container:
        # Check if the user data is in the specified group
        parent_group_id = bc[c4d.DESC_PARENTGROUP]

        if parent_group_id and obj[parent_group_id] == group_name:
            # Get the variable name and value
            variable_name = bc[c4d.DESC_NAME]
            variable_value = obj[id]

            #Bool Conversion. e verify if value has UINT which means it is real or vector
            #Maybe don't work if data is int'
            if bc[c4d.DESC_UNIT] is None:
                if variable_value == 0:
                    variable_value = 'false'
                elif variable_value == 1:
                    variable_value = 'true'
            else:
                #remove .0 a the end of int numbers
                if len(str(variable_value).split(".")) > 1:
                    if str(variable_value).split(".")[1] == '0':
                        variable_value = str(variable_value).split(".")[0]

            print("variable_value", bc[c4d.DESC_UNIT], variable_name, variable_value )

            # Get the parameter data type
            #data_entry = bc.GetCustomDataType(id)
            #dtype = data_entry.GetValue()

            #print('5', group_name, variable_name, ud_type, variable_value, bool(variable_value))
            user_data_dict[variable_name] =  str(variable_value)

    return user_data_dict

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
    Refpolygon_count = SampleReference.GetPolygonCount()
    if Refpolygon_count > 1:
        print("Polygon:", PolygonObject.GetName(), "Sample Reference has more than 1 polygon. This mean it is a wrong ref (not a ref sample) and it's not supported. Poly count:", Refpolygon_count)

    #print(type(PolygonObject), type(PolygonObject) is c4d.PolygonObject)

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
            print(REFuvPoints)

            Range = MaxAndMinCoord(REFuvPoints)

            uMin = Range[0]
            uMax = Range[1]
            vMin = Range[2]
            vMax = Range[3]

            #print ('REPoints ', REFuvPoints)
            #print ('uvPoints ', uvPoints)

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
                print(u, v)

                # Add the U and V components to the vertex UV coordinates string
                vertex_uvs += "{},{},".format(u, v)
                vertex_positions += "{},{},".format(x, y)

            # Remove the last comma from the strings

            vertex_uvs = vertex_uvs[:-1]
            #vertex_uvs = "0,0,1,0,0,1,1,1"
            #vertex_uvs = "1,1,0,1,1,0,0,0"
            vertex_positions = vertex_positions[:-1]

            # Print the UV coordinates
            #print(vertex_uvs)

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
    #print('old_min', old_min, '   /    old_max', old_max,  '   /  remapRange',   remapRange )
    #print('value', value, '   /    remapValue', remapValue,  '   /  minSize',   minSize )

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
    if SplineObject is not None and type(SplineObject)is c4d.SplineObject:
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

        #print("Points", PointsLocationsSrt)
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

#return the group for an object by the parent its belongs.
#It looks for a parent with name 'Group' then look for each number it has.
def getGroupByParent(obj):
    if obj is None:
        return 12

    parent = obj.GetUp()
    if parent is None:
        return 12

    ParentName = parent.GetName()
    if "Group" in ParentName:
        if len(ParentName.split(".")) > 1:
            GroupName = ParentName.split(".")[1]
            return str(GroupName)

    return getGroupByParent(parent)

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
    #print(Bound)
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
    raise ValueError("Object Has no Child With The Name Provided", name)
    return None

def PreDefineLevelArea(obj, obj_node):
    global AreaRoot
    AreaRoot = obj
    print("AreaRoot", AreaRoot.GetName())

    ObjectName = obj.GetName().split('.')[0]

    obj_node.set('regionName', GetUserData(obj, "regionName").replace(" ", "_"))
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
    obj_node.set('objectCount', ToIntStr(getChildCount(obj)))
    obj_node.set('spritesContainersCount', "f")
    obj_node.set('spriteCount', "f")

    print("==============")
    print("AREA PROCESSED")
    print("==============")

def PreDefineLevelBackground(obj, obj_node):
    global AreaRoot
    AreaRoot = obj
    print("BGRoot", AreaRoot.GetName())

    ObjectName = obj.GetName().split('.')[0]

    obj_node.set('regionName', GetUserData(obj, "regionName").replace(" ", "_"))
    obj_node.set('name', obj.GetName().split('.')[1])
    obj_node.set('globalId',  ToIntStr(GetUserData(obj, "globalId")))
    obj_node.set('objectCount', "Not Calculated")
    obj_node.set('spritesContainersCount', "Not Calculated")
    obj_node.set('spriteCount', "Not Calculated")
    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))

    obj_node.set('objectCount', ToIntStr(getChildCount(obj)))
    obj_node.set('spritesContainersCount', "Not Calculated")
    obj_node.set('spriteCount', "Not Calculated")

    print("==============")
    print("BACKGROUND PROCESSED")
    print("==============")

def PreLevelCollision(obj, obj_node):
    ObjectName = obj.GetName().split('.')[0]

    obj_node.set('name', obj.GetName())
    obj_node.set('parentAreaID', ToIntStr(GetUserData(obj, "parentAreaID")))

    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))

    #obj_node.set('physichScale', ToIntStr(GetUserData(obj, "physichScale")))

    print("==============")
    print("LEVEL COLLISION PROCESSED")
    print("==============")

def PreDefineContainer(obj, obj_node):
    global CurrentContainer
    CurrentContainer = obj

    ObjectName = obj.GetName().split('.')[1]

    obj_node.set('name', ObjectName)
    obj_node.set('className', (GetUserData(obj, "className")))

    obj_node.set('group', getGroupByParent(obj))

    obj_node.set('atlas', (GetUserData(obj, "atlas")))
    obj_node.set('blendMode', (GetUserData(obj, "blendMode")))
    obj_node.set('spriteCount', ToIntStr(getChildCount(obj)))

    print("==============")
    print("Container PROCESSED")
    print("==============")

def PreDefineGameSprite(obj, obj_node):
    ObjectName = obj.GetName()

    obj_node.set('name',  ObjectName)
    obj_node.set('group',  ToIntStr(GetUserData(obj, "group")))
    #obj_node.set('parentAreaID',  ToIntStr(GetUserData(obj, "parentAreaID", False)))
    obj_node.set('alpha', str(1))
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

    #print(obj_node)

    obj_node.set('type', GetUserData(obj, "type"))
    obj_node.set('className', GetUserData(obj, "className"))

    #HasOneWayData = HasUserData(CObject, UDName)
    ShapeType =  obj_node.get('type')

    if ShapeType in ["BoxPolygon", "RawPolygon", "RawPolygon"]:
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

    print(obj_node)

    obj_node.set('type', GetUserData(obj, "type"))
    obj_node.set('className', GetUserData(obj, "className"))
    obj_node.set('oneWay',  str(GetUserData(obj, "oneWay")))
    obj_node.set('group',  ToIntStr(GetUserData(obj, "group")))
    obj_node.set('parallax',  str(GetUserData(obj, "parallax")))

    Convert3DMatrixTo2DMatrix(obj, obj_node)

    obj_node.set('height',  str(GetUserData(obj, "height")))
    obj_node.set('width',  str(GetUserData(obj, "width")))

    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))
    obj_node.set('rotation',  str(GetUserData(obj, "rotation")))

    print("==============")
    print("BOX  COLLISION PROCESSED")
    print("==============")

def PreDefineImage(obj, obj_node):
    className = GetUserData(obj, "className", False)

    obj_node.tag = className
    ObjectName = className
    print(obj.GetName(), type(obj))
    obj_node.set('name', ObjectName)

    #print (type(obj).__name__)

    SampleReference = GetUserData(obj, "Sample Reference")
    print(SampleReference)

    #fixing code. Fix objects with wrong/none sample reference
    if SampleReference is None or SampleReference == obj:
        print("Sample Reference is NONE")
        MissingSampleName = obj.GetName()
        MissingSampleName = MissingSampleName.split("_")
        MissingSampleName = MissingSampleName[0] + "_" + MissingSampleName[1] + "_Sample"
        print("Sample Reference Missing Name", MissingSampleName)

        MissingSampleRoot = doc.SearchObject('ImageSamples')
        SampleReference  = search_for_object(MissingSampleName, MissingSampleRoot)
        update_user_data(obj, "Sample Reference", SampleReference)
        if (type(obj).__name__ == "InstanceObject"):
            obj[c4d.INSTANCEOBJECT_LINK] = SampleReference

        print("Sample Reference: ", SampleReference, GetUserData(obj, "Sample Reference"))

    isSample = GetUserData(SampleReference, "IsSpriteSheetSample")
    Texture = GetUserData(SampleReference, "texture")
    Atlas = GetUserData(SampleReference, "Atlas")

    if (isSample == False):
        raise ValueError("Sample Reference is not a SpriteSheetSample", SampleReference)

    #We use the data from the original sample if this is a Instance
    if (type(obj).__name__ == "InstanceObject"):
        obj_node.set('type', "Instance")
    else:
        obj_node.set('type', "Polygon")

    obj_node.set('className', className)

    if className == 'EffectArt':
        obj_node.set('texture', Atlas)
    else:
        obj_node.set('texture', Texture)

    if className == 'LightSprite':
        obj_node.set('radius', str(GetUserData(obj, "radius", False)))

    obj_node.set('atlas', Atlas)

    obj_node.set('transformMode', "normal")

    SetElementTransformWorldSpace(obj, obj_node)

    # Get the vertex map tag by name
    vtag = obj.GetTag(c4d.Tvertexcolor)

    #print('--------------------------------')
    #print('Tag ', vtag)

    # Get the number of fields in the Vertex Color Tag
    fields = vtag[c4d.ID_VERTEXCOLOR_FIELDS]
    fieldsCount = fields.GetCount()
    fieldsRoot = fields.GetLayersRoot()
    ColorField = fieldsRoot.GetFirst()
    AlphaFiels = ColorField.GetNext()

    obj_node.set('alpha', str(AlphaFiels.GetStrength()))
    
    color = ColorField[c4d.FIELDLAYER_COLORIZE_COLORTOP]
    color = rgb_to_uint(color)
    obj_node.set('color', str(color))
    
    obj_node.set('blendMode', (GetUserData(obj, "blendMode", False)))
    #obj_node.set('group', ToIntStr(GetUserData(obj, "group")))

    obj_node.set('skewX', '0')#skew is not supported. we will use vertex offset
    obj_node.set('skewY', '0')#skew is not supported. we will use vertex offset

    if (type(obj).__name__ == "PolygonObject"):
        SetPolygonVertexData(obj, obj_node, SampleReference)

    Convert3DMatrixTo2DMatrix(obj, obj_node)
    print("==============")
    print("IMAGE PROCESSED")
    print("==============")
    
def rgb_to_uint(color):
    r = int(color.x * 255)
    g = int(color.y * 255)
    b = int(color.z * 255)

    return (r << 16) | (g << 8) | b

def BoundsString(x, y, w, h):
    BoundsStr = "(x=" + str(x) + ", " + "y=" + str(y) + ", " + "w=" + str(w) + ", " + "h=" + str(h) + ")"
    return BoundsStr

def PreDefineGameObject(obj, obj_node):
    className = GetUserData(obj, "className", False)

    obj_node.tag = className.split('.')[-1]
    ObjectName = obj.GetName()

    print(obj.GetName(), type(obj))
    obj_node.set('name', ObjectName)

    #print(className)

    #SampleReference = GetUserData(obj, "Sample Reference")

    obj_node.set('className', className)

    SetElementTransformLocalSpace(obj, obj_node)

    obj_node.set("scaleOffsetX", str(1))
    obj_node.set("scaleOffsetY", str(1))

    UserDataValues = get_userdata_values(obj, "GAME PROPERTIES")
    obj_node.set('group', getGroupByParent(obj))

    for name, value in UserDataValues.items():
        if name not in ["name", "width", "height"]:
            #print('UserData', "{}: {}".format(name, value))
            obj_node.set(name, value)

    bounds = defineObjectBounds(obj)

    if bounds is not None:
        if(bounds[0] == "circle"):
            obj_node.set("radius", str(bounds[1]))
            obj_node.set("width", str(bounds[1]))
            obj_node.set("height", str(bounds[1]))
            obj_node.set("shapeType", "Circle")
        else:
            obj_node.set("width", str(bounds[1].x))
            obj_node.set("height", str(bounds[1].y))
            obj_node.set("shapeType", "Box")

    print("==============")
    print("GAME OBJECT PROCESSED")
    print("==============")

def PreDefineCompound(obj, obj_node, indent):
    HasModifiers = has_modifier_child(obj)

    print(obj.GetName(), "Has Modifiers?", HasModifiers)

    #store the parent and the position relative to the parent
    ObjGetMg = obj.GetMg()
    ObjeParent = obj.GetUp()

    if HasModifiers == False:
        CompoundCache = obj.GetCache()
    else:
        # Use SendModelingCommand to create a new object from the current state
        new_object = utils.SendModelingCommand(command=c4d.MCOMMAND_CURRENTSTATETOOBJECT,
                                               list=[obj],
                                               mode=c4d.MODELINGCOMMANDMODE_ALL,
                                               doc=doc)
        if new_object:
            #doc.InsertObject(new_object[0])
            CompoundCache = new_object[0]

            #restore the position in relation to the parent
            CompoundCache.SetMg(ObjGetMg)

            print(f"Newly created object: {CompoundCache.GetName()}")
            VerifyChildsTypes(CompoundCache)

    if CompoundCache:
        print(f"Compound object: {obj.GetName()}")
        print(f"Cache: {CompoundCache.GetName()}")
        parse_objects(CompoundCache, obj_node, ShouldGenerateNode(CompoundCache), indent, True)
    else:
        print("Compound cache not found")

def has_modifier_child(obj):
    child = obj.GetDown()
    while child:
        #print(" Modifier?", child.GetName(), child.GetType(), c4d.Oinstance)
        if child.GetType() in get_known_modifiers():
            return True
        if child.GetDown():  # Check if the current child has any children
            if has_modifier_child(child):  # Recursively check if the child's children have any modifiers
                return True
        child = child.GetNext()
    return False

def VerifyChildsTypes(obj):
    children = obj.GetChildren()
    print(" Compound Child Type?", obj.GetName(), obj.GetType(), c4d.Opolygon, type(obj).__name__)

    # Recursively parse through all children of the current object
    for child in children:
        VerifyChildsTypes(child)

def get_known_modifiers():
    return [
    c4d.Obend, c4d.Otwist, c4d.Otaper, c4d.Oshear, c4d.Obulge, c4d.Oformula, c4d.Ospherify, c4d.Osplinedeformer, c4d.Ocamorph, c4d.Oshrinkwrap, c4d.Ocasurface,
    c4d.Oexplosion, c4d.Omelt, c4d.Oshatter, c4d.Owind, c4d.Oattractor, c4d.Ocasmooth, c4d.Owrap, c4d.Ocacorrection, c4d.Omgsplinewrap
    ]

def defineObjectBounds(obj):
    # Get the bounding box of the object
    BoundObject = getChildByName(obj, "Bounds")

    if BoundObject is None:
        #print("object is None", c4d.Osplinecircle)
        return [None, None]
    elif BoundObject.GetType() == c4d.Osplinecircle:
        #print("object is Circle", BoundObject.GetType())
        return ["circle", BoundObject.GetRad().x]
    elif BoundObject.GetType() == c4d.Osplinerectangle:
        #print("object is box", BoundObject.GetType())
        return ["box", BoundObject.GetRad() * 2]
    else:
        #print("object is Anything", BoundObject.GetType(), BoundObject.GetName())
        return ["box", BoundObject.GetRad() * 2]

def SetElementTransformLocalSpace(obj, obj_node):
    obj_node.set('x', str(obj.GetAbsPos().x))
    obj_node.set('y', str(-obj.GetAbsPos().y))
    obj_node.set('rotation', str(obj[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z]))
    obj_node.set('scaleX', str(obj[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X]))
    obj_node.set('scaleY', str(obj[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y]))

def handle_negative_scale(rotation, scale, originalScale):
    if originalScale.x < 0:
        rotation += math.pi
        scale.x *= -1

    if originalScale.y < 0:
        #rotation += math.pi
        scale.y *= -1

    return rotation, scale

def SetElementTransformWorldSpace(obj, obj_node):
    global AreaRoot
    global CurrentContainer

    # Get world space transform
    global_matrix = obj.GetMg()
    area_root_inv_matrix = ~AreaRoot.GetMg()
    containerInvMatrix = ~CurrentContainer.GetMg()

    # Remove area transformation (added by Sephius Engine in the loading process)
    output_matrix = containerInvMatrix * global_matrix
    #output_matrix = area_root_inv_matrix * output_matrix

    #print("AreaRootTransform", area_root_inv_matrix.off)
    #print("OriginalMatrix", global_matrix.off, global_matrix.v1.GetLength())
    #print("OutputMatrix", output_matrix.off, output_matrix.v1.GetLength())

    # Extract position, rotation, and scale from the matrix
    position = output_matrix.off
    scale = c4d.Vector(
        output_matrix.v1.GetLength(),
        output_matrix.v2.GetLength(),
        output_matrix.v3.GetLength(),
    )
    rotation = c4d.utils.MatrixToHPB(output_matrix).z

    # Handle negative scale
    rotation, scale = handle_negative_scale(rotation, scale, obj[c4d.ID_BASEOBJECT_REL_SCALE])

    # Set object node attributes
    obj_node.set('x', str(position.x))
    obj_node.set('y', str(-position.y))
    obj_node.set('rotation', str(rotation))
    obj_node.set('scaleX', str(scale.x))
    obj_node.set('scaleY', str(scale.y))

def PreDefineBase(obj, obj_node):
    ObjectName = obj.GetName()
    print(obj.GetName(), type(obj))

    obj_node.set('x', str(obj.GetMg().off.x))
    obj_node.set('y',  str(-obj.GetMg().off.y))

#Define if object should generate XML node with information othetwise it will be ignored (beside it's childen will be processes)
def ShouldGenerateNode(obj):
    ObjectID = obj.GetName().split('.')[0]
    Parent = obj.GetUp()

    if Parent:
        ParentID = Parent.GetName().split('.')[0]
    else:
        ParentID = "None"

    if(ObjectID == "LevelArea"):
        return True
    elif(ObjectID == "LevelBackground"):
        return True
    elif(ObjectID == "GameSprite"):
        return True
    elif ObjectID in ["LevelCollision", "DamageCollision"]:
        return True
    elif ObjectID in ["RawCollision", "BoxCollision"]:
        return True
    elif ObjectID in ["BoxShape", "RawShape"]:
         return True
    elif ObjectID in ["AnimationContainer", "SpriteContainer", "QuadBatchContainer"]:
        return True
    elif(ObjectID == "Base"):
        return True
    elif(ObjectID == "Bases"):
        return True


    elif((GetUserData(obj, "IsSpriteSheetSample", False)) == True):
        #print('IsSpriteSheetSample GetType ', obj.GetName(), obj.GetType(), c4d.Oinstance, c4d.Opolygon )
        if(obj.GetType() in [c4d.Oinstance, c4d.Opolygon]):
            if ParentID == "Compound":#Objects that are child of a Compound object should not be processed since we will use the cached result
                return False
            else:
                return True
        else:
            return False


    elif((GetUserData(obj, "IsGameObject", False)) == True):
        return True


    else:
        return False

def PreDefineObjectType(obj, obj_node):
    ObjectID = obj.GetName().split('.')[0]

    if(ObjectID == "LevelArea"):
        PreDefineLevelArea(obj, obj_node)
    elif ObjectID in ["LevelCollision", "DamageCollision"]:
        PreLevelCollision(obj, obj_node)
    elif(ObjectID == "BoxShape"):
        PreDefineBoxCollision(obj, obj_node)
    elif(ObjectID == "RawShape"):
        PreDefineRawCollision(obj, obj_node)
    elif(ObjectID == "GameSprite"):
        PreDefineGameSprite(obj, obj_node)
    elif ObjectID in ["AnimationContainer", "SpriteContainer", "QuadBatchContainer"]:
        PreDefineContainer(obj, obj_node)
    elif(ObjectID == "LevelBackground"):
        PreDefineLevelBackground(obj, obj_node)
    elif(ObjectID == "Base"):
        PreDefineBase(obj, obj_node)

    #Special Type of Objects composed by Clonners and other special techniques
    elif(ObjectID == "Compound"):
        PreDefineCompound(obj, obj_node)

    #Images inside containers
    elif((GetUserData(obj, "IsSpriteSheetSample", False)) == True):
        PreDefineImage(obj, obj_node)
    elif((GetUserData(obj, "IsGameObject", False)) == True):
        PreDefineGameObject(obj, obj_node)


def parse_objects(obj, parent_node, GenerateNode, indent=0, Cached=False):

    #This function recursively parses through all children of the given object
    #and creates an XML describing their position, rotation, scale, and any user data.

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

    elif ObjectID == "Compound" and Cached == False:# Process compound objects
        print("Compound Object Detected")
        PassNode = parent_node;
        PreDefineCompound(obj, PassNode, indent)

    else:
        PassNode = parent_node;

    if(GenerateNode):
        NextIdent = indent+2
    else:
        NextIdent = indent

    if ObjectID not in ["Compound"] or  Cached == True:
        # Invert the order of the children list
        children = obj.GetChildren()[::-1]
        # Recursively parse through all children of the current object
        for child in children:
            parse_objects(child, PassNode, ShouldGenerateNode(child), NextIdent, Cached)

    if(GenerateNode):
        # Add line breaks and indentation to the closing XML string
        parent_node.text = '\n' + ' ' * indent
        PassNode.tail = '\n' + ' ' * indent

def main():
    # Get the active object in the scene
    obj = doc.GetActiveObject()

    #stop if root object is not a site
    if obj.GetName().split('.')[0] not in ("LevelSite", "LevelBackgrounds"):
        raise ValueError("OBJECT SELECTED IS NOT A VALID SITE OR BACKGROUNDS")

    global LevelSite
    LevelSite = obj

    Root = get_top_parent(obj)
    RegionName = Root.GetName().replace(" ", "")

    if obj.GetName().split('.')[0] in ("LevelSite"):
        Name =  'Site' + obj.GetName().split('.')[1].replace(" ", "")

        XMLFileName = RegionName + '_' + Name + '.xml'
        print ('XML File Name' + XMLFileName)

        # Create a new XML tree and root node
        root = ET.Element('LevelSite')
        root.set('regionName', GetUserData(obj, "regionName").replace(" ", "_"))
        root.set('siteName', obj.GetName().split('.')[1])
        root.set('siteID', str(int(GetUserData(obj,  "siteID"))))

        now = datetime.now()
        date_string = now.strftime("%Y-%m-%d %H:%M:%S")
        VersionString = "C4D_" + date_string
        root.set('Version', VersionString)

    # Parse through all children of the active object
    parse_objects(obj, root, False, 2)
    print("Fnished Pa")
    # Write the XML tree to a file
    tree = ET.ElementTree(root)
    tree.write(XMLFileName, encoding='utf-8', xml_declaration=False)
    print("Done!!!!")

if __name__=='__main__':
    main()