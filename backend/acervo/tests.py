from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from .models import (
    Assunto,
    Autor,
    Editora,
    Exemplar,
    Localizacao,
    LogAcervo,
    Obra,
    ObraAssunto,
    ObraAutor,
)


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

    def test_tombo_repetido_nao_cria_novo_registro(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Exemplar.objects.create(tombo="001", obra=self.obra)

        self.assertEqual(Exemplar.objects.filter(tombo="001").count(), 1)
        self.assertEqual(Exemplar.objects.count(), 1)

    def test_tombo_vazio_e_rejeitado_pela_validacao(self):
        exemplar = Exemplar(tombo="", obra=self.obra)

        with self.assertRaises(ValidationError) as contexto:
            exemplar.full_clean()

        self.assertIn("tombo", contexto.exception.message_dict)


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


class ReconhecimentoDosModelsTests(TestCase):
    TABELAS = {
        "Autor": "autor",
        "Editora": "editora",
        "Assunto": "assunto",
        "Localizacao": "localizacao",
        "Obra": "obra",
        "ObraAutor": "obra_autor",
        "ObraAssunto": "obra_assunto",
        "Exemplar": "exemplar",
        "LogAcervo": "log_acervo",
    }

    def test_models_do_acervo_estao_registrados_com_a_tabela_esperada(self):
        for nome, tabela in self.TABELAS.items():
            with self.subTest(model=nome):
                model = apps.get_model("acervo", nome)
                self.assertEqual(model._meta.db_table, tabela)

    def test_model_de_usuario_esta_registrado(self):
        model = apps.get_model("usuarios", "Usuario")

        self.assertIs(model, get_user_model())

    def test_tabelas_existem_no_banco(self):
        tabelas = set(connection.introspection.table_names())

        self.assertTrue(set(self.TABELAS.values()) <= tabelas)
        self.assertIn(get_user_model()._meta.db_table, tabelas)


class RelacionamentosObrigatoriosTests(TestCase):
    def test_exemplar_exige_obra(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Exemplar.objects.create(tombo="001")

    def test_associativas_exigem_obra_e_autor_ou_assunto(self):
        obra = Obra.objects.create(titulo="Dom Casmurro")
        autor = Autor.objects.create(nome="Machado de Assis")
        assunto = Assunto.objects.create(termo="Romance")

        with self.assertRaises(IntegrityError), transaction.atomic():
            ObraAutor.objects.create(autor=autor)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ObraAutor.objects.create(obra=obra)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ObraAssunto.objects.create(assunto=assunto)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ObraAssunto.objects.create(obra=obra)

    def test_log_exige_usuario(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            LogAcervo.objects.create(entidade="obra", entidade_id=1, acao="CRIAR")

    def test_autor_vinculado_a_obra_nao_pode_ser_excluido(self):
        obra = Obra.objects.create(titulo="Dom Casmurro")
        autor = Autor.objects.create(nome="Machado de Assis")
        ObraAutor.objects.create(obra=obra, autor=autor)

        with self.assertRaises(ProtectedError):
            autor.delete()

    def test_assunto_vinculado_a_obra_nao_pode_ser_excluido(self):
        obra = Obra.objects.create(titulo="Dom Casmurro")
        assunto = Assunto.objects.create(termo="Romance")
        ObraAssunto.objects.create(obra=obra, assunto=assunto)

        with self.assertRaises(ProtectedError):
            assunto.delete()

    def test_usuario_com_log_nao_pode_ser_excluido(self):
        usuario = get_user_model().objects.create_user(
            email="ana@exemplo.com", password="x", name="Ana"
        )
        LogAcervo.objects.create(usuario=usuario, entidade="obra", entidade_id=1, acao="CRIAR")

        with self.assertRaises(ProtectedError):
            usuario.delete()


class RelacionamentosOpcionaisTests(TestCase):
    def test_exemplar_pode_ficar_sem_localizacao(self):
        obra = Obra.objects.create(titulo="Dom Casmurro")

        exemplar = Exemplar.objects.create(tombo="001", obra=obra)
        exemplar.refresh_from_db()

        self.assertIsNone(exemplar.localizacao)

    def test_exemplar_com_localizacao_e_consultado_pela_localizacao(self):
        obra = Obra.objects.create(titulo="Dom Casmurro")
        localizacao = Localizacao.objects.create(setor="A", estante="3", prateleira="2")

        exemplar = Exemplar.objects.create(tombo="001", obra=obra, localizacao=localizacao)

        self.assertEqual(exemplar.localizacao, localizacao)
        self.assertEqual(list(localizacao.exemplares.all()), [exemplar])

    def test_obra_sem_autores_e_assuntos(self):
        obra = Obra.objects.create(titulo="Dom Casmurro")

        self.assertEqual(obra.autores.count(), 0)
        self.assertEqual(obra.assuntos.count(), 0)
        self.assertEqual(obra.exemplares.count(), 0)


class ConsultasManyToManyTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo="Dom Casmurro")
        self.machado = Autor.objects.create(nome="Machado de Assis")
        self.outro = Autor.objects.create(nome="Outro Autor")
        self.romance = Assunto.objects.create(termo="Romance")
        ObraAutor.objects.create(obra=self.obra, autor=self.machado, papel="autor", ordem=1)
        ObraAutor.objects.create(obra=self.obra, autor=self.outro, papel="tradutor", ordem=2)
        ObraAssunto.objects.create(obra=self.obra, assunto=self.romance)

    def test_obra_consulta_autores_pela_associativa(self):
        self.assertCountEqual(self.obra.autores.all(), [self.machado, self.outro])

    def test_obra_consulta_assuntos_pela_associativa(self):
        self.assertEqual(list(self.obra.assuntos.all()), [self.romance])

    def test_assunto_consulta_obras(self):
        self.assertEqual(list(self.romance.obras.all()), [self.obra])

    def test_dados_extras_ficam_na_associativa(self):
        vinculo = ObraAutor.objects.get(obra=self.obra, autor=self.outro)

        self.assertEqual(vinculo.papel, "tradutor")
        self.assertEqual(vinculo.ordem, 2)

    def test_filtro_atravessa_a_associativa(self):
        obras = Obra.objects.filter(autores__nome="Machado de Assis")

        self.assertEqual(list(obras), [self.obra])

    def test_excluir_obra_sem_exemplar_remove_os_vinculos(self):
        # Comportamento atual (CASCADE nas associativas); a politica ainda depende de decisao da equipe
        self.obra.delete()

        self.assertEqual(ObraAutor.objects.count(), 0)
        self.assertEqual(ObraAssunto.objects.count(), 0)
        self.assertTrue(Autor.objects.filter(pk=self.machado.pk).exists())


class PersistenciaRelacionadaTests(TestCase):
    def test_registros_relacionados_sao_relidos_do_banco(self):
        editora = Editora.objects.create(nome="Editora Teste")
        localizacao = Localizacao.objects.create(setor="A")
        obra = Obra.objects.create(titulo="Dom Casmurro", editora=editora)
        Exemplar.objects.create(tombo="001", obra=obra, localizacao=localizacao)

        exemplar = Exemplar.objects.select_related("obra__editora", "localizacao").get(tombo="001")

        self.assertEqual(exemplar.obra.titulo, "Dom Casmurro")
        self.assertEqual(exemplar.obra.editora.nome, "Editora Teste")
        self.assertEqual(exemplar.localizacao.setor, "A")
        self.assertEqual(list(obra.exemplares.all()), [exemplar])

    def test_log_guarda_usuario_e_json(self):
        usuario = get_user_model().objects.create_user(
            email="ana@exemplo.com", password="x", name="Ana"
        )

        log = LogAcervo.objects.create(
            usuario=usuario,
            entidade="obra",
            entidade_id=1,
            acao="ATUALIZAR",
            dados_anteriores={"titulo": "A"},
            dados_novos={"titulo": "B"},
        )
        log.refresh_from_db()

        self.assertEqual(log.usuario, usuario)
        self.assertEqual(log.dados_novos, {"titulo": "B"})
        self.assertEqual(list(usuario.logs_acervo.all()), [log])


class CamposObrigatoriosTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo="Dom Casmurro")

    def test_obra_exige_titulo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Obra.objects.create(titulo=None)

    def test_titulo_vazio_e_rejeitado_pela_validacao(self):
        with self.assertRaises(ValidationError) as contexto:
            Obra(titulo="").full_clean()

        self.assertIn("titulo", contexto.exception.message_dict)

    def test_exemplar_exige_tombo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Exemplar.objects.create(tombo=None, obra=self.obra)

    def test_exemplar_exige_situacao(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Exemplar.objects.create(tombo="001", obra=self.obra, situacao=None)

    def test_autor_editora_e_assunto_exigem_nome_ou_termo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Autor.objects.create(nome=None)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Editora.objects.create(nome=None)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Assunto.objects.create(termo=None)

    def test_log_exige_entidade_id_e_acao(self):
        usuario = get_user_model().objects.create_user(
            email="ana@exemplo.com", password="x", name="Ana"
        )

        for campo in ("entidade", "entidade_id", "acao"):
            with self.subTest(campo=campo):
                dados = {"usuario": usuario, "entidade": "obra", "entidade_id": 1, "acao": "CRIAR"}
                dados[campo] = None
                with self.assertRaises(IntegrityError), transaction.atomic():
                    LogAcervo.objects.create(**dados)

    def test_campos_opcionais_aceitam_nulo(self):
        obra = Obra.objects.create(titulo="Minimo")
        obra.refresh_from_db()

        self.assertIsNone(obra.subtitulo)
        self.assertIsNone(obra.isbn)
        self.assertIsNone(obra.ano_publicacao)


class AssuntoTermoTests(TestCase):
    def test_banco_rejeita_termo_repetido(self):
        Assunto.objects.create(termo="Romance")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Assunto.objects.create(termo="Romance")

        self.assertEqual(Assunto.objects.count(), 1)

    def test_validacao_do_model_rejeita_termo_repetido(self):
        Assunto.objects.create(termo="Romance")

        with self.assertRaises(ValidationError) as contexto:
            Assunto(termo="Romance").full_clean()

        self.assertIn("termo", contexto.exception.message_dict)

    def test_termos_diferentes_sao_aceitos(self):
        Assunto.objects.create(termo="Romance")
        Assunto.objects.create(termo="Poesia")

        self.assertEqual(Assunto.objects.count(), 2)


class ValoresPadraoTests(TestCase):
    def setUp(self):
        self.obra = Obra.objects.create(titulo="Dom Casmurro")

    def test_exemplar_usa_valores_padrao(self):
        exemplar = Exemplar.objects.create(tombo="001", obra=self.obra)
        exemplar.refresh_from_db()

        self.assertEqual(exemplar.situacao, "DISPONIVEL")
        self.assertTrue(exemplar.ativo)
        self.assertTrue(exemplar.emprestavel)
        self.assertIsNone(exemplar.data_aquisicao)

    def test_exemplar_preenche_timestamps(self):
        exemplar = Exemplar.objects.create(tombo="001", obra=self.obra)

        self.assertIsNotNone(exemplar.criado_em)
        self.assertIsNotNone(exemplar.atualizado_em)

    def test_obra_preenche_timestamps(self):
        self.assertIsNotNone(self.obra.criado_em)
        self.assertIsNotNone(self.obra.atualizado_em)

    def test_atualizado_em_muda_e_criado_em_permanece_ao_salvar(self):
        criado_em = self.obra.criado_em
        atualizado_em = self.obra.atualizado_em

        self.obra.titulo = "Dom Casmurro (2a edicao)"
        self.obra.save()
        self.obra.refresh_from_db()

        self.assertEqual(self.obra.criado_em, criado_em)
        self.assertGreater(self.obra.atualizado_em, atualizado_em)

    def test_log_preenche_ocorrido_em(self):
        usuario = get_user_model().objects.create_user(
            email="ana@exemplo.com", password="x", name="Ana"
        )

        log = LogAcervo.objects.create(usuario=usuario, entidade="obra", entidade_id=1, acao="CRIAR")

        self.assertIsNotNone(log.ocorrido_em)


class CriacaoDeEntidadesTests(TestCase):
    def test_criacao_e_leitura_de_autor(self):
        autor = Autor.objects.create(nome="Graciliano Ramos")
        autor_lido = Autor.objects.get(pk=autor.pk)

        self.assertEqual(autor_lido.nome, "Graciliano Ramos")

    def test_criacao_e_leitura_de_editora(self):
        editora = Editora.objects.create(nome="Companhia das Letras")
        editora_lida = Editora.objects.get(pk=editora.pk)

        self.assertEqual(editora_lida.nome, "Companhia das Letras")

    def test_criacao_e_leitura_de_obra(self):
        obra = Obra.objects.create(titulo="Vidas Secas", ano_publicacao=1938)
        obra_lida = Obra.objects.get(pk=obra.pk)

        self.assertEqual(obra_lida.titulo, "Vidas Secas")
        self.assertEqual(obra_lida.ano_publicacao, 1938)

    def test_criacao_e_leitura_de_localizacao(self):
        localizacao = Localizacao.objects.create(setor="B", estante="4", prateleira="1")
        localizacao_lida = Localizacao.objects.get(pk=localizacao.pk)

        self.assertEqual(localizacao_lida.setor, "B")
        self.assertEqual(localizacao_lida.estante, "4")
        self.assertEqual(localizacao_lida.prateleira, "1")

    def test_criacao_e_leitura_de_exemplar(self):
        obra = Obra.objects.create(titulo="Vidas Secas")
        exemplar = Exemplar.objects.create(tombo="TOMBO-100", obra=obra)
        exemplar_lido = Exemplar.objects.get(tombo="TOMBO-100")

        self.assertEqual(exemplar_lido.obra, obra)
        self.assertEqual(exemplar_lido.situacao, "DISPONIVEL")

    def test_atualizacao_de_campos_de_registro(self):
        autor = Autor.objects.create(nome="Nome Antigo")
        autor.nome = "Nome Atualizado"
        autor.save()
        autor.refresh_from_db()

        self.assertEqual(autor.nome, "Nome Atualizado")
