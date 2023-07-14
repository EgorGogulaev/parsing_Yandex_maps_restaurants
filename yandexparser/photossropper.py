from PIL import Image
import glob

class PhotoCropper:

    def __init__(self):
        self.photo_paths = glob.glob('yandexparser/photos/*')
        self.output_path = './yandexparser/photos/combined_photo.jpg'

    def combine_photos(self):
        # Open the first image to get the base dimensions
        base_image = Image.open(self.photo_paths[0])
        width, height = base_image.size

        # Calculate the size of each sub-image based on the desired proportion
        sub_width = width // 2
        sub_height = height // 2

        # Create a new blank image with the appropriate size
        combined_image = Image.new('RGB', (width, height))

        # Iterate over each photo path and resize it to fit into the combined image
        for i, path in enumerate(self.photo_paths):
            # Open the image and resize it to the sub-image size
            image = Image.open(path)
            image = image.resize((sub_width, sub_height))

            # Calculate the coordinates to paste the sub-image onto the combined image
            x = (i % 2) * sub_width
            y = (i // 2) * sub_height

            # Paste the sub-image onto the combined image
            combined_image.paste(image, (x, y))

        # Save the combined image
        combined_image.save(self.output_path)
        print(f"Combined image saved as {self.output_path}")
