from oauth2client.service_account import ServiceAccountCredentials
import gspread
import Database.FYPdatabase as db
from googleapiclient.discovery import build
from collections import OrderedDict

scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('testfyp-335718-845adade9f8b.json',scope)
client = gspread.authorize(creds)
sheetId ='0'
FYP_Test = client.open("FYP Example").sheet1
service = build('sheets', 'v4', credentials = creds)
canList = db.GetCandidates()

# request structure used from https://developers.google.com/sheets/api/samples/charts

request_body = {
    'requests': [
        {
            'addChart': {
                'chart': {
                    'spec': {
                        'title': 'Race to the Quota - Candidate First Preference',
                        'basicChart': {
                            'chartType': 'COLUMN',
                            'axis': [
                                {
                                    'position': "BOTTOM_AXIS",
                                    'title': 'Candidates'
                                },
                                {
                                    'position': "LEFT_AXIS",
                                    'title': 'First Preference Votes'
                                }

                            ],
"domains": [
                {
                  "domain": {
                    "sourceRange": {
                      "sources": [
                        {
                          "sheetId": sheetId,
                          "startRowIndex": 1,
                          "endRowIndex": len(canList)+1,
                          "startColumnIndex": 1,
                          "endColumnIndex": 2
                        }
                      ]
                    }
                  }
                }
              ],
                            'series': [
                                {
                                    'series': {
                                'sourceRange': {
                                    'sources': [
                                        {
                                            'sheetId': sheetId,
                                            'startRowIndex': 1,
                                            'endRowIndex': len(canList)+1,
                                            'startColumnIndex':3,
                                            'endColumnIndex':4

                                        }
                                    ]
                                }
                                },
                                    'targetAxis': 'LEFT_AXIS'
                                }
                            ]
                        }
                    },
                'position': {
                    'overlayPosition': {
                        "anchorCell": {
                                "sheetId": sheetId,
                                  "rowIndex": 1,
                                  "columnIndex": 6
                          }

                    }
                }
                }
            }
        }
    ]
}


totals =[]

partyList = list(OrderedDict.fromkeys(db.GetParties()))

party_chart = {
    'requests': [
        {
            'addChart': {
                'chart': {
                    'spec': {
                        'title': 'Party First Preferences',
                        'basicChart': {
                            'chartType': 'COLUMN',
                            'axis': [
                                {
                                    'position': "BOTTOM_AXIS",
                                    'title': 'Candidates'
                                },
                                {
                                    'position': "LEFT_AXIS",
                                    'title': 'First Preference Votes'
                                }

                            ],
"domains": [
                {
                  "domain": {
                    "sourceRange": {
                      "sources": [
                        {
                          "sheetId": sheetId,
                          'startRowIndex': len(canList)+3,
                          'endRowIndex': len(canList)+len(partyList)+3,
                          "startColumnIndex": 1,
                          "endColumnIndex": 2
                        }
                      ]
                    }
                  }
                }
              ],
                            'series': [
                                {
                                    'series': {
                                'sourceRange': {
                                    'sources': [
                                        {
                                            'sheetId': sheetId,
                                            'startRowIndex': len(canList)+3,
                                            'endRowIndex': len(canList)+len(partyList)+3,
                                            'startColumnIndex':2,
                                            'endColumnIndex':3

                                        }
                                    ]
                                }
                                },
                                    'targetAxis': 'LEFT_AXIS'
                                }
                            ]
                        }
                    },
                'position': {
                    'overlayPosition': {
                        "anchorCell": {
                                "sheetId": sheetId,
                                  "rowIndex": len(canList)+len(partyList)+9,
                                  "columnIndex": 6
                          }

                    }
                }
                }
            }
        }
    ]
}

count = 0
for i in canList:
    # adding candidate name and party to sheet
    FYP_Test.update_cell(canList.index(i)+2,2, i[0])
    FYP_Test.update_cell(canList.index(i)+2,3, i[1])
    FYP_Test.update_cell(canList.index(i)+2,5, '=(D'+str(canList.index(i)+2) + '/C' + str(len(canList) + len(partyList) + 7) + ') * 100')

