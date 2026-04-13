"""
Component that will perform facial recognition via CompPreFace AI api.
Places green boxes around objects that are within the selected confidence % and
slots them into the "object" sub-directory.


version 1.1 May 30, 2022
version 1.2 Mar 30, 2025
version 1.3 Mar 30, 2025
version 1.4 Aug 04, 2025
version 2.0 Mar 18, 2026
version 2.1 Mar 22, 2026

rev.1: Changed to try and reduce image size to 800x600 for MMS limit. -May 30th 2022
rev.2: Removed MMS not being used anymore -Mar 30th 2025
rev.3: Add LLM vision file save and json entry
rev.4: Added ability to process infile_path with appended camera area directory eg (www/capture/driveway). Removed ability to process multiple incoming files. So can only do one at a time now.
rev.2.0: Moved from executing on separate machine to Home Assistant machine using pyscript. Removed LLM vision file. Changed to use asyncio as well.
rev.2.1: Fixed all blocking calls — added async def to methods, awaited @pyscript_executor calls,
         wrapped blocking I/O (Image.open, save, getsize, os.path.exists/mkdir, DB) in executors,
         fixed bare asyncio.sleep(5) → await asyncio.sleep(5).
"""

import base64
import sqlite3
import datetime
# import pytz
from zoneinfo import ZoneInfo
import io
import json
import math
import os
import sys
import argparse
import uuid
from typing import Tuple
import requests
# from PIL import Image, ImageDraw
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import glob
import time
import asyncio
import concurrent.futures


DATETIME_FORMAT   = "%Y-%m-%d_%H:%M:%S"
BOX               = "box"
RED               = (255, 0, 0)
GREEN             = (0, 128, 0)
HTTP_OK           = 200
URL_CURL          = "http://192.x.x.x:8123/api/webhook/sensor_ai_face_data"
URL_CURL_GORTASH  = "http://192.x.x.x:7215/api/v1/recognition/recognize?limit=0&prediction_count=1&det_prob_threshold=0.5"
# x_api_key         = '5e7a4ecf-65ca-454f-a6e4-064d1ffe719a'
# x_api_key         = '281a1659-2b7e-498c-bf2f-fd71d417b152'
# x_api_key         = '9f24ef6e-f04d-4996-9b20-6b2ead86fa13'
x_api_key         = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx'
# MST               = pytz.timezone('America/Edmonton')
# MST               = ZoneInfo('America/Edmonton')
DBCONN            = sqlite3.connect('/config/ai_objects_db/ai_subjects.db')
CURSOR            = DBCONN.cursor()
WIDTH             = 1080
HEIGHT            = 720
MIN_WIDTH	  = 800
MIN_HEIGHT        = 600


class FaceRecognitionEntity:
    """Perform a facial recognition."""

    def __init__(
        self,
        path_in,
        image,
        image_area,
        target,
        confidence,
        local_path_ha,
        event_datetime,
        save_file_folder,

    ):
        self.image                = image
        self._path_in             = path_in
        self._target              = target
        self._confidence          = confidence
        self._local_path_ha       = local_path_ha
        self._event_datetime      = event_datetime
        self._name                = 'face'
        self._area                = image_area
        self._state               = None
        self._targets_confidences = [None] * len(self._target)
        self._targets_found       = [0] * len(self._target)
        self._predictions         = {}
#        self._last_detection      = None
        self._image_width         = None
        self._image_height        = None
        self._image               = image
        if save_file_folder:
            self._save_file_folder = save_file_folder


    async def generate(self):

        """Run the process on an image"""

        await self.process_image()



    async def process_image(self):
        """Process an image."""
#        print(self._image)
        log.info(f'Processing {self._image} file')
        img_tmp = await asyncio.to_thread(Image.open, self._path_in + self._image)
        self._image_width, self._image_height = img_tmp.size
