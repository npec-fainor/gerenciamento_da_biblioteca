from django.db import models
from django.conf import settings

class Autor(models.Model):
    nome = models.CharField(max_length=255)

    class Meta:
        db_table = "autor"

    def __str__(self):
        return self.nome
    
class Editora(models.Model):
    nome = models.CharField(max_length=255)

    class Meta:
        db_table = "editora"

    def __str__(self):
        return self.nome
    
class Assunto(models.Model):
    termo = models.CharField(max_length=225, unique=True)

    class Meta:
        db_table = "assunto"

    def __str__(self):
        return self.termo

class Localizacao(models.Model):
    setor = models.CharField(max_length=100, blank=True, null=True)
    estante = models.CharField(max_length=100, blank=True, null=True)
    prateleira = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "localizacao"
        verbose_name_plural = "localizações"

    def __str__(self):
        # Todos os campos sao opcionais, entao ignora os que nao foram preenchidos
        partes = [self.setor, self.estante, self.prateleira]
        return "/".join(parte for parte in partes if parte)

class Obra(models.Model):
    titulo = models.CharField(max_length=225)
    subtitulo = models.CharField(max_length=225, blank=True, null=True)
    isbn = models.CharField(max_length=20, blank=True, null=True)
    edicao = models.CharField(max_length=50, blank=True, null=True)
    ano_publicacao = models.IntegerField(blank=True, null=True)
    volume = models.CharField(max_length=50, blank=True, null=True)
    editora = models.ForeignKey(
        Editora, on_delete=models.PROTECT, blank=True, null=True, related_name="obras"
    )
    classificacao = models.CharField(max_length=50, blank=True, null=True)
    cutter = models.CharField(max_length=50, blank=True, null=True)
    tipo_material = models.CharField(max_length=50, blank=True, null=True)
    capa_url = models.CharField(max_length=500, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    autores = models.ManyToManyField(Autor, through="ObraAutor", related_name="obras")
    assuntos = models.ManyToManyField(Assunto, through="ObraAssunto", related_name="obras")

    class Meta:
        db_table = "obra"

    def __str__(self):
        return self.titulo

class ObraAutor(models.Model):
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE)
    autor = models.ForeignKey(Autor, on_delete=models.PROTECT)
    papel = models.CharField(max_length=50, blank=True, null=True)
    ordem = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "obra_autor"
        constraints = [
            models.UniqueConstraint(fields=["obra", "autor"], name="uq_obra_autor")
        ]

class ObraAssunto(models.Model):
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE)
    assunto = models.ForeignKey(Assunto, on_delete=models.PROTECT)

    class Meta:
        db_table = "obra_assunto"
        constraints = [
            models.UniqueConstraint(fields=["obra", "assunto"], name="uq_obra_assunto"),
        ]

class Exemplar(models.Model):
    tombo = models.CharField(max_length=50, unique=True) 
    obra = models.ForeignKey(Obra, on_delete=models.PROTECT, related_name="exemplares")
    localizacao = models.ForeignKey(
        Localizacao, on_delete=models.SET_NULL, blank=True, null=True, related_name="exemplares"
    )
    situacao = models.CharField(max_length=30, default="DISPONIVEL")
    ativo = models.BooleanField(default=True)
    emprestavel = models.BooleanField(default=True)
    data_aquisicao = models.DateField(blank=True, null=True)
    origem = models.CharField(max_length=100, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "exemplar"
        verbose_name_plural = "exemplares"

    def __str__(self):
        return self.tombo


class LogAcervo(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="logs_acervo"
    )
    entidade = models.CharField(max_length=50)
    entidade_id = models.IntegerField()
    acao = models.CharField(max_length=30)
    dados_anteriores = models.JSONField(blank=True, null=True)
    dados_novos = models.JSONField(blank=True, null=True)
    ocorrido_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "log_acervo"