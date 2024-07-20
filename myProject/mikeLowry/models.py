from django.db import models

class Stock(models.Model):
    date = models.DateField()
    closing_price = models.FloatField()
    signal = models.CharField(max_length=4)  # 'buy' or 'sell'

    def __str__(self):
        return f"{self.date} - {self.closing_price} - {self.signal}"