for x in range(len(canList)):
    FYP_Test.update_cell(x+2,4,str(0))


response = service.spreadsheets().batchUpdate(
    spreadsheetId = '1Iqhb0LOEcI7unI_483icoRx0IUy0pPFeE-6mPh-hC_4',
    body = request_body
).execute()

party_req = service.spreadsheets().batchUpdate(
    spreadsheetId = '1Iqhb0LOEcI7unI_483icoRx0IUy0pPFeE-6mPh-hC_4',
    body = party_chart
).execute()


def setup():
    FYP_Test.update_cell(1,1, 'Tally Sheet')
    FYP_Test.update_cell(1,2, 'Candidate Name')
    FYP_Test.update_cell(1,3, 'Party')
    FYP_Test.update_cell(1,4,'First Preferences')
    FYP_Test.update_cell(1,5,'Share of the Vote')
    FYP_Test.update_cell(3 + len(canList),2, 'Party Totals')
    FYP_Test.update_cell(3+len(canList),3, 'First Preferences')
    FYP_Test.update_cell(len(canList) + len(partyList) + 6,2, 'Electorate')
    FYP_Test.update_cell(len(canList) + len(partyList) + 7,2, 'Votes Cast')
    FYP_Test.update_cell(len(canList) + len(partyList) + 7,3, '=SUM(D2:D'+str((len(canList))+1)+')')

    FYP_Test.update_cell(len(canList) + len(partyList) + 8,2, 'Estimated Turnout (%)')
    FYP_Test.update_cell(len(canList) + len(partyList) + 8,3,'=(C'+str(len(canList) + len(partyList) + 7)+'/C'+ str(len(canList) + len(partyList) + 6) + ') * 100')
    FYP_Test.update_cell(len(canList) + len(partyList) + 9, 2, 'Available Seats')
    FYP_Test.update_cell(len(canList) + len(partyList) + 10, 2, 'Projected Quota')
    FYP_Test.update_cell(len(canList) + len(partyList) + 10, 3, '=rounddown(C' + str(len(canList) + len(partyList) + 7) + '/(C'+str(len(canList) + len(partyList) + 9) + '+1) +1)')


FYP_Test.update_cell(1,25,'=SUM(A1 + D2')

setup()

for p in partyList:
    p = str(p)
    p = str(p[p.find("'") + len("'"):p.rfind("'")])
    partyList[count] = p
    count = count +1

for party in partyList:
    party = str(party)
    tempPartyTotals = []

    cell_list = list(FYP_Test.findall(str(party)))
    count = 0
    print("Party total for: " + party)
    party_cell = ""
    for c in cell_list:
        if(c.col != 2):
            party_cell = party_cell + str('INDIRECT(ADDRESS(' +str(c.row) + ','+str(c.col + 1) + ')),')
    FYP_Test.update_cell(partyList.index(party)+4 + len(canList),3,'=SUM('+party_cell+')')
    FYP_Test.update_cell(partyList.index(party)+4 + len(canList),4, '=(C'+str(partyList.index(party)+4 + len(canList)) + '/C' + str(len(canList) + len(partyList) + 7) + ') * 100')


print(totals)
for p in partyList:
    FYP_Test.update_cell(partyList.index(p)+4 + len(canList),2, str(p))


count = 0
# while True:
#     print("--------------------------------------------")
#     count += 1
#     print("Ballot No.", count)
#     can1 = -1
#     for c in canList:
#         num1 = int(input("Enter preference for " + str(c[0] + " - " + c[1]) + " : "))
#         if num1 == 1:
#             can1 = int(canList.index(c))
#     FYP_Test.update_cell((can1+2),4, str(int(FYP_Test.cell((can1+2),4).value)+1))

def addToTally(pred):

    if(len(pred) != len(canList)):
        print("Incorrect number of boxes detected")
        print("Expected " + str(len(canList)) + " boxes but found " + str(len(pred)) + " boxes")

    elif(len(pred) == 0):
        print("Could not find any boxes")
    else:
        one = pred.index(1)
        print("First Preference vote for ", canList[one])
        FYP_Test.update_cell((one + 2), 4, str(int(FYP_Test.cell((one + 2), 4).value) + 1))