#        self._image_width, self._image_height = Image.open(self._path_in + self._image).size
#        print('Size ',self._image_width, self._image_height)
        self._state = None
#        print('Area: ',self._area)
        self._targets_confidences = [None] * len(self._target)
        self._targets_found = [0] * len(self._target)
        self._predictions = {}
        await self.detect()

#        print('Predictions', self._predictions)
#        log.warning(f'Preds: {self._predictions}')
        if self._predictions:
            for i, target in enumerate(self._target):
                raw_confidences = [pred["confidence"] for pred in self._predictions if pred["label"] == target]
                self._targets_confidences[i] = [round(float(confidence) * 100, 1) for confidence in raw_confidences]
#                print('confidence: ', self._targets_confidences[i])
#                self._targets_found[i] = len([val for val in self._targets_confidences[i] if val >= self._confidence])
                self._targets_found[i] = len([
                                              val for val in self._targets_confidences[i]
                                              if float(val) >= float(self._confidence)
                                            ])
#                print( self._targets_found[i])
            self._state = sum(self._targets_found)


            labels = [pred["label"] for pred in self._predictions]
            tconfidences = len([pred["confidence"] for pred in self._predictions if pred["label"] == target])

            if self._state > 0:
               await self.save_image(self._image, self._predictions, self._target, self._save_file_folder)
            else:
               log.info(f'No faces detected at the confidence level specified')

    async def save_image(self, image, predictions, target, directory):
        """Save a timestamped image with bounding boxes around targets."""

#        img= Image.open((self._path_in + self._image) ,'r')
        img = await asyncio.to_thread(Image.open, self._path_in + self._image)
        draw = ImageDraw.Draw(img)

        for singletarget in target:
            flag_target_found = False
            targetimg = await asyncio.to_thread(Image.open, self._path_in + self._image)
#            targetimg = Image.open((self._path_in + self._image) ,'r')
            draw = ImageDraw.Draw(targetimg)
            for prediction in predictions:
                prediction_confidence = math.floor(round(float(prediction["confidence"]) * 100, 1))
                if (prediction["label"] == singletarget and float(prediction_confidence) >= float(self._confidence)  ):
                      flag_target_found = True
                      pctout = prediction_confidence
                      box = self.get_box(prediction, self._image_width, self._image_height)
#                      print('Green ' , box)
                      self.draw_box(
                           draw,
                           box,
                           self._image_width,
                           self._image_height,
                           text=(singletarget+' '+str(prediction_confidence)),
                           color=GREEN )

            if flag_target_found:
               gen_file_name = "{0}_{1}_{2}_pct_{3:.0f}_{4}.jpg".format(self._name, singletarget, self._area, pctout, self._event_datetime)
#               print("Generated file name: ", gen_file_name)
               latest_save_path = directory + singletarget +  "/"  + gen_file_name
#               print("Writing out: ", latest_save_path)
               await asyncio.to_thread(targetimg.save, latest_save_path)
               file_size = (await asyncio.to_thread(os.path.getsize, latest_save_path)) / 1000
               log.info(f'Saving file to {latest_save_path} file')
               uid=str(uuid.uuid4())[:8] + "-0"
               await self.create_curl_json( gen_file_name, singletarget, pctout, uid )
# 7 seconds gives enough time for the sensor.face_detected_occurrence to work properly per occurrence

               await asyncio.sleep(5)



    def get_box(self,prediction, img_width, img_height):
        """
        Return the relative bounding box coordinates.

        Defined by the tuple (y_min, x_min, y_max, x_max)
        where the coordinates are floats in the range [0.0, 1.0] and
        relative to the width and height of the image.
        """
#        print( 'H x W ', img_height, ' ', img_width)
#        print( 'Pred min and maxs ', prediction["y_min"],  prediction["x_min"], prediction["y_max"], prediction["x_max"])
        box = [
            float(prediction["y_min"]) / float(img_height),
            float(prediction["x_min"]) / float(img_width),
            float(prediction["y_max"]) / float(img_height),
            float(prediction["x_max"]) / float(img_width),
        ]

        rounding_decimals = 3
        box = [round(coord, rounding_decimals) for coord in box]
