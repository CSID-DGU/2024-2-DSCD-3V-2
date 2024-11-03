# 벡터 DB 및 llm 라이브러리
import pinecone
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
import openai

# 임베딩 모델 위한 라이브러리
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
import numpy as np
import pandas as pd

# 1. OpenAI API 키 설정 및 임베딩 모델 초기화   ####### API 삭제 후 공유 #######
openai_api_key = "your-api-key"

# embedding 모델 로드
model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L6-v2')

# 2. 파인콘 초기화      ####### API 삭제 후 공유 #######
from pinecone import Pinecone, ServerlessSpec

pinecone = Pinecone(api_key="your-api-key")
index = pinecone.Index("trip-index")

# 3. 검색 함수 정의

# 선호 숙소 형태 및 동행인 기반
def search_places(city, companions, lodging_style):
    query = f"Best accommdations in {city} for {companions} with focus on {lodging_style}."
    query_embedding = model.encode(query).tolist()
    namespace = f"{city}_lodging"
    results_style = index.query(vector=query_embedding, top_k=20, namespace=namespace, include_metadata=True)
    return results_style


# 4. 숙소 리스트 생성을 위한 프롬프트 템플릿 - 영어 버전
prompt_template = prompt = """
Imagine you're a travel agent to recommend an accommodation list to your customers.
Your task is to recommend an accommodation list to your customers based on their <personal information> as written below.
Based on the <requirements> below, create a list of the **top 5** accommodations for your customer's trip.

<personal infomation>
- Travel City: {city}
- Duration of Stay: {trip_duration}
- Companions: {companions}
- Accommodation Preferences: {lodging_style}
</personal infomation>

**Note**: If any part of <personal information> is in Korean, please automatically translate it into English before generating the list.

<requirements>
- You should consider their accommodation preferences and accommodation budget per night.
- Provide a concise description of each accommodation’s features.
- Include location details such as proximity to major attractions and transportation convenience.
- Ensure the accommodations are in safe areas of {city}.
- Offer the proper option based on their travel companions among hotels, resorts, inns, hostels, B&B, and so on.
- Please make the list consist of the {recommendations}.
- Ensure the budget per night is not exceeded. The budget currency is the Korean won(KRW).
- **Please answer in Korean.**
- Provide the results in JSON format following the <output structure> below.
</requirements>

<output structure>
Please include 'name', 'location', 'features', 'services', 'rating', and 'approximate price(KRW)' in the output.
For the price, specify the currency.
</output structure>
"""


# 5. 프롬프트와 LLMChain 설정
llm = ChatOpenAI(
    temperature=0.1,
    model_name="gpt-4o",    # 4-turbo보다 빠르고, 한국어도 더 잘함
    openai_api_key = openai_api_key
)

# 숙소 추천 생성 함수
def generate_accommodation_recommendations(city, trip_duration, companions, lodging_style, recommendations):
    # 템플릿에 사용자 정보 삽입
    formatted_prompt = prompt_template.format(
        city=city,
        trip_duration=trip_duration,
        #travel_dates=travel_dates,
        companions=companions,
        lodging_style=lodging_style,
        #lodging_budget=lodging_budget,
        recommendations=recommendations,
        #itinerary=itinerary
    )

    # LangChain 프롬프트 구성
    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template("You are an AI expert in accommodation recommendations."),
            HumanMessagePromptTemplate.from_template(formatted_prompt)
        ]
    )

    # LLMChain 설정 및 실행
    conversation = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=True
    )

    # 결과 생성
    result = conversation.run({})
    return result

# 6. 메인 함수: 사용자 입력 및 숙소 추천 실행
def final_recommendations(city, trip_duration, companions, lodging_style):
    # 사용자 입력 예시
    accommodation_details = {
        "city": city,
        "trip_duration": trip_duration,
        #"travel_dates": "2024-11-15 ~ 2024-11-18",
        "companions": companions,
        "lodging_style": lodging_style,
        #"lodging_budget": "100,000 won(KRW) per one night"
    }

    # 파인콘에서 숙소 검색 실행
    search_results = search_places(
        city=accommodation_details["city"],
        companions=accommodation_details["companions"],
        lodging_style=accommodation_details["lodging_style"]
    )

    # 파인콘에서 가져온 추천 숙소 리스트 구성 (최대 20개)
    recommendations = "\n".join([
        f"- {match.metadata['1_이름']} (평점: {match.metadata['3_평점']}, 위치: {match.metadata['2_주소']}, 유형: {match.metadata['8_유형']})"
        for match in search_results.matches
    ])

    '''# 여행일정 리스트 구성
    file_path = 'paris_itinerary.csv'   # CSV 파일 경로 설정
    paris_travel_schedule = pd.read_csv(file_path)     # CSV 파일 로드
    itinerary = "\n".join([
        f"- {row['활동']} (운영시간: {row['운영시간']}, 위치: {row['주소']})"
        for _, row in paris_travel_schedule.iterrows()
    ])'''

    # 숙소 추천 생성 호출
    accommodation_recommendations = generate_accommodation_recommendations(
        city=accommodation_details["city"],
        trip_duration=accommodation_details["trip_duration"],
        #travel_dates=accommodation_details["travel_dates"],
        companions=accommodation_details["companions"],
        lodging_style=accommodation_details["lodging_style"],
        #lodging_budget=accommodation_details["lodging_budget"],
        recommendations=recommendations,
        #itinerary=itinerary
    )

    # 결과 출력
    return accommodation_recommendations