#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import cv2
import random
import numpy as np
import tensorflow as tf
import tensorflow.python.platform

# 識別ラベルの数(今回はザッカーバーグ:0,イーロンマスク：1,ビルゲイツ:2なので、3)
NUM_CLASSES = 3
#### これは画像の1辺のサイズに相当している模様
# 学習する時の画像のサイズ(px)
IMAGE_SIZE = 28
#### こっちがピクセル数。画像の縦×横のサイズ。RGBの場合は更に3倍する必要がある。
# 画像の次元数(28* 28*カラー(?))
IMAGE_PIXELS = IMAGE_SIZE*IMAGE_SIZE*3

#### tensorflowで使用する定数の定義をしている。
#### tf.app.flagsにDEFINE_●●の関数があるため、それを使用する。
#### 第一引数が定数名、第二引数が初期値、第三引数が説明。
#### "フラグ"となっているが、割と"変数(定数)"の方に近いはず。
#### 第三引数(説明)を入れると、コマンドライン実行の際に"--help"をつけるとこれら定数情報がhelpに追加されて表示される
# 学習に必要なデータのpathや学習の規模を設定
# パラメタの設定、デフォルト値やヘルプ画面の説明文を登録できるTensorFlow組み込み関数
flags = tf.app.flags
FLAGS = flags.FLAGS
# 学習用データ
flags.DEFINE_string('train', './data/train/data.txt', 'File name of train data')
# 検証用テストデータ
flags.DEFINE_string('test', './data/test/data.txt', 'File name of train data')
# データを置いてあるフォルダ
flags.DEFINE_string('train_dir', './data', 'Directory to put the training data.')
# データ学習訓練の試行回数
flags.DEFINE_integer('max_steps', 30, 'Number of steps to run trainer.')
# 1回の学習で何枚の画像を使うか
flags.DEFINE_integer('batch_size', 5, 'Batch size Must divide evenly into the dataset sizes.')
# 学習率、小さすぎると学習が進まないし、大きすぎても誤差が収束しなかったり発散したりしてダメとか
flags.DEFINE_float('learning_rate', 1e-4, 'Initial learning rate.')

