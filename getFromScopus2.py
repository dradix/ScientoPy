import paperUtils
import time
import os
from selenium import webdriver
import shutil
import random
from termcolor import colored
import re
import csv
import math

BASE_SCOPUS_URL = "https://www-scopus-com.ezproxyegre.uniandes.edu.co:8843"
DOWNLOAD_FOLDER = "/home/jpruiz84/scopusData"
DATAIN_FOLDER = "./idsData/"
SEARCH_STRING = "%22FPGA%22+OR+%22FPGAs%22+OR+%22Field+Programmable+Gate+Array%22+OR+%22Field-programmable+gate+array%22+OR+%22Field-programmable+gate+arrays%22+OR+%22Field programmable+gate+arrays%22"

SEARCH_URL = "https://www-scopus-com.ezproxyegre.uniandes.edu.co:8843/results/results.uri?sort=plf-f&src=s&sid=cdc4695c7a613d16887e1e1b1666c35d&sot=a&sdt=a&sl=155&s=TITLE-ABS-KEY%28SEARCH_STRING%29+AND+ORIG-LOAD-DATE+%3e+START_EPOCH+AND+ORIG-LOAD-DATE+%3c+END_EPOCH&origin=searchadvanced&editSaveSearch=&txGid=bf84f20c3def4d7b41d0e39fd8489f62"

RELOAD_MIN_DELAY = 15
RELOAD_MAX_DELAY = 30
LOAD_DMIN = 3
LOAD_DMAX = 5

START_LOAD_DATE = "2000-1-1"
END_LOAD_DATE = "2020-1-1"

NUM_PAPER_MAX = 1999
NUM_PAPER_MIN = 200


def startWebDriver(start_url):
  print("Starting WebDriver...")

  fp = webdriver.FirefoxProfile()

  fp.set_preference("browser.download.folderList",2)
  fp.set_preference("browser.download.manager.showWhenStarting",False)
  fp.set_preference("browser.download.dir", DOWNLOAD_FOLDER)
  fp.set_preference("browser.helperApps.neverAsk.saveToDisk","text/csv")

  driver = webdriver.Firefox(firefox_profile=fp)
  driver.set_page_load_timeout(30)
  driver.get(start_url)
  driver.maximize_window()
  driver.implicitly_wait(30)

  return driver

def scopusLogIn(driver):
  print("Login...")

  # Log in
  user = driver.find_element_by_css_selector("#capa1 > form:nth-child(5) > font:nth-child(1) > input:nth-child(1)")
  password = driver.find_element_by_css_selector("#capa1 > form:nth-child(5) > font:nth-child(1) > input:nth-child(5)")

  user.clear()
  user.send_keys("jpruiz84")
  password.clear()
  password.send_keys("clavetaio")
  login = driver.find_element_by_css_selector("#botingre")
  login.click()

def scopusSearchItem(driver, searchString, startEpoch, endEpoch):
  get_url = SEARCH_URL
  get_url = get_url.replace("SEARCH_STRING", searchString)
  get_url = get_url.replace("START_EPOCH", str(int(startEpoch)))
  get_url = get_url.replace("END_EPOCH", str(int(endEpoch)))

  while True:

    print("Loading page...")
    driver.get(get_url)

    try:

      time.sleep(random.randint(LOAD_DMAX, LOAD_DMAX))
      documentHeader = driver.find_element_by_css_selector(".documentHeader").text

      if re.findall("\d+", documentHeader.replace(",", "")) == []:
        totalResults = 0
      else:
        totalResults = int(re.findall("\d+", documentHeader.replace(",", ""))[0])

      return totalResults

    except:
      reloadDelay = random.randint(RELOAD_MIN_DELAY, RELOAD_MAX_DELAY)
      print colored("Error to load, wait (seg): " + str(reloadDelay), 'red')
      time.sleep(reloadDelay)
      continue


def scopusDownloadList(driver, countDownloads):

  try:
    # Click on all
    driver.find_element_by_css_selector("#showAllPageBubble").click()
    driver.find_element_by_css_selector("#selectAllMenuItem > span:nth-child(2) > span:nth-child(1) > ul:nth-child(1) > li:nth-child(1) > label:nth-child(3)").click()

    # Clikc on export results
    driver.find_element_by_css_selector("#export_results").click()

    # Export to cvs
    time.sleep(random.randint(LOAD_DMAX, LOAD_DMAX))
    driver.find_element_by_css_selector("#export_results").click()

    if(countDonwloads == 0):
      # CSV (Excel)
      time.sleep(random.randint(LOAD_DMAX, LOAD_DMAX))
      driver.find_element_by_css_selector("li.radio-inline:nth-child(4) > label:nth-child(2)").click()
      # Bibliographical information
      biographical = driver.find_element_by_css_selector(
        "#exportCheckboxHeaders > th:nth-child(2) > span:nth-child(1) > label:nth-child(2)")
      biographical.click()
      # Abstract and Keywords
      abstract = driver.find_element_by_css_selector(
        "#exportCheckboxHeaders > th:nth-child(3) > span:nth-child(1) > label:nth-child(2)")
      abstract.click()

    # Export button
    driver.find_element_by_css_selector("#exportTrigger").click()

    print("Downloading...")
    # Wait until file is created
    while not os.path.isfile(DOWNLOAD_FOLDER + "/scopus.csv"):
      time.sleep(0.5)

    # Wait until download is finished
    while os.path.isfile(DOWNLOAD_FOLDER + "/scopus.csv.part"):
      time.sleep(0.5)

    return True

  except:
    return False





