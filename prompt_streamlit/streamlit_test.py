
import streamlit as st
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

# Add custom CSS for styling (white theme)
st.markdown(
    """
    <style>
        body {
            background-color: #273346;
        }
        .title { font-size: 36px; font-weight: bold; color: #333333; }
        .subtitle { font-size: 24px; font-weight: bold; margin-top: 20px; color: #333333; }
        .bot-response, .user-response { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .bot-response { background-color: #f1f1f1; color: #333333; }
        .user-response { background-color: #e1f5fe; color: #0c5460; }
        .itinerary-content { margin-top: 10px; background-color: #fafafa; color: #333333; padding: 15px; border-radius: 8px; font-size: 16px; line-height: 1.6; }
    </style>
""",
    unsafe_allow_html=True,
)

# 제목과 설명
st.title("🌍 TRiPO 여행 일정 생성")  # 문구수정함
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


# 사이드바를 통한 입력 인터페이스
with st.sidebar:
    # Assistant message for greeting
    message(
        "안녕하세요 여행자님! 여행자님의 계획 생성을 도와줄 리포(RIPO)입니다👋 저와 함께 멋진 여행 일정을 만들어봐요!✨ 그럼 질문에 맞는 답을 체크박스로 선택해주시면 바로 시작해볼게요!",  # 문구변경함
        is_user=False,
    )

    # 도시 선택 체크박스 UI + 사용자 입력 상자 추가
    message(
    "어느 도시를 여행하고 싶으신가요? 아래에서 도시를 선택해주세요.",
    is_user=False,
    )

    # 도시 이름과 해당 영어 표기 매핑
    cities = {"오사카": "Osaka", "파리": "Paris", "방콕": "Bangkok", "뉴욕": "New York"}

    for city_kr, city_en in cities.items():
        if st.checkbox(
            city_kr, key=f"city_{city_en}", disabled=st.session_state.get("destination") is not None
        ):
            st.session_state.destination = city_en  # 영어 이름으로 세션 상태 업데이트
            st.session_state.current_step = 1
            message(f"{city_kr} 여행을 가고 싶어!", is_user=True)
            message(
                f"{city_kr} 여행을 계획해드리겠습니다.",
                is_user=False,
            )


    # 여행 기간 선택
    if st.session_state.get("destination"):
        message(
            "얼마나 여행을 떠날 예정인가요? 여행 기간을 선택하거나 직접 입력해주세요 ✏️",
            is_user=False,
        )
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
                message(
                    f"{duration_display} 동안 여행을 가고 싶어!",
                    is_user=True,
                )
                message(
                    f"{duration_display} 동안의 여행을 계획해드리겠습니다.",
                    is_user=False,
                )
            else:
                st.error("입력 형식이 올바르지 않습니다. 예: '2박 3일' 형태로 다시 입력해주세요.")
        elif selected_duration:
            st.session_state.stay_duration = durations[selected_duration]
            st.session_state.current_step = 2
            message(
                f"{selected_duration} 동안 여행을 가고 싶어!",
                is_user=True,
            )
            message(
                f"{selected_duration} 동안의 여행을 계획해드리겠습니다.",
                is_user=False,
            )


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
        message(
            "누구와 함께 여행을 떠나시나요? 골라주세요! 중복선택도 가능합니다 😎",
            is_user=False,
        )
        companions = {
            "혼자": "Alone",
            "친구와": "With friends",
            "연인과": "With partner",
            "가족과": "With family",
            "어린아이와": "With children",
            "반려동물과": "With pets",
            "단체 여행으로": "Group travel"
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
                selected_companions_kr += f", {custom_companion}"  # Append custom input in Korean for user clarity
            message(
                f"이번 여행은 {selected_companions_kr} 떠나고 싶어!",
                is_user=True,
            )
            message(
                f"{selected_companions_kr} 함께하는 멋진 여행을 준비해드리겠습니다!",
                is_user=False,
            )


    # 여행 스타일 선택 - 다중선택 변경완료
    if st.session_state.companion:
        message(
            "어떤 여행 스타일을 선호하시나요? 아래에서 선택하거나 직접 입력해주세요.",
            is_user=False,
        )
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
            message(
                f"{custom_style} 스타일의 여행을 떠나고 싶어",
                is_user=True,
            )
            message(
                f"{custom_style} 타입의 여행을 선택했습니다.",
                is_user=False,
            )
            
        if selected_styles:
            st.session_state.travel_style = selected_styles
            st.session_state.current_step = 4
            selected_styles_kr = ", ".join([key for key, value in travel_styles.items() if value in selected_styles])
            message(
                f"{selected_styles_kr} 스타일의 여행을 떠나고 싶어",
                is_user=True,
            )
            message(
                f"{selected_styles_kr} 타입의 여행을 선택했습니다.",
                is_user=False,
            )

    # 여행 일정 스타일 선택
    if st.session_state.travel_style:
        message(
            "선호하는 여행 일정 스타일은 무엇인가요? 선택하거나 직접 입력해주세요.",
            is_user=False,
        )
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
                message(
                    f"{preference_kr} 여행 일정을 선호해",
                    is_user=True,
                )
                message(
                    f"{preference_kr} 일정 스타일로 일정을 준비하겠습니다.",
                    is_user=False,
                )


    # 숙소 유형 선택 - 다중선택 변경완료
    if st.session_state.itinerary_preference:
        message(
            "어떤 숙소를 원하시나요? 아래에서 선택하거나 직접 입력해주세요.",
            is_user=False,
        )
        accommodations = {
            "공항 근처 숙소": "Accommodation near the airport",
            "5성급 호텔 이상": "5-star hotel or higher",
            "수영장이 있는 숙소": "Accommodation with a swimming pool",
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
                selected_accommodations_kr += f", {custom_accommodation}"  # Append custom input in Korean for user clarity
            message(
                f"{selected_accommodations_kr} 스타일의 숙소를 원해",     # 가성비 입력했는데 ", 가성비 스타일" 이런 식으로 나옴. 해결하기.
                is_user=True,
            )
            message(
                f"{selected_accommodations_kr} 스타일의 숙소로 추천해드리겠습니다.",
                is_user=False,
            )

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