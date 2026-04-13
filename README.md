# Facial-Recognition-Processing-for-Home-Assistant
Home assistant facial recognition processing using pyscript.


## Prerequisites.

1. Install Home assistant integration Pyscript. [https://hacs-pyscript.readthedocs.io/en/latest/]
2. Copy aiface.py to pyscript directory in home assistant.
3. Install and setup CompreFace. I recommend you host CompreFace on your own server using Docker. Adjust docker compose file with port 7215..this is the port my script is setup to use. [https://github.com/exadel-inc/CompreFace?tab=readme-ov-file]
4. Change the x_api_key in aiface.py to your api key from your installation of CompreFace.
5. Change the URL_CURL and URL_CURL_GORTASH to your ip addresses. URL_CURL is your home assistant ip address webhook. URL_CURL_GORTASH is your CompreFace hosted IP address and port from step 3. 