#        print(' Get box ', box)
        return box


    async def detect(self):
        """Process image_bytes, performing detection."""
        self._predictions = []
        log.info(f'Facial recognition process begin')
        log.info(f'Path in detect {self._path_in + self._image}')
        image_bytes = await load_image_bytes(self._path_in + self._image)
        files = {
                 'file': ('image.jpg', image_bytes, 'image/jpeg')
                 }
        headers = {'x-api-key': x_api_key} # Removed 'Content-Type'
        predictions_out = await send_prediction_request(URL_CURL_GORTASH, headers, files)

        predictions_raw = eval(predictions_out.text)

        if predictions_out.status_code != HTTP_OK:
           log.info(f'Got a {predictions_out.status_code} status code on a Curl post')

        if 'message' in predictions_raw:
           log.info(f'Received: {predictions_raw["message"]}')
           predictions_raw = {}
           preds = []
        elif 'result' in predictions_raw:
           preds = []
           for facerec in predictions_raw["result"]:
               for sub in facerec["subjects"]:
                   preds.append(
                           {
                               "confidence": float(sub["similarity"]),
                               "label": str(sub["subject"]),
                               "y_min": int(facerec["box"]["y_min"]),
                               "x_min": int(facerec["box"]["x_min"]),
                               "y_max": int(facerec["box"]["y_max"]),
                               "x_max": int(facerec["box"]["x_max"]),
                           }
                                )
        else:
           preds = []
        self._predictions = preds

#        print('sp: ', self._predictions)



    def draw_box(self, draw, box, img_width, img_height, text, color):
        """
        Draw a bounding box on and image.
        The bounding box is defined by the tuple (y_min, x_min, y_max, x_max)
        where the coordinates are floats in the range [0.0, 1.0] and
        relative to the width and height of the image.
        For example, if an image is 100 x 200 pixels (height x width) and the bounding
        box is `(0.1, 0.2, 0.5, 0.9)`, the upper-left and bottom-right coordinates of
        the bounding box will be `(40, 10)` to `(180, 50)` (in (x,y) coordinates).
        """

        line_width = 3
        font_height = 12
        y_min, x_min, y_max, x_max = box
        (left, right, top, bottom) = (
            x_min * img_width,
            x_max * img_width,
            y_min * img_height,
            y_max * img_height,
        )
        draw.line(
            [(left, top), (left, bottom), (right, bottom), (right, top), (left, top)],
            width=line_width,
            fill=color,
        )
        if text:
            draw.text(
                (left + line_width, abs(top - line_width - font_height)), text, fill=color
            )

    async def create_curl_json(self, gen_file_out, target_found, pct_out, uid_out):
        log.info(f'prepayload {uid_out}')
        dest_path_partial = self._local_path_ha
        file_name = gen_file_out
#        print('Image name ', file_name)
#        print('LLM vision file name: ', uid_out)
        temp_datetime = datetime.datetime.strptime(self._event_datetime, '%Y%m%d_%H%M%S')
#        curl_out_date = MST.localize(temp_datetime).strftime('%Y%m%d%H%M%S%z')
        curl_out_date = temp_datetime.replace(tzinfo=ZoneInfo('America/Edmonton')).strftime('%Y%m%d%H%M%S%z')
        dest_path_main = dest_path_partial + target_found + '/'
        target_subj = tuple([target_found])
        sql = "SELECT allowed_to_use_alarm_by_AI TEXT FROM subjects WHERE subject = ?"
        sql_result = await db_execute_query(sql, target_subj)
        allowed_by_facial_recog = sql_result[0][0]


        log.info(f'prepayload {uid_out}')
        payload = '{"image":"'+file_name+'", "face":"'+target_found+'", "allow":"'+allowed_by_facial_recog+'", "area":"'+self._area+'", "pct":"'+str(pct_out)+'", "path":"'+dest_path_main+'", "datewithtime":"'+curl_out_date+'", "uid":"'+str(uid_out)+'"}'

