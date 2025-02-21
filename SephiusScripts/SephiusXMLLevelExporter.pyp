import c4d # type: ignore
import xml.etree.ElementTree as ET
import math
from c4d import DescID, Vector, Matrix, utils # type: ignore
from datetime import datetime
import random
import time
from datetime import datetime
from c4d import plugins, bitmaps # type: ignore
import os

PLUGIN_ID = 2242900

class SephiusXMLLevelExporter(plugins.CommandData):
    def Execute(self, doc):
        # Coloque aqui o código que seu script deve executar
        main(doc)
        # c4d.gui.MessageDialog("Exportador de Níveis XML Sephius Executado")
        return True

    def GetState(self, doc):
        # Retorna o estado do comando
        return c4d.CMD_ENABLED

globalIDs = {}
def verifyGlobalIDs(object, ID):
    global globalIDs
    for key in globalIDs:
        if key != "None" and key == ID:
            c4d.gui.MessageDialog("Duplicated GlobalID:" + ID + " Object: " + object.GetName() + " Please regenerate the ID for the NEWER object. Caution to NOT change ID for OLDER object since this can break game's save data")  # Isso vai imprimir o código de erro
        return False
    else:
        globalIDs[ID] = 1
        True

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
    icon_path = os.path.join(dir_path, "SephiusXMLLevelExporter.tif")
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
    c4d.plugins.RegisterCommandPlugin(id=PLUGIN_ID, str="Sephius XML Level Exporter",
                                      info=0, icon=icon, help="Export levels to XML format",
                                      dat=SephiusXMLLevelExporter())
    

# def createUserData(obj, paramName, dataType, value):
    #Add UserData storing
    # Cbc = c4d.GetCustomDataTypeDefault(dataType) # Create Group
    # Cbc[c4d.DESC_NAME] = paramName
    # Cbc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    #print("Has Group ? ", userDataGroup)
    # if userDataGroup:
        # Cbc[c4d.DESC_PARENTGROUP] = userDataGroup
    # Celement = obj.AddUserData(Cbc)
    # obj[Celement] = value

total_digits = 0

def generate_number(dtotal_digits):
    global total_digits
    total_digits = int(dtotal_digits)

    # Get current date and time
    now = datetime.now()

    # Convert to a string with format: day + month + year + hour + minute + second
    timestamp_str = now.strftime("%d/%m/%Y-%H:%M:%S")  # This will be 14 characters long


    # Calculate how many random digits we need to add
    remaining_digits = total_digits - len(timestamp_str)

    # Generate a random number with the remaining number of digits
    random.seed()
    random_number = random.randint(0, 100000)

    # Combine the timestamp and random number to get a 20-digit number
    #final_number = int(timestamp_str + "-" + str(random_number))
    
    return timestamp_str + "-" + str(random_number)



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

def search_for_object_withPrefix(Prefix, obj):
    """
    Search for a child object with a specific prefix name.
    :param name: the name of the object to search for.
    :param obj: the current object in the hierarchy.
    :return: the object if found, else None.
    """
    while obj:
        #print(Prefix, obj.GetName())
        if obj.GetName().split('.')[0] in (Prefix):
            return obj

        obj = obj.GetNext()

    raise ValueError("No Valid Level Site exist. We expect a null wth name 'LevelSite.[SiteName]'")
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
    #print('updating user data')
    for id, bc in data:
        if bc[c4d.DESC_NAME] == param_name:
            #print(bc[c4d.DESC_NAME], param_name, value)
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

    #print('parameter_data', parameter_data)

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

def get_user_data_tag(obj):
    # Percorre as tags do objeto ativo para encontrar a tag de User Data
    for tag in obj.GetTags():
        if tag.GetType() == c4d.Tuserdata:
            return tag
    return None

def get_user_data_tags(obj):
    user_data_tags = {}
    # Get all user data tags to retrive it's data. Ignore if expose to object is false
    for tag in obj.GetTags():
        if tag.GetType() == c4d.Tuserdata and tag[c4d.ID_EXPOSETAB] and tag.GetName() != "OBJECT EXPORT INFO":
            user_data_tags[tag.GetName()] = tag

    return user_data_tags

