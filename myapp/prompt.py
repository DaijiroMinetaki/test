# 共通プロンプト（全ステップ共通で使うシステム側の指示）
COMMON_SYSTEM_PROMPT = '''
添付した画像は、カルバートの図面のイメージ図です。
図面内の各部位には業界基準で名前が付けられており、この画像内では赤文字で記載しています。

また、図面の読み方について補足です。

# 径の通し番号について
・便宜上、図面内左から順に1, 2, 3…と番号を振ることとします。
  例えばイメージ図では2径口の場合、左側の径が1、右側の径が2です。
  径の数が3つや4つの場合も同様に左から順番に番号を振ってください。

# 図面内に同じ名称の部位が複数ある場合
・径の通し番号を末尾に付与します。
  例えばイメージ図で「内空幅」が2つある場合、「内空幅1」「内空幅2」というように名付けます。
  「内空幅1」は左側の径の内空幅を意味します。

# 「ハンチ」について
・「ハンチ」は、強度を高める目的で鉄筋コンクリート造りの建物で、
  床やスラブ、梁が柱に接する部分を大きくしたものを指します。
・「ハンチ」は常にあるとは限りません。無い場合は径の内側角が直角となります。
・複数の「ハンチ」がある場合、向かい合ったハンチは同じ寸法となることが多いです。

# ステップ概要
・このアプリケーションでは以下のステップを順番に行います：
  1) 寸法抽出
  2) 図面突合
  3) 計算確認
・それぞれのステップに応じて必要な作業を実施してください。
'''

# DIMENSION_PROMPT_DEFAULT = '''
# このステップでは、図面に記載されている各部位の寸法数値を抽出します。
# 計算や推測は行わず、図面に書かれている数字のみを一覧化してください。

# ・値や部位が不明な場合は「不明」
# ・図面内に存在しない場合は「該当なし」
# と記載してください。
# '''

# DRAWING_PROMPT_DEFAULT = '''
# このステップでは、前ステップで抽出した寸法情報と、図面から詳細に抽出した数値を突合します。
# また、公式を用いて添付の計算結果が正しいか部分的に検証してください。
# 公式内では a が「ハンチ(W)」、b が「ハンチ(H)」とします。

# 前ステップ(寸法抽出)の結果との整合性を確認し、
# 数値に整合が取れない場合はその旨を指摘してください。
# '''

# CALCULATION_PROMPT_DEFAULT = '''
# このステップでは、計算結果が正しいかを最終的に確認します。
# また、計算に使用している値が図面から正しく抜き出されているか、
# 前ステップの突合結果と矛盾がないかを検証してください。
# '''

