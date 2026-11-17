from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.utils import timezone
from zoneinfo import ZoneInfo


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


class LoginHistoryDateTimeField(models.DateTimeField):
    def get_db_prep_value(self, value, connection, prepared=False):
        if not prepared:
            value = self.get_prep_value(value)
        if value is not None and timezone.is_aware(value):
            value = timezone.make_naive(value, ZoneInfo(settings.LOGIN_HISTORY_TIME_ZONE))
        return connection.ops.adapt_datetimefield_value(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        if timezone.is_aware(value):
            value = timezone.make_naive(value, connection.timezone)
        return timezone.make_aware(value, ZoneInfo(settings.LOGIN_HISTORY_TIME_ZONE))


class LoginUserHistory(models.Model):
    login_history_id = models.BigAutoField(primary_key=True, db_column="LoginHistoryId")
    user = models.ForeignKey(CredentialManager, db_column="UserId", null=True, on_delete=models.DO_NOTHING)
    role = models.ForeignKey(UserRoleMaster, db_column="RoleId", null=True, on_delete=models.DO_NOTHING)
    login_time = LoginHistoryDateTimeField(db_column="LoginTime", null=True)
    logout_time = LoginHistoryDateTimeField(db_column="LogoutTime", null=True)
    ip_address = models.TextField(db_column="IP", null=True)
    session_history = models.TextField(db_column="SessionHistory", null=True)

    class Meta:
        managed = False
        db_table = "T_LoginUser_History"


class ModuleMaster(models.Model):
    module_id = models.BigAutoField(primary_key=True, db_column="ModuleId")
    module_name = models.CharField(max_length=500, db_column="ModuleName", null=True)
    sequence = models.IntegerField(db_column="Sequence", null=True)
    icon = models.CharField(max_length=100, db_column="icon", null=True, blank=True)
    color = models.CharField(max_length=100, db_column="color", null=True, blank=True)
    admin_only = models.BooleanField(db_column="admin_only", null=True)

    class Meta:
        managed = False
        db_table = "T_Modules_Master"


class MenuMaster(models.Model):
    menu_id = models.BigAutoField(primary_key=True, db_column="MenuId")
    module_id = models.BigIntegerField(db_column="ModuleId", null=True)
    menu_name = models.CharField(max_length=500, db_column="MenuName", null=True)
    sequence = models.IntegerField(db_column="Sequence", null=True)
    url = models.CharField(max_length=2048, db_column="_URL_", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "T_Menu_Master"


class UserAccess(models.Model):
    access_id = models.BigAutoField(primary_key=True, db_column="AccessId")
    user_id = models.BigIntegerField(db_column="UserId", null=True)
    menu_id = models.BigIntegerField(db_column="MenuId", null=True)

    class Meta:
        managed = False
        db_table = "T_User_Access"


class MasterTableMapper(models.Model):
    mapper_id = models.BigAutoField(primary_key=True, db_column="MapperId")
    master_data_name = models.CharField(max_length=1000, db_column="MasterDataName", null=True)
    database_table_name = models.TextField(db_column="DB_TableName", null=True)
    mapped_by = models.BigIntegerField(db_column="MapedBy", null=True)
    map_date = LoginHistoryDateTimeField(db_column="MapDate", null=True)
    editable_columns = models.TextField(db_column="EditableColJSON", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "T_MasterTable_Mapper"


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
    multiple_tables = models.BooleanField(default=False)
    external_records_enabled = models.BooleanField(default=False)

    class Meta:
        db_table = "master_mapping"
        ordering = ["name"]

    def __str__(self):
        return self.name


class MasterMappingTable(models.Model):
    mapping = models.ForeignKey(MasterMapping, on_delete=models.CASCADE, related_name="mapped_tables")
    table_name = models.CharField(max_length=300)
    external_mapper_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = "master_mapping_table"
        ordering = ["table_name"]
        constraints = [models.UniqueConstraint(fields=["mapping", "table_name"], name="unique_master_mapping_table")]

    def __str__(self):
        return self.table_name


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