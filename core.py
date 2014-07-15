# Normalized Burn Ratio
# Hammer, Kraft, and Steele (Data Lab at WRI)
# GFW-Fires, prototype

# Reference
# Escuin, S., R. Navarro, P. Fernandez. 2008. Fire severity assessment by
#   using NBR (Normalized Burn Ratio) and NDVI (Normalized Difference
#   Vegetation Index) derived from LANDSAT TM/ETM images. Int. J. Remote
#   Sens. 29:1053-1073.

# Assets required:
#   LC8_L1T_TOA: Landsat 8 Top of Atmosphere, L1T product
#   Recent fires: ft:1UkooS2ir_Rx3Kbg7K2RWV9dTOCCtrjDWizZE_hL0

import ee
import sys
import getopt

FIRES = 'ft:1UkooS2ir_Rx3Kbg7K2RWV9dTOCCtrjDWizZE_hL0'
INIT = ['2013-03-30', '2013-09-30']
POST = ['2014-05-01', '2014-09-30']


def cloudDensity(img):
    '''Calculate the cloud score for the supplied L8 image'''

    def _rescale(img, exp, thresholds):
        # A helper to apply an expression and linearly rescale the output.
        return img.expression(exp, {'img': img}). \
            subtract(thresholds[0]). \
            divide(thresholds[1] - thresholds[0])

    score = ee.Image(1.0)
    # Clouds are reasonably bright in the blue band.
    score = score.min(_rescale(img, 'img.B2', [0.1, 0.3]))

    # Clouds are reasonably bright in all visible bands.
    score = score.min(_rescale(img, 'img.B4 + img.B3 + img.B2', [0.2, 0.8]))

    # Clouds are reasonably bright in all infrared bands.
    score = score.min(_rescale(img, 'img.B5 + img.B6 + img.B7', [0.3, 0.8]))

    # Clouds are reasonably cool in temperature.
    score = score.min(_rescale(img, 'img.B10', [300, 290]))

    # However, clouds are not snow.
    ndsi = img.normalizedDifference(['B3', 'B6'])
    return score.min(_rescale(ndsi, 'img', [0.8, 0.6]))


def cloudMask(img, cloud_scores, thresh):
    # Accepts an raw L8 image, a derived image of cloud scores corresponding
    # to each pixel and a threshold to screen out excessively cloudy pixels.
    # Returns the original image, with clouds masked.
    binary = cloud_scores.lte(thresh)
    return img.mask(binary)


def makeCloudFree(img):
    # Convenient wrapper `cloudMask` function that will only accept an L8
    # image and returns the cloud-masked image with the threshold set at 0.5
    clouds = cloudDensity(img)
    return cloudMask(img, clouds, 0.5)


def cloudScore(img):
    # Calculates the cloud score for the supplied image, specifically the
    # proportion of pixels in the image that are excessively cloudy.  If there
    # are no clouds then the return value is null.
    pix = cloudDensity(img)
    binary = pix.gt(0.5)
    num = binary.reduceRegion(ee.Reducer.mean())
    return num.getInfo().constant


def hsvpan(rgb, gray):
    # Accepts the RGB and gray banded image for the same location.  Returns  a
    # pan-sharpened image.
    huesat = rgb.rgbtohsv().select(['hue', 'saturation'])
    upres = ee.Image.cat(huesat, gray).hsvtorgb()
    return upres


def createComposite(time_range):
    # Accepts a start and end date, along with a bounding GEE polygon. Returns
    # the L8 cloud composite.
    start, end = time_range
    collection = ee.ImageCollection('LC8_L1T_TOA').filterDate(start, end)
    coll = collection.map(makeCloudFree)
    return coll.min()


def generateBurnRatio(init_season, post_season):
    # Accepts two tuples that delineate the beginning and end of the  fire
    # season for the previous and current seasons. Returns a binary  image of
    # the burn scars at the set parameter values.

    # create cloud free composites and mask out any remaining clouds from
    # subsequent analysis
    init = makeCloudFree(createComposite(init_season))
    post = makeCloudFree(createComposite(post_season))

    # Generate the difference between the normalized burn ratios for  the pre
    # and post periods
    nbr_init = init.normalizedDifference(['B6', 'B4'])
    nbr_post = post.normalizedDifference(['B6', 'B4'])
    nbr = nbr_post.subtract(nbr_init).gt(0.44)
    return nbr.mask(nbr)


def loadFireBuffer(fire_location, meters):
    # Accepts a fusion table location string and the distance of a buffer in
    # meters and returns a feature of the unioned buffers.
    fires = ee.FeatureCollection(fire_location)
    buffered = fires.map(lambda f: f.buffer(meters))
    return buffered.union()


def main():
    # Main function that accepts the number of meters and returns the
    # normalized burn ratio image clipped to the fire buffer defined by the
    # buffer length
    try:
        opts, args = getopt.getopt(sys.argv[1:], "m:")
    except getopt.GetoptError as err:
        print str(err)

    for opt, arg in opts:
        if opt in ('-m'):
            nbr = generateBurnRatio(INIT, POST)
            fire_buffer = loadFireBuffer(FIRES, int(arg))
            return nbr.clip(fire_buffer)

if __name__ == "__main__":
    main()
