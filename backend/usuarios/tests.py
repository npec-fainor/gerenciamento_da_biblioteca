from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings

Usuario = get_user_model()


class CriacaoDeUsuarioTests(TestCase):
    def test_create_user_usa_email_e_guarda_senha_com_hash(self):
        usuario = Usuario.objects.create_user(
            email="ana@exemplo.com", password="senha-segura-123", name="Ana"
        )

        self.assertEqual(usuario.email, "ana@exemplo.com")
        self.assertNotEqual(usuario.password, "senha-segura-123")
        self.assertTrue(usuario.check_password("senha-segura-123"))
        self.assertFalse(usuario.check_password("outra-senha"))

    def test_create_user_usa_valores_padrao(self):
        usuario = Usuario.objects.create_user(email="ana@exemplo.com", password="x", name="Ana")

        self.assertEqual(usuario.papel, Usuario.Papel.BIBLIOTECARIO)
        self.assertTrue(usuario.is_active)
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)

    def test_create_user_exige_email(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_user(email="", password="x", name="Ana")

    def test_email_nao_pode_se_repetir(self):
        Usuario.objects.create_user(email="ana@exemplo.com", password="x", name="Ana")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.create_user(email="ana@exemplo.com", password="y", name="Outra")

    def test_create_superuser_define_permissoes_e_papel(self):
        admin = Usuario.objects.create_superuser(
            email="admin@exemplo.com", password="x", name="Admin"
        )

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.papel, Usuario.Papel.ADMIN)

    def test_create_superuser_rejeita_is_staff_falso(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_superuser(
                email="admin@exemplo.com", password="x", name="Admin", is_staff=False
            )

    def test_create_superuser_rejeita_is_superuser_falso(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_superuser(
                email="admin@exemplo.com", password="x", name="Admin", is_superuser=False
            )


class AutenticacaoTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="ana@exemplo.com", password="senha-segura-123", name="Ana"
        )

    def test_autentica_com_email_e_senha_corretos(self):
        autenticado = authenticate(username="ana@exemplo.com", password="senha-segura-123")

        self.assertEqual(autenticado, self.usuario)

    def test_nao_autentica_com_senha_errada(self):
        self.assertIsNone(authenticate(username="ana@exemplo.com", password="errada"))

    def test_nao_autentica_usuario_inativo(self):
        self.usuario.is_active = False
        self.usuario.save()

        self.assertIsNone(authenticate(username="ana@exemplo.com", password="senha-segura-123"))


class CampoSenhaTests(TestCase):
    def test_campo_senha_tem_o_tamanho_padrao_do_django(self):
        campo = Usuario._meta.get_field("password")

        self.assertEqual(campo.max_length, 128)
        self.assertEqual(campo.column, "senha_hash")

    @override_settings(
        PASSWORD_HASHERS=["django.contrib.auth.hashers.ScryptPasswordHasher"]
    )
    def test_hash_scrypt_cabe_no_campo(self):
        # O hash do scrypt tem 128 caracteres e nao cabia no limite antigo de 120
        usuario = Usuario.objects.create_user(
            email="ana@exemplo.com", password="senha-segura-123", name="Ana"
        )
        usuario.refresh_from_db()

        self.assertTrue(usuario.password.startswith("scrypt$"))
        self.assertTrue(usuario.check_password("senha-segura-123"))


class CamposObrigatoriosDeUsuarioTests(TestCase):
    def test_banco_rejeita_email_nulo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.create(email=None, name="Ana", password="x")

    def test_banco_rejeita_nome_nulo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.create(email="ana@exemplo.com", name=None, password="x")

    def test_validacao_do_model_exige_nome_e_email(self):
        with self.assertRaises(ValidationError) as contexto:
            Usuario(email="", name="", password="x").full_clean()

        self.assertIn("name", contexto.exception.message_dict)
        self.assertIn("email", contexto.exception.message_dict)

    def test_email_repetido_nao_cria_novo_usuario(self):
        Usuario.objects.create_user(email="ana@exemplo.com", password="x", name="Ana")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.create_user(email="ana@exemplo.com", password="y", name="Outra")

        self.assertEqual(Usuario.objects.count(), 1)

    def test_validacao_do_model_rejeita_email_repetido(self):
        Usuario.objects.create_user(email="ana@exemplo.com", password="x", name="Ana")

        with self.assertRaises(ValidationError) as contexto:
            Usuario(email="ana@exemplo.com", name="Outra", password="y").full_clean()

        self.assertIn("email", contexto.exception.message_dict)
