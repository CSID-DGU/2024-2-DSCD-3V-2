
import streamlit as st
from PIL import Image   # 챗봇 이미지 로드에 필요
import requests         # 챗봇 이미지 로드에 필요
import base64           # 챗봇 이미지 로드에 필요
from io import BytesIO  # 챗봇 이미지 로드에 필요
import openai
import re
import json
from streamlit_chat import message
import pandas as pd
import lodging
import travel

# Set your OpenAI API key directly in the code
openai.api_key = "your-api-key"  # Replace with your actual API key

# 페이지 설정
st.set_page_config(page_title="Travel Planner Chatbot", layout="wide")

########################################## CHATBOT ##########################################

# CSS 스타일 정의     # 나영수정(11/10)
st.markdown("""
    <style>
        /* 사이드바 배경 흰색으로 설정 */
        [data-testid="stSidebar"] {
            background-color: white;
        }
        
        /* 사이드바와 메인 콘텐츠 사이에 고정된 구분선 */
        .main-divider {
            position: fixed;
            top: 0;
            left: 18rem; /* 사이드바 너비에 맞춰 구분선 위치 설정 */
            width: 1px;
            height: 100vh;
            background-color: #d3d3d3; /* 회색 구분선 색상 */
            z-index: 1;
        }

        /* 사이드바 스타일 수정 */
        .css-1y4p8pa {  /* Streamlit 사이드바 CSS 클래스 */
            padding-right: 1rem;
            padding-left: 1rem;
            overflow-y: auto;
        }

        /* 사이드바와 구분선 간격 확보 */
        .css-1y4p8pa .chatbox-container {
            margin-right: 10px; /* 구분선과 여유 간격 추가 */
        }
            
        /* 챗 섹션 배경을 완전히 흰색으로 설정 */
        .sidebar .css-1y4p8pa {
            background-color: #ffffff !important;
            padding: 10px;
            box-shadow: 2px 0px 5px rgba(0,0,0,0.1); /* 오른쪽에 가벼운 그림자 추가하여 구분 */
            border-right: 1px solid #ddd; /* 두 섹션을 분리하는 얇은 선 추가 */
        }

        /* 채팅창 스타일 */
        .chatbox {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            max-width: 700px;
            margin: auto;
        }

        /* 챗봇 말풍선 스타일 */
        .chatbot-bubble {
            background-color: #f0f0f0; /* 회색 배경색 */
            color: black; /* 글자색 검정 */
            padding: 10px;
            border-radius: 15px; /* 둥근 모서리 */
            margin: 5px 0;
            max-width: 80%; /* 말풍선이 차지하는 최대 너비 */
            display: inline-block;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1); /* 가벼운 그림자 */
            animation: fadeIn 0.5s; /* 서서히 나타나는 애니메이션 */
        }

        /* 사용자 말풍선 스타일 */
        .user-bubble {
            background-color: #007bff; /* 파란색 배경 */
            color: white; /* 글자색 흰색 */
            padding: 10px;
            border-radius: 15px; /* 둥근 모서리 */
            margin: 5px 0;
            max-width: 80%;
            display: inline-block;
            text-align: right; /* 텍스트 오른쪽 정렬 */
            float: right; /* 말풍선을 오른쪽으로 정렬 */
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1); /* 가벼운 그림자 */
            animation: fadeIn 0.5s; /* 서서히 나타나는 애니메이션 */
        }
            
        /* 오른쪽 콘텐츠 영역 스타일 */
        .content-area {
            padding: 20px;
            background-color: #ffffff;
            box-shadow: -2px 0px 5px rgba(0,0,0,0.1); /* 왼쪽에 가벼운 그림자 추가 */
        }
            
        /* 스크롤바 스타일 */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
            
        /* 챗봇 이미지 스타일 */
        .chatbot-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 10px;
            vertical-align: middle;
        }
        
        .chatbot-message, .user-message {
            display: flex;
            align-items: center;
        }
    
        /* 애니메이션 효과 */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        /* 입력창과 버튼 스타일 */
        .input-container {
            display: flex;
            margin-top: 20px;
        }

        .message-input {
            flex: 1;
            padding: 10px;
            border-radius: 20px;
            border: 1px solid #ddd;
            font-size: 16px;
            margin-right: 10px;
            box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.1);
        }

        .send-button {
            background-color: #007bff;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
            font-size: 16px;
        }

        /* 모바일 반응형 디자인 */
        @media (max-width: 768px) {
            .chatbox {
                max-width: 100%;
            }
            .message-input {
                font-size: 14px;
            }
            .send-button {
                font-size: 14px;
                padding: 8px 12px;
            }
        }

    </style>
""", unsafe_allow_html=True)