#        print('Json data: ', payload)
        log.info(f'Payload: {payload}')
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        req = await send_curl_payload(URL_CURL, payload, headers)
        if req.status_code != HTTP_OK:
#           print('Got a bad status code on a Curl post: ', req.status_code)
           log.error(f'Got a bad status code on a Curl post: {req.status_code}')

@pyscript_executor
def load_image_bytes(path):
    """Load image from path and return JPEG bytes (runs in thread pool)."""
    with Image.open(path) as f:
        img_byte_arr = io.BytesIO()
        f.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue()

@pyscript_executor
def db_execute_query(sql, params):
    """Execute a DB query and return results (runs in thread pool)."""
    conn = sqlite3.connect('/config/ai_objects_db/ai_subjects.db')
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.commit()
        return results
    finally:
        conn.close() # Always close the connection
@pyscript_executor
def send_prediction_request(url, headers, files):
    """Sends POST request to the prediction API."""
    predictions_out = requests.post(url, headers=headers, files=files)
    return predictions_out

@pyscript_executor
def send_curl_payload(url,pay,head):
    req_out = requests.post(url, data=pay, headers=head)
    return req_out

async def load_image_async_ai(path):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    loop = asyncio.get_running_loop()
    # Run the blocking Image.open in the executor
    imgv = await loop.run_in_executor(executor, Image.open, path)
    return imgv


async def main(infile_path, in_image_file, target, confidence, in_image_area, in_local_path, in_event_datetime, save_file_folder):
    log.warning(f'***** Starting a facial recognition job at {datetime.datetime.now()} in area {in_image_area} *****')

    if save_file_folder:
        save_file_folder = os.path.join(save_file_folder, "")  # If no trailing / add it
    log.info(f'Processing file {in_image_file}')
    log.info(f'Looking in area {in_image_area}')
    target = list(target.split(","))
#    print('List of targets: ', target)
    for subject_name in target:
        if not await asyncio.to_thread(os.path.exists, save_file_folder + subject_name):
           await asyncio.to_thread(os.mkdir, save_file_folder + subject_name)
    log.info(f'Processing jpg image: {in_image_file}')
    try:
#           imgv = Image.open(infile_path + in_image_file)
           imgv = await load_image_async_ai(infile_path + in_image_file)
           if imgv.format !=  'JPEG':
#              print('Bypassing, not a valid jpg file, instead found file type: ',imghdr.what(infile_path + in_image_file))
              log.info(f'Bypassing, not a valid jpg file, instead found file type: {imghdr.what(infile_path + in_image_file)}')
           else:
#              print('File ',in_image_file, ' is a valid jpeg file, continuing')
              log.info(f'File {in_image_file} is a valid jpeg file, continuing')
              FaceGenerator = FaceRecognitionEntity(infile_path, in_image_file, in_image_area, target, confidence, in_local_path, in_event_datetime, save_file_folder)
              await FaceGenerator.generate()
    except IOError:
#           print('File ',in_image_file, ' is not a valid image file or is corrupt, bypassing')
           log.error(f'File {in_image_file} is not a valid image file or is corrupt, bypassing')


    log.warning(f'***** Finishing a facial recognition job at {datetime.datetime.now()} *****')

@service
async def compreface_run_nonblocking(infile_path, in_image_file, target, confidence, in_image_area, in_local_path, in_event_datetime, save_file_folder):
    log.info('starting the script')
    log.info('Main')
    await main(infile_path, in_image_file, target, confidence, in_image_area, in_local_path, in_event_datetime, save_file_folder)



