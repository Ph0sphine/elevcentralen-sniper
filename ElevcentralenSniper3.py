import json
import re
import requests as r
import time as t
from datetime import timedelta
from datetime import datetime 
from bs4 import BeautifulSoup

startDate = datetime.now()
s = r.Session()

_webhookUrl = ""   #Discord webhook url
_user = ""   #Username for Elevcentralen
_pass = ""   #Password for Elevcentralen
_days = 80   #How many days from today to lookout for new lessons. A date beyond what the website can show will give wrong api response

bookings = []
def main():
    auth(_user, _pass)
    teachers = getTeachers()
    listBookings(_days, teachers)
    errors()    
    webHook("New lessons will appear here!", "Attention!", _webhookUrl)
    while True:
        print("Checking " + str(len(bookings)) + " lessons")
        oldBookingNames = []
        for x in bookings:
            oldBookingNames.append(x["formattedTitleDateAndTime"])

        listBookings(_days, teachers)

        for x in bookings:
            if x["formattedTitleDateAndTime"] not in oldBookingNames:
                webHook(x["formattedTitleDateAndTime"], "New lession!",  _webhookUrl)
                print("New Lesson! "+ x["formattedTitleDateAndTime"])
        
        t.sleep(5)

def listBookings(days, teachers):
    endDate = datetime.now() + timedelta(days)
    url = "https://www.elevcentralen.se/Booking/Home/Data/"

    payload = json.dumps({
    "Source": "StudentCentral",
    "Person": {
    "id": studentId
    },
    "EducationTypeId": 3,
    "Start": "{year}-{month}-{day}T00:00:00.000Z".format(day = startDate.day, month = startDate.month, year = startDate.year),
    "End": "{year}-{month}-{day}T00:00:00.000Z".format(day = endDate.day, month = endDate.month, year = endDate.year),
    "SelectedView": "Free",
    "ShowInListView": False,
    "TeacherIDs": teachers
    })

    headers = {
    "Connection": "keep-alive",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/json",
    }

    global bookingsResponse
    global bookings

    bookingsResponse = s.request("POST", url, headers=headers, data=payload)
    try:
        bookings = bookingsResponse.json()["items"]
    except:
        print("[ERROR] Json parsing failed!, request timeout?")

def auth(Username, Password): 
    s.cookies.clear

    response = s.request("POST", "https://www.elevcentralen.se/en/Login/Index")
    cookieToken = "__RequestVerificationToken=" + s.cookies["__RequestVerificationToken"]
    payloadToken = "__RequestVerificationToken=" + re.search('RequestVerificationToken" type="hidden" value="([^"]*)', response.text).group(1)

    payload="{token}&Username={username}&Password={password}".format(token = payloadToken, username = Username, password = Password)
    headers = {
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": cookieToken
    }
    
    url = f"https://www.elevcentralen.se/en/Login/Authenticate"
    response = s.request("POST", url, headers=headers, data=payload)

    global studentId
    studentId = re.search("\$\.sc\.person\.id = (\d*)", response.text).group(1)
    
def webHook(lession, title, url):
    payload = json.dumps({
    "embeds":
        [{
            "title": title,
            "description": "@everyone " + lession,
            "url": "https://www.elevcentralen.se/en/Booking",
            "color": 3061343
        }]
    })
    headers = {
        "Content-Type": "application/json"
    }

    r.request("POST", url, headers=headers, data=payload)

def getTeachers():
    teachersIdlist = []
    response = s.request("GET", "https://www.elevcentralen.se/en/Booking")
    soup = BeautifulSoup(response.content, 'html.parser')
    div = soup.find("div", {"class": "list-group teachers"})
    labels = div.findAll("label")

    count = 0
    for techer in labels:
        print(str(count) + " " +  techer["data-name"])
        count += 1
    print("Select techers")
    print("Example: 24, 42, 11")
    print("Only use commas for multiple teachers")
    teacherList = input("").replace(" ", "").split(",")
    for i in teacherList:
        teachersIdlist.append(int(labels[int(i)]["data-id"]))
        print("Selected: " + labels[int(i)]["data-name"] + " : " + labels[int(i)]["data-id"])

    return teachersIdlist

def errors():
    try:
        if "Du har bl\\u00E4ddrat f\\u00F6r l\\u00E5ngt" in bookingsResponse.text:
            print("[ERROR] Time period was to long, please lower your days")
            input()
            quit()
    except SystemExit:
        quit()


if __name__ == "__main__":
    main()