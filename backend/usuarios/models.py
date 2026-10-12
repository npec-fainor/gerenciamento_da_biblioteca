from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin

class UsuarioManager(BaseUserManager):
    """Gerenciador de usuário onde o email é a identificação única para autenticação
    no lugar do username"""
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        """Cria e gerencia o usuário com o email e senha dados"""
        if not email:
            raise ValueError("O e-mail é obrigatório!")
        user = self.model(email = self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        """Cria e salva um SuperUser com o email e senha dados"""
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_active", True)
        extra.setdefault("papel", "ADMIN")

        if extra.get("is_staff") is not True:
            raise ValueError("Superuser deve ser is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser deve ser is_superuser=True.")
        return self.create_user(email, password, **extra)

class Usuario(AbstractBaseUser, PermissionsMixin):
    class Papel(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        BIBLIOTECARIO = "BIBLIOTECARIO", "Bibliotecário"
    name = models.CharField(max_length=150)
    email = models.EmailField("email address", unique=True)
    # Mantem o nome da coluna definido na modelagem original.
    password = models.CharField(max_length=128, db_column="senha_hash")
    papel = models.CharField(max_length=20, choices=Papel.choices, default=Papel.BIBLIOTECARIO)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_column="ativo")
    date_joined = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    class Meta:
        db_table = "usuario"

    def __str__(self):
        return self.email



