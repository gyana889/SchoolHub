from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models


class UserRoleMaster(models.Model):
    role_id = models.BigAutoField(primary_key=True, db_column="RoleId")
    role_name = models.CharField(max_length=100, db_column="RoleName", null=True)
    status = models.BooleanField(db_column="Status", null=True)

    class Meta:
        managed = False
        db_table = "T_UserRole_Master"
        ordering = ["role_id"]

    def __str__(self):
        return self.role_name or ""


class CredentialManager(models.Model):
    user_id = models.BigAutoField(primary_key=True, db_column="UserId")
    role = models.ForeignKey(UserRoleMaster, db_column="RoleId", null=True, on_delete=models.DO_NOTHING, related_name="credentials")
    username = models.CharField(max_length=100, db_column="UserName", null=True)
    password = models.TextField(db_column="Password", null=True)
    status = models.BooleanField(db_column="Status", null=True)

    class Meta:
        managed = False
        db_table = "T_Credential_Manager"

    def __str__(self):
        return self.username or ""


class Menu(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    short = models.CharField(max_length=100)
    icon = models.CharField(max_length=50)
    description = models.CharField(max_length=240)
    color = models.CharField(max_length=20, default="mint")
    position = models.PositiveIntegerField(default=0)
    admin_only = models.BooleanField(default=False)
    roles = models.ManyToManyField(Group, blank=True, related_name="portal_menus")

    class Meta:
        db_table = "portal_menu"
        ordering = ["position", "name"]

    def __str__(self):
        return self.name


class SubMenu(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="submenus")
    slug = models.SlugField()
    name = models.CharField(max_length=100)
    path = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=0)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="portal_submenus")

    class Meta:
        db_table = "portal_submenu"
        ordering = ["position", "name"]
        constraints = [models.UniqueConstraint(fields=["menu", "slug"], name="unique_menu_submenu_slug")]

    def __str__(self):
        return f"{self.menu.name} / {self.name}"


class MasterMapping(models.Model):
    COUNTRY = "country"
    STATE = "state"
    CITY = "city"
    GENERIC = "generic"
    TABLE_CHOICES = [
        (COUNTRY, "Countries"),
        (STATE, "States"),
        (CITY, "Cities"),
        (GENERIC, "Other master values"),
    ]

    name = models.CharField(max_length=100, unique=True)
    table_key = models.CharField(max_length=20, choices=TABLE_CHOICES)

    class Meta:
        db_table = "master_mapping"
        ordering = ["name"]

    def clean(self):
        super().clean()
        if self.table_key != self.GENERIC and MasterMapping.objects.filter(table_key=self.table_key).exclude(pk=self.pk).exists():
            raise ValidationError({"table_key": "This table is already mapped to a master name."})
        if self.pk:
            original = MasterMapping.objects.get(pk=self.pk)
            if original.table_key != self.table_key:
                raise ValidationError({"table_key": "The table cannot be changed after a mapping is created."})

    def __str__(self):
        return self.name


class Country(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)

    class Meta:
        db_table = "master_country"
        ordering = ["name", "code"]
        verbose_name_plural = "countries"

    def __str__(self):
        return f"{self.name} ({self.code})"


class State(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="states")

    class Meta:
        db_table = "master_state"
        ordering = ["name", "code"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class City(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="cities")

    class Meta:
        db_table = "master_city"
        ordering = ["name", "code"]
        verbose_name_plural = "cities"

    def __str__(self):
        return f"{self.name} ({self.code})"


class MasterValue(models.Model):
    mapping = models.ForeignKey(MasterMapping, on_delete=models.PROTECT, related_name="values")
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=120)

    class Meta:
        db_table = "master_value"
        ordering = ["name", "code"]
        constraints = [models.UniqueConstraint(fields=["mapping", "code"], name="unique_master_value_code")]

    def __str__(self):
        return f"{self.name} ({self.code})"