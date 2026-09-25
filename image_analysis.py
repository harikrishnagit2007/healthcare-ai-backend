from PIL import Image

def analyze_image(image_path): return {
"file": image_path,
"format": Image.open(image_path).format,
"width": Image.open(image_path).width,
"height": Image.open(image_path).height,
"mode": Image.open(image_path).mode,
"status": "Image loaded successfully"
}