user_data_map = {}
def build_user_data_map(obj, groups):
    # Get the User Data tags from the object
    tags = get_user_data_tags(obj)
    userDataOwners = {}

    if not tags:
        # If there is no User Data tag, the object itself is the owner of the User Data
        userDataOwners[obj.GetName()] = obj
        usingDataTags = False
        #print("userDataOwners is main object", "obj: ", obj.GetName())	
    else:
        userDataOwners = tags
        #print("userDataOwners is Tags: ", userDataOwners, "obj: ", obj.GetName())	
        # If object is using User Data tag, ignore group filtering
        groups = []
        usingDataTags = True

    global user_data_map
    user_data_map = {}
    
    # Iterate through objects that have User Data
    for ownerName in userDataOwners:
        #print("userDataOnwer: ", ownerName)
        # Get the User Data from the tag
        userDataOnwer = userDataOwners[ownerName]
        user_data = userDataOnwer.GetUserDataContainer()

        current_group_name = None
            
        # Iterate through the User Data to build the mapping
        for desc_id, data in user_data:
            parameter_name = data[c4d.DESC_NAME]
            #print("parameter_name: ", parameter_name, "desc_id", desc_id, type(data))
            #print("desc_id[0].dtype", desc_id[1].dtype, c4d.DTYPE_GROUP, c4d.DTYPE_SUBCONTAINER)
            # Check if the desc_id represents a group
            if desc_id[1].dtype in [c4d.DTYPE_GROUP, c4d.DTYPE_SUBCONTAINER]:
                current_group_name = parameter_name
                print(f"{parameter_name} is a group, it will not be mapped.")
                continue
            
            # Check if the parameter belongs to the specified groups (in case it not using user data tags)
            if(not usingDataTags and groups and current_group_name not in groups):
                print(f"{parameter_name} is not present in one of the specified groups { groups }, it will not be mapped. Current group: { current_group_name }")
                continue
                    
            # Access the value of the parameter using the complete desc_id structure
            #print("desc_id[1].dtype: ", desc_id[1].dtype)

            if desc_id[1].dtype in [c4d.DTYPE_BOOL, c4d.CUSTOMGUI_BOOL, c4d.ID_GV_DATA_TYPE_BOOL, c4d.MD_BOOL, c4d.MD_TYPE_MD_BOOL]:   
                parameter_value = userDataOnwer[desc_id]
                if parameter_value == 1:
                    parameter_value = "true"
                else:   
                    parameter_value = "false"
            else:
                parameter_value = userDataOnwer[desc_id]

            #print("parameter_value: ", parameter_value)
            
            user_data_map[parameter_name] = {"paramName":parameter_name, "paramValue": parameter_value, "group": current_group_name, "dataOwner": userDataOnwer}
            #print("")
    
    return user_data_map


def get_user_data_value(parameter_name):
    global user_data_map

    # Verifica se o parâmetro existe no mapeamento e retorna seu valor
    if parameter_name in user_data_map:
        return user_data_map[parameter_name]["value"]
    return None

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

    #Print the minimum and maximum height and width values
    return [min_width, max_width, min_height, max_height]

