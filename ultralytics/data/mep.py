import io
from PIL import Image
import cv2
import numpy as np
import typing
import argparse
import os

class XorCipher:
	def __init__(self, key: str):
		super().__init__()
		self.ChangeKey(key)
		
	def Encrypt(self, data: bytes) -> bytes:
		# 使用异或操作加密或解密数据
		return bytes([data[i] ^ self.key[i % len(self.key)] for i in range(len(data))])
	
	def Decrypt(self, data: bytes) -> bytes:
		return self.Encrypt(data)
	
	def ChangeKey(self, key: str):
		self.key = key.encode(encoding='utf-8')

FileSuffix = ".mep"
MetadataFilename = "md" + FileSuffix

cipher: typing.Optional[XorCipher] = None

def SetKey(mep_key: str):
	global cipher
	cipher = XorCipher(mep_key)
	print("【】】】】 Using cipher.")

def decode(filename: str):
	with open(filename, 'rb') as f:
		data = f.read()
		data = cipher.Decrypt(data)
	buf = io.BytesIO(data)
	return buf

def encode(filename_or_data: typing.Union[str, bytes]):
	if type(filename_or_data) is str:
		with open(filename_or_data, 'rb') as f:
			data = f.read()
	elif type(filename_or_data) is bytes:
		data = filename_or_data
	else:
		raise Exception("filename_or_data must be str or bytes")
	
	if cipher is None:
		raise Exception("No ciper created.")
	
	return cipher.Encrypt(data)

def PILRead(filename: str):
	if cipher is None or not filename.endswith(FileSuffix):
		return Image.open(filename)
	else:
		buf = decode(filename)
		return Image.open(buf)

def CVRead(filename: str, flags: int = cv2.IMREAD_COLOR):
	if cipher is None or not filename.endswith(FileSuffix):
		return cv2.imread(filename, flags)
	else:
		img = PILRead(filename)
		img_np = np.array(img)
		cv_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
		return cv_img
	
def main(args):
	SetKey(args.mep_key)

	print("- Create directory: ", args.output)
	os.makedirs(args.output, exist_ok=True)

	print("- Loading dataset...")
	# 支持的图片扩展名
	image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
	folder_path: str = args.dataset
	# 遍历文件夹
	index = 1
	for filename in os.listdir(folder_path):
		name, ext = os.path.splitext(filename)

		# 检查是否为图片
		if ext.lower() not in image_extensions:
			continue

		image_path = os.path.join(folder_path, filename)
		img = Image.open(image_path)

		webpIO = io.BytesIO()
		if args.use_webp:
			if image_path.endswith('.webp'):
				with open(image_path, 'rb') as f:
					webpIO = io.BytesIO(f.read())
			else:
				img.save(webpIO, format="WebP", quality=95)
		img.close()

		mep_img_path = f"dat{index}.mep"
		target_txt_path = os.path.join(args.output, f"dat{index}.txt")
		outputfn = os.path.join(args.output, mep_img_path)
		if args.use_webp:
			data = encode(webpIO.getvalue())
		else:
			data = encode(image_path)
		with open(outputfn, 'wb') as f:
			f.write(data)

		txt_filename = f"{name}.txt"
		txt_path = os.path.join(folder_path, txt_filename)
		
		# 检查并读取对应的文本文件
		if os.path.exists(txt_path):
			with open(txt_path, 'r', encoding='utf-8') as f:
				prompt = f.read().strip()
		else:
			print("没有找到对应的txt文件：", name)
			raise Exception("Not found correspondent txt file.")
		
		with open(target_txt_path, 'w', encoding='utf-8') as f:
			f.write(prompt)
		
		print(f"-- Convert {image_path} => {mep_img_path}")
		index = index + 1

	print(f"- Converted {index - 1} images.")

	#check
	if index - 1 > 0:
		sample_fn = os.path.join(args.output, "dat1.mep")
		try:
			mat = CVRead(sample_fn)
			if not args.no_preview:
				cv2.imshow("test", mat)
				cv2.waitKey()
				cv2.destroyAllWindows()
		except Exception as e:
			print(f"Error in checking: {e}")
		print("- Check done.")


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--dataset", type=str, required=True)
	parser.add_argument("--output", type=str, required=True)
	parser.add_argument("--mep_key", type = str, required=True)
	parser.add_argument("--use_webp", action="store_true")
	parser.add_argument("--no_preview", action="store_true")

	args = parser.parse_args()
	main(args)
