import time
import traceback
import cv2
import cv2 as cv

from keras.models import load_model
import numpy as np
from tensorflow import keras
from Database import  FYPdatabase
from deskew import determine_skew
from scipy.spatial import distance
import matplotlib.pyplot as plt
from PIL import Image
from playsound import playsound
import imagehash

from skimage.transform import rotate
import Google_Sheet_Setup
num_boxes = len(FYPdatabase.GetCandidates())
print("num candidates: ",num_boxes)
model = load_model('newest_nn.h5')

# returns hash value of image
# method collected from https://pypi.org/project/ImageHash/.
def hashImage(img):
    return imagehash.phash(Image.fromarray(img))

def deskewing(img):# method that performs deskewing, and then crops to the region of the ballot paper
    rot = img[:img.shape[0] - 10, int(img.shape[1] / 2) - 100:int(img.shape[1] / 2)] # getting the area of the ballot paper that contains text, because deskew works best with text images
    # cv2.imshow("rot",rot)
    # cv2.waitKey(0)

    # code used from https://www.github.com/sbrunner/deskew
    angle = determine_skew(rot)
    rotated = rotate(img, angle, resize=True) * 255
    rotated = rotated.astype(np.uint8)

    after = determine_skew(rotated)
    # cv.imshow("orig", img)

    print("ANGLE AFTER SKEWING: ",after)

    rotated = cv.cvtColor(rotated, cv.COLOR_BGR2GRAY)

    _, thresh1 = cv.threshold(rotated, 150, 300,cv2.THRESH_BINARY)
    contours, h = cv.findContours(thresh1, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    biggest =0
    for c in contours:
        if(cv.contourArea(c)>biggest):
            biggest = cv.contourArea(c)
            maxCont = c

    x, y, w, h = cv.boundingRect(maxCont)
    # img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cropped = img[y:y + h, x:x + w]
    # cv.imshow("cropped", cropped)
    # cv.waitKey(0)

    return cropped

def processImage(img):# main implementation method
    squares = []
    rightSection = img
    img = deskewing(img)
    # cv.imshow("deskewed", img)
    # cv.waitKey(0)

    copy = img #copy is used to draw contours onto in a color image so that contours are visible

    # cv.imshow("split", hashed)
    # cv.waitKey(0)
    img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    img = cv.GaussianBlur(img,(3,3),0)

    # line used from https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html.
    img = cv.adaptiveThreshold(img,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C,cv.THRESH_BINARY,11,None)
    img = cv.bitwise_not(img)

    rightSection = img[:, int(img.shape[1]/1.3):] # taking rightmost portion of image

    # line used from https://docs.opencv.org/4.x/d4/d73/tutorial_py_contours_begin.html
    contours, x = cv.findContours(img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE) # finds contours on the ballot paper

    sectionContours, x = cv.findContours(rightSection, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE) # finds the contours inside the vertical slice of the image containing the boxes

    copy = cv.drawContours(copy, sectionContours, -1, (0,255,0),1)
    # cv.imshow('copy', copy)
    # # cv.imwrite('portion.png', copy)
    # cv.waitKey(0)
    predictions = [] # output array that stores digit predictions, and -1 values if no digit/irrelevant digit found inside box
    # cv.imshow('full image', img)
    # cv.waitKey(0)

    for contour in sectionContours:
        significant_contours = 0
        big_contours = 0
        if(cv.contourArea(contour)> 400):
            # print("CONTOUR AREA: ", cv.contourArea(contour))

            x, y, w, h = cv.boundingRect(contour)
            tmp = cv.rectangle(rightSection, (x, y), (x + w, y + h), (0, 0, 0), 0)
            # cv.imshow("TEMP ", tmp)
            # cv.waitKey(0)
            shape = tmp[y:y + h, x:x + w]
            if(cv.contourArea(contour) > 200 and abs(shape.shape[0] - shape.shape[1]) < 10):

                fullBox = tmp[y:y + h, x:x + w]

                boxContours, h = cv.findContours(fullBox, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)# finds  contours inside the box
                # print("num of contours in box: " + str(len(boxContours)))
                width = []
                height = []
                xval = []
                yval = []
                for cont in boxContours:
                    if(cv.contourArea(cont)>5):#filters out any small dots/noise
                        significant_contours = significant_contours + 1

                    if(cv.contourArea(cont) > 10):#counts large contours that could indicate a digit inside a box
                        big_contours  = big_contours + 1
                if(significant_contours >= 1):
                    for c in boxContours:

                            x, y, w, h = cv.boundingRect(c)
                            yval.append(y)
                            xval.append(x)
                            height.append(h)
                            width.append(w)
                    if (len(xval) == 0):
                        xval.append(0)
                    if (len(yval) == 0):
                        yval.append(0)
                    if (len(width) == 0):
                        width.append(0)
                    if (len(height) == 0):
                        height.append(0)

                    innerBox = fullBox[min(yval)-2:min(yval)+2 + max(height), min(xval)-2:2+min(xval) + max(width)]#used so that split digits can be cropped to based on max/min contour values
                    innerBox = innerBox[int(innerBox.shape[0]/ 8):int(innerBox.shape[0] / 8 * 7), int(innerBox.shape[1] / 8):int(innerBox.shape[1] / 8 * 7)] # cropping box to remove inner edges

                    print("Shape: " + str(innerBox.shape))
                    if(innerBox.shape[0] == 0 or innerBox.shape[1] == 0):
                        predictions.append(-1)
                        print("NO SHAPE")
                        continue
                    elif(abs(innerBox.shape[1] - innerBox.shape[0]) > 12):
                        predictions.append(-1)
                        print("NOT SQUARE")
                        continue
                    # cv.imshow("BOX",Box)
                    # cv.waitKey(0)
                    innerBox = cv.resize(innerBox, (28, 28), interpolation=cv.INTER_AREA)

                    innerBox = keras.utils.normalize(innerBox, axis=1)
                    innerBox = np.array(innerBox).reshape(1,28, 28, 1)
                    squares.append(innerBox)

                    predict = model.predict(innerBox)
                    print("PREDICTIONS: ", predict)
                    maximum = np.amax(predict)

                    if(maximum< 0.7):#if the model is unsure which digit to classify
                        print("NOT SURE OF PREDICTION")
                        predictions.append(-1)
                    else:
                        print("PREDICTION FOUND")
                        predictions.append(predict.argmax())
                else:
                    print("NO SIGNIFICANT CONTOURS FOUND")
                    predictions.append(-1)

    predictions = list(reversed(predictions))

    if len(predictions) == num_boxes:
        if(predictions.count(1) == 0):
            print("No 1st Preference Found")

        elif predictions.count(1) ==1:
            print("Ballot is acceptable")
            return (True, predictions, hashImage(rightSection))


        else:
            print("More than one first preference recognised")

    else:
        print("Error Occurred. Number of boxes does not match")
    print("PREDICTIONS:",predictions)
    return (False, None, None)


cap = cv.VideoCapture(1)
if not cap.isOpened():
    exit()

curr = None
num = None
diff = True
numSuccessfulBallots = 0
numUnsuccessfulBallots = 0
while True:

    ret, frame = cap.read()
    if not ret:
        break
    # Our operations on the frame come here
    # Display the resulting frame
    if cv.waitKey(1) == ord('q'):
        break
    blur = cv.GaussianBlur(frame, (5,5), 0)
    canny = cv2.Canny(blur, 127, 255, None, 3) #using canny edge detection to detect a ballot paper under the camera
    cv.imshow('frame', frame)

    contours, h = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    time.sleep(0.5)
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)

        if (cv2.contourArea(c) > 30000):
            print(x, y, w, h)
            print("Contour Area: " + str(cv2.contourArea(c)))
            ballotArea = frame[y:y + h, x:x + w]
            gray = cv2.cvtColor(ballotArea, cv2.COLOR_BGR2GRAY)
            cv2.imshow('canvasOutput', ballotArea)
            cv2.waitKey(0)
            try:
                num = processImage(ballotArea)

                if(num[0] == True):

                    if curr == None:
                        curr = num[2]
                        Google_Sheet_Setup.addToTally(num[1])
                        numSuccessfulBallots += 1
                    else:
                        print("DIFFERENCE: ", curr-num[2])
                        diff = abs(curr-num[2]) > 10
                        if (diff == True):
                            curr = num[2]
                            print("sending ballot to spreadsheet")
                            Google_Sheet_Setup.addToTally(num[1])
                            numSuccessfulBallots += 1
                else:
                    numUnsuccessfulBallots +=1
                time.sleep(1)
            except Exception:
                print(traceback.format_exc())
            break

print("Number of successful ballots counted: ", numSuccessfulBallots)
print("Number of unsuccessful ballots counted", numUnsuccessfulBallots)
cap.release()
cv.destroyAllWindows()

