# Normalized Burn Ratio on Google Earth Engine

```javascript
// Normalized Burn Ratio
// Hammer, Kraft, and Steele (Data Lab at WRI)
// GFW-Fires, prototype

// Reference
// Escuin, S., R. Navarro, P. Fernandez. 2008. Fire severity assessment by 
//   using NBR (Normalized Burn Ratio) and NDVI (Normalized Difference 
//   Vegetation Index) derived from LANDSAT TM/ETM images. Int. J. Remote 
//   Sens. 29:1053-1073.

// Assets required:
//   LC8_L1T_TOA: Landsat 8 Top of Atmosphere, L1T product
//   Recent fires: ft:1UkooS2ir_Rx3Kbg7K2RWV9dTOCCtrjDWizZE_hL0

var FIRES = 'ft:1UkooS2ir_Rx3Kbg7K2RWV9dTOCCtrjDWizZE_hL0';

var INIT = ['2013-03-30', '2013-09-30'];
var POST = ['2014-05-01', '2014-09-30'];

// BEGIN FUNCTIONS

var cloudDensity = function(img) {
  // Calculate the cloud score for the supplied L8 image

  var rescale = function(img, exp, thresholds) {
    // A helper to apply an expression and linearly rescale the output.
    return img.expression(exp, {img: img})
        .subtract(thresholds[0]).divide(thresholds[1] - thresholds[0]);
  };

  var score = ee.Image(1.0);
  // Clouds are reasonably bright in the blue band.
  score = score.min(rescale(img, 'img.B2', [0.1, 0.3]));

  // Clouds are reasonably bright in all visible bands.
  score = score.min(rescale(img, 'img.B4 + img.B3 + img.B2', [0.2, 0.8]));

  // Clouds are reasonably bright in all infrared bands.
  score = score.min(rescale(img, 'img.B5 + img.B6 + img.B7', [0.3, 0.8]));

  // Clouds are reasonably cool in temperature.
  score = score.min(rescale(img, 'img.B10', [300, 290]));

  // However, clouds are not snow.
  var ndsi = img.normalizedDifference(['B3', 'B6']);
  
  return(score.min(rescale(ndsi, 'img', [0.8, 0.6])));
};


function cloudMask(img, cloud_scores, thresh) {
  // Accepts an raw L8 image, a derived image of cloud scores corresponding 
  // to each pixel and a threshold to screen out excessively cloudy pixels.
  // Returns the original image, with clouds masked.
  var binary = cloud_scores.lte(thresh);
  return(img.mask(binary));
}


function makeCloudFree(img) {
  // Convenient wrapper `cloudMask` function that will only accept an L8
  // image and returns the cloud-masked image with the threshold set at 0.5
  var clouds = cloudDensity(img);
  return(cloudMask(img, clouds, 0.5));
}


function cloudScore(img) {
  // Calculates the cloud score for the supplied image, specifically the 
  // proportion of pixels in the image that are excessively cloudy.  If 
  // there are no clouds then the return value is null.
  var pix = cloudDensity(img);
  var binary = pix.gt(0.5);
  var num = binary.reduceRegion(ee.Reducer.mean());
  return(num.getInfo().constant);
}


function hsvpan(rgb, gray) {
  // Accepts the RGB and gray banded image for the same location.  Returns 
  // a pan-sharpened image.
	var huesat = rgb.rgbtohsv().select(['hue', 'saturation']);
	var upres = ee.Image.cat(huesat, gray).hsvtorgb();
	return(upres);
}


function createComposite(start, end) {
  // Accepts a start and end date, along with a bounding GEE polygon.  
  // Returns the L8 cloud composite. 
  var collection = ee.ImageCollection('LC8_L1T_TOA')
    .filterDate(start, end);
  var coll = collection.map(makeCloudFree);
  return(coll.min());
}


function generateBurnRatio(init_season, post_season) {
  // Accepts two tuples that delineate the beginning and end of the 
  // fire season for the previous and current seasons. Returns a binary 
  // image of the burn scars at the set parameter values.
  
  // create cloud free composites and mask out any remaining clouds 
  // from subsequent analysis
  var a = init_season[0]; var b = init_season[1];
  var c = post_season[0]; var d = post_season[1];
  var init = makeCloudFree(createComposite(a, b));
  var post = makeCloudFree(createComposite(c, d));
  
  // Add image layer as reference, visibility default set to false
  var rgb = post.select("B6","B5","B4");
  addToMap(rgb, {min:0.01, max:1.5, gamma:1.5}, 'post composite', false);

  // Generate the difference between the normalized burn ratios for 
  // the pre and post periods
  var nbr_init = init.normalizedDifference(['B6', 'B4']);
  var nbr_post = post.normalizedDifference(['B6', 'B4']);
  var nbr = nbr_post.subtract(nbr_init).gt(0.44);

  return(nbr.mask(nbr));
}


function loadFireBuffer(fire_location, meters) {
  // Accepts a fusion table location string and the distance of a buffer in 
  // meters and returns a feature of the unioned buffers.
  var fires = ee.FeatureCollection(fire_location);
  addToMap(fires, {color:'FF9900'}, 'fire points', false)
  var buffered = fires.map(function(f) { return f.buffer(meters); });
  return(buffered.union());
}


function burnRatio() {
  // Accepts the burn ratio image and the fire buffer features and returns
  // the burn scars clipped to the fire buffer extent.  
  var nbr = generateBurnRatio(INIT, POST);
  var fire_buffer = loadFireBuffer(FIRES, 5000);
  var img = nbr.clip(fire_buffer);
  
  return(img);
}


// Display the normalized burn ratio derived from L8 within 5km of fires.
centerMap(100.8, 1.7, 10);
addToMap(burnRatio(), {palette:'FF0000'}, 'NBR');
```
