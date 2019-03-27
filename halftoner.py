#!/usr/bin/python3

# //////////////////////////////////////////////////////////////////////////////
# //
# //  'Hex Halftoner' by Chris Molloy (http://chrismolloy.com/halftoner)
# //
# //  Released under Creative Commons Attribution Share Alike 4.0 International
# //
# //////////////////////////////////////////////////////////////////////////////

# NOTES:
# The ratio of the area of a circle to a hexagon = √3π/6 = 0.906899682 - this
# represents the amount by which the final result will be 'dimmer' than the source
# image - you may wish to adjust the brightness of your source to allow for that.
#
# My original 'circleMask' used cv2.circle() to create a 'white' circle on a black
# background to use as a convolution kernel (after scaling). Whilst this was 'neat',
# it was also kind of 'opaque', so I changed to using an explictly defined set of
# kernel weights.

import argparse
import cv2
import math
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input', required=True, help='path to the input image')
ap.add_argument('-o', '--output', required=True, help='path to the output image (PNG, JPG or SVG)')
ap.add_argument('-r', '--radius', type=int, default=10, help='grid radius, in pixels (default 10)')
ap.add_argument('-t', '--threshold', type=int, default=0, help='dots smaller than this are not drawn in output (default 0)')
ap.add_argument('-c', '--color', dest='color', action='store_true', help='Color output image')
ap.add_argument('-g', '--greyscale', dest='color', action='store_false', help='Grayscale output image')
ap.set_defaults(color=True)
args = vars(ap.parse_args())

img = cv2.imread(args['input'])
outFile = args['output']
outRadius = int(args['radius'])
threshold = int(args['threshold'])
colorOutput = args['color']

isSVG = (outFile[-4:].lower() == '.svg')
inRadius = math.ceil(math.sqrt(3 / 4) * outRadius)
diameter = (outRadius * 2) + 1  # pseudo-diameter (always odd, as per convolution kernel reqs)

circleMask = np.ones((diameter, diameter), dtype='float32')
for yy in range(0, outRadius):
    for xx in range(0, outRadius):
        if (math.hypot(xx, yy) >= outRadius):
            circleMask[xx + outRadius, yy + outRadius] = 0.0
            circleMask[outRadius - xx, yy + outRadius] = 0.0
            circleMask[xx + outRadius, outRadius - yy] = 0.0
            circleMask[outRadius - xx, outRadius - yy] = 0.0
    # end for xx
# end for yy
scaleFactor = np.count_nonzero(circleMask)
circleMask = circleMask / scaleFactor  # scale kernel to have a sum = 1.0

convolved = cv2.filter2D(img, -1, circleMask)
hsv = cv2.cvtColor(convolved, cv2.COLOR_BGR2HSV)
value = hsv[:, :, 2]

(iH, iW) = convolved.shape[:2]
countX = math.floor(iW / (outRadius * 3.0))
countY = math.floor(iH / inRadius)

if isSVG:
    sSVG = []
    sSVG.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
    sSVG.append('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">')
    sSVG.append('<svg viewBox="0 0 ' + str(iW) + ' ' + str(iH) + '" height="' + str(iH) + 'mm" width="' + str(iW) + 'mm" xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1">')
    sSVG.append('<title>Hex Halftoner</title>')
    sSVG.append('<desc>Author: Chris Molloy. License: Creative Commons Attribution Share Alike 4.0 International. For more information, see https://chrismolloy.com/halftoner</desc>')
    sSVG.append('<g id="docRoot" style="overflow:hidden;">')
    sSVG.append('<rect id="bg" height="100%" width="100%" fill="black"/>')
else:
    outImage = np.zeros((iH, iW, 3), dtype='float32')  # all black
# end if

ii = 0  # circle id index, prefixed with 'c'
for yy in range(0, countY):
    iY = math.floor(yy * inRadius)
    for xx in range(0, countX):
        iX = math.floor((((xx * 3.0) + 1.0) * outRadius) + (0 if (yy % 2 == 0) else (1.5 * outRadius)))
        iC = value[iY, iX]

        if iC > 0:  # ignore black
            fR = ((value[iY, iX] / 255.0) * inRadius) - 1.0  # 1px spacer
            if fR > threshold:  # ignore small
                convolvedColor = convolved[iY, iX]
                if colorOutput:
                    color = (int(convolvedColor[0]), int(convolvedColor[1]), int(convolvedColor[2]))
                else:
                    color = (255, 255, 255)
                # end if

                if isSVG:
                    # Careful, OpenCV is BGR, svg wants RGB...
                    svgColor = "rgb(" + str(color[2]) + "," + str(color[1]) + "," + str(color[0]) + ")"
                    sSVG.append('<circle id="c' + '{:04d}'.format(ii) + '" cx="' + str(iX) + '" cy="' + str(iY) + '" r="' + '{0:.2f}'.format(fR) + '" stroke="none" fill="' + svgColor + '" />')
                    ii += 1
                else:
                    cv2.circle(outImage, (iX, iY), math.floor(fR), color, -1)
                # end if
            # end if
        # end if
    # end for xx
# end for yy

if isSVG:
    sSVG.append('</g>')
    sSVG.append('</svg>')
    file_out = open(outFile, 'w')
    file_out.write('\n'.join(sSVG))
    file_out.close()
else:
    cv2.imwrite(outFile, outImage)
# end if
