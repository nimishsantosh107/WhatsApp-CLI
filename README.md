# WhatsApp-CLI

This is for y'all firefox users, chrome version is at https://github.com/zvovov/whatsapp-web  
It only requires firefox installed on your machine and for a one time login into your whatsapp account. after that you can chill.

## Instructions:
*	set up a new **firefox profile** by typing `about:profiles` in the URL bar and create a new profile in any directory **(profile will be a directory PROFILE_DIR)**
*	Open new profile in new browser and login to whatsapp web **(one time thing)**
*	Edit the config dict in **chat.py** to the set the location of the **PROFILE_DIR**.
*	Run the cli client using`python chat.py [NAME]`
*	Switch message thread using `SENDTO [NAME]`

## Requirements:
*	Selenium 
*	Geckodriver

### Additional addons in the future?:
*	improve use experience
*	imgcat

### NOTE: Proper documentation and instructions later, for now hmu.
*P.S This is in very early alpha? but works really well for an alpha :P*