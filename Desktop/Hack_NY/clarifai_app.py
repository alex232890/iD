from clarifai import rest
from clarifai.rest import ClarifaiApp
from clarifai.rest import Image as ClImage
from ximea import xiapi
from decimal import Decimal
import PIL.Image
import cv2
import time
import subprocess
import flask
from flask import render_template
import jinja2
import signal
import sys
from multiprocessing import Process

app = flask.Flask(__name__)

@app.route('/yield')
#@app.route('/index/')
#@app.route('/index/<display>')
def index(display = None):
    while True:
        file_of_results = open("results.txt", "r")
        file_str = "<br/>"
        for line in file_of_results:
            file_str += line + "<br/>"
        #return flask.Response(inner(), mimetype='text/html')  # text/html is required for most browsers to show th$
        return render_template("index.html", display=file_str)

def exitFunc(signum, frame):
    signal.signal(signal.SIGINT, original_sigint)
    try:
        if raw_input("\nClose the camera? (y/n)> ").lower().startswith('y'):
            sys.exit(1)
    except KeyboardInterrupt:
        print("Quitting")
        sys.exit(1)
    signal.signal(signal.SIGINT, exitFunc)

def operations():
    app = ClarifaiApp(api_key = "e0210c749e394a829a4913af2324af7d")
    model = app.models.get("iCheck")

    cam = xiapi.Camera()
    cam.open_device()
    cam.set_imgdataformat('XI_RGB24') 
    cam.enable_aeag()
    cam.enable_bpc()

    img = xiapi.Image()

    cam.start_acquisition()

    columbia_sub = "u'Columbia ID', u'value': "
    northeastern_sub = "u'Northeastern ID', u'value': "
    umass_sub = "u'UMass ID', u'value': "
    nyu_sub = "u'NYU ID', u'value': "
    notid_sub = "u'Not ID', u'value': "
    
    try:
        t0 = time.time()
        image_count = 0
        while True:
            cam.get_image(img)
            data = img.get_image_data_numpy()
            data_save = img.get_image_data_numpy(invert_rgb_order=True)
            time_format = Decimal(('% 6.1f' % float(time.time() - t0)))
            if time_format % 4 == 0:
                results_file = open("results.txt", "a")
                img_save = PIL.Image.fromarray(data_save, 'RGB')
                img_save.save('id_img_' + str(image_count) + '.bmp')
                image = ClImage(file_obj=open('id_img_' + str(image_count) + '.bmp', 'rb'))
                results = str(model.predict([image]))
                #print(results + "\n")

                columbia_val = float(results[results.find(columbia_sub) + 26 : results.find(columbia_sub) + 32])
                northeastern_val = float(results[results.find(northeastern_sub) + 30 : results.find(northeastern_sub) + 36])
                umass_val = float(results[results.find(umass_sub) + 23 : results.find(umass_sub) + 29])
                nyu_val = float(results[results.find(nyu_sub) + 21 : results.find(nyu_sub) + 27])
                notid_val = float(results[results.find(notid_sub) + 21 : results.find(notid_sub) + 27])
                columbia_val = columbia_val if columbia_val <= 1 else 0
                northeastern_val = northeastern_val if northeastern_val <= 1 else 0
                umass_val = umass_val if umass_val <= 1 else 0
                nyu_val = nyu_val if nyu_val <= 1 else 0
                notid_val = notid_val if notid_val <= 1 else 0
                print(columbia_val)
                print(northeastern_val)
                print(umass_val)
                print(nyu_val)
                print(notid_val)
                max_val = ""
                if columbia_val > northeastern_val and columbia_val > umass_val and columbia_val > nyu_val and columbia_val > notid_val:
                    max_val = "Columbia: " + str(columbia_val)
                elif northeastern_val > umass_val and northeastern_val > nyu_val and northeastern_val > notid_val:
                    max_val = "Northeastern: " + str(northeastern_val)
                elif umass_val > notid_val and umass_val > nyu_val:
                    max_val = "UMass Amherst: " + str(umass_val)
                elif nyu_val > notid_val:
                    max_val = "NYU: " + str(nyu_val)
                else:
                    max_val = "Not a Student ID: " + str(notid_val)
                results_file.write(max_val + "\n")
                image_count += 1
                results_file.close()
            cv2.imshow('iD', data)
            cv2.waitKey(1)
    except KeyboardInterrupt:
        cv2.destroyAllWindows()

    cam.stop_acquisition()

    cam.close_device()
def ui():
    app.run(debug=True, port=5000, host='127.0.0.1')

if __name__ == '__main__':
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exitFunc)
    procs = []
    procs.append(Process(target=ui))
    procs.append(Process(target=operations))
    map(lambda x: x.start(), procs)
    map(lambda x: x.join(), procs)
