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
ap.add_argument('-w', '--write', nargs='?', const='classes',
                help='file to write course codes to')
ap.add_argument('-o', '--output', default='out', help='output filename')

args = ap.parse_args()
print(args)
# exit()
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
                classes.add(course.replace("&"," "))
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
    with open((args.read + '.csv'), newline='') as f:
        reader = csv.reader(f)
        classes = list(reader)[0]

#initialize disctionary to store course GPA pair
cg = dict()

print("getting grades")
for course_code in classes:
    #madgrades api query course code to get internal madgrades ID
    url = 'https://api.madgrades.com/v1/courses'
    auth = {'Authorization': 'Token token=930be378f74e4bc9aeba6d982586cfbf'}
    payload = {'query': course_code}
    r = json.loads(requests.get(url, params=payload, headers=auth).text)
    #madgrades api get grades using madgrades ID
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
    cg[course_code] = avg_gpa #adding pair to dictionary

print("sorting\n")
courses_inorder = reversed(sorted(cg, key=cg.get))

cw = csv.writer(open((args.output + ".csv"),'w'))
for course in courses_inorder:
    print(course + ": " + str(cg[course]))
    #write output to csv to view later
    cw.writerow([course, cg[course]])
