use SchoolHub
select * from T_UserRole_Master

create table T_UserRole_Master
(
	RoleId bigint identity(1,1) constraint pk_T_UserRole_Master primary key,
	RoleName varchar(100),
	RoleShortName varchar(5),
	Status bit,
	CreatedDt datetime,
	CreatedBy bigint,
	CreatedIP nvarchar(max)
)

create table T_Credential_Manager
(
	UserId bigint identity(1,1) constraint pk_T_Credential_Manager primary key,
	RoleId bigint constraint fk_T_Credential_Manager_RoleId foreign key references T_UserRole_Master(RoleId),
	UserName varchar(100),
	Password nvarchar(max),
	Status bit,
	CreatedDt datetime,
	CreatedBy bigint,
	CreatedIP nvarchar(max)
)

insert into T_Credential_Manager(RoleId,UserName,Password,Status,CreatedDt, CreatedBy,CreatedIP) values (12,'admin','admin',1,getdate(),1,'::1')

create table T_Credential_Update_History
(
	CredUpdateId bigint identity(1,1) constraint pk_T_Credential_Update_History primary key,
	UserId bigint constraint fk_T_Credential_Update_History_UserId foreign key references T_Credential_Manager(UserId),	
	UpdateType varchar(100),--Update/Delete
	UserName varchar(100),
	ExistingPassword nvarchar(max),
	UpdatedPassword nvarchar(max),
	UpdatedDt datetime,
	UpdatedBy bigint,
	UpdatedIP  nvarchar(max)
)

create table T_LoginUser_History
(
	LoginHistoryId bigint identity(1,1) constraint pk_T_LoginUser_History primary key,	
	UserId bigint constraint fk_T_LoginUser_History foreign key references T_Credential_Manager(UserId),
	RoleId bigint constraint fk_T_LoginUser_History_RoleId foreign key references T_UserRole_Master(RoleId),
	LoginTime datetime,
	LogoutTime datetime,
	IP varchar(max),
	SessionHistory varchar(max)
)

insert into T_UserRole_Master(RoleName,RoleShortName,Status,CreatedDt,CreatedBy,CreatedIP) values ('Super Admin','SA',1,GETDATE(),1,'::1')
insert into T_UserRole_Master(RoleName,RoleShortName,Status,CreatedDt,CreatedBy,CreatedIP) values ('Admin','A',1,GETDATE(),1,'::1')
insert into T_UserRole_Master(RoleName,RoleShortName,Status,CreatedDt,CreatedBy,CreatedIP) values ('Teacher','T',1,GETDATE(),1,'::1')
insert into T_UserRole_Master(RoleName,RoleShortName,Status,CreatedDt,CreatedBy,CreatedIP) values ('Staff','ST',1,GETDATE(),1,'::1')
insert into T_UserRole_Master(RoleName,RoleShortName,Status,CreatedDt,CreatedBy,CreatedIP) values ('Student','S',1,GETDATE(),1,'::1')
insert into T_UserRole_Master(RoleName,RoleShortName,Status,CreatedDt,CreatedBy,CreatedIP) values ('Parent','P',1,GETDATE(),1,'::1')


select * from T_UserRole_Master