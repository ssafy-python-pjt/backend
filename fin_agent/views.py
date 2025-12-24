from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from .models import DepositProduct, DepositOptions, UserJoinedProduct, JeonseLoanProduct, JeonseLoanOption, Article
from .serializers import (
    DepositProductSerializer, DepositOptionsSerializer, UserJoinedProductSerializer, 
    JeonseLoanProductSerializer, JeonseLoanOptionSerializer, UserSerializer, 
    ArticleSerializer, ArticleListSerializer
)
import json
import requests
import socket
import re


# IPv6 문제 해결을 위한 패치
orig_getaddrinfo = socket.getaddrinfo
def ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = ipv4_only_getaddrinfo

# 환경변수 설정
API_KEY = settings.FINLIFE_API_KEY

# 1. 정기예금 데이터 수집
@api_view(['GET'])
def save_deposit_products(request):
    BASE_URL = 'http://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json'
    params = {'auth': API_KEY, 'topFinGrpNo': '020000', 'pageNo': 1}
    
    try:
        response = requests.get(BASE_URL, params=params).json()
        base_list = response.get('result').get('baseList')
        option_list = response.get('result').get('optionList')

        for product in base_list:
            DepositProduct.objects.update_or_create(
                fin_prdt_cd=product.get('fin_prdt_cd'),
                defaults={
                    'kor_co_nm': product.get('kor_co_nm'),
                    'fin_prdt_nm': product.get('fin_prdt_nm'),
                    'etc_note': product.get('etc_note'),
                    'join_deny': int(product.get('join_deny')),
                    'join_member': product.get('join_member'),
                    'join_way': product.get('join_way'),
                    'spcl_cnd': product.get('spcl_cnd'),
                    'product_type': 'deposit' 
                }
            )

        for option in option_list:
            product_instance = DepositProduct.objects.filter(fin_prdt_cd=option.get('fin_prdt_cd')).first()
            if product_instance:
                DepositOptions.objects.update_or_create(
                    product=product_instance,
                    save_trm=option.get('save_trm'),
                    intr_rate_type_nm=option.get('intr_rate_type_nm'),
                    defaults={
                        'fin_prdt_cd': option.get('fin_prdt_cd'),
                        'intr_rate': option.get('intr_rate') or 0,
                        'intr_rate2': option.get('intr_rate2') or 0,
                    }
                )

        return Response({"message": "정기예금 데이터 저장 완료!"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 2. 적금 데이터 수집
@api_view(['GET'])
def save_saving_products(request):
    SAVING_URL = 'http://finlife.fss.or.kr/finlifeapi/savingProductsSearch.json'
    params = {'auth': API_KEY, 'topFinGrpNo': '020000', 'pageNo': 1}
    
    try:
        response = requests.get(SAVING_URL, params=params).json()
        base_list = response.get('result').get('baseList')
        option_list = response.get('result').get('optionList')

        for product in base_list:
            DepositProduct.objects.update_or_create(
                fin_prdt_cd=product.get('fin_prdt_cd'),
                defaults={
                    'kor_co_nm': product.get('kor_co_nm'),
                    'fin_prdt_nm': product.get('fin_prdt_nm'),
                    'etc_note': product.get('etc_note'),
                    'join_deny': int(product.get('join_deny')),
                    'join_member': product.get('join_member'),
                    'join_way': product.get('join_way'),
                    'spcl_cnd': product.get('spcl_cnd'),
                    'product_type': 'saving'
                }
            )

        for option in option_list:
            product_instance = DepositProduct.objects.filter(fin_prdt_cd=option.get('fin_prdt_cd')).first()
            if product_instance:
                DepositOptions.objects.update_or_create(
                    product=product_instance,
                    save_trm=option.get('save_trm'),
                    intr_rate_type_nm=option.get('intr_rate_type_nm'),
                    defaults={
                        'fin_prdt_cd': option.get('fin_prdt_cd'),
                        'intr_rate': option.get('intr_rate') or 0,
                        'intr_rate2': option.get('intr_rate2') or 0,
                    }
                )

        return Response({"message": "적금 데이터 저장 완료!"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 3. 전세자금대출 데이터 수집
@api_view(['GET'])
def save_jeonse_loan_products(request):
    LOAN_URL = 'http://finlife.fss.or.kr/finlifeapi/rentHouseLoanProductsSearch.json'
    params = {'auth': API_KEY, 'topFinGrpNo': '020000', 'pageNo': 1}
    
    try:
        response = requests.get(LOAN_URL, params=params, verify=False).json()
        result = response.get('result', {})
        base_list = result.get('baseList', [])
        option_list = result.get('optionList', [])

        for product in base_list:
            JeonseLoanProduct.objects.update_or_create(
                fin_prdt_cd=product.get('fin_prdt_cd'),
                defaults={
                    'kor_co_nm': product.get('kor_co_nm'),
                    'fin_prdt_nm': product.get('fin_prdt_nm'),
                    'join_way': product.get('join_way'),
                    'loan_inci_expn': product.get('loan_inci_expn') or '정보 없음',
                    'erly_rpay_fee': product.get('erly_rpay_fee') or '정보 없음',
                    'dly_rate': product.get('dly_rate') or '정보 없음',
                    'loan_lmt': product.get('loan_lmt') or '한도 확인 필요',
                }
            )

        for option in option_list:
            product_instance = JeonseLoanProduct.objects.filter(fin_prdt_cd=option.get('fin_prdt_cd')).first()
            if product_instance:
                JeonseLoanOption.objects.update_or_create(
                    product=product_instance,
                    rpay_type_nm=option.get('rpay_type_nm'),
                    lend_rate_type_nm=option.get('lend_rate_type_nm'),
                    defaults={
                        'fin_prdt_cd': option.get('fin_prdt_cd'),
                        'lend_rate_min': option.get('lend_rate_min') or 0,
                        'lend_rate_max': option.get('lend_rate_max') or 0,
                        'lend_rate_avg': option.get('lend_rate_avg'),
                    }
                )
        return Response({"message": f"대출 상품 {len(base_list)}개 수집 완료!"})
    except Exception as e:
        return Response({"error": f"데이터 수집 중 오류: {str(e)}"}, status=500)
    
# 4. 예금/적금 통합 조회
@api_view(['GET'])
def deposit_products(request):
    product_type = request.GET.get('type')
    products = DepositProduct.objects.prefetch_related('options')
    
    if product_type:
        products = products.filter(product_type=product_type)
        
    serializer = DepositProductSerializer(products, many=True)
    return Response(serializer.data)

# 5. 전세자금대출 목록 조회
@api_view(['GET'])
def jeonse_loan_products(request):
    products = JeonseLoanProduct.objects.prefetch_related('options').all()
    serializer = JeonseLoanProductSerializer(products, many=True)
    return Response(serializer.data)

# 6. AI 상품 추천 (수정됨)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_product(request):
    user_info = request.data
    products = DepositProduct.objects.prefetch_related('options').all()
    
    product_list_text = ""
    for p in products:
        options_text = ", ".join([f"{opt.save_trm}개월({opt.intr_rate2}%)" for opt in p.options.all()])
        product_list_text += f"상품코드: {p.fin_prdt_cd} / 타입: {p.get_product_type_display()} / 상품명: {p.fin_prdt_nm} ({p.kor_co_nm})\n"
        product_list_text += f" - 금리옵션: {options_text}\n"
        product_list_text += f" - 우대조건: {p.spcl_cnd}\n\n"

    prompt = f"""
    당신은 꼼꼼한 금융 전문가입니다. 아래 사용자의 정보와 요청사항을 분석하여 제공된 [상품 목록] 중에서 가장 적합한 상품 **3개**를 추천해주세요.

    [사용자 프로필]
    - 나이: {user_info.get('age')}세
    - 연봉: {user_info.get('salary')}원
    - 현재 자산: {user_info.get('money')}원
    - 사용자 요청(목적): "{user_info.get('purpose')}"

    [상품 목록]
    {product_list_text}

    [분석 가이드]
    1. 사용자의 요청(목적)을 자연어 처리하여 의도를 파악하세요. 
    2. 연봉과 자산 규모를 고려하여 가입 가능한 상품인지 판단하세요.
    3. 금리가 높은 상품을 우선하되, 우대 조건 달성 가능성도 고려하세요.
    4. 위험 감수 성향 분석은 하지 마세요. 오직 목적 적합성과 금리 효율성만 따집니다.

    [응답 형식]
    반드시 아래와 같은 **JSON 형식**으로만 응답하세요.
    {{
      "analysis": {{
        "purpose": "사용자 요청을 분석하여 파악한 구체적인 재무 목적",
        "keywords": "분석된 핵심 키워드"
      }},
      "products": [
        {{
          "fin_prdt_cd": "상품코드",
          "fin_prdt_nm": "상품명",
          "kor_co_nm": "은행명",
          "max_rate": "대표 최고 우대 금리(숫자만)",
          "save_trm": "추천 가입 기간(개월수 숫자만)",
          "comment": "추천 이유"
        }}
      ]
    }}
    """
    
    final_url = f"{settings.SSAFY_GMS_URL}?key={settings.SSAFY_GMS_API_KEY}"
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(final_url, json=data, verify=False)
        response_data = response.json()
        
        # GMS 응답 텍스트 추출
        ai_text = response_data['candidates'][0]['content']['parts'][0]['text']
        
        # [핵심 수정] 정규표현식으로 JSON 부분만 정확히 추출 (```json 태그 유무 상관없이 동작)
        match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            result_json = json.loads(json_str)
            return Response(result_json)
        else:
            raise ValueError("JSON 형식을 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"AI 추천 에러: {e}")
        # 에러 발생 시 로그를 남기고 빈 배열 반환
        return Response({
            "analysis": {"purpose": "분석 실패", "keywords": "없음"}, 
            "products": []
        }, status=500)

# 7. 마이페이지 프로필 조회
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

# 8. 마이페이지 프로필 수정
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(serializer.data)

# 9. 가입한 상품 수정(PUT) 및 해지(DELETE)
@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_joined_product(request, joined_pk):
    joined_product = get_object_or_404(UserJoinedProduct, pk=joined_pk, user=request.user)
    
    if request.method == 'PUT':
        # [핵심] Serializer가 intr_rate, joined_at 등을 포함하므로 여기서 처리됨
        serializer = UserJoinedProductSerializer(joined_product, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
            
    elif request.method == 'DELETE':
        joined_product.delete()
        return Response({"message": "해지되었습니다."}, status=204)

# 10. 예적금 상품 가입
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_deposit_product(request, fin_prdt_cd):
    product = get_object_or_404(DepositProduct, fin_prdt_cd=fin_prdt_cd)
    
    # 중복 가입 체크
    if UserJoinedProduct.objects.filter(user=request.user, product=product).exists():
        return Response({"message": "이미 가입한 상품입니다."}, status=400)
    
    # [추가] 가입 시 사용자 편의를 위해 기본 금리 정보 자동 설정
    # 1. 12개월 옵션을 우선 탐색
    default_option = product.options.filter(save_trm=12).first()
    # 2. 없으면 첫 번째 아무 옵션이나 선택
    if not default_option:
        default_option = product.options.first()
        
    initial_rate = default_option.intr_rate if default_option else 0.0
    initial_rate_type = 'S' # 기본 단리
    if default_option and '복리' in default_option.intr_rate_type_nm:
        initial_rate_type = 'M' # 복리

    # 가입 처리 (초기값 설정)
    UserJoinedProduct.objects.create(
        user=request.user, 
        product=product, 
        save_trm=12,
        intr_rate=initial_rate,
        intr_rate_type=initial_rate_type
    )
    
    return Response({"message": f"'{product.fin_prdt_nm}' 가입 완료!"}, status=201)

# 11. 게시글 목록/생성
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def article_list_create(request):
    if request.method == 'GET':
        articles = Article.objects.all().order_by('-created_at')
        return Response(ArticleListSerializer(articles, many=True).data)
    elif request.method == 'POST':
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)

# 12. 게시글 상세/수정/삭제
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def article_detail(request, article_pk):
    article = get_object_or_404(Article, pk=article_pk)
    if request.method == 'GET':
        return Response(ArticleSerializer(article).data)
    if request.user != article.user:
        return Response({"detail": "권한 없음"}, status=403)
    if request.method == 'PUT':
        serializer = ArticleSerializer(article, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
    elif request.method == 'DELETE':
        article.delete()
        return Response(status=204)