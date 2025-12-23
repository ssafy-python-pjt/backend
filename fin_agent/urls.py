from django.urls import path
from . import views

urlpatterns = [
    # 1. 정기예금 상품 목록 조회 (GET) - 명세서 반영
    path('products/deposit/', views.deposit_products),
    
    path('products/save-saving/', views.save_saving_products),
    
    # 2. 데이터 수집용 (관리자용/내부용) - 명세서에는 없지만 DB 채우려면 필요함
    path('products/save-deposit/', views.save_deposit_products),
    
    # 3. AI 상품 추천 (POST) - 나중에 구현 예정
    # path('products/recommend/', views.recommend_product),

    path('products/deposit/<str:fin_prdt_cd>/join/', views.join_deposit_product),
    # [추가] 프로필 페이지
    path('profile/', views.profile),

    # [추가] AI 상품 추천
    path('products/recommend/', views.recommend_product),

    # [추가] 전세자금대출 데이터 저장 (최초 1회 실행용)
    path('products/save-loan/', views.save_jeonse_loan_products),
    
    # [추가] 전세자금대출 조회 (명세서 3번)
    path('products/loan/rent/', views.jeonse_loan_products),

    # [추가] 게시글 CRUD
    path('articles/', views.article_list_create),
    path('articles/<int:article_pk>/', views.article_detail),

    # 마이페이지 유저 정보 수정
    path('profile/update/', views.update_profile),
    
    # 가입한 상품 수정(PUT) 및 해지(DELETE)
    # <int:joined_pk>는 UserJoinedProduct 모델의 id값입니다.
    path('products/joined/<int:joined_pk>/', views.manage_joined_product),
    
]