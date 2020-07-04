import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup

driver = webdriver.Firefox(executable_path="./geckodriver") #relative path
url = "https://enroll.wisc.edu/search?term=1212" #local varibale is all caps
WAITTIME = 10 # seconds

driver.get(url) #navigate to the page
input()
time.sleep(2)
classes = set()

prev = ""
course = " "

actions = ActionChains(driver)
actions.send_keys(Keys.PAGE_DOWN)

fin = 1
while prev != course:
    prev = course
    for course_path in driver.find_elements_by_xpath("/html/body/div[1]/div/div/div/div/md-card[2]/md-content/md-virtual-repeat-container/div/div[2]/md-list/md-list-item/div"):
        try:
            html = course_path.get_attribute('innerHTML')
            soup = BeautifulSoup(html, "lxml")
            course = soup.find('div', {"class":'result__name flex-80'}).strong.text.strip()
            classes.add(course)
        except:
            pass
    driver.find_element_by_xpath("/html/body/div[1]/div/div/div/div/md-card[2]").click()
    actions.perform()
    time.sleep(1)
print(sorted(classes))

# cw = csv.writer(open("classes.csv",'wb'))
# cw.writerow(list(cols))
