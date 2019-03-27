# //////////////////////////////////////////////////////////////////////////////
# //  
# //  'Hex Halftoner' by Chris Molloy (http://chrismolloy.com/halftoner)
# //  
# //  Released under Creative Commons Attribution Share Alike 4.0 International
# //  
# //////////////////////////////////////////////////////////////////////////////

#!/usr/bin/python3

import argparse
import cv2
import math
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input', required=True, help='path to the input image')
ap.add_argument('-o', '--output', required=True, help='path to the output image (PNG, JPG or SVG)')
ap.add_argument('-r', '--radius', type=int, default=10, help='grid radius, in pixels (default 10)')
ap.add_argument('-t', '--threshold', type=int, default=0, help='dots smaller than this are not drawn in output (default 0)')
args = vars(ap.parse_args())

greyscale = cv2.cvtColor(cv2.imread(args['input']), cv2.COLOR_BGR2GRAY)
outFile = args['output']
outRadius = int(args['radius'])
threshold = int(args['threshold'])

isSVG = (outFile[-4:].lower() == '.svg')
inRadius = math.ceil(math.sqrt(3 / 4) * outRadius)
diameter = (outRadius * 2) + 1 # pseudo-diameter (always odd, as per convolution kernel reqs)

circleMask = np.zeros((diameter, diameter), dtype='float32')
cv2.circle(circleMask, (outRadius, outRadius), outRadius, (1, 1, 1), -1) # not sure why the colour here needs to be (1, 1, 1), as oppsed to (255, 255, 255) - scaling?
circleMask = circleMask * (1.0 / np.count_nonzero(circleMask))

convolved = cv2.filter2D(greyscale, -1, circleMask)

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
    outImage = np.zeros((iH, iW), dtype='float32') # all black
# end if

ii = 0 # circle id index, prefixed with 'c'
for yy in range(0, countY):
    iY = math.floor(yy * inRadius)
    for xx in range(0, countX):
        iX = math.floor((((xx * 3.0) + 1.0) * outRadius) + (0 if (yy % 2 == 0) else (1.5 * outRadius)))
        iC = convolved[iY, iX]
        if iC > 0: # ignore black
            fR = ((convolved[iY, iX] / 255.0) * inRadius) - 1.0 # 1px spacer
            if fR > threshold: # ignore small
                if isSVG:
                    sSVG.append('<circle id="c' + '{:04d}'.format(ii) + '" cx="' + str(iX) + '" cy="' + str(iY) + '" r="' + '{0:.2f}'.format(fR) + '" stroke="none" fill="white" />')
                    ii += 1
                else:
                    cv2.circle(outImage, (iX, iY), math.floor(fR), (255, 255, 255), -1) # white circle
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
