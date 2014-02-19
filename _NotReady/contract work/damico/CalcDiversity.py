from ATtILA2.constants import globalConstants

import arcpy, math, sys

TotalAreaDict = {}
ProportionsDict = {}
CopyDict = {}
ResultsDict = {}
def createValueDict(alist):
    valuedict={}
    for a in alist:
          valuedict[(int(a.split(":")[0]))] = float(a.split(":")[1])
    return valuedict


def createTotalTable(tabAreaTable):
    for tabAreaTableRow in tabAreaTable:
        alist = []
        TotalArea = 0
        #Calculate Total Area Dictionary
        for k in tabAreaTableRow.tabAreaDict.keys():
            TotalArea = TotalArea + tabAreaTableRow.tabAreaDict[k]
            alist.append(str(k) + ":" + str(tabAreaTableRow.tabAreaDict[k]))

        TotalAreaDict[tabAreaTableRow.zoneIdValue] = TotalArea
        CopyDict[tabAreaTableRow.zoneIdValue]= alist

    createProportionsDict(CopyDict,TotalAreaDict)

    return ResultsDict


#Calculate Proportions
def createProportionsDict(CopyDict, TotalAreaDict):

    for k in CopyDict.keys():
        indivrowdict = {}
        pSum = 0
        S = 0
        C = 0
        indivrowdict = createValueDict(CopyDict[k])
        for i in indivrowdict.keys():
            if indivrowdict[i] >0:

                P = indivrowdict[i] / TotalAreaDict[k]

                pSum = pSum + (P * math.log(P))
                C = C + P * P
                S = S + 1
                ProportionsDict[k] =  str(pSum) + "," + str(C) + "," + str(S)


    for k in ProportionsDict.keys():
        H = float(ProportionsDict[k].split(",") [0])* -1
        S = int(ProportionsDict[k].split(",")[2])
        Hprime = H/math.log(S)
        C = float(ProportionsDict[k].split(",")[1])
        ResultsDict[k] = str(H) + "," + str(Hprime) + "," + str(S) + "," + str(C)


    return ResultsDict


