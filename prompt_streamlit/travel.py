import pandas as pd
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
from langchain_core.output_parsers import StrOutputParser
output_parser = StrOutputParser()

import pandas as pd
import re
import requests
import openai

model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L6-v2')

# 2. 파인콘 초기화
pinecone = Pinecone(api_key="your-api-key")
index = pinecone.Index("trip-index")

# 3. 검색 함수 정의

# 여행 스타일 및 동행인 기반
def search_places_style(city, companions, travel_style):
    query = f"Best places in {city} for {companions} with focus on {travel_style}."
    query_embedding = model.encode(query).tolist()
    namespace = f"{city}_tour"
    results_style= index.query(vector=query_embedding, top_k=100, namespace=namespace, include_metadata=True)
    return results_style

# 기본 유명 관광지
def search_places(city):
    query = f"The most famous tour places in {city}"
    query_embedding = model.encode(query).tolist()
    namespace = f"{city}_tour"
    results_best= index.query(vector=query_embedding, top_k=100, namespace=namespace, include_metadata=True)
    return results_best

def merge_and_deduplicate_places(results_best, results_style):
    # 두 결과 리스트를 결합
    combined_results = results_best['matches'] + results_style['matches']

    # 중복을 제거하기 위해 장소 이름을 기준으로 필터링
    unique_places = {}
    for item in combined_results:
        place_name = item['metadata']['1_이름']
        if place_name not in unique_places:
            unique_places[place_name] = item

    # 중복이 제거된 결과를 리스트로 변환
    final_results = list(unique_places.values())
    
    return final_results

os.environ["OPENAI_API_KEY"] ="your-api-key"


## 여행일정 생성 프롬프트 (영어로)

# 페르소나 설정
persona = """
You are a travel AI expert specialized in generating optimized travel itineraries.

You always generate travel itineraries based on verifiable factual statements.
You mainly speak about factual information related to tourist attractions and restaurants, and recent updates, without adding information on your own.
"""


prompt_template = """You are a travel itinerary AI expert. Create a travel itinerary for {city} for a duration of {trip_duration}.  
The travel information is as follows:

- Trip duration: {trip_duration}
- Companions: {companions}
- Travel style: {travel_style}
- Preferred itinerary style: {itinerary_style}

**Please create a travel itinerary using the following list of places based on the conditions**:  
{places_list}

**Constraints**:  
1. Ensure the itinerary includes all {trip_duration} days, with each day divided into morning, afternoon, and evening. 
2. The same place or restaurant **should not appear more than once** in the itinerary. A place included on one day should not appear on any other day.  
3. Include the opening hours and address of each place.  
4. Add a brief one-sentence introduction for each place.  
5. Optimize the itinerary to **minimize travel time between places**.  
6. Consider **the operating hours** of each place when organizing the itinerary.  
7. Adjust the itinerary based on the selected itinerary style.  
   7-1. If the '빼곡한 일정' style is selected, include 2 tourist attractions and 1 restaurant in the morning, afternoon, and evening, totaling 9 activities per day.  
   7-2. If the '널널한 일정' style is selected, include 1 tourist attraction and 1 restaurant in the morning, afternoon, and evening, totaling 6 activities per day.  
8. Please provide the result in **JSON format**, using the example structure below. 
9. **The result should be provided in Korean.**

**Output Structure**:  
- Ensure the output contains the date, time period, place name, description, operating hours, and address for each entry.

**Example Output Structure**:  

```json
{{
    "여행 일정": [
        {{
            "날짜": "Day 1",
            "시간대": "오전",
            "장소명": "Galerie Vivienne",
            "장소 소개": "19세기 파리의 매력을 간직한 아름다운 쇼핑 아케이드입니다.",
            "운영시간": "8:30 AM – 8:00 PM",
            "주소": "4 Rue des Petits Champs, 75002 Paris, France"
        }},
        {{
            "날짜": "Day 1",
            "시간대": "오전",
            "장소명": "Domaine National du Palais-Royal",
            "장소 소개": "역사적인 궁전과 정원이 있는 관광 명소입니다.",
            "운영시간": "8:30 AM – 10:30 PM",
            "주소": "75001 Paris, France"
        }},
        {{
            "날짜": "Day 1",
            "시간대": "오전",
            "장소명": "Boulangerie LIBERTÉ",
            "장소 소개": "신선한 빵과 페이스트리를 제공하는 인기 있는 빵집입니다.",
            "운영시간": "7:30 AM – 8:00 PM",
            "주소": "58 Rue Saint-Dominique, 75007 Paris, France"
        }},
        {{
            "날짜": "Day 1",
            "시간대": "오후",
            "장소명": "Galeries Lafayette Champs-Élysées",
            "장소 소개": "파리의 대표적인 쇼핑 명소로 다양한 브랜드를 만날 수 있습니다.",
            "운영시간": "10:00 AM – 9:00 PM",
            "주소": "60 Av. des Champs-Élysées, 75008 Paris, France"
        }}
    ]
}}
"""

