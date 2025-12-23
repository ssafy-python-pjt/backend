from rest_framework import serializers
from .models import DepositProduct, DepositOptions
from django.contrib.auth import get_user_model # 현재 활성화된 유저 모델을 가져옴
from .models import JeonseLoanProduct, JeonseLoanOption, Article, UserJoinedProduct # import에 모델 추가!

# 1. 예금 옵션 시리얼라이저 (기존 유지)
class DepositOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositOptions
        fields = '__all__'
        read_only_fields = ('product',)

# 2. 예금 상품 시리얼라이저 (수정됨!)
class DepositProductSerializer(serializers.ModelSerializer):
    # [핵심 수정] related_name='options'를 통해 연결된 금리 정보를 가져옵니다.
    options = DepositOptionsSerializer(many=True, read_only=True)

    class Meta:
        model = DepositProduct
        fields = '__all__' # 이제 결과 JSON에 'options': [...] 가 포함됩니다.

User = get_user_model()


class UserJoinedProductSerializer(serializers.ModelSerializer):
    # 연결된 상품의 기본 정보도 함께 포함
    product_name = serializers.CharField(source='product.fin_prdt_nm', read_only=True)
    bank_name = serializers.CharField(source='product.kor_co_nm', read_only=True)
    save_trm = serializers.IntegerField(source='product.options.first.save_trm', read_only=True)
    product = DepositProductSerializer(read_only=True)
    
    class Meta:
        model = UserJoinedProduct
        fields = ('id', 'product', 'product_name', 'bank_name', 'amount', 'monthly_payment', 'joined_at', 'save_trm')


class UserSerializer(serializers.ModelSerializer):
    # ★ 핵심: 역참조 데이터를 가져올 때, 기존에 만든 ProductSerializer를 재사용합니다.
    # many=True: 가입한 상품이 여러 개일 수 있음
    # read_only=True: 프로필 조회 시 상품 정보를 수정하진 않음
    joined_details = UserJoinedProductSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'joined_details', 'age', 'money', 'salary')
        
# [추가] 전세자금대출 옵션 시리얼라이저
class JeonseLoanOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JeonseLoanOption
        fields = '__all__'
        read_only_fields = ('product',)

# [추가] 전세자금대출 상품 시리얼라이저 (옵션 포함)
class JeonseLoanProductSerializer(serializers.ModelSerializer):
    # 역참조 이름(related_name='options')을 사용해 옵션 정보를 같이 보여줍니다.
    options = JeonseLoanOptionSerializer(many=True, read_only=True)

    class Meta:
        model = JeonseLoanProduct
        fields = '__all__'

# [추가] ArticleSerializer
class ArticleSerializer(serializers.ModelSerializer):
    # 게시글 작성자를 위한 중첩 시리얼라이저 (읽기 전용)
    user = UserSerializer(read_only=True) 

    class Meta:
        model = Article
        fields = ('id', 'user', 'title', 'content', 'created_at', 'updated_at')
        read_only_fields = ('user', 'created_at', 'updated_at') # user는 자동으로 할당됨

# [추가] ArticleListSerializer (목록 조회 시 상세 유저 정보는 제외)
class ArticleListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True) # 사용자 이름만 표시

    class Meta:
        model = Article
        # [수정] 아래 fields 목록에 'content'를 꼭 추가해주세요!
        fields = ('id', 'user', 'title', 'content', 'created_at')