# AIの学習モデル部分(ニューラルネットワーク)を作成する
# images_placeholder: 画像のplaceholder, keep_prob: dropout率のplace_holderが引数になり
# 入力画像に対して、各ラベルの確率を出力して返す
def inference(images_placeholder, keep_prob):

  # 重みを標準偏差0.1の正規分布で初期化する
  def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)

  # バイアスを標準偏差0.1の正規分布で初期化する
  def bias_variable(shape):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)

  #### 畳み込み層：参考...http://postd.cc/how-do-convolutional-neural-networks-work/
  #### 2つの画像に対して一致度を検出しようとした際に、画像全範囲で検出すればほぼ不一致となる結果に対して、
  #### なにもなく人間のように「このへんとこのへんが似ている」と検出することはできないので、曖昧に認識させるためのデータとして
  #### 特定の区切りずつ（例えば9x9ピクセルの画像に対して、3x3ピクセルずつ）特徴を抽出するイメージ？
  #### それを行うのが畳み込み層。
  #### これ単体で使うと言うよりはこの後に出てくるプーリング層等と一緒に使うっぽい？？？
  # 畳み込み層を作成する
  def conv2d(x, W):
    return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

  #### プーリング層：参考...http://postd.cc/how-do-convolutional-neural-networks-work/
  #### 畳み込み層で畳み込みを行った後、大きな画像を重要な情報は残しつつ縮小する。
  #### 2x2ピクセルくらいの中で最大値をとっていく（これくらいのサイズが上手く機能するらしい）ことで、サイズが縮小される。（この例題1/4サイズになる)
  #### プーリング層によって「特定の区切り（2x2ピクセル内）のどこかに特徴と一致する部分があるかどうか」という曖昧検索が可能になる
  # プーリング層を作成する
  def max_pool_2x2(x):
    return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                          strides=[1, 2, 2, 1], padding='SAME')

  #### 与えられた画像をNNに必要なheight, width, channelに変換する。
  #### 第一引数がtensor：inputとなるテンソル。ここでは画像のプレースホルダー。呼び出し元を見ると、N×画像のピクセル数の行列が渡されている。
  #### 第二引数がshape：変えたい形。IMAGE_SIZE×IMAGE_SIZE×RGB(3)の行列を持つN次元行列を作っている？？？？？？？？
  # ベクトル形式で入力されてきた画像データを28px * 28pxの画像に戻す(?)。
  # 今回はカラー画像なので3(モノクロだと1)
  x_image = tf.reshape(images_placeholder, [-1, IMAGE_SIZE, IMAGE_SIZE, 3])

  #### この先●●層の部分で出てくるname_scopeはTensorBoard用にスコープを分けているだけっぽい？？
  #### これをやるだけでグラフの中にスコープ（グループのようなもの）が作成できるため、データフローが見やすくなるっぽい。

  # 畳み込み層第1レイヤーを作成
  with tf.name_scope('conv1') as scope:
    # 引数は[width, height, input, filters]。
    # 5px*5pxの範囲で画像をフィルターしている。今回はカラー画像なのでinputは3?
    # 32個の特徴を検出する
    W_conv1 = weight_variable([5, 5, 3, 32])
    # バイアスの数値を代入
    b_conv1 = bias_variable([32])
    #### Relu関数とは畳み込み層のアクティベーション関数(活性化関数)。
    #### 入力値（ここだと画像の特徴量？）に対して、0以下のときは0、それ以上の場合はその数値のまま出力する。
    #### 参考：https://qiita.com/namitop/items/d3d5091c7d0ab669195f#relu%E9%96%A2%E6%95%B0
    # 特徴として検出した有用そうな部分は残し、特徴として使えなさそうな部分は
    # 0として、特徴として扱わないようにしているという理解(Relu関数)
    h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)

  # プーリング層1の作成
  # 2*2の枠を作り、その枠内の特徴を1*1分にいい感じに圧縮させている。
  # その枠を2*2ずつスライドさせて画像全体に対して圧縮作業を適用するという理解
  # ざっくり理解で細分化された特徴たちをもうちょっといい感じに大まかにまとめる(圧縮する)
  with tf.name_scope('pool1') as scope:
    h_pool1 = max_pool_2x2(h_conv1)

  # 畳み込み層第2レイヤーの作成
  with tf.name_scope('conv2') as scope:
    # 第一レイヤーでの出力を第2レイヤー入力にしてもう一度フィルタリング実施。
    # 64個の特徴を検出する。inputが32なのはなんで?(教えて欲しい)
    W_conv2 = weight_variable([5, 5, 32, 64])
    # バイアスの数値を代入(第一レイヤーと同じ)
    b_conv2 = bias_variable([64])
    # 検出した特徴の整理(第一レイヤーと同じ)
    h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)

  # プーリング層2の作成(ブーリング層1と同じ)
  with tf.name_scope('pool2') as scope:
    h_pool2 = max_pool_2x2(h_conv2)

  # 全結合層1の作成
  with tf.name_scope('fc1') as scope:
    W_fc1 = weight_variable([7*7*64, 1024])
    b_fc1 = bias_variable([1024])
    # 画像の解析を結果をベクトルへ変換
    h_pool2_flat = tf.reshape(h_pool2, [-1, 7*7*64])
    # 第一、第二と同じく、検出した特徴を活性化させている
    h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)
    #### dropoutとは学習処理の際に特徴変数からの入力を1/2(?)の確率で故意に欠落させ、ノイズを発生させている。
    #### 学習データにだけ最適化されてしまう"過学習"の予防をしている。
    #### 参考：http://enakai00.hatenablog.com/entry/2016/02/29/090112
    # dropoutの設定
    # 訓練用データだけに最適化して、実際にあまり使えないような
    # AIになってしまう「過学習」を防止の役割を果たすらしい
    h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

  # 全結合層2の作成(読み出しレイヤー)
  with tf.name_scope('fc2') as scope:
    W_fc2 = weight_variable([1024, NUM_CLASSES])
    b_fc2 = bias_variable([NUM_CLASSES])

  #### 出力層の活性化関数として用いられる関数（ソフトマックス関数）
  #### 一般的に分類問題で使われる。
  #### 出力はラベル数分あり、各ラベルの出力は0~1かつ各ラベルの総和は1になる。
  #### つまり、[0.1, 0.4. 0.5]のような出力がされ、この結果から3番目のラベルに該当すると分類される。
  # ソフトマックス関数による正規化
  # ここまでのニューラルネットワークの出力を各ラベルの確率へ変換する
  with tf.name_scope('softmax') as scope:
    y_conv=tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)

  # 各ラベルの確率(のようなもの?)を返す
  return y_conv

