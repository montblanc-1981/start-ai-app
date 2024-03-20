import streamlit as st
from streamlit_chat import message
from langchain.chat_models import ChatOpenAI
from langchain.schema import (SystemMessage, HumanMessage, AIMessage)
from langchain.callbacks import get_openai_callback
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urlparse
import kaggle
import pandas as pd
import os
from kaggle.api.kaggle_api_extended import KaggleApi
import zipfile

def init_page():
    st.set_page_config(
        page_title="Kaggleコンペティション分析ツール",
        page_icon="🤗"
    )
    st.header("Kaggleコンペティション分析ツール 🤗")
    # サイドバーのタイトルを表示
    st.sidebar.title("Options")

def init_messages():
    # サイドバーにボタンを設置
    clear_button = st.sidebar.button("Clear Conversation", key="clear")
    # チャット履歴の初期化
    if clear_button or "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content="You are a helpful assistant.")          
        ]
        st.session_state.costs = []

def select_model():
    # サイドバーにオプションボタンを設置
    model = st.sidebar.radio("Choose a model:", ("GPT-3.5", "GPT-4"))
    if model == "GPT-3.5":
        model_name = "gpt-3.5-turbo"
    else:
        model_name = "gpt-4"
    
    return ChatOpenAI(temperature=0, model_name=model_name)

# def get_url_input():
#     url = st.text_input("URL: ", key="input")
#     return url

# def validate_url(url):
#     try:
#         result = urlparse(url)
#         return all([result.scheme, result.netloc])
#     except ValueError:
#         return False

def get_content_input():
    content = st.chat_input("OverView:")
    return content

def summary_prompt(content, n_chars=2000):
    return f"""以下英文はKaggleのコンペティションの説明文です。データ分析を行う上で必要なドメイン知識の情報を{n_chars}程度で高校生にわかるレベルで説明してください。参考WebサイトのURLも3～5つリストアップしてください。機械学習とKaggleの参考Webサイトは不要です。また、モデル候補についても2～3つ挙げて、各モデルについて説明してください。最後に、以下の英文から英検2級、英検準1級、英検1級程度の単語をリストアップしてください。
========

{content}

========
日本語でお願いします。
    """

# def get_content(url):
#     try:
#         with st.spinner("Fetching Content ..."):
#             response = requests.get(url)
#             soup = BeautifulSoup(response.text, 'html.parser')
#             overview_text = soup.find('div', data-testid='competition-detail-render-tid')
#             overview_text = overview_text.get_text()
#             print(overview_text)
#             return overview_text
            # for p_tag in soup.find_all('p'):
            #     return soup.p_tag.get_text()
            # fetch text from main (change the below code to filter page)
            # if soup.p:
            #     return soup.p.get_text()
            # elif soup.evaluation:
            #     return soup.evaluation.get_text()
            # else:
            #     return soup.h3.get_text()
    # except:
    #     st.write('something wrong')
    #     return None

# def build_prompt(content, n_chars=300):
#     return f"""以下はとある。Webページのコンテンツである。内容を{n_chars}程度でわかりやすく要約してください。

# ========

# {content[:1000]}

# ========

# 日本語で書いてね！
# """

def get_answer(llm, messages):
    # with get_openai_callback() as cb:
    answer = llm(messages)
    return answer.content

# コンペティションのデータをダウンロードし、最初のファイルのパスを返す
def download_competition_data(competition_name):
    api = kaggle.api
    # ダウンロード先のパスを指定
    download_path = f'kaggle_data/{competition_name}'
    # ダウンロード先のディレクトリが存在しない場合は作成
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    # コンペティションのデータをダウンロード（ZIPファイル）
    api.competition_download_files(competition_name, path=download_path, quiet=True, force=True)
    # ダウンロードしたZIPファイルのパス
    zip_file_path = f'{download_path}.zip'
    # ZIPファイルを展開
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(download_path)
    # 展開後のファイルリストを取得
    files = os.listdir(download_path)
    if files:
        return os.path.join(download_path, files[0])  # 最初のファイルのパスを返す
    else:
        return None

# データの基本的な前処理提案
def suggest_preprocessing(df):
    suggestions = []
    if df.isnull().sum().sum() > 0:
        suggestions.append("データに欠損値が含まれています。適切な欠損値処理が必要です。")
    if any(df.dtypes == 'object'):
        suggestions.append("カテゴリ変数が含まれています。エンコーディングが必要かもしれません。")
    if df.select_dtypes(include=['float64', 'int64']).apply(lambda x: x.max() - x.min()).max() > 1:
        suggestions.append("数値データのスケーリングを検討してください。")
    return suggestions


def main():
    init_page()

    llm = select_model()
    init_messages()

    
    # file = api.competition_download_file()
    # print(api.get_config_value("username"))
    # for competition in api.competitions_list():
    #     print(competition)
    
    
    container = st.container()
    response_container = st.container()

    with container:
        # url = get_url_input()
        # is_valid_url = validate_url(url)
        # if not is_valid_url:
        #     st.write('Please input valid url')
        #     answer = None
        # else:
        content = get_content_input()
        if content:
            prompt = summary_prompt(content)
            st.session_state.messages.append(HumanMessage(content=prompt))
            with st.spinner("ChatGPT is typing ..."):
                answer = get_answer(llm, st.session_state.messages)
        else:
            answer = None
    
    if answer:
        with response_container:
            st.markdown("## 概要説明")
            st.write(answer)
            st.markdown("---")
            st.markdown("## Original Text")
            st.write(content) 
    
    # ユーザー入力
    competition_name = st.text_input('Kaggleコンペ名を入力してください', '')

    if st.button('分析'):
        if competition_name:
            with st.spinner('データをダウンロードしています...'):
                file_path = download_competition_data(competition_name)
                if file_path:
                    try:
                        df = pd.read_csv(file_path, error_bad_lines=False)
                        st.success('データのダウンロードに成功しました。')
                        st.write('データの先頭5行:', df.head())
                        suggestions = suggest_preprocessing(df)
                        if suggestions:
                            st.write('前処理の提案:')
                            for suggestion in suggestions:
                                st.write('- ', suggestion)
                        else:
                            st.write('特に提案する前処理はありません。')
                    except Exception as e:
                        st.error(f'データの読み込み中にエラーが発生しました: {e}')
                else:
                    st.error('指定されたコンペティションのデータが見つかりません。')
        else:
            st.error('コンペ名が入力されていません。')


if __name__== '__main__':
    main()


