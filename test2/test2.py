#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 全体参考：http://uepon.hatenadiary.com/entry/2017/04/06/213128

import cv2
import time

# 顔認識に使用するカスケード分類器を読み込む（読み込むものによって認識できるものが変わる）
faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_alt.xml')
# faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
# faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_alt_tree.xml')

# カメラセット(0→1にするとUSB接続したWEBカメラとかが使える)
# https://note.nkmk.me/python-opencv-mac-facetime-hd-camera-capture/
capture = cv2.VideoCapture(0)
# 画像サイズの指定する場合はsetを使用するらしい
# ret = capture.set(3, 480)  # フレームの横幅width（3が横幅を示し、480が幅のサイズを示す）
# ret = capture.set(4, 320)  # フレームの縦幅height（4が縦幅を示し、320が幅のサイズを示す）

i = 0
while True:
    start = time.clock() # 開始時刻（フレーム計算用）

    # 画像をカメラから取得（retは取得成功フラグ、実際の画像はimageに）
    ret, image = capture.read()
    # 静止画の場合は下記のような感じで指定するらしい
    # img = cv2.imread('image.jpg', cv2.IMREAD_COLOR)

    # BGR2GRAY変換（グレースケール変換）というもの。顔検出のためにやるっぽい
    # 変換しなくても出来るようだが、処理が早くなるとのこと。一般的にはこれは行うらしい。
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 顔検出
    # 1つ目の引数が、検出につかうグレースケール変換した画像
    # 2つ目の引数が、分類機の制度と処理スピードに影響するパラメータ（数値を小さくすると検出率は上がるものの、ご検知増加と処理時間が長くなるらしい。ここはカメラとか精度とかで調整っぽい）
    # 3つ目の引数が、「物体候補となる矩形は，最低でもこの数だけの近傍矩形を含む必要があります」という説明があるが、これはまだよくわからず・・・。
    # 4つ目の引数が、「物体が取り得る最小サイズ．これよりも小さい物体は無視されます」となっているので、検出対象によって適宜変えるっぽい
    # 返り値が、「入力画像中から異なるサイズの物体を検出します．検出された物体は，矩形のリストとして返されます」となっているので、検出された顔を切り取った矩形のリストが返されるっぽい。
    face = faceCascade.detectMultiScale(gray_image, scaleFactor=1.2, minNeighbors=2, minSize=(30, 30))
    # face = faceCascade.detectMultiScale(gray_image, scaleFactor=1.3, minNeighbors=2, minSize=(30, 30))

    if len(face) > 0:
        # このforの1ループが検出された一人分の顔になるはず（rectが顔の位置）
        for rect in face:
            # 画像に対して、顔検出した場所に赤い四角を引く（RGBは右からRGBらしい・・・。気持ち悪い・・・）。一番最後の引数が千の太さ
            cv2.rectangle(image, tuple(rect[0:2]), tuple(rect[0:2]+rect[2:4]), (0, 0,255), thickness=2)

    get_image_time = int((time.clock()-start)*1000) # 処理時間計測（フレーム計算用）
    # 1フレーム取得するのにかかった時間を表示
    cv2.putText( image, str(get_image_time)+"ms", (10,10), 1, 1, (0,255,0))

    cv2.imshow("Camera Test",image)
    # キーが押されたら保存・終了
    if cv2.waitKey(10) == 32: # 32:[Space]
        cv2.imwrite(str(i)+".jpg",image)
        i+=1
        print("Save Image..."+str(i)+".jpg")
    elif cv2.waitKey(10) == 27: # 27:Esc
        capture.release()
        cv2.destroyAllWindows()
        break
