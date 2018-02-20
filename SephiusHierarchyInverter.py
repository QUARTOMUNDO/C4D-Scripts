import c4d
from c4d import gui
#Welcome to the world of Python


def main():
    doc.StartUndo()
    
    roots = doc.GetActiveObjects(1)
    
    if not roots:
        print gui.MessageDialog("No Objects Selected")
        return

    for root in roots:
        childs = []
        
        for child in getChildren(root):
            childs.append(child)
            
        #print childs
        
        if len(childs) == 0:
            print gui.MessageDialog("Object Selected has no childs")
        
        for child in childs:
            print child
            child.InsertUnder(root)
    
    c4d.EventAdd()
    doc.EndUndo()
    
def getChildren(parent):
    PChildren = []
    nextObject = parent.GetDown()
    PChildren.append(nextObject)
    
    while nextObject:
        nextObject = nextObject.GetNext()
        if nextObject:
            PChildren.append(nextObject)
    
    return PChildren 
  
if __name__=='__main__':
    main()
