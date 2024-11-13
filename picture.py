from PIL import Image, ImageOps

# 打开图片
img = Image.open('icon.png').convert("RGBA")

# 分离通道
r, g, b, a = img.split()

# 合并RGB通道并进行黑白翻转
rgb_img = Image.merge("RGB", (r, g, b)).convert("L")
inverted_rgb = ImageOps.invert(rgb_img)

# 重新合并Alpha通道
inverted_img = Image.merge("RGBA", (inverted_rgb, inverted_rgb, inverted_rgb, a))

# 保存反相后的图片，保留透明部分
inverted_img.save('icon_inverted.png')