#### 誤差関数の一つ（クロスエントロピー）
#### 真の確率(p)と推定確率(q)との誤差を計算している.
#### 誤差が小さいほうがいい為、クロスエントロピーは小さい値のほうが良い。
#### p=qのときがクロスエントロピーの最小となる
# 予測結果と正解にどれくらい「誤差」があったかを算出する
# logitsは計算結果:  float - [batch_size, NUM_CLASSES]
# labelsは正解ラベル: int32 - [batch_size, NUM_CLASSES]
def loss(logits, labels):
  # 交差エントロピーの計算
  cross_entropy = -tf.reduce_sum(labels*tf.log(logits))
  #### これはTensorBoard用の記述のため実際は不要
  # TensorBoardで表示するよう指定
  tf.summary.scalar("cross_entropy", cross_entropy)
  # 誤差の率の値(cross_entropy)を返す
  return cross_entropy

#### 訓練を実施する関数のようだた、詳細未調査
# 誤差(loss)を元に誤差逆伝播を用いて設計した学習モデルを訓練する
# 裏側何が起きているのかよくわかってないが、学習モデルの各層の重み(w)などを
# 誤差を元に最適化して調整しているという理解(?)
# (誤差逆伝播は「人工知能は人間を超えるか」書籍の説明が神)
def training(loss, learning_rate):
  #この関数がその当たりの全てをやってくれる様
  train_step = tf.train.AdamOptimizer(learning_rate).minimize(loss)
  return train_step

#### 未調査
# inferenceで学習モデルが出した予測結果の正解率を算出する
def accuracy(logits, labels):
  # 予測ラベルと正解ラベルが等しいか比べる。同じ値であればTrueが返される
  # argmaxは配列の中で一番値の大きい箇所のindex(=一番正解だと思われるラベルの番号)を返す
  correct_prediction = tf.equal(tf.argmax(logits, 1), tf.argmax(labels, 1))
  # booleanのcorrect_predictionをfloatに直して正解率の算出
  # false:0,true:1に変換して計算する
  accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))
  #### この記述はTensorBoard用の記述のため実際は不要
  # TensorBoardで表示する様設定
  tf.summary.scalar("accuracy", accuracy)
  return accuracy

