from django.db import models
from datetime import datetime


class Company(models.Model):
    """
    Model representing a company in the database

    Atributes:
        name: Name of company
        industry: Industry of company
        country: Location of company (country)
        city: Location of company (city)
        year: Year Founded
        proj_ebitda: Annual EBITDA of Project
        company_ebitda: Annual Company EBITDA
        value: Enterprise Value
        risk: Risk Appetite
        date: Date this information was uploaded
        on_hand: Current inventory units immediately available
        safety_stock: Buffer stock level maintained to mitigate stockouts
        reoder_points: Inventory level threshold that triggers a new purchase order
        order_backlog: Number of customer orders received but not yet fulfilled
        production_schedule: Planned output or manufacturing volume for a given period
        supplier_concentration: Measure of dependency on specific suppliers
        lead_time_sensitivity: Impact level of supply delays on business operations
    """
    name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    year = models.IntegerField("year founded")
    proj_ebitda = models.FloatField("annual project EBITDA")
    company_ebitda = models.FloatField("annual company EBITDA")
    value = models.FloatField()
    risk = models.FloatField()
    time = models.DateTimeField("time uploaded", default=datetime.now())
    on_hand = models.IntegerField("On-Hand Inventory")
    safety_stock = models.IntegerField("Safety Stock Levels")
    reorder_points = models.IntegerField("Reorder Points")
    order_backlog = models.IntegerField("Order Backlog")
    production_schedule = models.IntegerField("Production Schedule")
    supplier_concentration = models.IntegerField("Supplier Concentration")
    lead_time_sensitivity = models.IntegerField("Lead-Time Sensitivity")

    def __str__(self):
        data = {
            "name": self.name,
            "industry": self.industry,
            "country": self.country,
            "city": self.city,
            "year": self.year,
            "project EBITDA": self.proj_ebitda,
            "company EBITDA": self.company_ebitda,
            "value": self.value,
            "risk": self.risk,
            "time": self.time,
            "On-Hand Inventory": self.on_hand,
            "Safety Stock Levels": self.safety_stock,
            "Reorder Points": self.reorder_points,
            "Order Backlog": self.order_backlog,
            "Production Schedule": self.production_schedule,
            "Supplier Concentration": self.supplier_concentration,
            "Lead-Time Sensitivity": self.order_backlog
        }
        return "ID: " + str(self.id) + ", Uploaded: " + str(data["time"])


class Response(models.Model):
    response_text = models.TextField()
    company = models.OneToOneField(Company, on_delete=models.CASCADE)
    date = models.DateTimeField("time generated")

    def __str__(self):
        return self.response_text
