import c4d
import math
from c4d import gui
import json

#Welcome to the world of Python


def main():
    mapTag = doc.GetActiveTag()
    
    if not mapTag:
        print gui.MessageDialog("No vertex map tag Selected")
        return


    print mapTag
    if not mapTag.GetType() == 431000045:
        print gui.MessageDialog("Object is not vertex color tag ")
        
    # Obtains vertex colors data R/W addresses   
    DataR = mapTag.GetDataAddressR()
    
    IntegerMapData = ""
    
    op = mapTag.GetObject()
    print op.GetName()
    
    pointCount = op.GetPointCount()
    
    #create a 2d array with n width and m height
    n = int(op[c4d.ID_USERDATA,2])
    m = int(op[c4d.ID_USERDATA,3])
    unkownAreaGlonalID = 99
    
     
    areaList = [[0] * m for i in range(n)]
    
    print len(areaList)
    print len(areaList[0])
    
    for idx in xrange(pointCount):
        #Get the current line
        y = int(math.floor(idx / n))
        x = int(idx % n)
        
        #get the value at the current coord XY
        if op.GetName().split("_")[0] == "AreaMap":
            color = int(round(c4d.VertexColorTag.GetColor(DataR, None, None, idx)[0] * 100))
            areaList[x][y] = color
            
        elif op.GetName().split("_")[0] == "LumaMap":
            if c4d.VertexColorTag.GetColor(DataR, None, None, idx)[0] > 0.5:
                areaList[x][y] = True
            else:
                areaList[x][y] = False
    
    JSONData = []
    areaListSTR = []
    
    for index in xrange(4):
        JSONData.append({})
        JSONData[index]['Name'] = "Quadrant_" + str(index + 1) 
        
        if op.GetName().split("_")[0] == "AreaMap":
            JSONData[index]["IntegerMapData"] = []
            JSONData[index]["BooleanMapData"] = []
            
            if index == int(op.GetName().split("_")[1]) - 1:
                for idx in xrange(len(areaList)):
                    JSONData[index]["IntegerMapData"].append({})
                    JSONData[index]["IntegerMapData"][idx]["SingleLineData"] = []
                    
                    for idx2 in xrange(len(areaList[idx])):
                        JSONData[index]["IntegerMapData"][idx]["SingleLineData"].append(areaList[idx][idx2])
            else:
                JSONData[index]["IntegerMapData"] = []

        elif op.GetName().split("_")[0] == "LumaMap":
            JSONData[index]["BooleanMapData"] = []
            JSONData[index]["IntegerMapData"] = []
            
            if index == int(op.GetName().split("_")[1]) - 1:          
                for idx in xrange(len(areaList)):
                    JSONData[index]["BooleanMapData"].append({})
                    JSONData[index]["BooleanMapData"][idx]["SingleLineData"] = []
                    
                    for idx2 in xrange(len(areaList[idx])):
                        JSONData[index]["BooleanMapData"][idx]["SingleLineData"].append((areaList[idx][idx2]) > 0.5)
            else:
                JSONData[index]["BooleanMapData"] = []
                
        if index == 0:
            InvertedXCoord = False
            InvertedYCoord = True
            
        elif index == 1:
            InvertedXCoord = True
            InvertedYCoord = True

        elif index == 2:
            InvertedXCoord = True
            InvertedYCoord = False

        elif index == 3:
            InvertedXCoord = False
            InvertedYCoord = False
        
        JSONData[index]["InvertedXCoord"] = InvertedXCoord
        JSONData[index]["InvertedYCoord"] = InvertedYCoord
        JSONData[index]["OffsetX"] = op[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X]
        JSONData[index]["OffsetY"] = -op[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y]
        JSONData[index]["ScaleX"] = op[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y]
        JSONData[index]["ScaleY"] = op[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Z]
        
        JSONData[index]["unkownAreaGlonalID"] = unkownAreaGlonalID
        JSONData[index]["MapWidth"] = n
        JSONData[index]["MapHeight"] = m
        
        #print IntegerMapData
        #print len(areaList)
        
    print JSONData
        
    filePath = c4d.storage.SaveDialog(c4d.FILESELECTTYPE_ANYTHING, "", "", "D:\Dropbox (QUARTOMUNDO)\TheLightoftheDarknessGame\Coding\GameData\LevelMaps", "")
    
    with open(filePath, 'w') as outfile:
        json.dump(JSONData, outfile, sort_keys=True, indent=4)

if __name__=='__main__':
    main()