# 챗봇 이미지 로드 및 인코딩
image_url = "https://raw.githubusercontent.com/CSID-DGU/2024-2-DSCD-3V-2/main/data/RIPO_image.png?raw=true"
response = requests.get(image_url)
if response.status_code == 200:
    chatbot_image = Image.open(BytesIO(response.content))
    buffered = BytesIO()
    chatbot_image.save(buffered, format="PNG")
    chatbot_image_base64 = base64.b64encode(buffered.getvalue()).decode()
else:
    st.error("챗봇 이미지를 불러오는 데 실패했습니다.")
    chatbot_image_base64 = ""

# 챗봇 메시지 출력 함수
def chatbot_message(text):
    st.markdown(
        f"""
        <div class="chatbox">
            <div class="chatbot-message">
                <img src="data:image/png;base64,{chatbot_image_base64}" class="chatbot-avatar"/>
                <div class="chatbot-bubble">{text}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# 사용자 메시지 출력 함수
def user_message(text):
    st.markdown(
        f"""
        <div class="chatbox">
            <div class="user-bubble">{text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# 입력창 디자인
def message_input():
    st.markdown(
        """
        <div class="input-container">
            <input type="text" class="message-input" placeholder="메시지를 입력하세요..."/>
            <button class="send-button">보내기</button>
        </div>
        """, 
        unsafe_allow_html=True
    )


# 제목과 설명
st.title("TRiPO 여행 일정 생성")  # 문구수정함
st.write(
    "트리포와 함께 만든 여행일정으로 떠나보세요."  
)

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "destination" not in st.session_state:  # city
    st.session_state.destination = None
if "stay_duration" not in st.session_state:  # trip_duration
    st.session_state.stay_duration = None
if "companion" not in st.session_state:  # companions
    st.session_state.companion = None
if "travel_style" not in st.session_state:
    st.session_state.travel_style = None
if "itinerary_preference" not in st.session_state:
    st.session_state.itinerary_preference = None
if "accommodation_type" not in st.session_state:  # lodging_style
    st.session_state.accommodation_type = None
if "itinerary_generated" not in st.session_state:
    st.session_state.itinerary_generated = False
if "itinerary" not in st.session_state:
    st.session_state.itinerary = ""
if "current_step" not in st.session_state:
    st.session_state.current_step = 0  # 현재 단계 추적 변수


# Reset function to go back to the start
def reset_conversation():
    """전체 대화를 초기화하고 처음 단계로 돌아갑니다."""
    for key in [
        "destination",
        "stay_duration",
        "companion",
        "travel_style",
        "itinerary_preference",
        "accommodation_type",
        "itinerary_generated",
        "itinerary",
    ]:
        st.session_state[key] = None
    st.session_state.messages = []
    st.session_state.current_step = 0


# Go back to the previous step
def previous_step():
    """이전 단계로 돌아가 현재 단계의 선택을 초기화합니다."""
    if st.session_state.current_step > 0:
        st.session_state.current_step -= 1
        # Reset the specific choice based on the current step
        if st.session_state.current_step == 0:
            st.session_state.destination = None
        elif st.session_state.current_step == 1:
            st.session_state.stay_duration = None
        elif st.session_state.current_step == 2:
            st.session_state.companion = None
        elif st.session_state.current_step == 3:
            st.session_state.travel_style = None
        elif st.session_state.current_step == 4:
            st.session_state.itinerary_preference = None
        elif st.session_state.current_step == 5:
            st.session_state.accommodation_type = None
        st.session_state.itinerary_generated = False  # 일정 생성 상태 초기화

# 구분선 삽입
st.markdown('<div class="main-divider"></div>', unsafe_allow_html=True)

# 사이드바를 통한 입력 인터페이스
with st.sidebar:
    st.markdown("### 여행 일정 생성 Chat")
    # Assistant message for greeting
    chatbot_message(
        "안녕하세요 여행자님! 여행자님의 계획 생성을 도와줄 리포(RIPO)입니다👋 저와 함께 멋진 여행 일정을 만들어봐요!✨ 그럼 질문에 맞는 답을 체크박스로 선택해주시면 바로 시작해볼게요!",  # 문구변경함
    )

    # 도시 선택 체크박스 UI + 사용자 입력 상자 추가
    chatbot_message("어느 도시를 여행하고 싶으신가요? 아래에서 도시를 선택해주세요.")

    # 도시 이름과 해당 영어 표기 매핑
    cities = {"오사카": "Osaka", "파리": "Paris", "방콕": "Bangkok", "뉴욕": "New York"}

    for city_kr, city_en in cities.items():
        if st.checkbox(
            city_kr, key=f"city_{city_en}", disabled=st.session_state.get("destination") is not None
        ):
            st.session_state.destination = city_en  # 영어 이름으로 세션 상태 업데이트
            st.session_state.current_step = 1
            user_message(f"{city_kr}")    # 나영수정(11/10): 여행 도시 문구
            chatbot_message(f"{city_kr} 여행을 계획해드리겠습니다.")


    # 여행 기간 선택
    if st.session_state.get("destination"):
        chatbot_message("얼마나 여행을 떠날 예정인가요? 여행 기간을 선택하거나 직접 입력해주세요 ✏️")
        durations = {"1박 2일": "1 night 2 days", "2박 3일": "2 nights 3 days", 
                    "3박 4일": "3 nights 4 days", "4박 5일": "4 nights 5 days"}
        
        # 라디오 버튼으로 기간 선택
        duration_options = list(durations.keys())
        selected_duration = st.radio(
            "여행 기간을 선택하세요:",
            options=duration_options,
            key="selected_duration"
        )

        # 사용자가 다른 기간을 입력할 수 있는 텍스트 입력
        custom_duration = st.text_input(
            "다른 여행 기간을 'O박 O일' 형식으로 입력해주세요",
            key="custom_duration"
        )

        # 입력받은 사용자 정의 기간 검증 및 처리
        if custom_duration:
            if re.match(r"^\d+박\s*\d+일$", custom_duration):
                nights, days = map(int, re.findall(r'\d+', custom_duration))
                custom_duration_en = f"{nights} nights {days} days"
                st.session_state.stay_duration = custom_duration_en
                duration_display = custom_duration
                st.session_state.current_step = 2
                user_message(f"{duration_display}")   # 나영수정(11/10): 여행 기간 (사용자정의) 문구
                chatbot_message(f"{duration_display} 동안의 여행을 계획해드리겠습니다.")
            else:
                st.error("입력 형식이 올바르지 않습니다. 예: '2박 3일' 형태로 다시 입력해주세요.")
        elif selected_duration:
            st.session_state.stay_duration = durations[selected_duration]
            st.session_state.current_step = 2
            user_message(f"{selected_duration}")   # 나영수정(11/10): 여행 기간 문구
            chatbot_message(f"{selected_duration} 동안의 여행을 계획해드리겠습니다.")


    # 한글로 입력된 입력을 gpt 이용해서 영어로 번역해주는 함수     
    def translate_to_english(text):
        try:
            response = openai.Completion.create(
                engine="davinci",   # 가장 강력한 GPT-3 모델
                prompt=f"Translate the following Korean text to English: {text}",
                max_tokens=60  # 번역에 충분한 토큰 수
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return text  # 번역 실패 시 원본 텍스트 반환


    # 여행 동행인 선택 - 다중선택 변경완료
    if st.session_state.stay_duration:
        chatbot_message("누구와 함께 여행을 떠나시나요? 골라주세요! 중복선택도 가능합니다 😎")
        companions = {
            "혼자": "Alone",
            "친구와": "With friends",
            "연인과": "With partner",
            "가족과": "With family",
            "어린아이와": "With children",
            "반려동물과": "With pets",
            "단체 여행": "Group travel"
        }

        selected_companions = []
        for companion_kr, companion_en in companions.items():
            if st.checkbox(
                companion_kr,
                key=f"companion_{companion_en}"
            ):
                selected_companions.append(companion_en)

        custom_companion = st.text_input(
            "다른 동행인을 입력하시면 여기에 기입해주세요",
            key="custom_companion"
        )
        if custom_companion:
            translated_companion = translate_to_english(custom_companion)
            selected_companions.append(translated_companion)

        if selected_companions:
            st.session_state.companion = selected_companions
            st.session_state.current_step = 3
            selected_companions_kr = ", ".join([key for key, value in companions.items() if value in selected_companions])
            if custom_companion:
                selected_companions_kr += f", {custom_companion}"  # 나영수정(11/10): ", " 해결
            chatbot_message(f"{selected_companions_kr}")    # 나영수정(11/10): 동행인 문구
            user_message(f"{selected_companions_kr} 함께하는 멋진 여행을 준비해드리겠습니다!")


    # 여행 스타일 선택 - 다중선택 변경완료
    if st.session_state.companion:
        chatbot_message("어떤 여행 스타일을 선호하시나요? 아래에서 선택하거나 직접 입력해주세요.")
        travel_styles = {
            "액티비티": "Activity",
            "핫플레이스": "Hotspots",
            "자연": "Nature",
            "관광지": "Sightseeing",
            "힐링": "Relaxing",
            "쇼핑": "Shopping",
            "맛집": "Gourmet",
            "럭셔리 투어": "Luxury Tour"
        }

        selected_styles = []
        for style_kr, style_en in travel_styles.items():
            if st.checkbox(
                style_kr,
                key=f"style_{style_en}",
                disabled=st.session_state.get("travel_style") is not None,
            ):
                selected_styles.append(style_en)

        custom_style = st.text_input(
            "다른 스타일을 원하시면 입력해주세요", key="custom_style"
        )
        if custom_style:
            translated_style = translate_to_english(custom_style)
            if "travel_style" in st.session_state:
                st.session_state.travel_style.append(translated_style)
            else:
                st.session_state.travel_style = [translated_style]
            st.session_state.current_step = 4
            chatbot_message(f"{custom_style}")    # 나영수정(11/10): 여행 스타일 (사용자 정의) 문구
            user_message(f"{custom_style} 타입의 여행을 선택했습니다.")
            
        if selected_styles:
            st.session_state.travel_style = selected_styles
            st.session_state.current_step = 4
            selected_styles_kr = ", ".join([key for key, value in travel_styles.items() if value in selected_styles])
            chatbot_message(f"{selected_styles_kr}")    # 나영수정(11/10): 여행 스타일 문구
            user_message(f"{selected_styles_kr} 타입의 여행을 선택했습니다.")

    # 여행 일정 스타일 선택
    if st.session_state.travel_style:
        chatbot_message("선호하는 여행 일정 스타일은 무엇인가요? 두 가지 타입 중 선택해주세요 🤗")
        itinerary_preferences = {
            "빼곡한 일정": "Packed itinerary",
            "널널한 일정": "Relaxed itinerary"
        }

        for preference_kr, preference_en in itinerary_preferences.items():
            if st.checkbox(
                preference_kr,
                key=f"itinerary_{preference_en}",
                disabled=st.session_state.get("itinerary_preference") is not None,
            ):
                st.session_state.itinerary_preference = preference_en
                st.session_state.current_step = 5
                chatbot_message(f"{preference_kr}")   # 나영수정(11/10): 일정 스타일 문구
                user_message(f"{preference_kr} 일정 스타일로 일정을 준비하겠습니다.")


    # 숙소 유형 선택 - 다중선택 변경완료
    if st.session_state.itinerary_preference:
        chatbot_message("어떤 숙소를 원하시나요? 아래에서 선택하거나 직접 입력해주세요.")
        accommodations = {
            "공항 근처 숙소": "Accommodation near the airport",
            "5성급 호텔": "5-star hotel",
            "수영장이 있는 숙소": "with a swimming pool",
            "게스트 하우스": "Guest house",
            "민박집": "Bed and Breakfast",
            "전통가옥": "Traditional house"
        }

        selected_accommodations = []
        for accommodation_kr, accommodation_en in accommodations.items():
            if st.checkbox(
                accommodation_kr,
                key=f"accommodation_{accommodation_en}"
            ):
                selected_accommodations.append(accommodation_en)

        custom_accommodation = st.text_input(
            "다른 숙소 유형을 원하시면 입력해주세요", key="custom_accommodation"
        )
        if custom_accommodation:
            translated_accommodation = translate_to_english(custom_accommodation)
            selected_accommodations.append(translated_accommodation)

        if selected_accommodations:
            st.session_state.accommodation_type = selected_accommodations
            st.session_state.current_step = 6
            selected_accommodations_kr = ", ".join([key for key, value in accommodations.items() if value in selected_accommodations])
            if custom_accommodation:
                selected_accommodations_kr += f"{custom_accommodation}"  
            chatbot_message(f"{selected_accommodations_kr}")     # 나영수정(11/10): 숙소 스타일 문구
            user_message(f"{selected_accommodations_kr} 스타일의 숙소로 추천해드리겠습니다.")

# 여행 일정 생성 조건: 모든 필수 요소가 선택되었는지 확인
    if (
        st.session_state.destination
        and st.session_state.stay_duration
        and st.session_state.companion
        and st.session_state.travel_style
        and st.session_state.itinerary_preference
        and st.session_state.accommodation_type
    ):
        # itinerary_details = {
        #     "city": st.session_state.get("destination"),
        #     "trip_duration": st.session_state.get("stay_duration"),
        #     "travel_dates": "2024-11-15 ~ 2024-11-18",
        #     "companions": st.session_state.get("companion"),
        #     "travel_style": st.session_state.get("travel_style"),
        #     "itinerary_style": st.session_state.get("itinerary_preference"),
        # }
        # 위 코드는 여행계획 생성 함수에 넣을 변수들을 session에서 불러와서 저장하는 코드
        if not st.session_state.itinerary_generated:
            try:
                with st.spinner("여행 일정을 생성하는 중입니다..."):
                    # 만약 여행 계획 생성 함수가 있다면 여기에 넣어서 결과를 문자열 형태로 st.session_state.itinerary 변수에 넣어주면 됨.
                    # json 형태로 데이터를 넣어서 st.session_state.itinerary['key'] 이런 식으로 데이터를 뽑아서 사용하면 됨.
                    # 여행 일정 생성 함수 호출
                    itinerary = travel.final_recommendations(
                        city=st.session_state.destination,
                        trip_duration=st.session_state.stay_duration,
                        companions=st.session_state.companion,
                        travel_style=st.session_state.travel_style,
                        itinerary_style=st.session_state.itinerary_preference
                    )
                    st.session_state.itinerary = itinerary
                    st.session_state.messages.append(
                        {"role": "assistant", "content": st.session_state.itinerary}
                    )
                    st.session_state.itinerary_generated = True

            except Exception as e:
                st.error(f"여행 일정 생성 중 오류가 발생했습니다: {e}")

########################################## 여행일정 페이지 ##########################################

# 오른쪽에 지도 및 일정 표시
with st.container():
    # Google 지도 표시
    if st.session_state.destination:
        st.subheader("🗺️ 여행 지도")
        map_url = f"https://www.google.com/maps/embed/v1/place?key=AIzaSyBW3TJ70cZAU7A48hlbXBIk_YkJHu8nKsg&q={st.session_state.destination}&zoom=12"
        st.markdown(
            f"""
            <iframe width="100%" height="200" frameborder="0" style="border:0" 
            src="{map_url}" allowfullscreen></iframe>
            """,
            unsafe_allow_html=True,
        )
    # 일정 표시
    if st.session_state.itinerary:
        st.subheader("🗺️ 여행 일정")
        
    # 여행 일정 생성 조건: 모든 필수 요소가 선택되었는지 확인
    if (
        st.session_state.destination
        and st.session_state.stay_duration
        and st.session_state.companion
        and st.session_state.travel_style
        and st.session_state.itinerary_preference
        and st.session_state.accommodation_type
    ):

        # 불필요한 설명 제거 및 JSON 변환
        start_index = itinerary.find("{")
        end_index = itinerary.rfind("}")
        json_text = itinerary[start_index:end_index+1]
        data = json.loads(json_text)

        # "여행 일정" 키 아래의 리스트를 DataFrame으로 변환
        df = pd.DataFrame(data["여행 일정"])

        # Day 선택 박스 생성
        days = df['날짜'].unique()
        selected_day = st.selectbox("날짜 선택", days)

        # 시간대별 일정 표시
        time_periods = ["오전", "오후", "저녁"]
        for time_period in time_periods:
            st.subheader(f"{time_period} 일정")
    
            # 선택한 날짜와 시간대에 맞는 데이터 필터링
            filtered_df = df[(df['날짜'] == selected_day) & (df['시간대'] == time_period)]
    
            # 일정 카드 형식으로 표시
            for _, row in filtered_df.iterrows():
                st.markdown(
                    f"""
                    <style>
                        .itinerary-card {{
                            border: 1px solid #d1d1d1;
                            border-radius: 8px;
                            padding: 10px;
                            margin-bottom: 10px;
                            background-color: #f9f9f9;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            display: flex;
                            flex-direction: column;
                            justify-content: space-between;
                            height: 180px; /* Adjust height to fit content */
                        }}
                        .itinerary-card h4 {{
                            font-size: 16px; /* Larger font for title */
                            margin-bottom: 5px;
                        }}
                        .itinerary-card p {{
                            font-size: 14px; /* Smaller font for details */
                            margin: 4px 0;
                            color: #666; /* Lighter text color for details */
                        }}
                    </style>
                    <div class="itinerary-card">
                        <h4>{row['장소명']}</h4>
                        <p><strong>장소 소개:</strong> {row['장소 소개']}</p>
                        <p><strong>운영시간:</strong> {row['운영시간']}</p>
                        <p><strong>주소:</strong> {row['주소']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            

    # 숙소 추천
    if st.session_state.accommodation_type and st.session_state.destination:
        st.subheader("🛏️ 추천 숙소")

        # Get recommended accommodations for the selected city and accommodation type
        recommended_accommodations = lodging.final_recommendations(st.session_state.destination, st.session_state.stay_duration, 
                                                                   st.session_state.companion, st.session_state.accommodation_type)
         
        # 불필요한 설명 문장 및 뒤쪽 텍스트 제거하고 JSON 부분만 추출
        start_index = recommended_accommodations.find("[")
        end_index = recommended_accommodations.rfind("]")
        json_text = recommended_accommodations[start_index:end_index + 1].strip()

        # JSON 유효성 확인을 위해 공백 및 줄바꿈 제거
        json_text = re.sub(r"\n\s*", "", json_text)

        # JSON 문자열을 파싱하여 Python 객체로 변환
        datas = json.loads(json_text)    

        # Display the top 5 recommendations
        # 5열로 나눠서 숙소 리스트 표시
        cols = st.columns(5)  # 5열로 나누기

        # 카드 스타일 CSS 정의
        card_style = """
            <style>
                .card {
                    border: 1px solid #d1d1d1;
                    border-radius: 8px;
                    padding: 10px;
                    margin: 5px;
                    background-color: #f9f9f9;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                }
                .card h6 {
                    font-size: 14px;
                    margin: 5px 0;
                }
                .card p {
                    font-size: 12px;
                    margin: 3px 0;
                }
            </style>
        """

        # CSS를 페이지에 추가
        st.markdown(card_style, unsafe_allow_html=True)

        # 카드 표시
        for i, accommodation in enumerate(datas):
            with cols[i % 5]:  # 각 열에 하나씩 표시
                # 카드 스타일을 적용하여 각 숙소 정보를 출력
                st.markdown(
                    f"""
                    <div class="card">
                        <h6>{accommodation.get('name', '이름없음')}</h6>
                        <p>위치: {accommodation.get('location', '이름없음')}</p>
                        <p>평점: ⭐ {accommodation.get('rating', '이름없음')} - {accommodation.get('features', '이름없음')}</p>
                        <p>가격: {accommodation.get('approximate price(KRW)', '이름없음')}</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )