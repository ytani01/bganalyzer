# TODO-133 の試し

サブエージェントは使っていない。main が試したスクリプトだけを残す（写真は顔が写っているので残さない）。

- `masktry.py`: 手で決めた四角い範囲の勾配を 0 にして `find_corners` を流す。範囲が盤の縁にかかり、比べにならなかった
- `yolotry.py`: YOLOv8n-seg（ultralytics 8.4、CPU 版 PyTorch、使い捨ての venv）の見つけた人や物の画素を、勾配から外して流す
