from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from .models import Assunto, Autor, Editora, Exemplar, Localizacao, Obra, ObraAssunto, ObraAutor


class ObraEditoraTests(TestCase):
    def test_obra_guarda_a_editora_em_editora_id(self):
        editora = Editora.objects.create(nome="Editora Teste")
        obra = Obra.objects.create(titulo="Dom Casmurro", editora=editora)

        self.assertEqual(obra.editora, editora)
        self.assertEqual(obra.editora_id, editora.pk)
        self.assertIn(obra, editora.obras.all())

    def test_obra_pode_ficar_sem_editora(self):
        obra = Obra.objects.create(titulo="Sem editora")

        self.assertIsNone(obra.editora)
        self.assertIsNone(obra.editora_id)

    def test_editora_com_obras_nao_pode_ser_excluida(self):
        editora = Editora.objects.create(nome="Editora Teste")
        Obra.objects.create(titulo="Dom Casmurro", editora=editora)

        with self.assertRaises(ProtectedError):
            editora.delete()


class TomboTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo="Dom Casmurro")
        Exemplar.objects.create(tombo="001", obra=self.obra)

    def test_banco_rejeita_tombo_repetido(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Exemplar.objects.create(tombo="001", obra=self.obra)

    def test_validacao_do_model_rejeita_tombo_repetido(self):
        exemplar = Exemplar(tombo="001", obra=self.obra)

        with self.assertRaises(ValidationError) as contexto:
            exemplar.full_clean()

        self.assertIn("tombo", contexto.exception.message_dict)

    def test_tombo_diferente_e_aceito(self):
        exemplar = Exemplar(tombo="002", obra=self.obra)

        exemplar.full_clean()
        exemplar.save()

        self.assertEqual(Exemplar.objects.count(), 2)


class AssociacoesTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo="Dom Casmurro")

    def test_autor_nao_se_repete_na_mesma_obra(self):
        autor = Autor.objects.create(nome="Machado de Assis")
        ObraAutor.objects.create(obra=self.obra, autor=autor)

        with self.assertRaises(IntegrityError), transaction.atomic():
            ObraAutor.objects.create(obra=self.obra, autor=autor)

    def test_assunto_nao_se_repete_na_mesma_obra(self):
        assunto = Assunto.objects.create(termo="Romance")
        ObraAssunto.objects.create(obra=self.obra, assunto=assunto)

        with self.assertRaises(IntegrityError), transaction.atomic():
            ObraAssunto.objects.create(obra=self.obra, assunto=assunto)

    def test_mesmo_autor_pode_estar_em_obras_diferentes(self):
        autor = Autor.objects.create(nome="Machado de Assis")
        outra_obra = Obra.objects.create(titulo="Quincas Borba")
        ObraAutor.objects.create(obra=self.obra, autor=autor)
        ObraAutor.objects.create(obra=outra_obra, autor=autor)

        self.assertEqual(autor.obras.count(), 2)


class ExclusaoDeObraTests(TestCase):
    def test_obra_com_exemplar_nao_pode_ser_excluida(self):
        obra = Obra.objects.create(titulo="Dom Casmurro")
        Exemplar.objects.create(tombo="001", obra=obra)

        with self.assertRaises(ProtectedError):
            obra.delete()

        self.assertTrue(Obra.objects.filter(pk=obra.pk).exists())

    def test_obra_sem_exemplar_pode_ser_excluida(self):
        obra = Obra.objects.create(titulo="Dom Casmurro")

        obra.delete()

        self.assertFalse(Obra.objects.filter(pk=obra.pk).exists())


class LocalizacaoStrTests(TestCase):
    def test_str_com_todos_os_campos(self):
        localizacao = Localizacao(setor="A", estante="3", prateleira="2")

        self.assertEqual(str(localizacao), "A/3/2")

    def test_str_ignora_campos_vazios(self):
        localizacao = Localizacao(setor="A", estante=None, prateleira="2")

        self.assertEqual(str(localizacao), "A/2")

    def test_str_sem_nenhum_campo(self):
        self.assertEqual(str(Localizacao()), "")