def SetPolygonVertexData(PolygonObject, node, SampleReference):
    isPolygon = type(SampleReference) is c4d.PolygonObject

    #print("Reference Is Polygon? ", SampleReference.GetName(), " type: ", type(SampleReference), " ", isPolygon)

    if isPolygon:
        Refpolygon_count = SampleReference.GetPolygonCount()
        #if Refpolygon_count > 1:
            #print("Polygon:", SampleReference.GetName(), "Sample Reference has more than 1 polygon. This mean it is a wrong ref (not a ref sample) and it's not supported. Poly count:", Refpolygon_count)
    else:
        print("Provided object is not a polygon object ", PolygonObject)


    #print(type(PolygonObject), type(PolygonObject) is c4d.PolygonObject)

    if PolygonObject is not None and isPolygon:
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

        # Get the U and V components of the vertex's UV coordinates for ref sample
        uvwRef = Refuv_tag.GetSlow(0)
        REFuvPoints = [uvwRef["b"], uvwRef["a"], uvwRef["c"], uvwRef["d"]]
        #print (' REPoints ', REFuvPoints)

        node.set('PolyCount', str(polygon_count))

        uTooBig = False
        vTooBig = False

        # Loop through each polygon and get the UV coordinates for its vertices
        for i in range(polygon_count):
            #verify on the second polygon if there is something wrong with the uvs
            #Cinema 4D has a bug related with uvs and cache which makes uvs coming with wrong values.
            #This is a workaround to fix it.
            #If UV is is greater than reference max ir should be divided by number of polygons (crazy but...)
            if(polygon_count > 1 and i==0):
                uvw = uv_tag.GetSlow(i+1)
                uvPoints = [uvw["b"], uvw["a"], uvw["c"], uvw["d"]]
                nextUVpoint = uvPoints[0]

                Range = MaxAndMinCoord(REFuvPoints)
                
                uMin = Range[0]
                uMax = Range[1]
                vMin = Range[2]
                vMax = Range[3]

                u = nextUVpoint.x
                v = nextUVpoint.y

                if(u > uMax):
                    uTooBig = True
                if(v > vMax):
                    vTooBig = True

            #print("---------------------------------------------")
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
            Range = MaxAndMinCoord(REFuvPoints)
            
            uMin = Range[0]
            uMax = Range[1]
            vMin = Range[2]
            vMax = Range[3]

            #print("uMin", uMin, "uMax", uMax, "vMin", vMin, "vMax", vMax)

            for j in range(4):

                # Get the vertex sindex for the current vertex of the polygon
                point = PolygonObject.GetPoint(pointsIndx[j])
                x = point.x
                y = -point.y

                # Get the U and V components of the vertex's UV coordinates
                UVpoint = uvPoints[j]
                u = UVpoint.x
                v = UVpoint.y

                #remap uv to be proportional to reference sample. In SephiusEngine, we acess the sub texture which has values from 0 to 1.
                #print("u", u, "v", v)
                u = remap(u, uMin, uMax)
                v = remap(v, vMin, vMax)
                #print("u Remaped", u, "v Rempaed", v)

                if(uTooBig):
                    u = u / polygon_count
                if(vTooBig):
                    v = v / polygon_count   

                # Add the U and V components to the vertex UV coordinates string
                vertex_uvs += "{},{},".format(u, v)
                vertex_positions += "{},{},".format(x, y)

            # Remove the last comma from the strings

            vertex_uvs = vertex_uvs[:-1]
            #vertex_uvs = "0,0,1,0,0,1,1,1"
            #vertex_uvs = "1,1,0,1,1,0,0,0"
            vertex_positions = vertex_positions[:-1]

            #Print the UV coordinates
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
            #print("---------------------------------------------")
            #print("Polygon:", PolygonObject.GetName(), "Processed")
    else:
       print("Provided object is not a polygon object ", PolygonObject)

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
       raise ValueError("Provided object is not a spline ")

def GetSplinePointsPositions(SplineObject):
    if SplineObject is not None and type(SplineObject)is c4d.SplineObject:
        # Get the number of points on the spline
        point_count = SplineObject.GetPointCount()

        PointsLocationsSrt = ""

        # Iterate over each point and get its location
        for i in range(point_count):
            #print(i, SplineObject.GetPoint(i))
            point_location = SplineObject.GetPoint(i)

            if i < point_count - 1:
                Divisior = ','
            else:
                Divisior= ''

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

    node.set('matrixTx', str(obj.GetRelPos().x))#???? Used for level collisions
    node.set('matrixTy', str(-obj.GetRelPos().y))#??? Used for level collisions

#Return value for a user data by name
def GetUserData(obj, UDName, stopIfNone=True):
    if(stopIfNone == True):
        if(obj is None):
            raise ValueError("Object is None")
        if(UDName is None):
            raise ValueError(UDName, "is None")
    
    #print("obj: ", obj, obj.GetName())
    
    for id, bc in obj.GetUserDataContainer():
        # Print debug information about the user data
        #print("UserData Name: ", bc[c4d.DESC_NAME])
        #print("Parameter ID: ", id)
        
        #print("bc[c4d.DESC_NAME: ", bc[c4d.DESC_NAME])
        #obj[id]
        #print("obj[id]: ", obj[id])
        #obID = obj[id]
        if bc[c4d.DESC_NAME] == UDName:
            try:
                return obj[id]
            except AttributeError as e:
                #print(f"AttributeError: {e}")
                print(f"Failed to access parameter with ID {id} on object {obj.GetName()}")
                raise AttributeError(UDName, f"AttributeError: {e}")

    return "None"

def ToIntStr(value):
    return str(int(value))

def getChildByName(obj, name, halt=True):
    """
    This function gets the child of the given object with the specified name.
    """
    child = obj.GetDown()
    while child is not None:
        if child.GetName() == name:
            return child
        child = child.GetNext()
    if halt:
        raise ValueError("Object Has no Child With The Name Provided", name)
    return None

LocalID = -1
def PreDefineLevelArea(obj, obj_node, doc):
    global AreaRoot  
    global LocalID

    print("LocalID: " + str(LocalID))
    
    AreaRoot = obj
    print("AreaRoot", AreaRoot.GetName())

    ObjectName = obj.GetName().split('.')[0]
    GlobalID = ToIntStr(obj.GetName().split('.')[1])
    LocalID = LocalID + 1

    obj_node.set('regionName', GetUserData(obj, "regionName").replace(" ", "_"))
    obj_node.set('globalId',  GlobalID)
    obj_node.set('localId',  str(LocalID))
    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))

    BoundName = "Bounds." + obj.GetName()
    BoundName = BoundName.split('.')[0] + "." + BoundName.split('.')[1]

    # Get the bounding box of the object
    BoundObject = getChildByName(obj, BoundName)

    if(BoundObject is None):
        raise ValueError("No Bounds Found for ", BoundName)

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
    print("AREA PROCESSED", obj.GetName())
    print("==============")

