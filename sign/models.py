from django.db import models

# Create your models here.
from django.core.files.storage import FileSystemStorage

# fs = FileSystemStorage(location='/case')


class apis(models.Model):
    id = models.AutoField('ID', max_length=5, primary_key=True)
    address = models.URLField('URL', max_length=100)
    name = models.CharField('接口名称', max_length=20)
    method = models.CharField(max_length=10, choices=(('POST','POST'), ('GET', 'GET')), default='POST')
    params = models.TextField(max_length=500)
    create_time = models.DateTimeField('创建时间', auto_now=True)
    status = models.BooleanField('状态')
    files = models.FileField('测试文件-Excel', upload_to='./case', default='无')

    class Meta:
        verbose_name = "接口列表"
        verbose_name_plural = "接口列表"

    def __str__(self):
        return self.name

