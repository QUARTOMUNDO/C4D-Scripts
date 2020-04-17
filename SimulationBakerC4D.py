import c4d
from c4d import gui
from c4d import BaseSelect
from c4d import utils

# Return a list of all childen on the first level
def get_all_objects(op, output):
    nextObject = op.GetDown()
    while nextObject:
        print "Getting Childs" + str(nextObject)
        output.append(nextObject)
        nextObject = nextObject.GetNext()
    return output

def SetCurrentTime(currentTime, doc):
    doc.SetTime(currentTime)
    c4d.GeSyncMessage(c4d.EVMSG_TIMECHANGED)
    doc.ExecutePasses(None, True, True, True, 4)
    
def BakeAnimationsForSelection(op, doc):
    minTime = doc[c4d.DOCUMENT_MINTIME]
    maxTime = doc[c4d.DOCUMENT_MAXTIME]
    fps = doc.GetFps()
    
    if minTime != maxTime:
        currentTime = minTime
        while (currentTime <= maxTime): 
            SetCurrentTime(currentTime, doc)
            
            #New since version R19.
            #Records the active objects in the document.
            doc.Record()
            
            currentTime += c4d.BaseTime(1, fps)
    
    SetCurrentTime(minTime, doc)

def MakeEditable(op, doc, parent):
    #opParent = op.GetUp();
    
    if not op: 
        raise TypeError("there's no object selected")
    res = utils.SendModelingCommand(
                              command = c4d.MCOMMAND_MAKEEDITABLE,
                              list = [op])
    #check if res is a list 
    if res is False:
        raise TypeError("make editable didn't worked")
    elif res is True:
        print "make editable should not return true"
    elif isinstance(res, list):
        if parent:
            parent.InsertUnder(res[0])
        else:
            doc.InsertObject(res[0])
    
    c4d.EventAdd()
    
    return res[0]
       
# Main function
def main():
    if (not op):
        gui.MessageDialog("No Object Selected!")
        return
    
    if op.CheckType(c4d.Opolygon) | op.CheckType(c4d.Ospline) | op.CheckType(c4d.Onull): 
        print "object is non editable. Getting it´s childs"
        objects = get_all_objects(op, [])
    else:
        print "Object is non editable. Making it editable then getting it´s childs"
        doc.SetActiveObject(op, 0)
        c4d.CallCommand(12236)
        #eobject = MakeEditable(op, doc, None)
        print "Objects returned from make editable: " + str(op)
        objects = get_all_objects(op, [])
        
    if (not objects):
        gui.MessageDialog("Can´t get list of objects")
    
    if len(objects) == 0:
        gui.MessageDialog("Selected objects has no childs")
        
    doc.SetActiveObject(objects[0], 0)    
    for pObject in objects:
        doc.SetActiveObject(pObject, 1) 
    c4d.CallCommand(12236)
    
    # Start the Undo process.
    doc.StartUndo()
    print "Start To Bake"
    
    if objects[0]:
        doc.SetActiveObject(objects[0], 0)
    for pObject in objects:
        doc.SetActiveObject(pObject, 1)    
        
    #dont work, record only current values without considering the simulation  
    BakeAnimationsForSelection(op, doc)
    op.KillTag(180000102)
    
    #A Null that will have all the created joints
    JointsParant = c4d.BaseObject(c4d.Onull)
    JointsParant.SetName(op.GetName() + "Joints")
    doc.InsertObject(JointsParant)
    doc.AddUndo(c4d.UNDOTYPE_NEW, JointsParant)
    
    cParentJoint = c4d.BaseObject(c4d.Ojoint)
    doc.AddUndo(c4d.UNDOTYPE_NEW, cParentJoint)
    cParentJoint.SetName(pObject.GetUp().GetName() + "_Root")
    cParentJoint.InsertUnder(JointsParant) 
    
    #Iterate on all objects that will be baked
    for pObject in objects:
        print "CreatingJoints"
        cJoint = c4d.BaseObject(c4d.Ojoint)
        doc.AddUndo(c4d.UNDOTYPE_NEW, cJoint)
        cJoint.SetName(pObject.GetName())
        print cJoint.GetName()
        
        #Copy the object transform to the joint
        cJoint.InsertUnder(cParentJoint)       
        cJoint[c4d.ID_BASEOBJECT_REL_POSITION] = pObject[c4d.ID_BASEOBJECT_REL_POSITION]
        cJoint[c4d.ID_BASEOBJECT_REL_ROTATION] = pObject[c4d.ID_BASEOBJECT_REL_ROTATION]
        cJoint[c4d.ID_BASEOBJECT_REL_SCALE] = pObject[c4d.ID_BASEOBJECT_REL_SCALE]
        
        #Create a weight tag and apply to the object
        CWeightTag = pObject.MakeTag(c4d.Tweights)
        doc.AddUndo(c4d.UNDOTYPE_NEW, CWeightTag)

        jointIndex = CWeightTag.AddJoint(cJoint)
        
        #Set the weight for each object point to 1 for the joint
        pIndex = 0
        while pIndex < pObject.GetPointCount():
            CWeightTag.SetWeight(0, pIndex, 1)
            pIndex = pIndex + 1

        print CWeightTag
        
        # Defines a list that will contains the ID of parameters we want to copies.
        # Such ID can be found by drag-and-drop a parameter into the python console.
        trackListToCopy = [c4d.ID_BASEOBJECT_POSITION, c4d.ID_BASEOBJECT_ROTATION, c4d.ID_BASEOBJECT_SCALE]
        
        tracks = pObject.GetCTracks()
        if tracks:
            # Iterates overs the CTracks of obj1.
            for track in tracks:
                
                # Retrieves the full parameter ID (DescID) describing a parameter.
                did = track.GetDescriptionID()
                
                # If the Parameter ID of the current CTracks is on the trackListToCopy
                if did[0].id in trackListToCopy:
                    
                    # Find if our static object already got an animation track for this parameter ID.
                    foundTrack = cJoint.FindCTrack(did)
                    if foundTrack:
                        # Removes the track if found.
                        doc.AddUndo(c4d.UNDOTYPE_DELETE, foundTrack)
                        foundTrack.Remove()
                    
                    # Copies the initial CTrack in memory. All CCurve and CKey are kept in this CTrack.
                    clone = track.GetClone()   
                
                    # Inserts the copied CTrack to the static object.
                    cJoint.InsertTrackSorted(clone)
                    doc.AddUndo(c4d.UNDOTYPE_NEW, clone)  
                    
                    #remove the track from the original object
                    track.Remove()
                    doc.AddUndo(c4d.UNDOTYPE_NEW, track)
        
        #Create and apply a skin modifer to the object
        Skin = c4d.BaseObject(c4d.Oskin)
        Skin.InsertUnder(pObject)   
        doc.AddUndo(c4d.UNDOTYPE_NEW, Skin) 
        
        NTag = pObject.GetTag(c4d.Tnormal)
        pObject.KillTag(NTag.GetType())    
        
        DYTag = op.GetTag(180000102)
        doc.AddUndo(c4d.UNDOTYPE_NEW, op) 
        op.KillTag(180000102)
                   
    doc.EndUndo()
    c4d.EventAdd()
    
# Execute main()
if __name__=='__main__':
    main()