# -*- coding:utf-8 -*-

#### イーロン・マスクが映っている画像から顔を抽出するプログラム。（学習データ/テストデータ用）
#### 複数人映っている場合、この段階ではどれがイーロン・マスクかは判別できず、抽出した画像からイーロン・マスクの画像のみを取捨選択する必要がある。
#### 精度もOpenCVのデフォルト分類器（haarcascade_frontalface_default.xml）に従うため、例えば首元が顔として認識されて1つの抽出画像になったりすることもある。
#### やっていることは静止画をOpenCVのデフォルト分類器を通して顔を検出し、名前を付けて別画像として指定のディレクトリに出力しているだけ。



import cv2
import numpy as np
import os


# 集めてきた画像データのあるディレクトリ
input_data_path = './elonmusk_images/elonmusk'
# 切り抜いた画像の保存先ディレクトリ
save_path = './cutted_elon_images/'
# OpenCVのデフォルトの分類器のpath。(https://github.com/opencv/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xmlのファイルを使う)
cascade_path = '../../opencv-master/data/haarcascades/haarcascade_frontalface_default.xml'
faceCascade = cv2.CascadeClassifier(cascade_path)

# 収集した画像の枚数(任意で変更)
image_count = 10
# 顔検知に成功した数(デフォルトで0を指定)
face_detect_count = 0

# ディレクトリがなければ作る
if not os.path.isdir(save_path):
  os.makedirs(save_path)


# 集めた画像データから顔が検知されたら、切り取り、保存する。
for i in range(image_count):
  img = cv2.imread(input_data_path + str(i) + '.jpg', cv2.IMREAD_COLOR)
  cv2.imshow("loaded", img)
  gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  face = faceCascade.detectMultiScale(gray, 1.1, 3)
  if len(face) > 0:
    for rect in face:
      # 顔認識部分を赤線で囲み保存(今はこの部分は必要ない)
      # cv2.rectangle(img, tuple(rect[0:2]), tuple(rect[0:2]+rect[2:4]), (0, 0,255), thickness=1)
      # cv2.imwrite('detected.jpg', img)
      x = rect[0]
      y = rect[1]
      w = rect[2]
      h = rect[3]
      cv2.imwrite(save_path + 'cutted_elon' + str(face_detect_count) + '.jpg', img[y:y+h, x:x+w])
      face_detect_count = face_detect_count + 1
  else:
    print('image' + str(i) + ':NoFace')
