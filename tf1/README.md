# tensorflowを使用した顔認証サンプル
参考
https://qiita.com/AkiyoshiOkano/items/72f3e4ba9caf514460ee

## TensorBoard実行コマンド
```sh
cd tf1
tensorboard --logdir=./data
```

## ローカルで画像認識用のwebページを表示
```sh
pip install Flask

cd tf1
python web.py
```