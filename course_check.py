import time
import sys
import os  
import logging

from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

try:
    from mcgill_login import uname, pwd
except:
    pass

search_url = "https://horizon.mcgill.ca/pban1/bwskfcls.P_GetCrse"
login_url = "https://horizon.mcgill.ca/pban1/twbkwbis.P_ValLogin"
logout_url = "https://horizon.mcgill.ca/pban1/twbkwbis.P_Logout"

chrome_options = Options()
chrome_options.add_argument("--headless")
# chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--remote-debugging-port=9222')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def login(username, password):
    #get login page
    driver.get(login_url)
    time.sleep(2)

    #give email
    # uname = driver.find_element_by_xpath("//*[@id=\"mcg_un\"]")
    uname = driver.find_element(By.XPATH, "//td[@class='login_table_guest']/input[@id='UserID']")

    #give password
    # pw = driver.find_element_by_xpath("//*[@id=\"mcg_pw\"]")
    pw = driver.find_element(By.XPATH, "//td[@class='login_table_guest']/input[@id='PIN']")

    uname.send_keys(username)
    pw.send_keys(password)

    time.sleep(1)

    submit = driver.find_element(By.XPATH, "//td/input[@id='mcg_id_submit']")

    submit.click()

    # Close the WebDriver
    # driver.quit()

    return driver.page_source 

def logout():
    driver.get("https://horizon.mcgill.ca/pban1/twbkwbis.P_Logout")
    pass

def check_availability(course, crn, term="Fall 2024", dept="MGCR"):

    """
        Returns:
            dict: keys are info fields and values are status. eg.
            dict['status']: "Active"
            dict['remaining']: 3

    """
    driver.get("https://horizon.mcgill.ca/pban1/bwskfcls.p_sel_crse_search")
    # select = Select(driver.find_element_by_id("term_input_id"))

    # select = Select(driver.find_element_by_xpath("/html/body/div[3]/form/table/tbody/tr/td/select"))
    select = Select(driver.find_element(By.NAME, "p_term"))

    print("Checking --> ")
    print(dept, " ", course, ": ",crn)
    print("   ")

    select.select_by_visible_text(term)

    driver.find_element(By.XPATH, "/html/body/div[3]/form/input[3]").click()

    sel = driver.find_elements(By.NAME, "sel_subj")[1]
    select = Select(sel)
    select.select_by_value(dept)
        
    
    #submit department
    driver.find_element(By.NAME, "SUB_BTN").click()
    logging.debug(driver.current_url)

    #select course
    rows = driver.find_elements(By.TAG_NAME, "tr")
    for row in rows:
        try:
            course_num = row.text.split()[0]
        except IndexError:
            continue
        else:
            if course_num == course:
                row.find_element(By.NAME, "SUB_BTN").click()
                break

    rows = driver.find_elements(By.TAG_NAME, "tr")
    info_dict = {}
    for row in rows:
        if crn in row.text:
            #get info from data row
            rem = row.find_elements(By.TAG_NAME, "td")[12].text
            rem_wait = row.find_elements(By.TAG_NAME, "td")[15].text
            status = row.find_elements(By.TAG_NAME, "td")[19].text
            info_dict["spots"] = rem
            info_dict["wait_spots"] = rem_wait
            info_dict["status"] = status

            if(int(rem) > 0):
                logging.info(f"Attempting to Register for course: {dept} {course} {crn} {term}")
                # Checkbox is the only input element in the row
                row.find_element(By.TAG_NAME, "input").click()

                driver.find_element(By.XPATH, "//input[@value='Register']").click()

                # # sel = driver.find_elements_by_xpath("/html/body/div[3]/form/table[4]/tbody/tr[2]/td[2]/select")
                # # select = Select(sel)
                # # select.select_by_value("LW")

                # dropdown = Select(driver.find_element_by_id('waitaction_id1'))
                # dropdown.select_by_value("LW")

                # # driver.find_element_by_xpath("/html/body/div[3]/form/table[4]/tbody/tr[2]/td[2]/select/option[2]").click()

                # driver.find_element(By.XPATH, "/html/body/div[3]/form/input[19]").click()
                info_dict["register_attempted_crn"] = crn

            return info_dict 
    
    
if __name__ == "__main__":
    login(uname, pwd)
    rem = check_availability("250", "7824")