def PreDefineLevelBackground(obj, obj_node, doc):
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
    print("BACKGROUND PROCESSED", obj.GetName())
    print("==============")

def PreLevelCollision(obj, obj_node, doc):
    ObjectName = obj.GetName().split('.')[0]

    obj_node.set('name', obj.GetName())
    obj_node.set('parentAreaID', ToIntStr(GetUserData(obj, "parentAreaID")))

    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))

    #obj_node.set('physichScale', ToIntStr(GetUserData(obj, "physichScale")))

    print("==============")
    print("LEVEL COLLISION PROCESSED", obj.GetName())
    print("==============")

def PreDefineContainer(obj, obj_node, doc):
    global CurrentContainer
    CurrentContainer = obj

    ObjectName = obj.GetName().split('.')[1]

    obj_node.set('name', ObjectName)
    obj_node.set('className', (GetUserData(obj, "className")))

    #obj_node.set('group', getGroupByParent(obj))

    obj_node.set('atlas', (GetUserData(obj, "atlas")))
    obj_node.set('blendMode', (GetUserData(obj, "blendMode")))
    obj_node.set('spriteCount', ToIntStr(getChildCount(obj)))

    print("==============")
    print("Container PROCESSED", obj.GetName())
    print("==============")

def PreDefineGameSprite(obj, obj_node, doc):
    ObjectName = obj.GetName()

    obj_node.set('name',  ObjectName)
    obj_node.set('group',  str(getGroupByParent(obj)))

    #obj_node.set('parentAreaID',  ToIntStr(GetUserData(obj, "parentAreaID", False)))
    obj_node.set('alpha', str(1))
    obj_node.set('blendMode',  str(GetUserData(obj, "blendMode")))

    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))

    Group = obj.GetUp()
    scaleOffsetX = 1/Group[c4d.ID_BASEOBJECT_FROZEN_SCALE,c4d.VECTOR_X]
    scaleOffsetY = 1/Group[c4d.ID_BASEOBJECT_FROZEN_SCALE,c4d.VECTOR_Y]

    obj_node.set('scaleOffsetX',  str(1))#Should be decided by game system
    obj_node.set('scaleOffsetY',  str(1))#Should be decided by game system

    parallax = GetUserData(obj, "parallax")

    # Certifique-se de que 'parallax' é tratado corretamente como inteiro ou None
    if parallax is None or parallax == -1 or str(parallax) == "None" or str(parallax) == "-1":
        print("Parallax should be calculated", parallax)
        parallax = str(findParallax(obj))  # Converte para string apenas depois

    print("Parallax UserData: ", str(GetUserData(obj, "parallax")), "Calculated Parallax: ", parallax)

    obj_node.set('parallax',  str(parallax))
    #obj_node.set('parallax',  str(GetUserData(obj, "parallax")))

    print("==============")
    print("GAME SPRITE PROCESSED", obj.GetName())
    print("==============")

def findParallax(obj):
    Group = obj.GetUp()
    distance = Group[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] + 1920

    if distance == 0:
        parallax = 1
    else:
        parallax = (1/distance) * 1920

    parallax = int(parallax * 1000) / 1000

    return parallax

def PreDefineRawCollision(obj, obj_node, doc):
    ObjectName = obj.GetName().split('.')[0]

    #print(obj_node)
    obj_node.set('name', obj.GetName())
    obj_node.set('type', GetUserData(obj, "type"))
    obj_node.set('className', GetUserData(obj, "className"))

    #HasOneWayData = HasUserData(CObject, UDName)
    ShapeType =  obj_node.get('type')

    if ShapeType in ["BoxPolygon", "RawPolygon", "RawPolygon"]:
        obj_node.set('oneWay',  str(GetUserData(obj, "oneWay")))
        obj_node.set('group',  ToIntStr(GetUserData(obj, "group")))
        #obj_node.set('parallax',  str(GetUserData(obj, "parallax")))

    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))
    obj_node.set('rotation',  str(obj[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z]))
    obj_node.set('points',  GetSplinePointsPositions(obj))

    #print("==============")
    #print("Raw COLLISION PROCESSED", obj.GetName())
    #print("==============")

