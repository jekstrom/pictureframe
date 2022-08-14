import PIL
from PIL import Image
import io
import sys

EPD_WIDTH       = 600
EPD_HEIGHT      = 448

class Test:
    def __init__(self):
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.BLACK  = 0x000000   #   0000  BGR
        self.WHITE  = 0xffffff   #   0001
        self.GREEN  = 0x00ff00   #   0010
        self.BLUE   = 0xff0000   #   0011
        self.RED    = 0x0000ff   #   0100
        self.YELLOW = 0x00ffff   #   0101
        self.ORANGE = 0x0080ff   #   0110

    def getbuffer(self, image):
        # Create a pallette with the 7 colors supported by the panel
        pal_image = Image.new("P", (1,1))
        pal_image.putpalette( (0,0,0,  255,255,255,  0,255,0,   0,0,255,  255,0,0,  255,255,0, 255,128,0) + (0,0,0)*249)
        
        imwidth, imheight = image.size
        if (imwidth > self.width and imheight > self.height):
            image_temp = image.resize((self.width, self.height), resample=0)

        # Check if we need to rotate the image
        imwidth, imheight = image_temp.size
        if(imwidth == self.width and imheight == self.height):
            image_temp = image_temp
        elif(imwidth == self.height and imheight == self.width):
            image_temp = image_temp.rotate(90, expand=True)

        # Convert the soruce image to the 7 colors, dithering if needed
        image_7color = image_temp.convert("RGB").quantize(palette=pal_image)

        newimg = image_7color.convert(mode='RGB', colors=24)
        newimg.save('quantized.bmp')


def main():
    Test().getbuffer(Image.open(sys.argv[1], 'r'))
  
  

if __name__=="__main__":
    main()