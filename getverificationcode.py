from PIL import ImageFilter
from PIL import Image
import pytesseract
import os

threshold = 144
'''
number_1_site = (5, 1, 17, 16)
number_2_site = (29, 1, 41, 16)
operator_site = (16, 2, 26, 16)
suitable_window_width = 850
suitable_window_height = 800
sub_shot_site = (450, 417, 505, 437)
'''
number_1_site = (5, 1, 16, 15)
number_2_site = (29, 1, 40, 15)
operator_site = (17, 1, 25, 13)
suitable_window_width = 850
suitable_window_height = 800
sub_shot_site = (450, 462, 505, 481)


def get_verification_code_from_shot(image):
    image = image.crop(sub_shot_site)
    image = image.convert('L')
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    image = image.point(table, '1')
    # image.save('/home/syner/subshot.png')
    number_1_image = image.crop(number_1_site).resize((48, 60))
    number_2_image = image.crop(number_2_site).resize((48, 60))
    operator_image = image.crop(operator_site).resize((40, 56))

    number_1_image = number_1_image.filter(ImageFilter.BLUR)
    number_2_image = number_2_image.filter(ImageFilter.BLUR)
    operator_image = operator_image.filter(ImageFilter.BLUR)
    '''
    number_1_image.save('/home/syner/num1.png')
    number_2_image.save('/home/syner/num2.png')
    operator_image.save('/home/syner/oper.png')
    '''
    number_1 = pytesseract.image_to_string(number_1_image, config="-psm 10 -c tessedit_char_whitelist=1234567890")
    number_2 = pytesseract.image_to_string(number_2_image, config="-psm 10 -c tessedit_char_whitelist=1234567890")
    operator = pytesseract.image_to_string(operator_image, config="-psm 10 -c tessedit_char_whitelist=*+")
    return number_1+operator+number_2


def get_verification_code_from_driver(driver):
    driver.set_window_size(suitable_window_width, suitable_window_height)
    driver.get_screenshot_as_file("shot.png")
    image = Image.open('shot.png')
    res = get_verification_code_from_shot(image)
    # print(res)
    os.remove('shot.png')
    return res

