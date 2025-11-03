


Follow these steps to clone and run the Django version of the project locally.

Clone the Repository

Clone **only the `django` branch** from GitHub:

INSTRUCTIONS
git clone -b django https://github.com/UNO-CSCI4830/Disable-Short-form-Content.git
cd Disable-Short-form-Content
python -m venv .venv                        <------------#creates the virtual environment
.venv\Scripts\activate  
pip install -r requirements.txt                <---------#install requirements
create new .env file, paste contents from file sent via discord
python manage.py migrate              <--------------#set up local database
python manage.py runserver            <------------------#run server
#Click on 127.0.0.1:8000 to reach website