def PreDefineBoxCollision(obj, obj_node, doc):
    ObjectName = obj.GetName().split('.')[0]

    #print(obj_node)
    obj_node.set('name', obj.GetName())
    obj_node.set('type', GetUserData(obj, "type"))
    obj_node.set('className', GetUserData(obj, "className"))
    obj_node.set('oneWay',  str(GetUserData(obj, "oneWay")))
    obj_node.set('group',  ToIntStr(GetUserData(obj, "group")))
    #obj_node.set('parallax',  str(GetUserData(obj, "parallax")))

    Convert3DMatrixTo2DMatrix(obj, obj_node)

    obj_node.set('width',  str(obj[c4d.PRIM_RECTANGLE_WIDTH]))
    obj_node.set('height',  str(obj[c4d.PRIM_RECTANGLE_HEIGHT]))

    obj_node.set('x',  str(obj.GetAbsPos().x))
    obj_node.set('y',  str(-obj.GetAbsPos().y))
    obj_node.set('rotation',  str(obj[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z]))

    #print("==============")
    #print("BOX  COLLISION PROCESSED")
    #print("==============")

def PreDefineImage(obj, obj_node, doc):
    objCache = obj.GetCache()

    SampleReference = GetUserData(obj, "Sample Reference")
    #print(SampleReference)

    #fixing code. Fix objects with wrong/none sample reference
    if SampleReference is None or SampleReference == obj:
        print("Sample Reference is NONE", " Trying to get it")
        MissingSampleName = obj.GetName()
        MissingSampleName = MissingSampleName.split("_")
        MissingSampleName = MissingSampleName[0] + "_" + MissingSampleName[1] + "_Sample"
        print("Sample Reference Missing Name: ", MissingSampleName)

        #global doc 
        #update_doc()   
            
        MissingSampleRoot = doc.SearchObject('SiteSamples')

        if MissingSampleRoot is None:
            raise ValueError("MissingSampleRoot is NONE ", MissingSampleName, " Samples root should have this name")

        SampleReference  = search_for_object(MissingSampleName, MissingSampleRoot)
        update_user_data(obj, "Sample Reference", SampleReference)

        if (type(obj).__name__ == "InstanceObject"):
            obj[c4d.INSTANCEOBJECT_LINK] = SampleReference

        #print("Sample Reference: ", SampleReference, GetUserData(obj, "Sample Reference"))

    if SampleReference is None:
        raise ValueError(obj.GetName(), "SampleReference is still NONE")

    if HasUserData(obj, "className"):
        className = GetUserData(obj, "className", False)
    else:
        className = GetUserData(SampleReference, "className", False)

    obj_node.tag = className
    ObjectName = className
    #print(obj.GetName(), type(obj))
    #obj_node.set('name', ObjectName)

    #print (type(obj).__name__)

    isSample = GetUserData(SampleReference, "IsSpriteSheetSample")
    Texture = GetUserData(SampleReference, "texture")
    Atlas = GetUserData(SampleReference, "Atlas")

    if (isSample == False):
        raise ValueError("Sample Reference is not a SpriteSheetSample", SampleReference)

    #We use the data from the original sample if this is a Instance
    if (type(obj).__name__ == "InstanceObject"):
        #print("InstanceObject", obj.GetName())
        obj_node.set('type', "Instance")
    else:
        #print("ImageObject", obj.GetName())
        obj_node.set('type', "Polygon")

    obj_node.set('className', className)
    obj_node.set('Name', obj.GetName())

    if className == 'EffectArt':
        obj_node.set('texture', Atlas)
    else:
        obj_node.set('texture', Texture)

    if className == 'LightSprite':
        obj_node.set('radius', str(GetUserData(obj, "radius", False)))

        if GetUserData(obj, "castShadow", False) == 0:
            castShadow = "false"
        else:
            castShadow = "true"

        obj_node.set('castShadow', castShadow)

    obj_node.set('atlas', Atlas)

    obj_node.set('transformMode', "normal")

    SetElementTransformWorldSpace(obj, obj_node)
    
    #DO NOT remove print bellow. 
    #Script can result in error due strange behavior of cinema 4D (garbage collection?)
    print("ObjectName", obj.GetName(), " objCache", objCache, "Alive?", obj.IsAlive())

    # Get the vertex map tag by name
    if(objCache is not None):
        vtag = objCache.GetTag(c4d.Tvertexcolor)
    else:
        vtag = obj.GetTag(c4d.Tvertexcolor)

    #print('--------------------------------')
    #print('Tag ', vtag)

    if (vtag):
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
    else:
        obj_node.set('alpha', str(1))
        color = rgb_to_uint(c4d.Vector(1, 1, 1))
        obj_node.set('color', str(color))

    blendMode = GetUserData(obj, "blendMode", False)
    if(blendMode == "None"):
        blendMode = "normal"
    obj_node.set('blendMode', blendMode)

    obj_node.set('skewX', '0')#skew is not supported. we will use vertex offset
    obj_node.set('skewY', '0')#skew is not supported. we will use vertex offset

    if (type(obj).__name__ == "PolygonObject"):
        SetPolygonVertexData(obj, obj_node, SampleReference)

    Convert3DMatrixTo2DMatrix(obj, obj_node)
    #print("==============")
    #print("IMAGE PROCESSED")
    #print("==============")

