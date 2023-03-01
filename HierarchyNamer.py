import c4d
from c4d import gui
from c4d import plugins
import math
import json

ObjectNamesRelations = {
        "Root" :                          "Root",
        "Pelvis" :                        "Pelvis",
        "Spline1" :                       "Spine.01",
        "Spline2" :                       "Spine.02",
        "Spline3" :                       "Spine.03",
        "Torax" :                         "Torax",
        "Neck" :                          "Neck.01",
        "Head" :                          "Head",
        "LUpperEyePalpebraRoot" :         "EyePalpebra.Upper.Root_L",
        "LUpperEyePalpebra1" :            "EyePalpebra.Upper.01_L",
        "LUpperEyePalpebra1.End" :        "EyePalpebra.Upper.01.End_L",
        "LUpperEyePalpebra2" :            "EyePalpebra.Upper.02_L",
        "LUpperEyePalpebra2.End" :        "EyePalpebra.Upper.02.End_L",
        "LUpperEyePalpebra3" :            "EyePalpebra.Upper.03_L",
        "LUpperEyePalpebra3.End" :        "EyePalpebra.Upper.03.End_L",
        "LUpperEyePalpebra4" :            "EyePalpebra.Upper.04_L",
        "LUpperEyePalpebra4.End" :        "EyePalpebra.Upper.04.End_L",
        "LUpperEyePalpebra5" :            "EyePalpebra.Upper.05_L",
        "LUpperEyePalpebra5.End" :        "EyePalpebra.Upper.05.End_L",
        "LUpperEyePalpebra6" :            "EyePalpebra.Upper.06_L",
        "LUpperEyePalpebra6.End" :        "EyePalpebra.Upper.06.End_L",
        "LUpperEyePalpebra7" :            "EyePalpebra.Upper.07_L",
        "LUpperEyePalpebra7.End" :        "EyePalpebra.Upper.07.End_L",
        "LLowerEyePalpebraRoot" :         "EyePalpebra.Lower.Root_L",
        "LLowerEyePalpebra1" :            "EyePalpebra.Lower.01_L",
        "LLowerEyePalpebra1.End" :        "EyePalpebra.Lower.01.End_L",
        "LLowerEyePalpebra2" :            "EyePalpebra.Lower.02_L",
        "LLowerEyePalpebra2.End" :        "EyePalpebra.Lower.02.End_L",
        "LLowerEyePalpebra3" :            "EyePalpebra.Lower.03_L",
        "LLowerEyePalpebra3.End" :        "EyePalpebra.Lower.03.End_L",
        "LLowerEyePalpebra4" :            "EyePalpebra.Lower.04_L",
        "LLowerEyePalpebra4.End" :        "EyePalpebra.Lower.04.End_L",
        "LLowerEyePalpebra5" :            "EyePalpebra.Lower.05_L",
        "LLowerEyePalpebra5.End" :        "EyePalpebra.Lower.05.End_L",
        "LLowerEyePalpebra6" :            "EyePalpebra.Lower.06_L",
        "LLowerEyePalpebra6.End" :        "EyePalpebra.Lower.06.End_L",
        "LLowerEyePalpebra7" :            "EyePalpebra.Lower.07_L",
        "LLowerEyePalpebra7.End" :        "EyePalpebra.Lower.07.End_L",
        "RUpperEyePalpebraRoot" :         "EyePalpebra.Upper.Root_R",
        "RUpperEyePalpebra1" :            "EyePalpebra.Upper.01_R",
        "RUpperEyePalpebra1.End" :        "EyePalpebra.Upper.01.End_R",
        "RUpperEyePalpebra2" :            "EyePalpebra.Upper.02_R",
        "RUpperEyePalpebra2.End" :        "EyePalpebra.Upper.02.End_R",
        "RUpperEyePalpebra3" :            "EyePalpebra.Upper.03_R",
        "RUpperEyePalpebra3.End" :        "EyePalpebra.Upper.03.End_R",
        "RUpperEyePalpebra4" :            "EyePalpebra.Upper.04_R",
        "RUpperEyePalpebra4.End" :        "EyePalpebra.Upper.04.End_R",
        "RUpperEyePalpebra5" :            "EyePalpebra.Upper.05_R",
        "RUpperEyePalpebra5.End" :        "EyePalpebra.Upper.05.End_R",
        "RUpperEyePalpebra6" :            "EyePalpebra.Upper.06_R",
        "RUpperEyePalpebra6.End" :        "EyePalpebra.Upper.06.End_R",
        "RUpperEyePalpebra7" :            "EyePalpebra.Upper.07_R",
        "RUpperEyePalpebra7.End" :        "EyePalpebra.Upper.07.End_R",
        "RLowerEyePalpebraRoot" :         "EyePalpebra.Lower.Root_R",
        "RLowerEyePalpebra1" :            "EyePalpebra.Lower.01_R",
        "RLowerEyePalpebra1.End" :        "EyePalpebra.Lower.01.End_R",
        "RLowerEyePalpebra2" :            "EyePalpebra.Lower.02_R",
        "RLowerEyePalpebra2.End" :        "EyePalpebra.Lower.02.End_R",
        "RLowerEyePalpebra3" :            "EyePalpebra.Lower.03_R",
        "RLowerEyePalpebra3.End" :        "EyePalpebra.Lower.03.End_R",
        "RLowerEyePalpebra4" :            "EyePalpebra.Lower.04_R",
        "RLowerEyePalpebra4.End" :        "EyePalpebra.Lower.04.End_R",
        "RLowerEyePalpebra5" :            "EyePalpebra.Lower.05_R",
        "RLowerEyePalpebra5.End" :        "EyePalpebra.Lower.05.End_R",
        "RLowerEyePalpebra6" :            "EyePalpebra.Lower.06_R",
        "RLowerEyePalpebra6.End" :        "EyePalpebra.Lower.06.End_R",
        "RLowerEyePalpebra7" :            "EyePalpebra.Lower.07_R",
        "RLowerEyePalpebra7.End" :        "EyePalpebra.Lower.07.End_R",
        "LCheecks" :                      "Cheecks_L",
        "LCheecksEnd" :                   "Cheecks.End_L",
        "RCheecks" :                      "Cheecks_R",
        "RCheecksEnd" :                   "Cheecks.End_R",
        "Jaw" :                           "Jaw",
        "JawEnd" :                        "Jaw.End",
        "LEyeBrow" :                      "EyeBrow_L",
        "LEyeBrow.End" :                  "EyeBrow.End_L",
        "REyeBrow" :                      "EyeBrow_R",
        "REyeBrow.End" :                  "EyeBrow.End_R",
        "LEye" :                          "Eye_L",
        "LEye.End" :                      "Eye.End_L",
        "REye" :                          "Eye_R",
        "REye.End" :                      "Eye.End_R",
        "Head.End" :                      "Head.End",
        "LClavicle" :                     "Clavicle_L",
        "LDarkWing.Shoulder" :            "BigWing.Shoulder_L",
        "LDarkWing.Elbow" :               "BigWing.Elbow_L",
        "LDarkWing.Elbow3" :              "BigWing.Elbow.02_L",
        "LDarkWing.Elbow_Fist" :          "BigWing.Fist_L",
        "LDarkWing.Index.1.1" :           "BigWing.Finger.Index.01.1_L",
        "LDarkWing.Index.1.2" :           "BigWing.Finger.Index.01.2_L",
        "LDarkWing.Index.1.3" :           "BigWing.Finger.Index.01.3_L",
        "LDarkWing.Index.1.4" :           "BigWing.Finger.Index.01.4_L",
        "LDarkWing.Index.1.5" :           "BigWing.Finger.Index.01.5_L",
        "LDarkWing.Index.End" :           "BigWing.Finger.Index.End_L",
        "LDarkWing.Middle.1" :            "BigWing.Finger.Middle.01_L",
        "LDarkWing.Middle.2" :            "BigWing.Finger.Middle.02_L",
        "LDarkWing.Middle.3" :            "BigWing.Finger.Middle.03_L",
        "LDarkWing.Middle.4" :            "BigWing.Finger.Middle.04_L",
        "LDarkWing.Middle.5" :            "BigWing.Finger.Middle.05_L",
        "LDarkWing.Middle.End" :          "BigWing.Finger.Middle.End_L",
        "LDarkWing.Ring.1" :              "BigWing.Finger.Ring.01_L",
        "LDarkWing.Ring.2" :              "BigWing.Finger.Ring.02_L",
        "LDarkWing.Ring.3" :              "BigWing.Finger.Ring.03_L",
        "LDarkWing.Ring.4" :              "BigWing.Finger.Ring.04_L",
        "LDarkWing.Ring.5" :              "BigWing.Finger.Ring.05_L",
        "LDarkWing.Ring.End" :            "BigWing.Finger.Ring.End_L",
        "LDarkWing.Pinky.1" :             "BigWing.Finger.Pinky.01_L",
        "LDarkWing.Pinky.2" :             "BigWing.Finger.Pinky.02_L",
        "LDarkWing.Pinky.3" :             "BigWing.Finger.Pinky.03_L",
        "LDarkWing.Pinky.4" :             "BigWing.Finger.Pinky.04_L",
        "LDarkWing.Pinky.5" :             "BigWing.Finger.Pinky.05_L",
        "LDarkWing.RPinky.End" :          "BigWing.Finger.Pinky.End_L",
        "LDarkWing.ElbowFinger.1.1" :     "BigWing.Elbow.Finger.01.1_L",
        "LDarkWing.ElbowFinger.1.2" :     "BigWing.Elbow.Finger.01.2_L",
        "LDarkWing.ElbowFinger.2.End" :   "BigWing.Elbow.Finger.02.End_L",
        "LDarkWing.ElbowFinger.2.1" :     "BigWing.Elbow.Finger.02.1_L",
        "LDarkWing.ElbowFinger.2.2" :     "BigWing.Elbow.Finger.02.2_L",
        "LDarkWing.Finger.2.End" :        "BigWing.Elbow.Finger.02.End_L",
        "LPaleWing.Shoulder" :            "SmallWing.Shoulder_L",
        "LPaleWing.Elbow1" :              "SmallWing.Elbow_L",
        "LPaleWing.Elbow2" :              "SmallWing.First_L",
        "LPaleWing.ElbowEndEnd" :         "SmallWing.First.End_L",
        "LArm" :                          "UpperArm_L",
        "LForeArm" :                      "LowerArm_L",
        "LHand" :                         "Hand_L",
        "LThumb.1" :                      "FingerThumb.01_L",
        "LThumb.2" :                      "FingerThumb.02_L",
        "LThumb.3" :                      "FingerThumb.03_L",
        "LThumb.End" :                    "FingerThumb.End_L",
        "LFinger.1.1" :                   "FingerIndex.01.01_L",
        "LFinger.1.2" :                   "FingerIndex.01.02_L",
        "LFinger.1.3" :                   "FingerIndex.01.03_L",
        "LFinger.1.4" :                   "FingerIndex.01.04_L",
        "LFinger.1.End" :                 "FingerIndex.01.End_L",
        "LFinger.2.1" :                   "FingerMiddle.02.01_L",
        "LFinger.2.2" :                   "FingerMiddle.02.02_L",
        "LFinger.2.3" :                   "FingerMiddle.02.03_L",
        "LFinger.2.4" :                   "FingerMiddle.02.04_L",
        "LFinger.2.End" :                 "FingerMiddle.02.End_L",
        "LFinger.3.1" :                   "FingerRing.03.01_L",
        "LFinger.3.2" :                   "FingerRing.03.02_L",
        "LFinger.3.3" :                   "FingerRing.03.03_L",
        "LFinger.3.4" :                   "FingerRing.03.04_L",
        "LFinger.3.End" :                 "FingerRing.03.End_L",
        "LFinger.4.1" :                   "FingerPinky.04.01_L",
        "LFinger.4.2" :                   "FingerPinky.04.02_L",
        "LFinger.4.3" :                   "FingerPinky.04.03_L",
        "LFinger.4.4" :                   "FingerPinky.04.04_L",
        "LFinger.4.End" :                 "FingerPinky.04.End_L",
        "LShield" :                       "Shield_L",
        "LShield.End" :                   "Shield.End_L",
        "LWeapon" :                       "Weapon_L",
        "LWeapon.End" :                   "Weapon.End_L",
        "RCRavicle" :                     "Clavicle_R",
        "RDarkWing.Shoulder" :            "SmallWing.Shoulder_R",
        "RDarkWing.Elbow1" :              "SmallWing.Elbow_R",
        "RDarkWing.Elbow2" :              "SmallWing.Elbow.02_R",
        "LDarkWing.First" :               "SmallWing.First_R",
        "RDarkWing.ElbowEndEnd" :         "SmallWing.First.End_R",
        "RPaleWing.Shoulder" :            "BigWing.Shoulder_R",
        "BigFreather.0" :                 "BigWing.BigFreather.00_R",
        "BigFreather.1" :                 "BigWing.BigFreather.01_R",
        "BigFreather.2" :                 "BigWing.BigFreather.02_R",
        "BigFreather.3" :                 "BigWing.BigFreather.03_R",
        "BigFreather.4" :                 "BigWing.BigFreather.04_R",
        "BigFreather.5" :                 "BigWing.BigFreather.05_R",
        "BigFreather.6" :                 "BigWing.BigFreather.06_R",
        "SmalFrontlFeather.0" :           "BigWing.SmalFrontlFeather.00_R",
        "SmalFrontlFeather.1" :           "BigWing.SmalFrontlFeather.01_R",
        "SmalFrontlFeather.2" :           "BigWing.SmalFrontlFeather.02_R",
        "SmalFrontlFeather.3" :           "BigWing.SmalFrontlFeather.03_R",
        "SmalFrontlFeather.4" :           "BigWing.SmalFrontlFeather.04_R",
        "SmalFrontlFeather.5" :           "BigWing.SmalFrontlFeather.05_R",
        "SmallBackFeather.0" :            "BigWing.SmallBackFeather.00_R",
        "SmallBackFeather.1" :            "BigWing.SmallBackFeather.01_R",
        "SmallBackFeather.2" :            "BigWing.SmallBackFeather.02_R",
        "SmallBackFeather.3" :            "BigWing.SmallBackFeather.03_R",
        "SmallBackFeather.4" :            "BigWing.SmallBackFeather.04_R",
        "SmallBackFeather.5" :            "BigWing.SmallBackFeather.05_R",
        "SmallBackFeather.6" :            "BigWing.SmallBackFeather.06_R",
        "RPaleWing.Elbow1" :              "BigWing.Elbow_R",
        "BigFeather.7" :                  "BigWing.BigFeather.07_R",
        "BigFeather.8" :                  "BigWing.BigFeather.08_R",
        "BigFeather.9" :                  "BigWing.BigFeather.09_R",
        "SmalFrontlFeather.6" :           "BigWing.SmalFrontlFeather.06_R",
        "SmalFrontlFeather.7" :           "BigWing.SmalFrontlFeather.07_R",
        "SmalFrontlFeather.8" :           "BigWing.SmalFrontlFeather.08_R",
        "SmalFrontlFeather.9" :           "BigWing.SmalFrontlFeather.09_R",
        "SmalFrontlFeather.10" :          "BigWing.SmalFrontlFeather.10_R",
        "SmallBackFeather.7" :            "BigWing.SmallBackFeather.07_R",
        "SmallBackFeather.8" :            "BigWing.SmallBackFeather.08_R",
        "SmallBackFeather.9" :            "BigWing.SmallBackFeather.09_R",
        "SmallBackFeather.10" :           "BigWing.SmallBackFeather.10_R",
        "RPaleWing.Elbow2" :              "BigWing.Elbow.02_R",
        "BigFreather.10" :                "BigWing.BigFreather.10_R",
        "BigFreather.11" :                "BigWing.BigFreather.11_R",
        "BigFreather.12" :                "BigWing.BigFreather.12_R",
        "BigFreather.13" :                "BigWing.BigFreather.13_R",
        "BigFreather.14" :                "BigWing.BigFreather.14_R",
        "SmalFrontlFeather.11" :          "BigWing.SmalFrontlFeather.11_R",
        "SmalFrontlFeather.12" :          "BigWing.SmalFrontlFeather.12_R",
        "SmalFrontlFeather.13" :          "BigWing.SmalFrontlFeather.13_R",
        "SmalFrontlFeather.14" :          "BigWing.SmalFrontlFeather.14_R",
        "SmallBackFeather.11" :           "BigWing.SmallBackFeather.11_R",
        "SmallBackFeather.12" :           "BigWing.SmallBackFeather.12_R",
        "SmallBackFeather.13" :           "BigWing.SmallBackFeather.13_R",
        "SmallBackFeather.14" :           "BigWing.SmallBackFeather.14_R",
        "RPaleWing.Fist" :                "BigWing.Fist_R",
        "BigFreather.15" :                "BigWing.BigFreather.15_R",
        "BigFreather.16" :                "BigWing.BigFreather.16_R",
        "BigFreather.17" :                "BigWing.BigFreather.17_R",
        "BigFreather.18" :                "BigWing.BigFreather.18_R",
        "BigFreather.19" :                "BigWing.BigFreather.19_R",
        "BigFreather.20" :                "BigWing.BigFreather.20_R",
        "SmalFrontlFeather.15" :          "BigWing.SmalFrontlFeather.15_R",
        "SmalFrontlFeather.16" :          "BigWing.SmalFrontlFeather.16_R",
        "SmalFrontlFeather.17" :          "BigWing.SmalFrontlFeather.17_R",
        "SmalFrontlFeather.18" :          "BigWing.SmalFrontlFeather.18_R",
        "SmalFrontlFeather.19" :          "BigWing.SmalFrontlFeather.19_R",
        "SmallBackFeather.15" :           "BigWing.SmallBackFeather.15_R",
        "SmallBackFeather.16" :           "BigWing.SmallBackFeather.16_R",
        "SmallBackFeather.17" :           "BigWing.SmallBackFeather.17_R",
        "SmallBackFeather.18" :           "BigWing.SmallBackFeather.18_R",
        "SmallBackFeather.19" :           "BigWing.SmallBackFeather.19_R",
        "RPaleWing.FeatherErratic.2" :    "BigWing.FeatherErratic.02_R",
        "RPaleWing.FeatherErratic.1" :    "BigWing.FeatherErratic.01_R",
        "RPaleWing.FirstEnd" :            "BigWing.First.End_R",
        "RArm" :                          "UpperArm_R",
        "RForeArm" :                      "LowerArm_R",
        "RHand" :                         "Hand_R",
        "RThumb.1" :                      "FingerThumb.01_R",
        "RThumb.2" :                      "FingerThumb.02_R",
        "RThumb.3" :                      "FingerThumb.03_R",
        "RThumb.End" :                    "FingerThumb.End_R",
        "RFinger.1.1" :                   "FingerIndex.01.01_R",
        "RFinger.1.2" :                   "FingerIndex.01.02_R",
        "RFinger.1.3" :                   "FingerIndex.01.03_R",
        "RFinger.1.4" :                   "FingerIndex.01.04_R",
        "RFinger.1.End" :                 "FingerIndex.01.End_R",
        "RFinger.2.1" :                   "FingerMiddle.02.01_R",
        "RFinger.2.2" :                   "FingerMiddle.02.02_R",
        "RFinger.2.3" :                   "FingerMiddle.02.03_R",
        "RFinger.2.4" :                   "FingerMiddle.02.04_R",
        "RFinger.2.End" :                 "FingerMiddle.02.End_R",
        "RFinger.3.1" :                   "FingerRing.03.01_R",
        "RFinger.3.2" :                   "FingerRing.03.02_R",
        "RFinger.3.3" :                   "FingerRing.03.03_R",
        "RFinger.3.4" :                   "FingerRing.03.04_R",
        "RFinger.3.End" :                 "FingerRing.03.End_R",
        "RFinger.4.1" :                   "FingerPinky.04.01_R",
        "RFinger.4.2" :                   "FingerPinky.04.02_R",
        "RFinger.4.3" :                   "FingerPinky.04.03_R",
        "RFinger.4.4" :                   "FingerPinky.04.04_R",
        "RFinger.4.End" :                 "FingerPinky.04.End_R",
        "RShield" :                       "Shield_R",
        "RShield.End" :                   "Shield.End_R",
        "RWeapon" :                       "Weapon_R",
        "RWeapon.End" :                   "Weapon.End_R",
        "WeaponGuard1" :                  "WeaponGuard.Back",
        "WeaponGuard1.End" :              "WeaponGuard.Back.End",
        "WeaponGuard.2" :                 "WeaponGuard_R",
        "WeaponGuard.2.End" :             "WeaponGuard.End_R",
        "WeaponGuard.3" :                 "WeaponGuard_L",
        "WeaponGuard.3.End" :             "WeaponGuard.End_L",
        "LFemur" :                        "Thigh_L",
        "LTibia" :                        "Calf_L",
        "LFoot" :                         "Foot_L",
        "LFingers" :                      "FootBall_L",
        "LFingers.End" :                  "FootBall.End_L",
        "RFemur" :                        "Thigh_R",
        "RTibia" :                        "Calf_R",
        "RFoot" :                         "Foot_R",
        "RFingers" :                      "FootBall_R",
        "RFingers.End" :                  "FootBall.End_R"
}

