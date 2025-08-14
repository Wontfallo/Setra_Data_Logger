import board
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_ssd1306

# Release any currently occupied displays
displayio.release_displays()

# Define the I2C pins for the OLED display
# SDA is GP0, SCL is GP1
i2c = board.I2C(scl=board.GP1, sda=board.GP0)

# Create the SSD1306 display object
# The OLED is 128x31
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_ssd1306.SSD1306(display_bus, width=128, height=31)

# Clear the display
display.fill(0)
display.show()

# Create a text label
text_area = label.Label(terminalio.FONT, text="Hello World!", color=0xFFFFFF)

# Position the text in the center of the display
text_area.x = (display.width - text_area.bounding_box[2]) // 2
text_area.y = display.height // 2 - text_area.bounding_box[3] // 2

# Create a group to hold the text and add it to the display
splash = displayio.Group()
splash.append(text_area)
display.show(splash)

# Keep the code running to display the text
while True:
    pass
