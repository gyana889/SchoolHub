use SchoolHub
select * from T_UserRole_Master

--create table T_UserRole_Master
--(
--	RoleId bigint identity(1,1) constraint pk_T_UserRole_Master primary key,
--	RoleName varchar(100),
--	RoleShortName varchar(5),
--	Status bit,
--	CreatedDt datetime,
--	CreatedBy bigint,
--	CreatedIP nvarchar(max)
--)

--create table T_Credential_Manager
--(
--	UserId bigint identity(1,1) constraint pk_T_Credential_Manager primary key,
--	RoleId bigint constraint fk_T_Credential_Manager_RoleId foreign key references T_UserRole_Master(RoleId),
--	UserName varchar(100),
--	Password nvarchar(max),
--	Status bit,
--	CreatedDt datetime,
--	CreatedBy bigint,
--	CreatedIP nvarchar(max)
--)

--create table T_Credential_Update_History
--(
--	CredUpdateId bigint identity(1,1) constraint pk_T_Credential_Update_History primary key,
--	UserId bigint constraint fk_T_Credential_Update_History_UserId foreign key references T_Credential_Manager(UserId),	
--	UpdateType varchar(100),--Update/Delete
--	UserName varchar(100),
--	ExistingPassword nvarchar(max),
--	UpdatedPassword nvarchar(max),
--	UpdatedDt datetime,
--	UpdatedBy bigint,
--	UpdatedIP  nvarchar(max)
--)

--create table T_LoginUser_History
--(
--	LoginHistoryId bigint identity(1,1) constraint pk_T_LoginUser_History primary key,	
--	UserId bigint constraint fk_T_LoginUser_History foreign key references T_Credential_Manager(UserId),
--	RoleId bigint constraint fk_T_LoginUser_History_RoleId foreign key references T_UserRole_Master(RoleId),
--	LoginTime datetime,
--	LogoutTime datetime,
--	IP varchar(max),
--	SessionHistory varchar(max)
--)

--insert into T_UserRole_Master(RoleName,RoleShortName,Status,CreatedDt,CreatedBy,CreatedIP) values ('Super Admin','SA',1,GETDATE(),1,'::1')
--insert into T_UserRole_Master(RoleName,RoleShortName,Status,CreatedDt,CreatedBy,CreatedIP) values ('Admin','A',1,GETDATE(),1,'::1')
--insert into T_UserRole_Master(RoleName,RoleShortName,Status,CreatedDt,CreatedBy,CreatedIP) values ('Teacher','T',1,GETDATE(),1,'::1')
--insert into T_UserRole_Master(RoleName,RoleShortName,Status,CreatedDt,CreatedBy,CreatedIP) values ('Staff','ST',1,GETDATE(),1,'::1')
--insert into T_UserRole_Master(RoleName,RoleShortName,Status,CreatedDt,CreatedBy,CreatedIP) values ('Student','S',1,GETDATE(),1,'::1')
--insert into T_UserRole_Master(RoleName,RoleShortName,Status,CreatedDt,CreatedBy,CreatedIP) values ('Parent','P',1,GETDATE(),1,'::1')


--insert into T_Credential_Manager(RoleId,UserName,Password,Status,CreatedDt, CreatedBy,CreatedIP) values (12,'admin','admin',1,getdate(),1,'::1')


--/****** Object:  Table [dbo].[T_Modules_Master]    Script Date: 10-12-2025 11:42:13 ******/
--SET ANSI_NULLS ON
--GO
--SET QUOTED_IDENTIFIER ON
--GO
--CREATE TABLE [dbo].[T_Modules_Master](
--	[ModuleId] [bigint] IDENTITY(1,1) NOT NULL,
--	[ModuleName] [varchar](500) NULL,
--	[Sequence] [int] NULL,
--	[CreatedBy] [bigint] NULL,
--	[CreatedDt] [datetime] NULL,
-- CONSTRAINT [pk_T_Modules_Master] PRIMARY KEY CLUSTERED 
--(
--	[ModuleId] ASC
--)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
--) ON [PRIMARY]
--GO

--/****** Object:  Table [dbo].[T_Menu_Master]    Script Date: 10-12-2025 11:42:13 ******/
--SET ANSI_NULLS ON
--GO
--SET QUOTED_IDENTIFIER ON
--GO
--CREATE TABLE [dbo].[T_Menu_Master](
--	[MenuId] [bigint] IDENTITY(1,1) NOT NULL,
--	[ModuleId] [bigint] NULL constraint fk_T_Menu_Master_ModuleId foreign key references [T_Modules_Master](ModuleId),
--	[MenuName] [varchar](500) NULL,
--	[Sequence] [int] NULL,
--	[CreatedBy] [bigint] NULL,
--	[CreatedDt] [datetime] NULL,
-- CONSTRAINT [pk_T_Menu_Master] PRIMARY KEY CLUSTERED 
--(
--	[MenuId] ASC
--)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
--) ON [PRIMARY]
--GO

--/****** Object:  Table [dbo].[T_Menu_Item]    Script Date: 10-12-2025 11:42:13 ******/
--SET ANSI_NULLS ON
--GO
--SET QUOTED_IDENTIFIER ON
--GO
--CREATE TABLE [dbo].[T_Menu_Item](
--	[MenuItemId] [bigint] IDENTITY(1,1) NOT NULL,
--	[MenuId] [bigint] NULL  constraint fk_T_Menu_Item_MenuId foreign key references [T_Menu_Master](MenuId),
--	[MenuItemName] [varchar](500) NULL,
--	[Sequence] [int] NULL,
--	[CreatedBy] [bigint] NULL,
--	[CreatedDt] [datetime] NULL,
-- CONSTRAINT [pk_T_Menu_Item] PRIMARY KEY CLUSTERED 
--(
--	[MenuItemId] ASC
--)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
--) ON [PRIMARY]
--GO


