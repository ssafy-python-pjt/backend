from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone # [추가] 가입일 Default 처리를 위해 추가

# 1. 금융 상품 기본 정보 (정기예금/적금 공용)
class DepositProduct(models.Model):
    # [추가] 상품 유형 구분 (정기예금 vs 적금)
    PRODUCT_TYPE_CHOICES = [
        ('deposit', '정기예금'),
        ('saving', '적금'),
    ]
    product_type = models.CharField(
        max_length=10, 
        choices=PRODUCT_TYPE_CHOICES, 
        default='deposit',
        help_text="상품 유형 (예금 또는 적금)"
    )
    
    fin_prdt_cd = models.TextField(unique=True)  # 금융상품코드
    kor_co_nm = models.TextField()               # 금융회사명
    fin_prdt_nm = models.TextField()             # 금융상품명
    etc_note = models.TextField()                # 유의사항
    join_deny = models.IntegerField(null=True)   # 가입제한
    join_member = models.TextField()             # 가입대상
    join_way = models.TextField()                # 가입방법
    spcl_cnd = models.TextField()                # 우대조건

    def __str__(self):
        return f"[{self.get_product_type_display()}] {self.fin_prdt_nm}"

# 2. 금융 상품 옵션 정보 (금리 정보)
class DepositOptions(models.Model):
    product = models.ForeignKey(DepositProduct, on_delete=models.CASCADE, related_name='options')
    fin_prdt_cd = models.TextField()             # 금융상품코드
    intr_rate_type_nm = models.CharField(max_length=100) # 저축 금리 유형명
    intr_rate = models.FloatField(null=True)     # 저축 금리 (기본)
    intr_rate2 = models.FloatField(null=True)    # 최고 우대 금리
    save_trm = models.IntegerField()             # 저축 기간 (단위: 개월)

    def __str__(self):
        return f"{self.product.fin_prdt_nm} ({self.save_trm}개월)"

# 3. 커스텀 유저 모델
class User(AbstractUser):
    # 사용자가 가입한 상품 목록 (중개 모델 UserJoinedProduct 사용)
    financial_products = models.ManyToManyField(
        DepositProduct, 
        related_name='joined_users',
        blank=True,
        through='UserJoinedProduct'
    )
    age = models.IntegerField(null=True, blank=True)
    money = models.BigIntegerField(null=True, blank=True)  # 현재 보유 자산
    salary = models.BigIntegerField(null=True, blank=True) # 연봉

# 4. 전세자금대출 상품 정보
class JeonseLoanProduct(models.Model):
    fin_prdt_cd = models.TextField(unique=True)
    kor_co_nm = models.TextField()
    fin_prdt_nm = models.TextField()
    join_way = models.TextField()
    loan_inci_expn = models.TextField()
    erly_rpay_fee = models.TextField()
    dly_rate = models.TextField()
    loan_lmt = models.TextField()
    
    # [보완] AI 분석용 태그 또는 핵심 정보 필드 (필요시 활용)
    search_tag = models.TextField(null=True, blank=True) 

    def __str__(self):
        return self.fin_prdt_nm

class JeonseLoanOption(models.Model):
    product = models.ForeignKey(JeonseLoanProduct, on_delete=models.CASCADE, related_name='options')
    fin_prdt_cd = models.TextField()
    rpay_type_nm = models.TextField()
    lend_rate_type_nm = models.TextField()
    lend_rate_min = models.FloatField()
    lend_rate_max = models.FloatField()
    lend_rate_avg = models.FloatField(null=True)

    def __str__(self):
        return f"{self.product.fin_prdt_nm} 옵션"

# 5. 커뮤니티 게시글 모델
class Article(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# 6. 유저-상품 중개 모델 (상세 가입 정보 저장)
class UserJoinedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='joined_details')
    product = models.ForeignKey(DepositProduct, on_delete=models.CASCADE)
    
    amount = models.BigIntegerField(default=0, help_text="현재 총 예치금액 또는 총 납입액")
    monthly_payment = models.BigIntegerField(default=0, help_text="적금일 경우 월 납입액")
    save_trm = models.IntegerField(default=12, help_text="가입 기간 (단위: 개월, 만기일 계산용)")
    
    # [수정] auto_now_add=True 제거하고 default=timezone.now로 변경하여 수정 가능하도록 함
    joined_at = models.DateField(default=timezone.now, help_text="가입일")

    # [추가] 사용자가 실제 적용받는 금리 및 유형 저장
    intr_rate = models.FloatField(default=0.0, help_text="적용 금리")
    intr_rate_type = models.CharField(max_length=10, default='S', help_text="금리 유형(S:단리, M:복리)")

    class Meta:
        unique_together = ('user', 'product') # 중복 가입 방지

    def __str__(self):
        return f"{self.user.username} - {self.product.fin_prdt_nm}"