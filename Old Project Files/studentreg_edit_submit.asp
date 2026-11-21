<!--#include virtual="/asp_lib/DbConnect.asp"-->
<!--#include virtual="/asp_lib/displaymessage.asp"-->
<!--#include virtual="/asp_lib/clearsessionvariables.asp" -->
<!--#include virtual="/asp_lib/dateconverter.asp"-->
<!--#include virtual="/asp_lib/crypt.asp"-->
<!--#include virtual="/asp_lib/Page_Loading.asp"-->
<!--#include virtual="/js_lib/date.inc"-->
<%

	'''''''''''''''Open Connection'''''''''''''''
	OpenDB
	'''''''''''''''''''''''''''''''''''''''''''''
'	response.Write session("schoolid")
	
'	response.Write(session("rABFromYear"))
'	response.Write(session("rABToYear"))
'	response.End()
	Agediff=datediff("yyyy",Session("rDOB"),now())
	
function Getcategory(vId)
   	sql="select * from t_house_Category where fromAge<=" & vId&" and ToAge>=" & vId&""
	'response.Write(sql)
	'response.End()
	set rs=server.CreateObject("adodb.recordset")
	rs.Open sql,conn,1,3
	if not rs.EOF then
		Getcategory=rs("HouseCategoryId")
	end if
	rs.Close 

end function
	
	SET rsRegistration=SERVER.CreateObject("ADODB.RECORDSET")
	sstr = "select * from students where student_id = " & Session("studentID") & ""
	rsRegistration.open sstr,conn,1,3
	if rsRegistration.EOF = false then
			rsRegistration("loginname")= Session("rLoginID")
			'rsRegistration("password")= encrypt(trim(Session("rPassword")))
			rsRegistration("parentlogin")= Session("rLoginID")
			'rsRegistration("parentpassword")= encrypt(trim(Session("pPassword")))
			rsRegistration("first_name")= ucase(Session("rfirstName"))
			rsRegistration("last_name")= ucase(Session("rlastName"))
			rsRegistration("sex")= Session("rsex")

			'rsRegistration("date_applied")= Session("rDateApplied")
			rsRegistration("nationalityId")= Session("rNationality")
			rsRegistration("religionId")= Session("rReligion")
			rsRegistration("dob")= convertdate(trim(Session("rDOB")))

			
						
		'Second Page Variables
			rsRegistration("local_address_l1")= ucase(Session("rAddress1"))
			rsRegistration("local_address_l2")= ucase(Session("rAddress2"))
			rsRegistration("local_address_l3")= ucase(Session("rAddress3"))
			rsRegistration("local_address_city")= ucase(Session("rCity"))
			rsRegistration("State")= Session("State")
			rsRegistration("local_address_country")= Session("rCountry")
			rsRegistration("local_address_zip")= Session("rZip")
			rsRegistration("Local_address_phone")= Session("rHomePhone")


			rsRegistration("communication_address_line_1")= ucase(Session("rCommAddress1"))
			rsRegistration("communication_address_line_2")= ucase(Session("rCommAddress2"))
			rsRegistration("communication_address_line_3")= ucase(Session("rCommAddress3"))
			rsRegistration("communication_address_city")= ucase(Session("rCommCity"))
			rsRegistration("communication_state")= Session("rCommState")
			rsRegistration("communication_address_country")= Session("rCommCountry")
			rsRegistration("communication_zip")= Session("rCommZip")
			rsRegistration("communication_phone")= Session("rCommPhone")
			rsRegistration("student_email")= Session("rStudentEmail")


			rsRegistration("guardian_name")= ucase(Session("rContactPerson"))
			rsRegistration("guardian_relation")= ucase(Session("rContactRelation"))
			rsRegistration("guardian_telephone")= Session("rContactNumber") 
			rsRegistration("emergency_number")= Session("rContactEmergencyNumber")
			rsRegistration("guardian_address_l1")= ucase(Session("rGuardianAddress1"))
			rsRegistration("guardian_address_l2")= ucase(Session("rGuardianAddress2"))
			rsRegistration("guardian_address_l3")= ucase(Session("rGuardianAddress3"))
			rsRegistration("guardian_address_city")= ucase(Session("rGuardianCity"))
			rsRegistration("guardian_State")=ucase(session("rGuardianState"))
			rsRegistration("guardian_address_country")= Session("rGuardianrCountry")
			rsRegistration("guardian_address_zip")= Session("rGuardianrZip")
			rsRegistration("guardian_home_phone")= Session("rGuardianrHomePhone")

			


		'Third page variables
		
			rsRegistration("fathers_name")= ucase(Session("rFathername"))
			rsRegistration("fathers_occupation")= ucase(Session("rFatherOccupation"))
			rsRegistration("Fathers_Profession")=trim(Session("rFatherprofession"))
			rsRegistration("fathers_office_number")= Session("rFatherOfficePhone")
			rsRegistration("fathers_mobile_num")= Session("rFatherMobilePhone")
			rsRegistration("fathers_email")= Session("rFatherEmail")
			rsRegistration("mothers_name")= ucase(Session("rMothername"))
			rsRegistration("mothers_occupation")= ucase(Session("rMotherOccupation"))
			
			rsRegistration("Mothers_Profession")=trim(Session("rMotherprofession"))
			rsRegistration("mothers_office_number")= Session("rMotherOfficePhone")
			rsRegistration("mothers_mobile_num")= Session("rMotherMobilePhone")
			rsRegistration("mothers_email")= Session("rMotherEmail")
			
			rsRegistration("brother_scholar1")=Session("rBrotherScholar1")
			rsRegistration("brother_name1")=Session("rBrotherName1")
			'rsRegistration("brother_age1")=Session("rBrotherAge1")

			rsRegistration("brother_Class1")= Session("rbrotherClass1")
			rsRegistration("brother_section1")=Session("rbrothersection1")
			'rsRegistration("brother_remarks1")=Session("rbrotherRemarks1")

			rsRegistration("brother_scholar2")=Session("rBrotherScholar2")
			rsRegistration("brother_name2")=Session("rBrotherName2")
			'rsRegistration("brother_age2")=Session("rBrotherAge2")

			rsRegistration("brother_Class2")= Session("rbrotherClass2")
			rsRegistration("brother_section2")=Session("rbrothersection2")
			'rsRegistration("brother_remarks2")=Session("rbrotherRemarks2")

			rsRegistration("sister_scholar1")=Session("rsisterScholar1")
			rsRegistration("sister_name1")=Session("rSisterName1")
			'rsRegistration("sister_age1")=Session("rSisterAge1")

			rsRegistration("sister_Class1")= Session("rsisterClass1")
			rsRegistration("sister_section1")=Session("rsistersection1")
			'rsRegistration("sister_remarks1")=Session("rsisterRemarks1")

			rsRegistration("sister_scholar2")=Session("rsisterScholar2")
			rsRegistration("sister_name2")=Session("rSisterName2")
			'rsRegistration("sister_age2")=Session("rSisterAge2")

			rsRegistration("sister_Class2")= Session("rsisterClass2")
			rsRegistration("sister_section2")=Session("rsistersection2")
			'rsRegistration("sister_remarks2")=Session("rsisterRemarks2")

			rsRegistration("Person_Name1")=Session("rPerson1")
			rsRegistration("Relation1")=Session("rRelation1")
			rsRegistration("Year1")=Session("rYear1")
			rsRegistration("Person_Name2")=Session("rPerson2")
			rsRegistration("Relation2")=Session("rRelation2")
			rsRegistration("Year2")=Session("rYear2")
			rsRegistration("Person_Name3")=Session("rPerson3")
			rsRegistration("Relation3")=Session("rRelation3")
			rsRegistration("Year3")=Session("rYear3")
		
		'Fifth page variables
			rsRegistration("Achievements")=Session("achievements")
			rsRegistration("Hobbies")=Session("hobbies")
		    rsRegistration("Special_Interests")=Session("Interest")
		    rsRegistration("Other_Info")=Session("other")
		'Sixth page variables

			rsRegistration("class_id")= Session("rClass")
			
			rsRegistration("section_id")= Session("rsection")
			rsRegistration("WithIPS")=Session("rIP")
			
			'rsRegistration("Admission_Class")=Session("radmitclass")
			rsRegistration("date_joined")=(trim(Session("classjoindate")))
			
			rsRegistration("AdmissionMonth")= Session("AdmissionMonth")
			rsRegistration("hostel_reqd")= Session("Hostelreq")
			rsRegistration("year")= Session("academicyear")
			rsRegistration("SC")=  Session("CategorySC")
			rsRegistration("OB")=  Session("CategoryOB")
			rsRegistration("BR")=  Session("CategoryBR")
			rsRegistration("GS")=  Session("CategoryGS")
			rsRegistration("NR")=  Session("CategoryNR")
			rsRegistration("SIS")= Session("CategorySIS")
			rsRegistration("WD")=  Session("CategoryWD")
			rsRegistration("DS")=  Session("CategoryDS")
			rsRegistration("RTE")=  Session("CategoryRTE")
			rsRegistration("Rebate")=  session("Rebate")
			rsRegistration("StudentCategory")=  Session("StudentCategory")
			rsRegistration("ScholarNo")= session("ScholarNo")

'==============================================================================================
'on 29th Aug 2012
			rsRegistration("ABrotherName") = Session("rABrotherName")
			rsRegistration("ABrotherSchno") = session("rABrotherScholarno")
			rsRegistration("ABFromYear") = session("rABFromYear")
			rsRegistration("ABToYear") = session("rABToYear")
			rsRegistration("ABLastClass") = Session("rABrotherClass")
			
			rsRegistration("ABrotherName1") = Session("rABrotherName1")
			rsRegistration("ABrotherSchno1") = session("rABrotherScholarno1")
			rsRegistration("ABFromYear1") = session("rABFromYear1")
			rsRegistration("ABToYear1") = session("rABToYear1")
			rsRegistration("ABLastClass1") = Session("rABrotherClass1")
			
			rsRegistration("ASisterName") = Session("rASisterName")
			rsRegistration("ASisterSchno") = session("rASisterScholarno")
			rsRegistration("ASFromYear") = session("rASFromYear")
			rsRegistration("ASToYear") = session("rASToYear")
			rsRegistration("ASLastClass") = Session("rASisterClass")

			rsRegistration("ASisterName1") = Session("rASisterName1")
			rsRegistration("ASisterSchno1") = session("rASisterScholarno1")
			rsRegistration("ASFromYear1") = session("rASFromYear1")
			rsRegistration("ASToYear1") = session("rASToYear1")
			rsRegistration("ASLastClass1") = Session("rASisterClass1")

'==============================================================================================

'==============================================================================================
'on 1st Sept 2012
			rsRegistration("Fathersubprofession") = Session("rFatherSubProfession")
			rsRegistration("Mothersubprofession") = Session("rMotherSubProfession")
			
			rsRegistration("Father_SubProfession1") = Session("rFatherOccupation1")
'==============================================================================================


			'rsRegistration("HouseNo")= session("HouseNo")
			'rsRegistration("OldHouseNo")= session("OldHouseNo")
			if trim(session("DBBDS"))<>"" then
			rsRegistration("DtDBBDS")= session("DBBDS")
			else
			rsRegistration("DtDBBDS")= null
			end if
			rsRegistration("RegistrationNo")= session("RegdNo")
			rsRegistration("remarks")=session("comments")
			rsRegistration("year_admission")=year(Session("classjoindate"))
			rsRegistration("Club1")=Session("Club1")
			rsRegistration("Club2")=Session("Club2")
			rsRegistration("Club3")=Session("Club3")
			rsRegistration("Student_Age")=trim(Agediff)		
			if (Session("rClass")<>1 or Session("rClass")<>2 or Session("rClass")<>3) then
			rsRegistration("HousecategoryId")=trim(Getcategory(Agediff))
			end if
			' if a student is marked as WD then Inactive the student
			
			if trim(Session("CategoryWD"))="Y" then
				rsRegistration("Status")="InActive"
				rsRegistration("InActive_Date")=date()
			end if
		'Seventh Page Variables

'			response.write "XXX" &rsRegistration("remarks")
'			response.end

			
		'Eighth Page variables
			'rsRegistration("Hobbies")= Session("Hobbies")
			'rsRegistration("Spec_prob")= Session("SpecProb")
			'rsRegistration("Add_Info")= Session("AddInfo")
			
			rsRegistration.Update 
			rsRegistration.close
	END IF
			'if err.number = 0 then
if Trim(Session("CategorySC")) = "Y" then
	sql="update T_Hostel_Boarders set JB='S' where Student_Id ="& Session("studentID")
elseif Trim(Session("CategoryDS")) = "Y" then
	sql="update T_Hostel_Boarders set JB='D' where Student_Id ="& Session("studentID")
else
	sql="update T_Hostel_Boarders set JB='B' where Student_Id ="& Session("studentID")
end if
	conn.execute Sql
'sqldel="delete from Student_concession where student_id="&Session("studentID")
'conn.execute(sqldel)
'if Session("rBrotherName1")<>"" or  Session("rSisterName1")<>"" then
'sql="insert into Student_concession (Student_Id,ConcessionId)values("&Session("studentID")&",1)" ' 1 for brothesister concession
'conn.execute(sql)
'end if
'if Session("rPerson1") <>"" then
'sql="insert into Student_concession (Student_Id,ConcessionId)values("&Session("studentID")&",2)"  ' 2 for oldboys concession
'conn.execute(sql)
'end if
'if ucase(Session("rFatherOccupation"))="MAYOOR" or ucase(Session("rMotherOccupation"))="MAYOOR" then '3 for mayooremployee Conces
'sql="insert into Student_concession (Student_Id,ConcessionId)values("&Session("studentID")&",3)"
'conn.execute(sql)
'end if
					
vActivityId=split(Session("vChValue"),",")
		
		
		for ctr=0 to Ubound(vActivityId)
		sqldel="delete from Student_Activity where student_id=" & Session("studentID")
			conn.execute(sqldel)
			'Inserting into Student_Class_Subjects
			sql="insert into Student_Activity(StudentId,Batch,classId,SectionId,ActivityId) values" & _
			"(" & Session("studentID") & ","& Session("academicyear")&","&Session("rClass")&","& Session("rsection")&"," & vActivityId(ctr) & ")"
		'Response.Write sql
		'Response.End 
		conn.execute(sql)
		next
		
		
		'Created on 01-Feb-2014
		vIpAddree = trim(request.ServerVariables("REMOTE_ADDR"))
		sql = "insert into T_Student_Update_Details(Student_id,UpdateDt,UpdateBy,IpAddreess)"&_
			  " values "&_
	   		  " ("&trim(Session("studentID"))&",'"&now()&"',"&trim(session("UserID"))&",'"&trim(vIpAddree)&"')"
		conn.execute sql
			
			'Updating the swimming pool contribution and status of the contribution
			sql = "delete from T_SwimmingPool_Contribution where student_id = "&trim(Session("studentID"))
			Conn.execute sql
						
			sql = "insert into T_SwimmingPool_Contribution(Student_Id,ContributionAmount,Status_Of_Contribution,createdDt,CreatedBy)"&_
			" values ("& trim(Session("studentID")) &","& trim(session("ContributionAmount")) &",'"& trim(session("StatusOfContr")) &"','"& now() &"',"&session("userid")&")"
			Conn.execute sql				
						
			'if (Session("rClass")<>1 or Session("rClass")<>2 or Session("rClass")<>3) then
			'sql="insert into T_Hostel_Student(Studentid,batch,ClassId,SectionId,HouseCategoryId) values(" & trim(Session("studentID")) & ","& Session("academicyear")&","&Session("rClass")&","& Session("rsection")&","&Getcategory(Agediff)&")"
			'sql="update T_Hostel_Student set Studentid="&trim(Session("studentID"))&",batch="& Session("academicyear")&",ClassId="& Session("rClass")&",SectionId="& Session("rsection")&",HouseCategoryId="&Getcategory(Agediff)
			'sql="update Students set HouseCategoryId="&Getcategory(Agediff)&" where Student_id=" & trim(Session("studentID"))
			'Response.Write sql
			'Response.End 
			'Conn.execute(sql)
			'end if
			
										
					asp_showmessage ("Student Information Updated")
					X = 1
				
		
		'else
					'Response.Write err.description
					'Response.End 
					'Response.Redirect "/asp_lib/ErrorPage.asp"
					ClearEditSessionVariables
			'end if

'''''''''''''''Close Connection'''''''''''''''	
CloseDB
''''''''''''''''''''''''''''''''''''''''''''''

set rsRegistration = nothing	
%>
<html>
	<head>
		<%if x = 1 then%>
		<%if cstr(trim(Session("vType")))="1" then%>
		<META HTTP-EQUIV="Refresh" CONTENT="1; URL=/modules/studentmgt/registration/common_frame.asp?mode=E&file=/modules/studentmgt/registration/StudentsTempEdit/student_view.asp">
		<%elseif cstr(trim(Session("vType")))="2" then%>
		<META HTTP-EQUIV="Refresh" CONTENT="1; URL=/modules/studentmgt/registration/common_frame.asp?mode=E&file=/modules/studentmgt/registration/StudentsTempEdit/student_view_Sr.asp">
		<%elseif cstr(trim(Session("vType")))="3" then%>
		<META HTTP-EQUIV="Refresh" CONTENT="1; URL=/modules/studentmgt/registration/common_frame.asp?mode=E&file=/modules/studentmgt/registration/StudentsTempEdit/student_view_All.asp">
		<%end if%>
		<%end if%>
	</head>
	
</html>
