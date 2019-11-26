#Auth
The quickest way to obtain Google API Credentials
is to go https://developers.google.com/calendar/quickstart/python  
click the button ***Enable the Google Calendar API***  
follow the wizard -> download ***credentials.json***  

store ***credentials.json*** safely and set his path in ***settings.json***  
at the first start an action may be required (click on a link and google login to authorize the token),  
in future no action will be required thanks to ***token.pickle*** which will store the authentication token.

# Management
Google API can be managed (created,removed,buy a quota, etc...) through google developer console

# calendar_id
to obtain calendar_id turn to true "show_calendars" in settings.json and check the logs.  
remember to turn "show_calendars" to false.

# to Docker
```
docker build -t <image_name> .
docker run --name <container_name> -v $(pwd)/src/settings.json:/app/src/settings.json:ro -v $(pwd)/src/credentials.json:/app/src/credentials.json:ro -v $(pwd)/src/token.pickle:/app/src/token.pickle:ro -e BOT_TOKEN=$BOT_TOKEN -e BOT_ENDPOINT=$BOT_ENDPOINT <image_name>
```