def rgb_to_uint(color):
    r = int(color.x * 255)
    g = int(color.y * 255)
    b = int(color.z * 255)

    return (r << 16) | (g << 8) | b

def BoundsString(x, y, w, h):
    BoundsStr = "(x=" + str(x) + ", " + "y=" + str(y) + ", " + "w=" + str(w) + ", " + "h=" + str(h) + ")"
    return BoundsStr

def PreDefineGameObject(obj, obj_node, doc):
    print("==============")
    print("Object Name: ", obj.GetName())
    UserDataValues = build_user_data_map(obj, ["GAME PROPERTIES"])
    
    if "globalID" in UserDataValues:
        className = UserDataValues["className"]["paramValue"]
    else:
        className = GetUserData(obj, "className")

    print("GameObject Class: ", className)

    obj_node.tag = className.split('.')[-1]
    ObjectName = obj.GetName()

    obj_node.set('name', ObjectName)

    global total_digits

    if "globalID" in UserDataValues:
        globalID = UserDataValues["globalID"]["paramValue"]
    else:
        globalID = "None"#ignore id if there no parameter with this name

    print("GlobalID: ", globalID, "Object Name: ", obj.GetName())
    if globalID is None or globalID == "":
        globalID = str(generate_number(total_digits))
        update_user_data(UserDataValues["globalID"]["dataOwner"], "globalID", globalID)

    verifyGlobalIDs(obj, globalID)
    
    SetElementTransformLocalSpace(obj, obj_node)

    obj_node.set("scaleOffsetX", str(1))#??
    obj_node.set("scaleOffsetY", str(1))#??

    obj_node.set('group', str(getGroupByParent(obj)))
 
    for name, value in UserDataValues.items():
        if name not in ["name", "width", "height"]:
            obj_node.set(name, str(value["paramValue"]))
            print('Game Object UserData ', "{}: {}".format(name, value))
            
    bounds = defineObjectBounds(obj)

    if bounds[1] is not None:
        if(bounds[0] == "circle"):
            obj_node.set("radius", str(bounds[1]))
            obj_node.set("width", str(bounds[1]))
            obj_node.set("height", str(bounds[1]))
            obj_node.set("shapeType", "Circle")
        else:
            obj_node.set("width", str(bounds[1].x))
            obj_node.set("height", str(bounds[1].y))
            obj_node.set("shapeType", "Box")
    
    # Get the vertex map tag by name
    if(obj is not None):
        vtag = obj.GetTag(c4d.Tvertexcolor)

    #print('--------------------------------')
    #print('Tag ', vtag)
    
    #Get Alpha and Color from vertex color tag
    if (vtag):
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
    else:
        obj_node.set('alpha', str(1))
        color = rgb_to_uint(c4d.Vector(1, 1, 1))
        obj_node.set('color', str(color))

    print("==============")
    print("GAME OBJECT PROCESSED")
    print("==============")

