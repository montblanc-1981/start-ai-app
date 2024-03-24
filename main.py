import streamlit as st
from streamlit_chat import message
from langchain.chat_models import ChatOpenAI
from langchain.schema import (SystemMessage, HumanMessage, AIMessage)
from langchain.callbacks import get_openai_callback
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from time import sleep
import os

def init_page():
    st.set_page_config(
        page_title="Kaggleコンペティション分析ツール",
        page_icon="💡"
    )
    st.header("Kaggleコンペティション分析ツール 💡")
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
    model = st.sidebar.radio("Choose a model:", ("GPT-4", "GPT-3.5"))
    if model == "GPT-4":
        model_name = "gpt-4"
    else:
        model_name = "gpt-3.5-turbo"
    
    return ChatOpenAI(temperature=0, model_name=model_name)

def get_url_input():
    url = st.text_input("KaggleのURLを入力してください。コンペについて概要説明します。", key="input")
    return url

def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_content(url):
    try:
        with st.spinner("Fetching Content ..."):
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
            driver.get(url)
            content = driver.find_element(By.ID, "site-content").text
            driver.quit()
            return content
    except:
        st.write('something wrong')
        return None
    
def summary_prompt(content, n_chars=2000):
    return f"""以下英文はKaggleのコンペティションの説明文です。
    まず、英文のOverviewという単語以降で、DescriptionやEvaluationなどコンペに関する重要な内容のみを英文で抽出してください。
    次に、その抽出した英文について、DescriptionやEvaluationなどを日本語訳してください。また、データ分析を行う上で必要なドメイン知識の情報を{n_chars}程度で高校生にわかるレベルで説明してください。参考WebサイトのURLも3～5つリストアップしてください。機械学習とKaggleの参考Webサイトは不要です。
    さらに、モデル候補についても2～3つ挙げて、各モデルについて説明してください。
    最後に、以下の英文から英検2級、英検準1級、英検1級程度の英単語や熟語を最大30個リストアップして、[英単語:日本語の意味]を表示してください。
========

{content}

========
日本語でお願いします。
出力する際に、指示した内容を冒頭に表示する必要はありません。説明から始めてください。
    """

def get_answer(llm, messages):
    answer = llm(messages)
    return answer.content


def main():
    init_page()

    llm = select_model()
    init_messages()
    
    container = st.container()
    response_container = st.container()

    with container:
        url = get_url_input()
        is_valid_url = validate_url(url)
        if not is_valid_url:
            st.write('Please input valid url')
            answer = None
        else:
            content = get_content(url)
            if content:
                prompt = summary_prompt(content)
                st.session_state.messages.append(HumanMessage(content=prompt))
                with st.spinner("ChatGPT is typing ..."):
                    answer = get_answer(llm, st.session_state.messages)
            else:
                answer = None
    
    if answer:
        with response_container:
            st.markdown("### コンペ概要説明")
            st.write(answer)

if __name__== '__main__':
    main()


