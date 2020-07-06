import csv
import time
import json
import argparse
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

ap = argparse.ArgumentParser(description='Sort classes by GPA')
ap.add_argument('-r', '--read', nargs='?', const='classes',
                help='file to read course codes from')
ap.add_argument('-w', '--write', nargs='?', const='classes.csv',
                help='file to write course codes to')
ap.add_argument('-o', '--output', default='out.csv', help='output filename')
ap.add_argument('-p', '--print', nargs='*',
                help='print course grade pair from file')
args = ap.parse_args()

if args.print is None:
    if args.read is None:
        #get classes from Course Search and Enroll Page
        driver = webdriver.Firefox(executable_path="./geckodriver") #relative path
        url = "https://enroll.wisc.edu/search"

        driver.get(url) #navigate to the page
        input() #wait for user to indicate user has logged in/set settings as user wished

        #initialize variables needed
        classes = set()
        prev = ""
        course = " "
        actions = ActionChains(driver)
        actions.send_keys(Keys.PAGE_DOWN)

        print("getting courses")
        while prev != course:
            prev = course
            #for each course "block"
            for course_path in driver.find_elements_by_xpath("/html/body/div[1]/div/div/div/div/md-card[2]/md-content/md-virtual-repeat-container/div/div[2]/md-list/md-list-item/div"):
                try: #last block is null so must put in try
                    #BeautifulSoup parses better than selenium
                    html = course_path.get_attribute('innerHTML')
                    soup = BeautifulSoup(html, "lxml") #only works after initialization
                    #find course code (ex. "CS 101")
                    course = soup.find('div', {"class":'result__name flex-80'}).strong.text.strip()
                    #adding to set - set because repeats may happen as scroll may not scroll 1 view length
                    code = course.replace("&"," ")
                    #not adding empty strings
                    if code != "":
                        classes.add(code)
                except:
                    pass
             #have to click a card to scroll correct element of page
            driver.find_element_by_xpath("/html/body/div[1]/div/div/div/div/md-card[2]").click()
            actions.perform() #scroll PAGE_DOWN
            time.sleep(1) #have to wait or next cards won't load. havent tested lower settings than 1

        driver.quit()
        if args.write is not None:
            #write course codes to load later
            cw = csv.writer(open((args.write + ".csv"),'w'))
            cw.writerow(list(classes))
    else:
        #load course coads
        with open((args.read), newline='') as f:
            reader = csv.reader(f)
            classes = list(reader)[0]

    #initialize disctionary to store course GPA pair
    cg = dict()

    print("getting grades", end='\r')
    i=1
    for course_code in classes:
        #madgrades api query course code to get internal madgrades ID
        url = 'https://api.madgrades.com/v1/courses'
        auth = {'Authorization': 'Token token=930be378f74e4bc9aeba6d982586cfbf'}
        payload = {'query': course_code}
        r = json.loads(requests.get(url, params=payload, headers=auth).text)
        #madgrades api get grades using madgrades ID
        #checking only 0 because madgrades search pulls up the course first if
        #  given the course code and searching more might lead to finding an incorrect
        #  course, as can only check the course number
        try:
            if int(r["results"][0]["number"]) == int(course_code.split(" ")[-1]):
                url = r["results"][0]["url"] + "/grades"
                grade = json.loads(requests.get(url, headers=auth).text)
                #calculate average
                #not using certain values, contact registrar for more info
                avg_gpa = (((grade["cumulative"]["aCount"] * 4.0) + (grade["cumulative"]["abCount"] * 3.5) +
                            (grade["cumulative"]["bCount"] * 3.0) + (grade["cumulative"]["bcCount"] * 2.5) +
                            (grade["cumulative"]["cCount"] * 2.0) + (grade["cumulative"]["dCount"])) /
                           (grade["cumulative"]["aCount"] + grade["cumulative"]["abCount"] +
                            grade["cumulative"]["bCount"] + grade["cumulative"]["bcCount"] +
                            grade["cumulative"]["cCount"] + grade["cumulative"]["dCount"] +
                            grade["cumulative"]["fCount"]))
            else:
                avg_gpa = 0 #cound not find course in MadGrades
        except: #no previous data or error in data
            avg_gpa = 0
        try:
            print(("getting grades: " + str('%.1f' % (i / len(classes) *100)) +
               " percent complete"), end='\r')
        except:
            pass
        i=i+1
        cg[course_code] = avg_gpa #adding pair to dictionary

    print("sorting\n")
    courses_inorder = (sorted(cg, key=cg.get))

    cw = csv.writer(open((args.output + ".csv"),'w'))
    for course in courses_inorder:
        print(course + ": " + str(cg[course]))
        #write output to csv to view later
        cw.writerow([course, cg[course]])
else:
    #check arguments
    if args.print == []:
        args.print = ["out.csv",1000]
    if len(args.print) == 1:
        try:
            args.print = ["out.csv",int(args.print[0])]
        except:
            args.print = [str(args.print[0]),1000]

    # load course codes
    try:
        with open((args.print[0]), newline='') as f:
            reader = csv.reader(f)
            for rows in reader:
                if int(rows[0].split(" ")[-1]) <= int(args.print[1]):
                    print(rows[0] + ": " + rows[1])
    except Exception as e:
        try:
            with open((args.print[1]), newline='') as f:
                reader = csv.reader(f)
                for rows in reader:
                    if int(rows[0].split(" ")[-1]) <= int(args.print[0]):
                        print(rows[0] + ": " + rows[1])
        except Exception as u:
            print("Please enter file and/or max course code")
            exit()
