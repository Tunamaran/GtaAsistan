from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([10, 10, 246, 246], radius=30, fill='#1e1e1e', outline='#00FF96', width=6)

try:
    fnt = ImageFont.truetype('segoeui.ttf', 90)
    fnt2 = ImageFont.truetype('segoeui.ttf', 40)
except:
    fnt = ImageFont.truetype('arial.ttf', 90)
    fnt2 = ImageFont.truetype('arial.ttf', 40)

d.text((128, 100), 'GTA', fill='#00FF96', font=fnt, anchor='mm')
d.text((128, 170), 'Asistan', fill='#ffffff', font=fnt2, anchor='mm')

img.save('app_icon.png')
img.save('app_icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])
print('Icon created!')
