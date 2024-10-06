from PIL import Image, ImageFont, ImageDraw 

class ImageCreator:
    EPD_WIDTH = 600
    EPD_HEIGHT = 448

    def __init__(self, temperature, location, weather, todays_date, metric):
        self.width = self.EPD_WIDTH
        self.height = self.EPD_HEIGHT
        self.BLACK  = 0x000000   #   0000  BGR
        self.WHITE  = 0xffffff   #   0001
        self.GREEN  = 0x00ff00   #   0010
        self.BLUE   = 0xff0000   #   0011
        self.RED    = 0x0000ff   #   0100
        self.YELLOW = 0x00ffff   #   0101
        self.ORANGE = 0x0080ff   #   0110

        self.temperature = temperature
        self.location = location
        self.weather = weather
        self.todays_date = todays_date
        self.metric = metric

    def draw_text(self, image):
        draw = ImageDraw.Draw(image)
        # font = ImageFont.truetype(<font-file>, <font-size>)
        heading = ImageFont.truetype("Ubuntu-R.ttf", 36, encoding="unic")
        subheading = ImageFont.truetype("Ubuntu-R.ttf", 28, encoding="unic")
        shadow_color = (255,255,255)
        text_color = (0,0,0)
        heading_x = 32
        heading_y = 64
        subheading_x = 32
        subheading_y = 32
        border_thickness = 2
        # draw.text((x, y),"Sample Text",(r,g,b))
        degree_text = "°C" if self.metric else "°F"
        draw.text((heading_x-border_thickness, heading_y), f"{self.temperature}{degree_text} {self.weather}", shadow_color, font=heading)
        draw.text((heading_x+border_thickness, heading_y), f"{self.temperature}{degree_text} {self.weather}", shadow_color, font=heading)
        draw.text((heading_x, heading_y-border_thickness), f"{self.temperature}{degree_text} {self.weather}", shadow_color, font=heading)
        draw.text((heading_x, heading_y+border_thickness), f"{self.temperature}{degree_text} {self.weather}", shadow_color, font=heading)
        draw.text((heading_x, heading_y), f"{self.temperature}{degree_text} {self.weather}", text_color, font=heading)

        draw.text((subheading_x-border_thickness, subheading_y), f"{self.location} {self.todays_date}", shadow_color, font=subheading)
        draw.text((subheading_x+border_thickness, subheading_y), f"{self.location} {self.todays_date}", shadow_color, font=subheading)
        draw.text((subheading_x, subheading_y-border_thickness), f"{self.location} {self.todays_date}", shadow_color, font=subheading)
        draw.text((subheading_x, subheading_y+border_thickness), f"{self.location} {self.todays_date}", shadow_color, font=subheading)
        draw.text((subheading_x, subheading_y), f"{self.location} {self.todays_date}", text_color, font=subheading)

        return image

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

        image_temp = self.draw_text(image_temp)
        image_temp.save('sample-out.jpg')

        # Convert the source image to the 7 colors, dithering if needed
        image_7color = image_temp.convert("RGB").quantize(palette=pal_image)
        buf_7color = bytearray(image_7color.tobytes('raw'))

        # PIL does not support 4 bit color, so pack the 4 bits of color
        # into a single byte to transfer to the panel
        buf = [0x00] * int(self.width * self.height / 2)
        idx = 0
        for i in range(0, len(buf_7color), 2):
            buf[idx] = (buf_7color[i] << 4) + buf_7color[i+1]
            idx += 1
            
        with open('quantized.bmp', 'wb') as file:
            file.write(bytearray(buf))
        return buf
