from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. 금융 상품 기본 정보 (Base)
class DepositProduct(models.Model):
    fin_prdt_cd = models.TextField(unique=True)  # 금융상품코드 (PK 역할)
    kor_co_nm = models.TextField()               # 금융회사명
    fin_prdt_nm = models.TextField()             # 금융상품명
    etc_note = models.TextField()                # 유의사항
    join_deny = models.IntegerField(null=True)   # 가입제한
    join_member = models.TextField()             # 가입대상
    join_way = models.TextField()                # 가입방법
    spcl_cnd = models.TextField()                # 우대조건

    def __str__(self):
        return self.fin_prdt_nm

# 2. 금융 상품 옵션 정보 (Options - 금리 정보) [NEW]
class DepositOptions(models.Model):
    # 어떤 상품의 옵션인지 연결 (ForeignKey)
    product = models.ForeignKey(DepositProduct, on_delete=models.CASCADE, related_name='options')
    fin_prdt_cd = models.TextField()             # 금융상품코드 (매핑용)
    intr_rate_type_nm = models.CharField(max_length=100) # 저축 금리 유형명
    intr_rate = models.FloatField(null=True)     # 저축 금리 (기본)
    intr_rate2 = models.FloatField(null=True)    # 최고 우대 금리
    save_trm = models.IntegerField()             # 저축 기간 (단위: 개월)

    def __str__(self):
        return f"{self.product.fin_prdt_nm} ({self.save_trm}개월)"

# 3. 커스텀 유저 모델
class User(AbstractUser):
    # 사용자가 가입한 상품 목록
    financial_products = models.ManyToManyField(
        DepositProduct, 
        related_name='joined_users',
        blank=True
    )
    age = models.IntegerField(null=True, blank=True)
    money = models.BigIntegerField(null=True, blank=True)
    salary = models.BigIntegerField(null=True, blank=True)


# [추가] 전세자금대출 상품 (기본 정보)
class JeonseLoanProduct(models.Model):
    fin_prdt_cd = models.TextField(unique=True) # 상품 코드
    kor_co_nm = models.TextField()   # 금융회사명
    fin_prdt_nm = models.TextField() # 상품명
    join_way = models.TextField()    # 가입 방법
    loan_inci_expn = models.TextField() # 대출 부대비용
    erly_rpay_fee = models.TextField()  # 조기 상환 수수료
    dly_rate = models.TextField()       # 연체 이자율
    loan_lmt = models.TextField()       # 대출 한도

# [추가] 전세자금대출 옵션 (금리 정보)
class JeonseLoanOption(models.Model):
    product = models.ForeignKey(JeonseLoanProduct, on_delete=models.CASCADE, related_name='options')
    fin_prdt_cd = models.TextField()
    rpay_type_nm = models.TextField()      # 상환 방식
    lend_rate_type_nm = models.TextField() # 금리 유형
    lend_rate_min = models.FloatField()    # 최저 금리
    lend_rate_max = models.FloatField()    # 최고 금리
    lend_rate_avg = models.FloatField(null=True) # 평균 금리

# [추가] 커뮤니티 게시글 모델
class Article(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title