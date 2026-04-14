# Facial-Recognition-Processing-for-Home-Assistant
Home assistant facial recognition processing using pyscript and Exadel CompreFace.


## Prerequisites. ##

1. Install Home Assistant integration Pyscript. [https://hacs-pyscript.readthedocs.io/en/latest/]
2. Install Home Assistant application Grafana. Add plugin: **dalvany-image-panel** 
3. Install and setup CompreFace. I recommend you host CompreFace on your own server using Docker compose. Adjust docker compose file with port 7215..this is the port my Pyscript is setup to use. [https://github.com/exadel-inc/CompreFace?tab=readme-ov-file]
  

## Installation. ##
1. Copy **aiface.py** to pyscript directory in home assistant.
2. Change the x_api_key in aiface.py to your api key from your installation of CompreFace.
3. Change the URL_CURL and URL_CURL_COMPRE, in aiface.py to your ip addresses. URL_CURL is your home assistant ip address webhook. URL_CURL_COMPRE is your CompreFace hosted IP address.
4. Install sqlite database using script **subjects.db**. Place in location **/config/ai_objects_db/ai_subjects.db**
5. Create directories /config/www/capture/ and /config/AI. In /config/www/capture create subdirectories named with areas in and around your home. So for example /config/www/capture/driveway, /config/www/capture/mainfloor (as many of these areas that you have cameras in and plan on doing face recognition in).
6. Put or merge with your configuration **template_sensor.yaml**.  This will create **sensor.face_detected_occurrence**.
7. Put or merge with your configuration **input-text.yaml**. This will create **input_text.faces_selected**  **input_text.face_confidence** **input_text.capture_path**  **input_text.full_ai_stored_path** **input_text.local_file_path**.
8. Create helper pairs for each area (driveway,mainfloor, etc) you are doing face recognition in **input_text.driveway_mask** and **input_text.driveway_camera_filename**.
9. 
   
