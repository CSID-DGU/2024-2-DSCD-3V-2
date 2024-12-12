import streamlit as st

import pandas as pd
from dotenv import load_dotenv
import ast
from sentence_transformers import SentenceTransformer
import pinecone
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
import numpy as np
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate
import getpass
import os
import pandas as pd
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
output_parser = StrOutputParser()

import pandas as pd
import json
import re
import requests
import openai

# api 로드에 필요
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 1. OpenAI API 키 설정 및 임베딩 모델 초기화   

# 배포용 api 설정
#openai_api_key = st.secrets["OPENAI_API_KEY"]
#pinecone_api_key = st.secrets["PINECONE_API_KEY"]

#if not openai_api_key or not pinecone_api_key:
#    raise ValueError("API 키가 Streamlit Secrets에 설정되지 않았습니다.")

# API 키 가져오기
openai_api_key = os.getenv("OPENAI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
# OpenAI 라이브러리에 API 키 설정
import openai
openai.api_key = openai_api_key

model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L6-v2')

pinecone = Pinecone(api_key=pinecone_api_key)
index = pinecone.Index("travel-index")

# 3. 검색 함수 정의
# 3. 검색 함수 정의
# 선호 숙소 형태 및 동행인 기반
def search_places(city, companions, lodging_style):
    query = f"Best accommdations in {city} for {companions} with focus on {lodging_style}."
    query_embedding = model.encode(query).tolist()
    namespace = f"{city}_lodging"
    results_style = index.query(vector=query_embedding, top_k=20, namespace=namespace, include_metadata=True)
    return results_style

def places_to_df(lodging_best) :
  combined_results = lodging_best['matches'] 
  
  # 각 항목에서 메타데이터 추출하여 데이터프레임 생성
  places_data = []
  for item in combined_results:
      places_data.append({
            "PlaceID" :item['metadata'].get('0_placeID', 'N/A'),
            "name": item['metadata'].get('1_이름', 'N/A'),
            "address": item['metadata'].get('2_주소', 'N/A'),
            "rating": item['metadata'].get('3_평점', 0),
            "latitude": item['metadata'].get('4_위도', 0),
            "longitude": item['metadata'].get('5_경도', 0),
            "review": item['metadata'].get('6_리뷰', 'N/A'),
            "opening_hours": item['metadata'].get('7_영업시간', 'N/A'),
            "type": item['metadata'].get('8_유형', 'N/A'),
            "image_url": item['metadata'].get('9_이미지', 'N/A')  # 원본 이미지 데이터 그대로 추가
        })

# 데이터프레임 생성
  df = pd.DataFrame(places_data)

    # 중복 제거 (장소 이름과 주소를 기준으로)
  df = df.drop_duplicates(subset=["name", "address"]).reset_index(drop=True)

    # 이미지 URL 처리: 대괄호 제거 및 첫 번째 URL 추출
  df['image_url'] = df['image_url'].apply(
                    lambda x: ast.literal_eval(x)[0] 
                    if isinstance(x, str) and x.startswith("[") and x.endswith("]") 
                    else x.split(", ")[0] if isinstance(x, str) and ", " in x 
                    else x
                )

  return df


# 4. 숙소 리스트 생성을 위한 프롬프트 템플릿 - 영어 버전
persona = """
You are an AI expert in accommodation recommendations, acting as a travel agent to recommend a personalized accommodation list to your customers.

Do not hallucinate information. Only provide accurate and reliable details based on the given data or context.
"""

prompt_template = """
Create a list of the **top 5** accommodations for your customer's trip based on their <personal information> and the <requirements>.

<personal infomation>
1. Travel City: {city}
2. Companions: {companions}
3. Accommodation Preferences: {lodging_style}
</personal infomation>

<requirements>
1. Offer the proper option based on their accommodation preferences and travel companions among hotels, resorts, inns, hostels, B&B, and so on.
2. Ensure the accommodations are in safe areas of {city}.
3. Please make the list consist of the \n{recommendations}.
</requirements>

<Example Output Structure>

```json
{{
    "숙소 추천": [
        {{"장소명": "Familia Hôtel"}},
        {{"장소명": "Beau M Hostel"}}
    ]
}}
</Example Output Structure>
"""


# 5. 프롬프트와 LLMChain 설정
llm = ChatOpenAI(
    temperature=0.1,
    model_name="gpt-4o"
)


from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


# 숙소 추천 생성 함수
def generate_accommodation_recommendations(city, companions, lodging_style, recommendations):

    # 페르소나 주입
    filled_persona = persona

    # 템플릿에 사용자 정보 삽입
    formatted_prompt = prompt_template.format(
        city=city,
        companions=companions,
        lodging_style=lodging_style,
        recommendations=recommendations
    )
    # 프롬프트 구성
    prompt = ChatPromptTemplate(
        template=formatted_prompt,
        messages=[
            SystemMessagePromptTemplate.from_template(filled_persona),  # 페르소나 주입
            HumanMessagePromptTemplate.from_template("{input}")  # 질문 입력
        ]
    )

    # RunnableSequence로 구성
    conversation = prompt | llm

    # 여러 입력 변수를 하나의 딕셔너리로 전달 (invoke로 변경)
    result = conversation.invoke({
        "input": formatted_prompt
    })
    return result


def process_and_merge_lodging(itinerary, final_results):
    """
    프롬프트 결과물과 검색된 장소 데이터를 결합하여 최종 DataFrame을 생성하는 함수.

    Parameters:
        itinerary (str): 프롬프트 결과물(JSON 문자열 포함)
        places_df (pd.DataFrame): merge_and_deduplicate_places_to_df 결과 DataFrame

    Returns:
        pd.DataFrame: itinerary와 places_df를 장소명을 기준으로 결합한 DataFrame
    """
    # Step 1: itinerary에서 JSON 부분만 추출
    start_index = itinerary.find("{")  # JSON 시작 위치
    end_index = itinerary.rfind("}")   # JSON 끝 위치
    json_text = itinerary[start_index:end_index+1]
    data = json.loads(json_text)

    # Step 2: "여행 일정" 키 아래의 리스트를 DataFrame으로 변환
    lodging_df = pd.DataFrame(data["숙소 추천"])

    # Step 3: places_df에서 필요한 열 선택 및 컬럼 이름 통일
    final_results = final_results.rename(columns={
        'name': '장소명',  # 이름 열 통일
        'address': '주소',     # 주소 열 이름 통일
        'image_url': '이미지',
        'rating' : '평점',
        'type' : '유형'
    })

    # Step 5: inner join 수행 (장소명을 기준으로)
    merged_df = pd.merge(lodging_df, final_results[['장소명', '주소', '이미지','평점','유형','PlaceID']], on='장소명', how='inner')

    # Step 6: 최종 DataFrame 반환
    return merged_df



# 6. 메인 함수: 사용자 입력 및 숙소 추천 실행

# 최종 추천 함수 생성
def final_recommendations(city, companions, lodging_style):

    # 사용자 입력 예시
    accommodation_details = {
        "city": city,
        "companions": companions,
        "lodging_style": lodging_style
    }

    # 파인콘에서 숙소 검색 실행
    search_results = search_places(
        city=accommodation_details["city"],
        companions=accommodation_details["companions"],
        lodging_style=accommodation_details["lodging_style"]
    )

    final_results = places_to_df(search_results)
  
    recommendations = "\n".join([
        f"- {row['name']} (주소: {row['address']}, 평점: {row['rating']})"
        for _, row in final_results.iterrows()
    ])

    # 숙소 추천 생성 호출
    accommodation_recommendations = generate_accommodation_recommendations(
        city=accommodation_details["city"],
        companions=accommodation_details["companions"],
        lodging_style=accommodation_details["lodging_style"],
        recommendations=recommendations
    )

    df_lodging = process_and_merge_lodging(accommodation_recommendations.content, final_results)


    # 결과 출력
    return df_lodging