def PreDefineCompound(obj, obj_node, indent, doc):
    HasModifiers = has_modifier_child(obj)

    #print(obj.GetName(), "Has Modifiers?", HasModifiers)

    #store the parent and the position relative to the parent
    ObjGetMg = obj.GetMg()
    ObjeParent = obj.GetUp()

    obj.Message(c4d.MSG_UPDATE)
    
    if HasModifiers == False:
        CompoundCache = obj.GetCache()#caution with this. Can create problems with garbage collection
    else:
        # Use SendModelingCommand to create a new object from the current state
        new_object = utils.SendModelingCommand(command=c4d.MCOMMAND_CURRENTSTATETOOBJECT,
                                               list=[obj],
                                               mode=c4d.MODELINGCOMMANDMODE_ALL,
                                               doc=doc)
        if new_object:
            #global doc 
            #update_doc()
            #doc.InsertObject(new_object[0])
            CompoundCache = new_object[0]
            CompoundCache.Message(c4d.MSG_UPDATE)
            #restore the position in relation to the parent
            CompoundCache.SetMg(ObjGetMg)

            #print(f"Newly created object: {CompoundCache.GetName()}")
            VerifyChildsTypes(CompoundCache)

    if CompoundCache:
        #print(f"Compound object: {obj.GetName()}")
        #print(f"Cache: {CompoundCache.GetName()}")
        parse_objects(CompoundCache, obj_node, ShouldGenerateNode(CompoundCache), doc, indent, True)
    #else:
        #print("Compound cache not found")

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
    #print(" Compound Child Type?", obj.GetName(), obj.GetType(), c4d.Opolygon, type(obj).__name__)

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
    BoundObject = getChildByName(obj, "Bounds", False)

    if BoundObject is None:
       #print("object is None")
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
    rotation = obj[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z]
    rotation = str(math.degrees(rotation))

    obj_node.set('rotation', rotation)

    #for this cases we can't have negative scales'
    scaleX = (obj[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X])
    scaleY = (obj[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y])

    if scaleX < 0:
        obj_node.set('inverted', "true")

    obj_node.set('scaleX', str(abs(scaleX)))
    obj_node.set('scaleY', str(abs(scaleY)))

def handle_negative_scale(rotation, scale, originalScale):
    # Handle negative scale when both x and y are negative
    if (originalScale.x < 0 and originalScale.y < 0):
        rotation += math.pi
        scale.x *= -1
        scale.y *= -1

    # Handle negative scale when only x is negative
    if originalScale.x < 0:
        rotation += math.pi
        scale.x *= -1
        
    # Handle negative scale when only y is negative
    if originalScale.y < 0:
        rotation += math.pi
        #scale.y *= 1
        scale.x *= -1

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

def PreDefineBase(obj, obj_node, doc):
    ObjectName = obj.GetName()
    #print(obj.GetName(), type(obj))

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

def PreDefineObjectType(obj, obj_node, doc, indent):
    ObjectID = obj.GetName().split('.')[0]

    if(ObjectID == "LevelArea"):
        PreDefineLevelArea(obj, obj_node, doc)
    elif ObjectID in ["LevelCollision", "DamageCollision"]:
        PreLevelCollision(obj, obj_node, doc)
    elif(ObjectID == "BoxShape"):
        PreDefineBoxCollision(obj, obj_node, doc)
    elif(ObjectID == "RawShape"):
        PreDefineRawCollision(obj, obj_node, doc)
    elif(ObjectID == "GameSprite"):
        PreDefineGameSprite(obj, obj_node, doc)
    elif ObjectID in ["AnimationContainer", "SpriteContainer", "QuadBatchContainer"]:
        PreDefineContainer(obj, obj_node, doc)
    elif(ObjectID == "LevelBackground"):
        PreDefineLevelBackground(obj, obj_node, doc)
    elif(ObjectID == "Base"):
        PreDefineBase(obj, obj_node, doc)

    #Special Type of Objects composed by Clonners and other special techniques
    elif(ObjectID == "Compound"):
        PreDefineCompound(obj, obj_node, indent, doc)
    else:
        HasSSSUserData = HasUserData(obj, "IsSpriteSheetSample")
        HasIGOUserData = HasUserData(obj, "IsGameObject")
        IsSpriteSheetSample = False
        IsGameObject = False

        #Test both object user data and user data tags
        if HasSSSUserData:
            IsSpriteSheetSample = GetUserData(obj, "IsSpriteSheetSample", False) == True
        elif HasIGOUserData:
            IsGameObject = GetUserData(obj, "IsGameObject", False) == True
        else:
            UserDataValues = build_user_data_map(obj, ["GAME PROPERTIES"])
            if "IsSpriteSheetSample" in UserDataValues:
                IsSpriteSheetSample = UserDataValues["IsSpriteSheetSample"] == True
            elif "IsGameObject" in UserDataValues:
                IsGameObject = UserDataValues["IsGameObject"] == True

        #Images inside containers
        if IsSpriteSheetSample:
            PreDefineImage(obj, obj_node, doc)
        #Game Objects
        elif IsGameObject:
            PreDefineGameObject(obj, obj_node, doc)


