from django.contrib import admin
from .models import DepositProduct, UserJoinedProduct, User, JeonseLoanProduct, Article

# 유저 모델도 등록
admin.site.register(User)
admin.site.register(DepositProduct)
admin.site.register(UserJoinedProduct)
admin.site.register(JeonseLoanProduct)
admin.site.register(Article)