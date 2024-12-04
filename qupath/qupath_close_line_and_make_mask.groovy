// Import necessary QuPath libraries
import qupath.lib.common.GeneralTools
import qupath.lib.common.ColorTools
import qupath.lib.images.servers.LabeledImageServer

// Convert line annotations to polygon annotations
// https://forum.image.sc/t/converting-a-polyline-annotation-into-a-polygon/36307
def lineObjects = getAnnotationObjects().findAll { it.getROI().isLine() }
def polygonObjects = []
for (lineObject in lineObjects) {
    def line = lineObject.getROI()
    def polygon = ROIs.createPolygonROI(line.getAllPoints(), line.getImagePlane())
    def polygonObject = PathObjects.createAnnotationObject(polygon, lineObject.getPathClass())
    polygonObject.setName(lineObject.getName())
    polygonObject.setColorRGB(lineObject.getColorRGB())
    polygonObjects << polygonObject
}
// Remove original line objects and add new polygon objects
removeObjects(lineObjects, true)
addObjects(polygonObjects)

// Get current image data and file path
def imageData = getCurrentImageData()
def serverPath = imageData.getServer().getPath()

// Create an output directory for masks within the image directory
def imagePath = serverPath.find(/file:\/.*/)  
imagePath = imagePath.replace("file:", "") 
def imageDir = new File(imagePath).getParent()  
def outputDir = new File(imageDir, 'masks').getAbsolutePath()
mkdirs(outputDir)  
def name = GeneralTools.stripExtension(imageData.getServer().getMetadata().getName())
def path = buildFilePath(outputDir, name + "_mask_new.png")

// Configure export settings
double downsample = 2               // Downsampling step size
def ClassificationLabel = "Layer 1" // Selected classification to convert

// Create a labeled image server for exporting the mask
def labelServer = new LabeledImageServer.Builder(imageData)
    .backgroundLabel(0, ColorTools.BLACK)  // Set background color to black
    .downsample(downsample)                // Apply downsampling
    .addLabel(ClassificationLabel, 1)      // Set label for selected classification with a value of 1
    .multichannelOutput(false)             // Set to single-channel output
    .build()

// Save the mask image to the specified path
writeImage(labelServer, path)
print("Mask generation completed! File path: " + path)