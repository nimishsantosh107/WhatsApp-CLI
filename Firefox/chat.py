import os
import re
import sys
import time
import sched
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException as WebDriverException

config = {
    'MSG_INTERVAL': 5,                      # Time (seconds). Recommended value: 5
    'WW_URL': "https://web.whatsapp.com/",
    'PROFILE_PATH': "/Users/nimish/Library/Application Support/Firefox/Profiles/s9ggtid9.whatsappcli"
}

incoming_scheduler = sched.scheduler(time.time, time.sleep)
last_printed_msg = None
last_thread_name = ''

try:
    def main():
        global last_thread_name

        if len(sys.argv) > 1:
            #set firefox options
            options = webdriver.FirefoxOptions()
            options.add_argument('-headless')
            options.add_argument("--disable-extensions")

            #set profile path
            profile = webdriver.FirefoxProfile(config['PROFILE_PATH'])

            #build driver
            driver = webdriver.Firefox(options=options,firefox_profile=profile)
            driver.get(config['WW_URL'])

            # prompt user to connect device to WW
            while True:
                isConnected = input("\n\t\033[1;36mPHONE CONNECTED? y/n: \033[0m")
                if isConnected.lower() == 'y':
                    break

            # check if connected to WhatsAppWeb
            assert "WhatsApp" in driver.title

            chooseReceiver(driver)

            # getting true name of contact/group
            last_thread_name = driver.find_element(By.XPATH, '//*[@id="main"]/header//span[contains(@dir, "auto")]').text

            # start background thread(receive messages)
            incoming_thread = threading.Thread(target=startGetMsg, args=(driver,))
            incoming_thread.daemon = True
            incoming_thread.start()

            # main code
            while True:
                msg = input().strip()
                if len(msg) > 7 and 'SENDTO ' in msg[:7]:
                        chooseReceiver(driver, receiver=msg[7:])
                elif msg == 'STOPSENDING':
                    print("\t\033[1;31mYOU WILL ONLY RECEIVE MSGS NOW.\n\tPRESS Ctrl+C TO EXIT.\033[0m")
                    # TODO: stop the incoming_scheduler event
                    break
                else:
                    sendMsg(driver, msg)

        else:
            sys.exit("\n\033[1;31mERROR: MISSING NAME OF CONTACT/GROUP\npython chat.PY <name>\033[0m")

        # open all contacts page
        # driver.find_element(By.TAG_NAME, "button").click()


    def sendMsg(driver, msg):
        """
        Type 'msg' in 'driver' and press RETURN
        """
        # select correct input box to type msg
        input_box = driver.find_element(By.XPATH, '//*[@id="main"]//footer//div[contains(@contenteditable, "true")]')
        # input_box.clear()
        input_box.click()

        action = ActionChains(driver)
        action.send_keys(msg)
        action.send_keys(Keys.RETURN)
        action.perform()


    def startGetMsg(driver):
        """
        Start schdeuler that gets incoming msgs every MSG_INTERVAL seconds
        """
        incoming_scheduler.enter(config['MSG_INTERVAL'], 1, getMsg, (driver, incoming_scheduler))
        incoming_scheduler.run()


    def getMsg(driver, scheduler):
        """
        Get incoming msgs from the driver repeatedly
        """
        global last_printed_msg

        # print conversation name
        curr_thread_name = printThreadName(driver)

        try:
            # get all msgs
            all_msgs = driver.find_elements(By.XPATH, '//*[@id="main"]//div[contains(@class, "message")]')

            # check if there is atleast one message in the chat
            if len(all_msgs) >= 1:
                last_msg_outgoing = outgoingMsgCheck(all_msgs[-1])
                last_msg_sender, last_msg_text = getMsgMetaInfo(all_msgs[-1])
                msgs_present = True
            else:
                msgs_present = False
        except Exception as e:
            print(e)
            msgs_present = False

        if msgs_present:
            # if last msg was incoming
            if not last_msg_outgoing:
                # if last_msg is already printed
                if last_printed_msg == last_msg_sender + last_msg_text:
                    pass
                # else print new msgs
                else:
                    print_from = 0
                    # loop from last msg to first
                    for i, curr_msg in reversed(list(enumerate(all_msgs))):
                        curr_msg_outgoing = outgoingMsgCheck(curr_msg)
                        curr_msg_sender, curr_msg_text = getMsgMetaInfo(curr_msg)

                        # if curr_msg is outgoing OR if last_printed_msg is found
                        if curr_msg_outgoing or last_printed_msg == curr_msg_sender + curr_msg_text:
                            # break
                            print_from = i
                            break
                    # Print all msgs from last printed msg till newest msg
                    for i in range(print_from + 1, len(all_msgs)):
                        msg_sender, msg_text = getMsgMetaInfo(all_msgs[i])
                        last_printed_msg = msg_sender + msg_text
                        
                        txt = msg_sender.split(']')
                        txt[0] = re.search(r'([0-9]?[0-9]):([0-9]?[0-9]) [AP]M',txt[0]).group()
                        msg_sender = "["+txt[0]+"]"+txt[1]
                        
                        msg_sender = "\033[1;34m"+msg_sender+"\033[0m"
                        msg_text = "\033[1;32m"+msg_text+"\033[0m"
                        print(msg_sender + msg_text)

        # add the task to the scheduler again
        incoming_scheduler.enter(config['MSG_INTERVAL'], 1, getMsg, (driver, scheduler,))


    def outgoingMsgCheck(webdriver_element):
        """
        Returns True if the selenium webdriver_element has "message-out" in its class.
        False, otherwise.
        """
        for _class in webdriver_element.get_attribute('class').split():
            if _class == "message-out":
                return True
        return False


    def getMsgMetaInfo(webdriver_element):
        """
        Returns webdriver_element's sender and message text.
        Message Text is a blank string, if it is a non-text message
        TODO: Identify msg type and print accordingly
        """
        # check for non-text message
        try:
            msg = webdriver_element.find_element(By.XPATH, './/div[contains(@class, "copyable-text")]')
            msg_sender = msg.get_attribute('data-pre-plain-text')
            msg_text = msg.find_elements(By.XPATH, './/span[contains(@class, "selectable-text")]')[-1].text
        except IndexError:
            msg_text = ""
        except Exception:
            msg_sender = ""
            msg_text = ""

        return msg_sender, msg_text


    def printThreadName(driver):
        global last_thread_name
        curr_thread_name = driver.find_element(By.XPATH, '//*[@id="main"]/header//span[contains(@dir, "auto")]').text
        if curr_thread_name != last_thread_name:
            last_thread_name = curr_thread_name
            print("\n\033[1;36mSENDING MESSAGES TO:\033[0m",curr_thread_name)
        return curr_thread_name


    def chooseReceiver(driver, receiver=None):
        # search name of friend/group
        friend_name = receiver if receiver else ' '.join(sys.argv[1:])
        input_box = driver.find_element(By.XPATH, '//*[@id="side"]//input')
        input_box.clear()
        input_box.click()
        input_box.send_keys(friend_name)
        input_box.send_keys(Keys.RETURN)
        printThreadName(driver)


    if __name__ == '__main__':
        main()

except AssertionError as e:
    sys.exit("\n\t\033[1;31mCANNOT OPEN WhatsApp WEB URL.\033[0m")

except KeyboardInterrupt as e:
    sys.exit("\n\t\033[1;31mEXITING\033[0m")

except WebDriverException as e:
	sys.exit("\n\t\033[1;31mGECKODRIVER ERROR. READ THE ABOVE ERROR (IF ANY)\033[0m")