# 객체 생성
llm = ChatOpenAI(
    temperature=0.1,  # 창의성 (0.0 ~ 2.0)
    model_name="gpt-4o",  # 모델명
)

import openai

client = openai.OpenAI()
#############
# 여행일정 생성 함수
def generate_itinerary_recommendations(city, trip_duration, companions, travel_style, itinerary_style, places_list ):
    
    # 페르소나 주입
    filled_persona = persona.format()
    
    # 템플릿에 사용자 정보 삽입
    formatted_prompt = prompt_template.format(
        city=city,
        trip_duration=trip_duration,
        companions=companions,
        travel_style=travel_style,  # travel_style 리스트를 문자열로 변환
        itinerary_style=itinerary_style,
        places_list=places_list
    )

    # 프롬프트 구성
    prompt = ChatPromptTemplate(
        template=formatted_prompt,
        messages=[
            SystemMessagePromptTemplate.from_template(filled_persona),  # 페르소나 주입
            MessagesPlaceholder(variable_name="chat_history"),  # 메모리 활용
            HumanMessagePromptTemplate.from_template("{question}")
        ]
    )

    # 메모리 설정
    memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=1000, memory_key="chat_history", return_messages=True)

    # LLMChain 설정
    conversation = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=True,
        memory=memory
    )

    # 여러 입력 변수를 하나의 딕셔너리로 전달
    result = conversation({
        "question": formatted_prompt
    })
    return result['text']


# 6. 메인 함수: 사용자 입력 및 여행일정 생성
def final_recommendations(city, trip_duration, companions, travel_style, itinerary_style):

    # 여행 일수 추출
    #days_match = re.search(r"(\d+)\s*days", trip_duration)
    #if days_match:
    #    num_days = int(days_match.group(1))
    #    print(num_days)
    #else:
    #    raise ValueError("trip_duration should contain 'days' for parsing.")
    
    # 사용자 입력 예시
    itinerary_details = {
        "city": city,
        "trip_duration": trip_duration,
        #"travel_dates": "2024-11-15 ~ 2024-11-18",
        "companions": companions,
        "travel_style": travel_style,
        "itinerary_style" : itinerary_style,
    }

    # 파인콘에서 장소 검색 실행
    results_style = search_places_style(
        city=itinerary_details["city"],
        companions=itinerary_details["companions"],
        travel_style=itinerary_details["travel_style"]
    )

    results_best = search_places(
        city=itinerary_details["city"]
    )

    final_results = merge_and_deduplicate_places(results_style, results_best)

    # 파인콘에서 가져온 추천 장소리스트
    places_list = "\n".join([
        f"- {match.metadata['1_이름']} (카테고리: {match.metadata['8_유형']}, 주소: {match.metadata['2_주소']}, 운영시간: {match['metadata'].get('7_영업시간', 'N/A')})"
        for match in final_results
    ])
    # 여행일정 생성 호출
    itinerary = generate_itinerary_recommendations(
        city=itinerary_details["city"],
        trip_duration=itinerary_details["trip_duration"],
        #travel_dates=accommodation_details["travel_dates"],
        companions=itinerary_details["companions"],
        travel_style=itinerary_details["travel_style"],
        itinerary_style=itinerary_details["itinerary_style"],
        places_list=places_list,
        #itinerary=itinerary
    )

    # 결과 출력
    return itinerary
