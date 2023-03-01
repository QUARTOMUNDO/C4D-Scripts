import c4d
from c4d import gui
from c4d import BaseSelect
from c4d import utils

# Return a list of all childen on the first level
def get_all_objects(op, output):
    nextObject = op.GetDown()
    while nextObject:
        print("Getting Childs" + str(nextObject))
        output.append(nextObject)
        nextObject = nextObject.GetNext()
    return output

# Main function
def main():
    print("Starting")
    if (not op):
        gui.MessageDialog("No Object Selected!")
        return

    if op.CheckType(c4d.Onull):
        objects = get_all_objects(op, [])
    else:
        gui.MessageDialog("Selected Object Should be Null")

    if (not objects):
        gui.MessageDialog("Can´t get list of objects")

    if len(objects) == 0:
        gui.MessageDialog("Selected objects has no childs")

    # Start the Undo process.
    doc.StartUndo()
    print("Start To Bake")

    JointsParent = doc.SearchObject("Created Joints")

    if not JointsParent:
        #A Null that will have all the created joints
        JointsParent = c4d.BaseObject(c4d.Onull)
        JointsParent.SetName("Created Joints")
        doc.InsertObject(JointsParent)
        doc.AddUndo(c4d.UNDOTYPE_NEW, JointsParent)

    #The ROOT Joint
    cParentJoint = c4d.BaseObject(c4d.Ojoint)
    doc.AddUndo(c4d.UNDOTYPE_NEW, cParentJoint)
    cParentJoint.SetName(op.GetName() + "_Root")
    cParentJoint.InsertUnder(JointsParent)

    #Copy the object transform to the ROOT joint
    cParentJoint[c4d.ID_BASEOBJECT_ABS_POSITION] = op.GetMg().off

    #Iterate on all nulls that will proccesed
    for pObject in objects:
        print("CreatingJoints")
                
        cJoint = doc.SearchObject(pObject.GetName() + ".Joint")

        if not cJoint:
            cJoint = c4d.BaseObject(c4d.Ojoint)

            doc.AddUndo(c4d.UNDOTYPE_NEW, cJoint)
            cJoint.SetName(pObject.GetName() + ".Joint")
            print(cJoint.GetName() + ".Joint")

            #Copy the object transform to the joint
            cJoint.InsertUnder(cParentJoint)
            cJoint[c4d.ID_BASEOBJECT_REL_POSITION] = pObject[c4d.ID_BASEOBJECT_REL_POSITION]
            cJoint[c4d.ID_BASEOBJECT_REL_ROTATION] = pObject[c4d.ID_BASEOBJECT_REL_ROTATION]
            cJoint[c4d.ID_BASEOBJECT_REL_SCALE] = pObject[c4d.ID_BASEOBJECT_REL_SCALE]

        cObjects = get_all_objects(pObject, [])

        if (not cObjects):
            gui.MessageDialog("Can´t get list of childs from child lol")

        if len(cObjects) == 0:
            gui.MessageDialog("Selected child has no childs")

        #iterates the pObject childs and apply wight tag to each
        for cObject in cObjects:
            #Create a weight tag and apply to the object
            CWeightTag = cObject.MakeTag(c4d.Tweights)
            doc.AddUndo(c4d.UNDOTYPE_NEW, CWeightTag)

            jointIndex = CWeightTag.AddJoint(cJoint)

            #Set the weight for each object point to 1 for the joint
            pIndex = 0
            while pIndex < cObject.GetPointCount():
                CWeightTag.SetWeight(0, pIndex, 1)
                pIndex = pIndex + 1

            print(CWeightTag)

            #Create and apply a skin modifer to the object
            Skin = c4d.BaseObject(c4d.Oskin)
            Skin.InsertUnder(cObject)
            doc.AddUndo(c4d.UNDOTYPE_NEW, Skin)

    doc.EndUndo()
    c4d.CallCommand(12147)#redraw

# Execute main()
if __name__=='__main__':
    main()