from google.cloud import vision

def analyze_image(image_path):
    client = vision.ImageAnnotatorClient()

    with open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    feature = vision.Feature(type=vision.Feature.Type.IMAGE_PROPERTIES)
    request = vision.AnnotateImageRequest(image=image, features=[feature])
    response = client.batch_annotate_images(requests=[request])

    if response.responses[0].error.message:
        raise Exception(f'Image Properties Error: {response.responses[0].error.message}')

    props = response.responses[0].image_properties_annotation
    for color_info in props.dominant_colors.colors:
        color = color_info.color
        print(f'Red: {color.red}, Green: {color.green}, Blue: {color.blue}')

# Test the function with an image path
analyze_image("C:\\Users\\31621\\Downloads\\Hele alkoen.jpg")