def get_all_objects_Names(op, filter, output, Intend, UseIntend):
    DefaultIntend = "    "
    FinalIntend = ""
    while op:
        if UseIntend:
            FinalIntend = Intend + DefaultIntend
        else:
            FinalIntend = ""

        if filter(op):
            output.append(Intend + op.GetName())

        get_all_objects_Names(op.GetDown(), filter, output, FinalIntend, UseIntend)
        op = op.GetNext()
    return output

def get_all_objects(op, filter, output):
    while op:
        if filter(op):
            output.append(op)
        get_all_objects(op.GetDown(), filter, output)
        op = op.GetNext()
    return output

def ConvertName(CurrentName):
    if CurrentName in ObjectNamesRelations:
        print ("has Name" + ObjectNamesRelations[CurrentName])
        return ObjectNamesRelations[CurrentName]
    else:
        print ("has not Name" + CurrentName)
        return CurrentName

def main():
    doc.StartUndo()
    JSONData = []

    roots = doc.GetActiveObjects(1)
    print ("-----------------", roots[0])
    if not roots:
        print gui.MessageDialog("No Objects Selected")
        return

    for root in roots:
        childs = []
        print ("-----------------", root)
        childs = get_all_objects(root, lambda x: x.CheckType(c4d.Ojoint), [])

        #print childs

        if len(childs) == 0:
            print gui.MessageDialog("Object Selected has no childs")

        for child in childs:
            print child

            #Custom name fixer
            if child.GetName() == "RPaleWing.ElbowEndEnd":
                child.SetName("LPaleWing.ElbowEndEnd")

            if child.GetName() == "LWeapon.End":
                print "------------------------------------------"
                print child.GetUp().GetName()
                if child.GetUp().GetName() == "LShield":
                    child.SetName("LShield.End")
                if child.GetUp().GetName() == "Shield_L":
                    child.SetName("LShield.End")

            if child.GetName() == "LWeapon.End":
                if child.GetUp().GetName() == "RShield":
                    child.SetName("RShield.End")
                if child.GetUp().GetName() == "Shield_R":
                    child.SetName("RShield.End")

            if child.GetName() == "CheecksEnd":
                if child.GetUp().GetName() == "LCheecks":
                    child.SetName("LCheecksEnd")
                if child.GetUp().GetName() == "Cheecks_L":
                    child.SetName("LCheecksEnd")

                if child.GetUp().GetName() == "RCheecks":
                     child.SetName("RCheecksEnd")
                if child.GetUp().GetName() == "Cheecks_R":
                     child.SetName("RCheecksEnd")

            child.SetName(ConvertName(child.GetName()))
            #JSONData.append(child.GetName())

        #JSONData = get_all_objects_Names(root, lambda x: x.CheckType(c4d.Ojoint), [], "", False)

    #print JSONData

    #filePath = c4d.storage.SaveDialog(c4d.FILESELECTTYPE_ANYTHING, "", "", "D:\Dropbox (QUARTOMUNDO)\TheLightoftheDarknessGame\Coding\GameData", "")

    #with open(filePath, 'w') as outfile:
        #json.dump(JSONData, outfile, sort_keys=False, indent=4)
        
    #reset root bone to origin
    obj = doc.GetActiveObject()
    zero = c4d.Vector(0,0,0)
    normScale = c4d.Vector(1,1,1)
    obj.SetAbsPos(zero)
    obj.SetAbsRot(zero)
    obj.SetAbsScale(normScale)
    
    c4d.EventAdd()
    doc.EndUndo()


if __name__=='__main__':
    main()
