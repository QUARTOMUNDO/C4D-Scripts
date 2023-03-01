import c4d
from c4d import gui
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
    DataW = mapTag.GetDataAddressW()
    
    op = mapTag.GetObject()
    print op.GetName()
    
    pointCount = op.GetPointCount()
    
    #doc.AddUndo(c4d.UNDOTYPE_NEW, mapTag)
    
    for idx in xrange(pointCount):
        color = (round(c4d.VertexColorTag.GetColor(DataW, None, None, idx)[0] * 100)) / 100
        colorVec = c4d.Vector4d(color, color, color, 1)
        print colorVec
        c4d.VertexColorTag.SetPoint(DataW, None, None, idx, colorVec)
    
    #doc.EndUndo()    
    c4d.EventAdd()
    
if __name__=='__main__':
    main()