# Start main program ********************************************

print("Get CSV from Scopus")

# Remove all files from download folder
try:
  shutil.rmtree(DOWNLOAD_FOLDER)
except:
  print("No dowwload folder")

ofile = open("getScopusResults.csv", 'w')

fieldnames = ["Start", "End", "Papers", "Time", "startEpoch", "endEpoch"]

writer = csv.DictWriter(ofile, fieldnames=fieldnames, dialect=csv.excel_tab)

writer.writeheader()


# Log in to scopus
driver = startWebDriver(BASE_SCOPUS_URL)
scopusLogIn(driver)

startEpoch = time.mktime(time.strptime(START_LOAD_DATE, "%Y-%m-%d"))
endEpoch = time.mktime(time.strptime(END_LOAD_DATE, "%Y-%m-%d"))
totalEndEpoch = endEpoch
endEpochPrev = endEpoch


totalPapersToFind = scopusSearchItem(driver, SEARCH_STRING, startEpoch, endEpoch)
print("totalPapersToFind: " + str(totalPapersToFind))

papersCount = 0
countDonwloads = 0
fDividedByTwo = False
startTime = time.time()
while True:

  print("")
  print(time.strftime('Start time: %Y-%m-%d %H:%M:%S', time.localtime(startEpoch)))
  print(time.strftime('End time: %Y-%m-%d %H:%M:%S', time.localtime(endEpoch)))
  totalResults = scopusSearchItem(driver, SEARCH_STRING, startEpoch, endEpoch)
  print("totalResults: " + str(totalResults))

  # If total inside acceptable range
  if((totalResults <= NUM_PAPER_MAX) and (totalResults >= NUM_PAPER_MIN)):
    if(scopusDownloadList(driver, countDonwloads) == False):
      reloadDelay = random.randint(RELOAD_MIN_DELAY, RELOAD_MAX_DELAY)
      print colored("Error to load, wait (seg): " + str(reloadDelay), 'red')
      time.sleep(reloadDelay)
      continue

    countDonwloads += 1
    dataWrite = {}
    dataWrite["Start"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(startEpoch))
    dataWrite["End"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(endEpoch))
    dataWrite["Papers"] = totalResults
    dataWrite["Time"] = int(time.time() - startTime)
    dataWrite["startEpoch"] = str(startEpoch)
    dataWrite["endEpoch"] = str(endEpoch)
    writer.writerow(dataWrite)
    papersCount +=  totalResults
    print("Good totalResults found: " + str(totalResults))
    print("TOTAL papersCount: " + str(papersCount) +  ", from: " + str(totalPapersToFind))

    number = "scopus_%03d-%06d" % (countDonwloads, papersCount)
    os.rename(DOWNLOAD_FOLDER + "/scopus.csv",
              "/home/jpruiz84/scopusData/{0}.csv".format(number))


    if(papersCount >= totalPapersToFind):
      break

    startEpochPrev = startEpoch
    startEpoch = endEpoch - 1
    endEpoch = startEpoch + (endEpoch - startEpochPrev) * 2
    fDividedByTwo = False
    continue

  # If more than the needed, get next half
  if(totalResults > NUM_PAPER_MAX):
    endEpochPrev = endEpoch
    endEpoch = startEpoch + int((endEpoch - startEpoch)/2)
    fDividedByTwo = True
    continue

  # If zero, take up division
  if((totalResults == 0) and (fDividedByTwo == True)):
    startEpoch = endEpoch - 1
    endEpoch = endEpochPrev
    fDividedByTwo = False
    continue

  # If less than the needed, duplicate time
  if(totalResults < NUM_PAPER_MIN):
    endEpoch = startEpoch + int((endEpoch - startEpoch)*1.33)

    # If final results
    if(endEpoch >= totalEndEpoch):

      if (scopusDownloadList(driver) == False):
        reloadDelay = random.randint(RELOAD_MIN_DELAY, RELOAD_MAX_DELAY)
        print colored("Error to load, wait (seg): " + str(reloadDelay), 'red')
        time.sleep(reloadDelay)
        continue

      countDonwloads += 1
      dataWrite = {}
      dataWrite["Start"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(startEpoch))
      dataWrite["End"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(endEpoch))
      dataWrite["Papers"] = totalResults
      dataWrite["Time"] = int(time.time() - startTime)
      dataWrite["startEpoch"] = str(startEpoch)
      dataWrite["endEpoch"] = str(endEpoch)
      writer.writerow(dataWrite)
      papersCount += totalResults
      print("Good end totalResults found: " + str(totalResults))
      print("TOTAL papersCount: " + str(papersCount) + ", from: " + str(totalPapersToFind))

      number = "scopus_%03d-%06d" % (countDonwloads, papersCount)
      os.rename(DOWNLOAD_FOLDER + "/scopus.csv",
                "/home/jpruiz84/scopusData/{0}.csv".format(number))

      break
    fDividedByTwo = False
    continue

  # If final results
  if (endEpoch >= totalEndEpoch):
    print("END by totalEndEpoch")
    break

ofile.close()

#driver.close()