if __name__ == '__main__':
  #### トレーニング用の画像パスとラベルが書いてあるファイルを開く
  # ファイルを開く
  f = open(FLAGS.train, 'r')
  # データを入れる配列
  train_image = []
  train_label = []
  #### 1画像ずつ変換して配列に追加する
  for line in f:
    # 改行を除いてスペース区切りにする
    line = line.rstrip()
    l = line.split()
    # データを読み込んで28x28に縮小
    img = cv2.imread(l[0])
    img = cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE))
    # 一列にした後、0-1のfloat値にする
    train_image.append(img.flatten().astype(np.float32)/255.0)
    # ラベルを1-of-k方式で用意する
    tmp = np.zeros(NUM_CLASSES)
    tmp[int(l[1])] = 1
    train_label.append(tmp)
  # numpy形式に変換
  train_image = np.asarray(train_image)
  train_label = np.asarray(train_label)
  f.close()

  #### テスト用データもトレーニング用画像と同じ処理を行う
  f = open(FLAGS.test, 'r')
  test_image = []
  test_label = []
  for line in f:
    line = line.rstrip()
    l = line.split()
    img = cv2.imread(l[0])
    img = cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE))
    test_image.append(img.flatten().astype(np.float32)/255.0)
    tmp = np.zeros(NUM_CLASSES)
    tmp[int(l[1])] = 1
    test_label.append(tmp)
  test_image = np.asarray(test_image)
  test_label = np.asarray(test_label)
  f.close()

  #### このwith内の処理はすべてTensorBoard用の記述を含むため、その部分は無くてもOK
  #TensorBoardのグラフに出力するスコープを指定
  with tf.Graph().as_default():
    # 画像を入れるためのTensor(28*28*3(IMAGE_PIXELS)次元の画像が任意の枚数(None)分はいる)
    images_placeholder = tf.placeholder("float", shape=(None, IMAGE_PIXELS))
    # ラベルを入れるためのTensor(3(NUM_CLASSES)次元のラベルが任意の枚数(None)分入る)
    labels_placeholder = tf.placeholder("float", shape=(None, NUM_CLASSES))
    # dropout率を入れる仮のTensor
    keep_prob = tf.placeholder("float")

    # inference()を呼び出してモデルを作る
    logits = inference(images_placeholder, keep_prob)
    # loss()を呼び出して損失を計算
    loss_value = loss(logits, labels_placeholder)
    # training()を呼び出して訓練して学習モデルのパラメーターを調整する
    train_op = training(loss_value, FLAGS.learning_rate)
    # 精度の計算
    acc = accuracy(logits, labels_placeholder)

    # 保存の準備
    saver = tf.train.Saver()
    # Sessionの作成(TensorFlowの計算は絶対Sessionの中でやらなきゃだめ)
    sess = tf.Session()
    # 変数の初期化(Sessionを開始したらまず初期化)
    sess.run(tf.global_variables_initializer())
    # TensorBoard表示の設定(TensorBoardの宣言的な?)
    summary_op = tf.summary.merge_all()
    # train_dirでTensorBoardログを出力するpathを指定
    summary_writer = tf.summary.FileWriter(FLAGS.train_dir, sess.graph_def)

    # 実際にmax_stepの回数だけ訓練の実行していく
    for step in range(FLAGS.max_steps):
      for i in range(int(len(train_image)/FLAGS.batch_size)):
        # batch_size分の画像に対して訓練の実行
        batch = FLAGS.batch_size*i
        # feed_dictでplaceholderに入れるデータを指定する
        sess.run(train_op, feed_dict={
          images_placeholder: train_image[batch:batch+FLAGS.batch_size],
          labels_placeholder: train_label[batch:batch+FLAGS.batch_size],
          keep_prob: 0.5})

      # 1step終わるたびに精度を計算する
      train_accuracy = sess.run(acc, feed_dict={
        images_placeholder: train_image,
        labels_placeholder: train_label,
        keep_prob: 1.0})
      print("step %d, training accuracy %g" % (step, train_accuracy))

      #### この処理はTensorBoard用の処理のため実際は不要
      # 1step終わるたびにTensorBoardに表示する値を追加する
      summary_str = sess.run(summary_op, feed_dict={
        images_placeholder: train_image,
        labels_placeholder: train_label,
        keep_prob: 1.0})
      summary_writer.add_summary(summary_str, step)

  # 訓練が終了したらテストデータに対する精度を表示する
  print("test accuracy %g" % sess.run(acc, feed_dict={
    images_placeholder: test_image,
    labels_placeholder: test_label,
    keep_prob: 1.0}))

  # データを学習して最終的に出来上がったモデルを保存
  # "model.ckpt"は出力されるファイル名
  save_path = saver.save(sess, "./model.ckpt")
