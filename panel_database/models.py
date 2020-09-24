from django.db import models

# Create your models here.


class Test(models.Model):
    r_id = models.CharField()
    name = models.CharField()
    method = models.CharField()
    version = models.CharField()


class TestPanel(models.Model):
    test_id = models.ForeignKey(Test, on_delete=models.DO_NOTHING)
    panel_id = models.ForeignKey("Panel", on_delete=models.DO_NOTHING)


class Panel(models.Model):
    name = models.CharField()
    version = models.CharField()
    signedoff = models.CharField()


class PanelStr(models.Model):
    panel_id = models.ForeignKey(Panel, on_delete=models.DO_NOTHING)
    str_id = models.ForeignKey("Str", on_delete=models.DO_NOTHING)


class Str(models.Model):
    nb_repeats = models.IntegerField()
    nb_pathogenic_repeats = models.IntegerField()
    region_id = models.ForeignKey("Region", on_delete=models.DO_NOTHING)


class PanelCnv(models.Model):
    panel_id = models.ForeignKey(Panel, on_delete=models.DO_NOTHING)
    cnv_id = models.ForeignKey("Cnv", on_delete=models.DO_NOTHING)


class Cnv(models.Model):
    choices = (
        ("Gain", "Gain"),
        ("Loss", "Loss")
    )

    variant_type = models.CharField(choices=choices)
    region_id = models.ForeignKey("Region", on_delete=models.DO_NOTHING)


class PanelGene(models.Model):
    panel_id = models.ForeignKey(Panel, on_delete=models.DO_NOTHING)
    gene_id = models.ForeignKey("Gene", on_delete=models.DO_NOTHING)


class Gene(models.Model):
    symbol = models.CharField()
    clinical_transcript = models.ForeignKey(
        "Transcript", on_delete=models.DO_NOTHING
    )


class Transcript(models.Model):
    refseq = models.CharField()
    version = models.CharField()
    gene = models.ForeignKey(Gene, on_delete=models.DO_NOTHING)


class Exon(models.Model):
    number = models.IntegerField()
    transcript_id = models.ForeignKey(Transcript, on_delete=models.DO_NOTHING)
    region_id = models.ForeignKey("Region", on_delete=models.DO_NOTHING)


class Region(models.Model):
    choices = [(f"{i}", f"{i}") for i in range(1, 23)]
    choices.append(("X", "X"))
    choices.append(("Y", "Y"))
    choices = tuple(choices)

    chrom = models.CharField(choices=choices)
    start = models.IntegerField()
    end = models.IntegerField()
    build = models.ForeignKey("Reference", on_delete=models.DO_NOTHING)


class Reference(models.Model):
    build = models.CharField()
