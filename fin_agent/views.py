from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
from .models import DepositProduct, DepositOptions
from .serializers import DepositProductSerializer, DepositOptionsSerializer
from django.shortcuts import get_object_or_404
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .serializers import DepositProductSerializer, DepositOptionsSerializer, UserSerializer, JeonseLoanProductSerializer, JeonseLoanOptionSerializer, ArticleSerializer, ArticleListSerializer
import json
from .models import JeonseLoanProduct, JeonseLoanOption, Article
from .serializers import JeonseLoanProductSerializer, JeonseLoanOptionSerializer

# 환경변수에서 API 키 가져오기
API_KEY = settings.FINLIFE_API_KEY
BASE_URL = 'http://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json'

@api_view(['GET'])
def save_deposit_products(request):
    # 1. API 파라미터 설정 (실제 요청)
    params = {
        'auth': API_KEY,
        'topFinGrpNo': '020000', # 은행권
        'pageNo': 1
    }
    
    try:
        # 2. 금융감독원 API 호출
        response = requests.get(BASE_URL, params=params).json()
        
        # 3. 데이터 파싱
        base_list = response.get('result').get('baseList')   # 상품 목록
        option_list = response.get('result').get('optionList') # 금리 옵션 목록

        # [단계 A] 상품 기본 정보(Base) 먼저 저장
        for product in base_list:
            # 이미 있는 상품 코드는 건너뜀 (중복 방지)
            if DepositProduct.objects.filter(fin_prdt_cd=product.get('fin_prdt_cd')).exists():
                continue

            save_data = {
                'fin_prdt_cd': product.get('fin_prdt_cd'),
                'kor_co_nm': product.get('kor_co_nm'),
                'fin_prdt_nm': product.get('fin_prdt_nm'),
                'etc_note': product.get('etc_note'),
                'join_deny': int(product.get('join_deny')),
                'join_member': product.get('join_member'),
                'join_way': product.get('join_way'),
                'spcl_cnd': product.get('spcl_cnd'),
            }
            serializer = DepositProductSerializer(data=save_data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()

        # [단계 B] 옵션 정보(Options) 저장 (부모 상품과 연결)
        for option in option_list:
            # 1. 이 옵션의 부모 상품이 DB에 있는지 찾기
            try:
                product_instance = DepositProduct.objects.get(fin_prdt_cd=option.get('fin_prdt_cd'))
            except DepositProduct.DoesNotExist:
                # 부모 상품이 아직 저장이 안 됐다면 옵션도 저장 불가 -> 건너뜀
                continue

            # 2. 이미 저장된 옵션인지 확인 (중복 방지)
            if DepositOptions.objects.filter(
                product=product_instance,
                save_trm=option.get('save_trm'),
                intr_rate_type_nm=option.get('intr_rate_type_nm')
            ).exists():
                continue

            # 3. 데이터 매핑
            save_data = {
                'fin_prdt_cd': option.get('fin_prdt_cd'),
                'intr_rate_type_nm': option.get('intr_rate_type_nm'),
                'intr_rate': option.get('intr_rate') or 0, # 금리가 없으면 0 처리
                'intr_rate2': option.get('intr_rate2') or 0,
                'save_trm': int(option.get('save_trm')),
            }
            
            serializer = DepositOptionsSerializer(data=save_data)
            if serializer.is_valid(raise_exception=True):
                # ★ 핵심: 저장할 때 부모 객체(product)를 같이 넣어줌
                serializer.save(product=product_instance)

        return Response({"message": "금융 상품 및 옵션 데이터 저장 완료!"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": f"저장 실패: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# [조회용 API]
@api_view(['GET'])
def deposit_products(request):
    # [수정] prefetch_related('options')를 추가하여 DB 쿼리 효율성을 높입니다.
    # serializer가 'options' 필드를 참조할 때 발생하는 N+1 문제를 방지합니다.
    products = DepositProduct.objects.prefetch_related('options').all()
    
    serializer = DepositProductSerializer(products, many=True)
    return Response(serializer.data)

@permission_classes([IsAuthenticated]) # 로그인 필수
@api_view(['GET'])
def profile(request):
    # request.user: 현재 로그인한 유저 (Django가 토큰을 보고 찾아줌)
    user = request.user
    
    # 시리얼라이저를 통해 JSON으로 변환
    serializer = UserSerializer(user)
    
    return Response(serializer.data)

# [추가] 상품 가입 기능 (POST)
@api_view(['POST'])
@permission_classes([IsAuthenticated]) # 로그인한 사람만 접근 가능!
def join_deposit_product(request, fin_prdt_cd):
    # 1. 가입하려는 상품 찾기 (없으면 404 에러 자동 발생)
    product = get_object_or_404(DepositProduct, fin_prdt_cd=fin_prdt_cd)
    
    # 2. 현재 로그인한 유저 가져오기
    user = request.user 
    
    # 3. 이미 가입했는지 확인 (Optional)
    if user.financial_products.filter(fin_prdt_cd=fin_prdt_cd).exists():
        return Response({
            "message": "이미 가입한 상품입니다.",
            "type": "warning"
        }, status=status.HTTP_200_OK)
    
    # 4. 가입 처리 (M:N 관계 연결)
    # user.financial_products.add(product) -> DB의 중개 테이블에 데이터 생성
    user.financial_products.add(product)
    
    return Response({
        "message": f"'{product.fin_prdt_nm}' 상품에 성공적으로 가입되었습니다!",
        "current_join_count": user.financial_products.count()
    }, status=status.HTTP_201_CREATED)

# [추가] AI 금융 상품 추천 API


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_product(request):
    print(request)
    # 1. 사용자 정보 수신
    user_info = request.data
    
    # 2. 추천 후보군 선정
    products = DepositProduct.objects.all()
    product_list_text = ""
    for p in products:
        max_rate = 0
        trm = 0
        for opt in p.options.all():
            if opt.intr_rate2 and opt.intr_rate2 > max_rate:
                max_rate = opt.intr_rate2
            trm = opt.save_trm
        product_list_text += f"- 상품명: {p.fin_prdt_nm} (은행: {p.kor_co_nm}), 가입기간: {trm} 최고금리: {max_rate}%\n"

    # 3. 프롬프트(질문) 구성
    # Gemini에게 JSON 형식을 강제하기 위해 명확한 지시가 필요합니다.
    prompt = f"""
    당신은 금융 전문가입니다. 아래 사용자의 정보를 바탕으로 가장 적합한 금융 상품을 1개 추천해주세요.
    
    [사용자 정보]
    - 나이: {user_info.get('age')}세
    - 연봉: {user_info.get('salary')}원
    - 현재 자산: {user_info.get('money')}원
    - 목표 금액: {user_info.get('target_amount')}원
    - 금융 목적: {user_info.get('purpose')}
    
    [추천 가능 상품 목록]
    {product_list_text}
    
    [요청 사항]
    1. 사용자의 목적과 자산 상황을 고려하여 가장 적합한 상품 1개를 선택하세요.
    2. 선택한 이유를 친절하게 설명해주세요. 예: "목표 금액에 근접한 상품을 추천한 이유", "안정형 투자를 원하는 고객님을 위해 안정적인 금리를 제공하는 상품을 선택"
    3. 반드시 아래 JSON 형식으로만 답변해주세요. 마크다운(```json)이나 추가 설명 없이 순수 JSON만 출력하세요.
    
    {{
        "analysis": {{
            "purpose": "{user_info.get('purpose')}",
            "risk_profile": "안정형", 
            "comment": "여기에 추천 이유를 적어주세요."
        }},
        "products": [
            {{
                "fin_prdt_nm": "추천한 상품명",
                "kor_co_nm": "해당 은행명",
                "max_rate": "최고 금리",
                "save_trm": "가입 기간"
            }}
        ]
    }}
    """
    
    # 4. GMS (Gemini) API 호출
    # 스크린샷 기준: URL 뒤에 ?key=API_KEY 파라미터를 붙여야 합니다.
    base_url = settings.SSAFY_GMS_URL
    api_key = settings.SSAFY_GMS_API_KEY
    final_url = f"{base_url}?key={api_key}"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    # ★ Gemini API 전용 포맷 (OpenAI와 다름)
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    try:
        # POST 요청 전송
        response = requests.post(final_url, headers=headers, json=data, verify=False)
        response_data = response.json()
        
        # 5. Gemini 응답 파싱
        # 구조: candidates[0] -> content -> parts[0] -> text
        try:
            ai_text = response_data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            print(f"Gemini 응답 구조 에러: {response_data}")
            raise Exception("AI 응답을 해석할 수 없습니다.")

        # JSON 포맷팅 정리 (Gemini가 마크다운을 포함할 경우 제거)
        if ai_text.startswith('```json'):
            ai_text = ai_text.replace('```json', '').replace('```', '').strip()
        elif ai_text.startswith('```'):
            ai_text = ai_text.replace('```', '').strip()

        result = json.loads(ai_text)
        return Response(result)

    except Exception as e:
        print(f"AI 호출 에러: {e}")
        return Response({
            "analysis": {"comment": "AI 서비스 연결 실패. 잠시 후 다시 시도해주세요."},
            "products": []
        }, status=500)


# 1. 게시글 목록 조회 & 작성
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly]) 
def article_list_create(request):
    if request.method == 'GET':
        articles = Article.objects.all().order_by('-created_at')
        serializer = ArticleListSerializer(articles, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)

# 2. 게시글 상세 조회 & 수정 & 삭제 (통합)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly]) 
def article_detail(request, article_pk):
    article = get_object_or_404(Article, pk=article_pk)

    # [GET] 상세 조회: 누구나 가능 (권한 체크 위로 올림)
    if request.method == 'GET':
        serializer = ArticleSerializer(article)
        return Response(serializer.data)

    # --- 여기서부터는 수정/삭제이므로 본인 확인 ---
    if request.user != article.user:
        return Response({"detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

    # [PUT] 수정
    if request.method == 'PUT':
        serializer = ArticleSerializer(article, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)

    # [DELETE] 삭제
    elif request.method == 'DELETE':
        article.delete()
        return Response({"message": "삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def save_jeonse_loan_products(request):
    # 여기에 실제 로직을 추가하세요.
    return Response({"message": "전세자금대출 데이터 저장 완료!"}, status=status.HTTP_200_OK)

@api_view(['GET'])
def jeonse_loan_products(request):
    # 전세자금대출 상품 목록을 조회
    products = JeonseLoanProduct.objects.all()
    serializer = JeonseLoanProductSerializer(products, many=True)
    return Response(serializer.data)