from rest_framework import serializers
from .models import DepositProduct, DepositOptions, UserJoinedProduct, JeonseLoanProduct, JeonseLoanOption, Article
from django.contrib.auth import get_user_model

User = get_user_model()

# 1. 예금/적금 옵션 시리얼라이저
class DepositOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositOptions
        fields = '__all__'
        read_only_fields = ('product',)

# 2. 예금/적금 상품 시리얼라이저
class DepositProductSerializer(serializers.ModelSerializer):
    options = DepositOptionsSerializer(many=True, read_only=True)

    class Meta:
        model = DepositProduct
        fields = '__all__'

# 3. 유저-상품 중개 모델 시리얼라이저 (핵심 수정)
class UserJoinedProductSerializer(serializers.ModelSerializer):
    # [수정] 상품 상세 정보를 중첩해서 가져와 프론트엔드에서 product.fin_prdt_nm 및 options 접근 가능
    product = DepositProductSerializer(read_only=True)
    
    class Meta:
        model = UserJoinedProduct
        # [수정] joined_at, intr_rate, intr_rate_type 필드 추가하여 수정 가능하도록 설정
        fields = (
            'id', 'product', 'amount', 'monthly_payment', 
            'joined_at', 'save_trm', 'intr_rate', 'intr_rate_type'
        )

# 4. 유저 시리얼라이저 (마이페이지용)
class UserSerializer(serializers.ModelSerializer):
    # [수정] 사용자가 가입한 상품의 상세 내역(금액, 기간, 적용금리 등)을 포함
    joined_details = UserJoinedProductSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'joined_details', 'age', 'money', 'salary')

# 5. 전세자금대출 관련 시리얼라이저
class JeonseLoanOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JeonseLoanOption
        fields = '__all__'
        read_only_fields = ('product',)

class JeonseLoanProductSerializer(serializers.ModelSerializer):
    options = JeonseLoanOptionSerializer(many=True, read_only=True)

    class Meta:
        model = JeonseLoanProduct
        fields = '__all__'

# 6. 커뮤니티 게시글 시리얼라이저
class ArticleSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Article
        fields = ('id', 'user', 'title', 'content', 'created_at', 'updated_at')
        read_only_fields = ('user', 'created_at', 'updated_at')

class ArticleListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Article
        fields = ('id', 'user', 'title', 'content', 'created_at')