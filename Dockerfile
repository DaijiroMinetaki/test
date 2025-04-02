# ベースイメージ
FROM python:3.13

# 作業ディレクトリを設定
WORKDIR /usr/src/app

# pip をアップグレードしておく
RUN python -m pip install --upgrade pip

# ホスト側の requirements.txtとwhlをコンテナ内にコピーし、インストール
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# プロジェクト全体を作業ディレクトリにコピー
COPY . /usr/src/app/

# ポートを公開 (Gunicorn 用)
EXPOSE 8000

# Gunicorn を使った起動コマンド
# "myproject" が Django プロジェクト名
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "myproject.wsgi:application"]