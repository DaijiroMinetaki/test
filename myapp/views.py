import os
import json
import base64  # base64 エンコーディング/デコーディング用
from dotenv import load_dotenv
load_dotenv()

# from pdf2image import convert_from_bytes
import fitz

from openai import AzureOpenAI

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from django.shortcuts import render

from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient

from myapp.prompt import COMMON_SYSTEM_PROMPT


# 環境変数から設定を読み込む
OPENAI_API_URL = os.getenv("OPENAI_API_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = "gpt-4o"
API_VERSION = "2024-10-21"

# Azure Blob Storage 接続情報
connection_string = os.getenv("BLOB_CONNECTION")
prompt_container_name = os.getenv("BLOB_CONTAINER_PROMPT")
jpeg_container_name = os.getenv("BLOB_CONTAINER_JPEG")  # JPEG 保存用コンテナ

# BlobServiceClient のインスタンスは使いまわす
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
prompt_container_client = blob_service_client.get_container_client(prompt_container_name)
jpeg_container_client = blob_service_client.get_container_client(jpeg_container_name)

def index(request):
    """
    1ページ構成の index.html をレンダリングするビュー
    """
    return render(request, 'myapp/index.html')

@csrf_exempt
def get_prompt(request):
    """
    指定されたBlobファイルからプロンプトテキストを取得する
    """
    blob_name = request.GET.get('blobName')
    if not blob_name:
        return JsonResponse({"error": "Blob name is required"}, status=400)

    blob_client = prompt_container_client.get_blob_client(blob_name)
    try:
        download_stream = blob_client.download_blob()
        prompt_text = download_stream.readall().decode('utf-8')
        return HttpResponse(prompt_text, content_type="text/plain")
    except Exception as e:
        return JsonResponse({"error": f"Failed to get prompt: {str(e)}"}, status=500)

@csrf_exempt
def save_prompt(request):
    """
    指定されたBlobファイルにプロンプトテキストを保存する
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            blob_name = data.get('blobName')
            text = data.get('text')

            if not blob_name or not text:
                return JsonResponse({'error': 'blobName and text are required'}, status=400)

            blob_client = prompt_container_client.get_blob_client(blob_name)
            blob_client.upload_blob(text, overwrite=True)
            return JsonResponse({'message': 'Prompt saved successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def save_result(request):
    """
    OpenAI応答など「結果」をBlobに保存するサンプル
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            blob_name = data.get('blobName')
            text = data.get('text')

            if not blob_name or text is None:
                return JsonResponse({'error': 'blobName and text are required'}, status=400)

            # 必要に応じて、result用のコンテナを作る
            # ここでは prompt_container_client を使い回す例
            blob_client = prompt_container_client.get_blob_client(blob_name)
            blob_client.upload_blob(text, overwrite=True)

            return JsonResponse({'message': 'Result saved successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

# PDF を JPEG に変換
def convert_to_jpegs(pdf_bytes):
    images = []
    # PDFをメモリ上でオープン（bytestream, filetype="pdf"）
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            # ピクセルマップ（Pix）を取得
            pix = page.get_pixmap()
            # JPEG形式のバイト列を作成
            img_bytes = pix.pil_tobytes(format="JPEG")
            images.append(img_bytes)
    return images

@csrf_exempt
def upload(request):
    print("upload view called")
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method."}, status=405)

    if 'pdf' not in request.FILES:
        return JsonResponse({"error": "アップロードされたファイルがありません。"}, status=400)

    pdf_file = request.FILES['pdf']
    print("pdf_file:", pdf_file)

    try:
        checkcount = int(request.POST.get('checkcount', '0'))
        user_prompt = request.POST.get('prompt', '')
        print("checkcount:", checkcount, "user_prompt:", user_prompt)
    except ValueError:
        checkcount = 0

    if checkcount == 0:
        prefix = "【寸法抽出】"
    elif checkcount == 1:
        prefix = "【図面突合】"
    elif checkcount == 2:
        prefix = "【計算確認】"
    else:
        prefix = ""

    pdf_file.seek(0)
    if not pdf_file.name.lower().endswith('.pdf'):
        return JsonResponse({"error": "PDFファイルのみアップロード可能です。"}, status=400)

    try:
        images = convert_to_jpegs(pdf_file.read())
        print("images converted")
    except Exception as e:
        print(f"PDF conversion error: {e}")
        return JsonResponse({"error": f"PDFの変換に失敗しました: {str(e)}"}, status=500)

    if not images:
        return JsonResponse({"error": "PDFから画像を生成できませんでした。"}, status=500)

    # 必要であればBlob Storageに保存 (今回はBase64エンコードするので、Blob保存はコメントアウト)
    # save_to_blob = True  # 例：設定や条件に応じて切り替え
    # if save_to_blob:
        # ... (Blob Storageへの保存処理) ...  #ここはコメントアウト、もしくは削除

    # Base64エンコード
    buffer = BytesIO()
    buffer.write(images[0])  # images[0] (bytesオブジェクト) を直接 buffer に書き込む
    jpeg_data = buffer.getvalue()
    base64_image = base64.b64encode(jpeg_data).decode('utf-8')

    top_text = f"{prefix}PDFファイル '{pdf_file.name}' の処理が完了しました。"

    openai_client = AzureOpenAI(
        api_key=OPENAI_API_KEY,
        api_version=API_VERSION,
        azure_endpoint=OPENAI_API_URL
    )

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": COMMON_SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]},
            ],
            max_tokens=3000
        )
        response_text = response.choices[0].message.content if response and response.choices else "エラー: OpenAIからの応答がありません。APIキーやモデルの設定を確認してください。"
    except AzureError as e:
        print(f"OpenAI API call error: {e}")
        return JsonResponse({"error": f"OpenAI API呼び出しエラー: {str(e)}"}, status=500)

    response_data = {
        "result": top_text,
        "bottomText": response_text
    }
    return JsonResponse(response_data)