--create table T_MasterTable_Mapper
--(
--	MapperId bigint identity(1,1) constraint pk_T_MasterTable_Mapper primary key,
--	MasterDataName varchar(1000),
--	DB_TableName varchar(max),
--	MapedBy bigint,
--	MapDate datetime
--)

--alter table T_State_Master
--add CountryId numeric(18,0) constraint fk_T_State_Master_CountryId references T_Country_Master(CountryId), CreatedBy bigint, CreatedDt datetime

--alter table T_Country_Master
--add CreatedBy bigint, CreatedDt datetime

--create table T_City_Master
--(
--	CityId bigint identity(1,1) constraint pk_T_City_Master primary key,
--	CityName varchar(1000),
--	StateId numeric(18,0) constraint fk_T_City_Master_StateId references T_State_Master(StateId),
--	CreatedBy bigint, 
--	CreatedDt datetime
--)


--alter table T_MasterTable_Mapper
--add EditableColJSON nvarchar(max)

--update T_Country_Master set CreatedBy = 1, CreatedDt = GETDATE()
--update T_State_Master set CreatedBy = 1, CreatedDt = GETDATE(), CountryId = 1

--create table T_User_Access
--(
--	AccessId bigint identity(1,1) constraint pk_T_User_Access primary key,	
--	UserId bigint constraint fk_T_User_Access_UserId foreign key references T_Credential_Manager(UserId),
--	MenuId bigint constraint fk_T_User_Access_MenuId foreign key references T_Menu_Master(MenuId),
--	CreatedBy bigint,
--	CreatedDt datetime
--)

--alter table T_Menu_Master
--add _URL_ varchar(1000)

--update T_Menu_Master set _URL_ = '/dashboard/master-data/' where MenuName = 'Master records'
--update T_Menu_Master set _URL_ = '/dashboard/master-data/mappings/' where MenuName = 'Table mappings'
--update T_Menu_Master set _URL_ = '/dashboard/access-control/role-module-mapping/' where MenuName = 'Role Module Mapping'
--update T_Menu_Master set _URL_ = '/dashboard/access-control/user-menu-access/' where MenuName = 'User-menu mapping'
--update T_Menu_Master set _URL_ = '/dashboard/access-control/credential-manager/' where MenuName = 'Change Password'


--update T_Modules_Master set icon='database',color='mint',admin_only=0 where ModuleName='Master Data'
--update T_Modules_Master set icon='shield-check',color='blue',admin_only=1 where ModuleName='Access Control'
--update T_Modules_Master set icon='graduation-cap',color='mint',admin_only=0 where ModuleName='Students'
--update T_Modules_Master set icon='contact-round',color='peach',admin_only=0 where ModuleName='Staff'
--update T_Modules_Master set icon='calendar-check-2',color='yellow',admin_only=0 where ModuleName='Attendance'
--update T_Modules_Master set icon='clipboard-list',color='lavender',admin_only=0 where ModuleName='Examination'
--update T_Modules_Master set icon='book-open',color='blue',admin_only=0 where ModuleName='Libray'
--update T_Modules_Master set icon='wallet-cards',color='coral',admin_only=0 where ModuleName='Fees & Payment'
--update T_Modules_Master set icon='badge-dollar-sign',color='mint',admin_only=0 where ModuleName='Payroll'
--update T_Modules_Master set icon='boxes',color='yellow',admin_only=0 where ModuleName='Inventory'
--update T_Modules_Master set icon='receipt-text',color='lavender',admin_only=0 where ModuleName='Tax'

--create table T_Role_Module_Mapping
--(
--	RoleModuleMappingId bigint identity(1,1) constraint pk_T_Role_Module_Mapping primary key,
--	ModuleId bigint constraint fk_T_Role_Module_Mapping_ModuleId foreign key references T_Modules_Master(ModuleId),
--	RoleId bigint constraint fk_T_Role_Module_Mapping_RoleId  foreign key references T_UserRole_Master(RoleId),
--	MappedBy bigint,
--	MappedDt datetime,
--	MappedIP nvarchar(200)
--)

--alter table T_Credential_Manager
--add MobileNo varchar(20), EmailId varchar(200)

select * from portal_menu 
select * from T_Modules_Master
select * from portal_menu_roles 
select * from T_Credential_Manager
select * from auth_user



select * from T_LoginUser_History
select * from T_Modules_Master
select * from T_Credential_Manager





select * from T_menu_Item
select * from T_MasterTable_Mapper

select * from user_registry
select * from T_User_Access


select * from user_registry_config where reg_module  = 'Student_Management'

select * from T_State_Master


select * from T_Country_Master

select * from INFORMATION_SCHEMA.COLUMNS where TABLE_NAME = 'T_Country_Master'

select * from V_Students order by ScholarNo desc

select * from T_Student_Update_Details

--changes: 

--1. During student registration, it should also allow to add blood group, PEN No., Adhar No.
--2. As there are more than 50 fields to edit, so I don't want to show all the fields in editable mode, when they only need few fields to edit. So there should be a dynamic edit option where user can select which field they want to edit and my edit page should only show those fields. Scholar no and Name should appear in every edit field to identify the student.