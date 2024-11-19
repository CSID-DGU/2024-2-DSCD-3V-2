def get_css():
    return """
    <style>
        /* 사이드바 배경 흰색으로 설정 */
        [data-testid="stSidebar"] {
            background-color: white;
        }
        
        /* 사이드바 오른쪽에 회색 구분선과 그림자 추가 (필수)*/
        [data-testid="stSidebar"] {
            border-right: 1px solid #d3d3d3; /* 회색 구분선 */
            box-shadow: 2px 0px 5px rgba(0, 0, 0, 0.1); /* 오른쪽에 그림자 추가 */
        } 

        /* 사이드바 제목을 우측 화살표와 같은 행에 배치 */
        .sidebar-title {
            display: flex;
            align-items: center;
            font-size: 20px;
            font-weight: bold;
        }
        
        /* 텍스트 입력 상자의 테두리 색상 회색으로 설정 (필수)*/
        input[type="text"] {
            border: 1px solid #d3d3d3;
            padding: 10px;
            border-radius: 5px;
        }
        
        /* 선택된 텍스트 입력 필드의 테두리 강조 색상 (필수)*/
        input[type="text"]:focus {
            border-color: #a9a9a9;  /* 강조 회색 */
            box-shadow: none;
            outline: none;
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

        /* 선택된 pills 색상을 파란색 테두리로 변경 - 적용안되는 중...ㅠ */ 
        .st-pills [data-selected="true"] {
            border-color: #007bff !important; /* 파란색 테두리 */
            color: #007bff !important; /* 파란색 텍스트 */
            font-weight: bold !important;
        }
            
        /* 비선택 pills 스타일 - 적용안되는 중...ㅠ */
        .st-pills [data-selected="false"] {
            color: #444 !important;
        }

        /* 결과 파트 전체 페이지의 상단 여백을 최소화하는 CSS 스타일 추가 */

        .main .block-container, .css-1lcbmhc.e1fqkh3o5 {
            padding-top: 0px;  /* 페이지 최상단 간격 제거 */
        }
        .header-container {
            text-align: center;
            margin-top: -80px;  /* 화면 상단에서 일정한 거리 유지 */
            margin-bottom: 20px;
        }
        .header-title {
            font-size: 24px;
            font-weight: bold;
            margin: 5px 0;
        }
        .header-subtitle {
            font-size: 16px;
            color: #888888;
            margin: 0;
        }
        .loading-container {
            text-align: center;
            margin-top: 50px;
        }
        .loading-container img {
            width: 150px;
            margin-top: 20px;
        }
        .loading-container p {
            font-size: 16px;
            color: #333333;
            margin-top: 10px;
        }
    </style>
"""

# 여행 일정 카드 스타일 정의
def travel_card_style():
    return """
    <style>
    /* 여행 일정 카드 스타일 정의 */
        .subheader {
        font-size: 18px;
        margin-top: 0px;
        }
        .travel-card {
            border: 1px solid #d1d1d1;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
            background-color: #f9f9f9;
            font-size: 14px;
        }
        .travel-card h5 {
            margin: 0;
            font-size: 16px;
            display: inline;
        }
        .travel-card p.time {
            color: #888888;
            font-size: 12px;
            display: inline;
            margin-left: 8px;
        }
        .travel-card hr {
            margin: 5px 0;
            border: none;
            border-top: 1px solid #d1d1d1;
        }
        .travel-card p.description {
            font-size: 13px;
            margin: 0;
        }

    </style>
"""

# 숙소 추천 카드 스타일 정의
def accommodation_card_style():
    return """
    <style>
        .accommodation-card {
            height: 150px; /* 카드의 고정된 높이 */
            border: 1px solid #d1d1d1;
            border-radius: 8px;
            padding: 10px;
            margin: 5px auto; /* 중앙 정렬 */
            background-color: #f9f9f9;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
            text-align: center; /* 중앙 정렬 */
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .accommodation-card h6 {
            font-size: 14px;
            margin: 5px 0;
            font-weight: bold;
        }
        .accommodation-card p {
            font-size: 12px;
            margin: 3px 0;
        }
    </style>
"""

# 여행 일정 제목 스타일 정의
def title_style():
    return """
    <style>
        .accommodation-title {
            font-size: 20px; /* 원하는 크기로 조정 */
            font-weight: bold;
            color: #333333;
            margin-bottom: 10px;
        }
    </style>
"""