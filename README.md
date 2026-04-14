# Facial-Recognition-Processing-for-Home-Assistant
Home assistant facial recognition processing using pyscript and Exadel CompreFace.


## Prerequisites. ##

1. Install Home Assistant integration Pyscript. [https://hacs-pyscript.readthedocs.io/en/latest/]
2. Install Home Assistant application Grafana. Add plugins: **dalvany-image-panel** 
3. Install and setup CompreFace. I recommend you host CompreFace on your own server using Docker compose. Adjust docker compose file with port 7215..this is the port my Pyscript is setup to use. [https://github.com/exadel-inc/CompreFace?tab=readme-ov-file]
  

## Installation. ##
1. Copy aiface.py to pyscript directory in home assistant.
2. Change the x_api_key in aiface.py to your api key from your installation of CompreFace.
5. Change the URL_CURL and URL_CURL_COMPRE to your ip addresses. URL_CURL is your home assistant ip address webhook. URL_CURL_COMPRE is your CompreFace hosted IP address and port from step 3.
6. Install sqlite database using script subjects.db. Place in **/config/ai_objects_db/ai_subjects.db**
7. Create directories /config/www/capture/ and /config/AI. In /config/www/capture create subdirectories named with areas in and around your home. So for example /config/www/capture/driveway, /config/www/capture/mainfloor (as many of these areas that you have cameras in and plan on doing face recognition in).
8. Install sensor face_detected_occurrence from **template_sensor.yaml**.
   
