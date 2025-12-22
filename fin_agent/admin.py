from django.contrib import admin
from .models import DepositProduct, User

# 관리자 페이지에서 데이터를 표(Table) 형태로 예쁘게 보기 위한 설정
@admin.register(DepositProduct)
class DepositProductAdmin(admin.ModelAdmin):
    list_display = ('fin_prdt_cd', 'fin_prdt_nm', 'kor_co_nm', 'join_deny') # 목록에 보여줄 칼럼
    search_fields = ('fin_prdt_nm', 'kor_co_nm') # 검색 기능 추가

# 유저 모델도 등록
admin.site.register(User)