def parse_objects(obj, parent_node, GenerateNode, doc, indent=0, Cached=False):

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
        PreDefineObjectType(obj, PassNode, doc, indent)

    elif ObjectID == "Compound" and Cached == False:# Process compound objects
        #print("Compound Object Detected")
        PassNode = parent_node;
        obj.Message(c4d.MSG_UPDATE)  # Send an update message to the object
        PreDefineCompound(obj, PassNode, indent, doc)

    else:
        PassNode = parent_node;

    if(GenerateNode):
        NextIdent = indent+2
    else:
        NextIdent = indent

    if ObjectID not in ["Compound"] or  Cached == True:
        # Invert the order of the children list
        #print("Processing Children of ", obj)
        #print("Processing Children of ", obj.GetName())
        #print("Testing Child alive ", obj.IsAlive())#removing this could make script crash for some unknown reason reaon (garbage collection?)
        #print("Testing Child retrive ", obj.GetDown())
        children = obj.GetChildren()[::-1]
        # Recursively parse through all children of the current object
        for child in children:
            parse_objects(child, PassNode, ShouldGenerateNode(child), doc, NextIdent, Cached)

    if(GenerateNode):
        # Add line breaks and indentation to the closing XML string
        parent_node.text = '\n' + ' ' * indent
        PassNode.tail = '\n' + ' ' * indent

def process_level_site(obj, save_path, doc):
    """
    Processa um objeto LevelSite e salva em um arquivo XML separado.
    """
    if obj is not None:
        region_name = obj.GetUp().GetName().replace(" ", "")
        siteName = obj.GetName().split('.')[1].replace(" ", "")
        xml_file_name = os.path.join(save_path, f"{region_name}_Site{siteName}.xml")
        
        root = ET.Element('LevelSite')
        root.set('regionName', GetUserData(obj, "regionName").replace(" ", "_"))
        root.set('siteName', siteName)
        root.set('siteID', str(int(GetUserData(obj, "siteID"))))
        
        now = datetime.now()
        date_string = now.strftime("%Y-%m-%d %H:%M:%S")
        version_string = "C4D_" + date_string
        root.set('Version', version_string)
        
        parse_objects(obj, root, False, doc, 2)
        
        tree = ET.ElementTree(root)
        tree.write(xml_file_name, encoding='utf-8', xml_declaration=False)
        print(f"Exportação concluída! Arquivo salvo: {xml_file_name}")

def process_level_background(obj, save_path, doc):
    """
    Processa um objeto LevelBackground e salva em um arquivo XML separado.
    """
    if obj is not None:
        region_name = obj.GetUp().GetName().replace(" ", "")
        bgID = obj.GetName().split('.')[1].replace(" ", "")
        bgName = obj.GetName().split('.')[2]
        xml_file_name = os.path.join(save_path, f"{region_name}_BG{bgID}.xml")
        
        root = ET.Element('LevelBackground')
        root.set('regionName', GetUserData(obj, "regionName").replace(" ", "_"))
        root.set('name', bgName)
        root.set('globalId', str(int(GetUserData(obj, "globalId"))))
        root.set('x', str(obj.GetAbsPos().x))
        root.set('y', str(-obj.GetAbsPos().y))
      
        now = datetime.now()
        date_string = now.strftime("%Y-%m-%d %H:%M:%S")
        version_string = "C4D_" + date_string
        root.set('Version', version_string)
      
        parse_objects(obj, root, False, doc, 2)
        
        tree = ET.ElementTree(root)
        tree.write(xml_file_name, encoding='utf-8', xml_declaration=False)
        print(f"Exportação concluída! Arquivo salvo: {xml_file_name}")
            

def main(doc):
    """
    Função principal que gerencia a exportação do LevelSite e do LevelBackground.
    """
    global globalIDs    
    globalIDs = {}  # Resetando os IDs globais
    
    c4d.EventAdd()
    
    root = doc.SearchObject('LANDS OF OBLIVION')
    if root is None:
        c4d.gui.MessageDialog("Raiz da Região de Nível não encontrada. Um objeto nulo chamado LANDS OF OBLIVION deve existir na cena")
        return
    
    # Pergunta apenas uma vez onde salvar os arquivos
    save_path = c4d.storage.LoadDialog(title="Escolha a pasta para salvar os XMLs", flags=c4d.FILESELECT_DIRECTORY)
    if not save_path:
        return
    
    # Processa o LevelSite
    level_site = search_for_object_withPrefix("LevelSite", root.GetDown())
    process_level_site(level_site, save_path, doc)
    
    # Processa o LevelBackground
    level_background = search_for_object_withPrefix("LevelBackground", root.GetDown())
    process_level_background(level_background, save_path, doc)
  
    c4d.gui.MessageDialog(f"Exportação bem-sucedida! Arquivos salvos em: {save_path}")
  
    globalIDs = {}  # Resetando os IDs globais
    global total_digits
    total_digits = 0
