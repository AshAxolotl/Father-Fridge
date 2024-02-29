# Discord Bot Father Fridge
 a discord bot for VHions

(this bot is for personal use so i will not fix or explain any issues!)



## Setup bot
##### 1. Create a file named bot_config.py with:
   ```python
   # Base Settings (needed  to run)
   TOKEN = ""
   DEBUG = True 
   COMMAND_PREFIX = "!" 
   
   # Extra Settings 
   OWNER_USERIDS = {}
   
   # Google forms
   BASE_FORM_ID = ""
   SERVICE_ACCOUNT = {}
   ```

##### 2. Create virtual environment:
   ```
   $ python3 -m venv .venv
   $ source .venv/bin/activate (Windows: .venv\Scripts\activate.bat)
   ```

##### 3. Install dependies:
   ```
   $ pip install -r requirements.txt
   ```
