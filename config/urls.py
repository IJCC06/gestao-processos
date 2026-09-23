from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from processos import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("clientes/", views.cliente_list, name="cliente_list"),
    path("clientes/novo/", views.cliente_create, name="cliente_create"),
    path("clientes/<int:pk>/", views.cliente_detail, name="cliente_detail"),
    path("clientes/<int:pk>/editar/", views.cliente_update, name="cliente_update"),
    path("clientes/<int:pk>/excluir/", views.cliente_delete, name="cliente_delete"),
    path("processos/", views.processo_list, name="processo_list"),
    path("processos/novo/", views.processo_create, name="processo_create"),
    path("processos/<int:pk>/", views.processo_detail, name="processo_detail"),
    path("processos/<int:pk>/editar/", views.processo_update, name="processo_update"),
    path("prazos/", views.prazo_list, name="prazo_list"),
    path("prazos/novo/", views.prazo_create, name="prazo_create"),
    path("prazos/<int:pk>/", views.prazo_detail, name="prazo_detail"),
    path("prazos/<int:pk>/editar/", views.prazo_update, name="prazo_update"),
    path("prazos/<int:pk>/concluir/", views.prazo_concluir, name="prazo_concluir"),
    path("notificacoes/", views.notificacoes, name="notificacoes"),
]
