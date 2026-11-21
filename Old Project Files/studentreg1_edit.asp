<!--#include virtual="/asp_lib/LoginConnect.asp"-->
<!--#include virtual="/asp_lib/displaymessage.asp"-->
<!--#include virtual="/asp_lib/crypt.asp"-->
<!--#include virtual="/asp_lib/displaydate.asp"-->
<%
	'''''''''''''''Open Connection'''''''''''''''
	OpenDB
	
if request.QueryString("mode")="E" then
conn.execute ("delete from student_schools where student_id is NULL")
elseif request.QueryString("mode")="V" and request.QueryString("ptype")=2 then
session("mode")="V"
end if			
'Fill Nationality
private sub FillNationality()
'Filling Designation from master
dim tempRs
set tempRs=server.CreateObject("adodb.recordset")
Sql="Select * from T_Nationality_Master order by NationalityName"
tempRs.Open sql,conn,1,3%>
<option value="" selected>Choose Nationality</OPTION>

<%do while tempRs.EOF=false%>
	<OPTION VALUE="<%=tempRs("Nationality_Id")%>"><%=tempRs("NationalityName")%></OPTION>
<%tempRs.MoveNext
LOOP 
end sub

private sub FillReligion()
'Filling Designation from master
dim tempRs
set tempRs=server.CreateObject("adodb.recordset")
Sql="Select * from T_Religion_Master order by ReligionName"
tempRs.Open sql,conn,1,3%>
<option value="" selected>Choose Religion</OPTION>

<%do while tempRs.EOF=false%>
	<OPTION VALUE="<%=tempRs("ReligionId")%>"><%=tempRs("ReligionName")%></OPTION>
<%tempRs.MoveNext
LOOP 
end sub

if Request.QueryString("ID") <> "" then
	Session("studentid") = Request.QueryString("ID")
end if
'Response.Write "Student Id :" & Session("studentid")
'Assigning Session Variables
if request.querystring("mode") <> "" then
	sql_select = "select *,cast(scholarno as varchar(50))+'.jpg' as photo_file_1 from students where student_id= " & Session("StudentID") 
	'Response.Write sql_select
	set rsStudents = server.CreateObject("ADODB.Recordset")
	set rsStudents=conn.Execute(sql_select)

	if not (rsStudents.EOF and rsStudents.BOF) then
			
			'Session("schoolid")=rsStudents("schoolid")
			Session("rLoginID")=rsStudents("loginname")
			Session("prevlogin")=rsStudents("loginname")
			Session("rPassword")=decrypt(rsStudents("password"))
			Session("rfirstName")=rsStudents("first_name")
			Session("rlastName")=rsStudents("last_name")
			Session("oUID")=Session("studentid")

			Session("rsex")=rsStudents("sex")
			'Session("rDateApplied")=rsStudents("date_applied")
			Session("rNationality")=rsStudents("nationalityId")
			Session("rReligion")=rsStudents("religionId")
			Session("rDOB")=Ndate(rsStudents("dob"),"%d-%b-%Y")
			session("photofile")=rsstudents("photo_file_1")
			'Second Page Variables
			Session("rAddress1")=rsStudents("local_address_l1")
			Session("rAddress2")=rsStudents("local_address_l2")
			Session("rAddress3")=rsStudents("local_address_l3")
			Session("rCity")=rsStudents("local_address_city")
			Session("State")=rsStudents("State")
			Session("rCountry")=rsStudents("local_address_country")
			Session("rZip")=rsStudents("local_address_zip")
			Session("rHomePhone")=rsStudents("Local_address_phone")

			Session("rCommAddress1")=rsStudents("communication_address_line_1")
			Session("rCommAddress2")=rsStudents("communication_address_line_2")
			Session("rCommAddress3")=rsStudents("communication_address_line_3")
			Session("rCommCity")=rsStudents("communication_address_city")
			Session("rCommState")=rsStudents("communication_state")
			Session("rCommCountry")=rsStudents("communication_address_country")
			Session("rCommZip")=rsStudents("communication_zip")
			Session("rCommPhone")=rsStudents("communication_phone")
			Session("rStudentEmail")=rsStudents("student_email")

			Session("rContactPerson")=rsStudents("guardian_name")
			Session("rContactRelation")=rsStudents("guardian_relation")
			Session("rContactNumber")=rsStudents("guardian_telephone")
			Session("rContactEmergencyNumber")=rsStudents("emergency_number")
			Session("rGuardianAddress1")= rsStudents("guardian_address_l1")
			Session("rGuardianAddress2")= rsStudents("guardian_address_l2")
			Session("rGuardianAddress3")= rsStudents("guardian_address_l3")
			Session("rGuardianCity")= rsStudents("guardian_address_city")
			session("rGuardianState")= rsStudents("guardian_State") 
			Session("rGuardianrCountry") = rsStudents("guardian_address_country")
			Session("rGuardianrZip")= rsStudents("guardian_address_zip")
			Session("rGuardianrHomePhone")= rsStudents("guardian_home_phone")	

		'Third page variables
			session("pLogin")=rsStudents("parentlogin")
			Session("rFathername")=rsStudents("fathers_name")
			Session("rFatherProfession")=rsStudents("Fathers_Profession")
			Session("rFatherOccupation")=rsStudents("fathers_Occupation")
			Session("rFatherOfficePhone")= rsStudents("fathers_office_number")
			Session("rFatherMobilePhone")= rsStudents("fathers_mobile_num")
			Session("rFatherEmail")= rsStudents("fathers_email")
			Session("rMothername") = rsStudents("mothers_name")
			Session("rMotherprofession") = rsStudents("Mothers_Profession")
			Session("rMotherOccupation") = rsStudents("Mothers_Occupation")
			Session("rMotherOfficePhone") = rsStudents("mothers_office_number")
			Session("rMotherMobilePhone") = rsStudents("mothers_mobile_num")
			Session("rMotherEmail")= rsStudents("mothers_email")	
			Session("rBrotherName1")=rsStudents("brother_name1")
			Session("rBrotherAge1")=rsStudents("brother_age1")

			Session("rBrotherClass1")=rsStudents("brother_class1")
			Session("rBrothersection1")=rsStudents("brother_section1")
			Session("rBrotherremarks1")=rsStudents("brother_remarks1")

			Session("rBrotherName2")=rsStudents("brother_name2")
			Session("rBrotherAge2")=rsStudents("brother_age2")

			Session("rBrotherClass2")=rsStudents("brother_class2")
			Session("rBrothersection2")=rsStudents("brother_section2")
			Session("rBrotherremarks2")=rsStudents("brother_remarks2")


			Session("rSisterName1")=rsStudents("sister_name1")
			Session("rSisterAge1")=rsStudents("sister_age1")

			Session("rsisterClass1")=rsStudents("sister_class1")
			Session("rsistersection1")=rsStudents("sister_section1")
			Session("rsisterremarks1")=rsStudents("sister_remarks1")

			Session("rSisterName2")=rsStudents("sister_name2")
			Session("rSisterAge2")=rsStudents("sister_age2")

			Session("rsisterClass2")=rsStudents("sister_class2")
			Session("rsistersection2")=rsStudents("sister_section2")
			Session("rsisterremarks2")=rsStudents("sister_remarks2")

		     'relation details
			Session("rPerson1")= rsStudents("Person_Name1")
			Session("rRelation1")= rsStudents("Relation1")
			Session("rYear1")=rsStudents("Year1")
			Session("rPerson2")=rsStudents("Person_Name2")
			Session("rRelation2")=rsStudents("Relation2")
			Session("rYear2")=rsStudents("Year2")
			Session("rPerson3")=rsStudents("Person_Name3")
			Session("rRelation3")=rsStudents("Relation3")
			Session("rYear3")= rsStudents("Year3")
		
		'Fourth page variables
			Session("Hobbies")=rsStudents("Hobbies")
			Session("other")=rsStudents("Other_Info")
			Session("Achievements")=rsStudents("achievements")
			Session("Interest")=rsStudents("Special_Interests")
			
		'Sixth page variables
			Session("rclass") = rsStudents("class_id")
			Session("rsection")=rsStudents("section_id")
			Session("rIP")=rsStudents("WithIPS")
			Session("classjoindate")=rsStudents("date_joined")
			Session("AdmissionMonth")=rsStudents("AdmissionMonth")
			Session("Hostelreq")=rsStudents("hostel_reqd")
			session("ScholarNo")=rsStudents("ScholarNo")
			Session("CategorySC")=rsstudents("SC")
			Session("CategoryOB")=rsstudents("OB")
			Session("CategoryBR")=rsstudents("BR")
			Session("CategoryGS")=rsstudents("GS")
			Session("CategoryNR")=rsstudents("NR")
			Session("CategorySIS")=rsstudents("SIS")
			Session("CategoryWD")=rsstudents("WD")
			Session("CategoryDS")=rsstudents("DS")
			Session("CategoryRTE") = rsstudents("RTE")
			Session("Rebate")=rsstudents("Rebate")
			Session("StudentCategory")=rsstudents("StudentCategory")
			session("HouseNo")=rsStudents("HouseNo")
			session("OldHouseNo")=rsStudents("OldHouseNo")
			session("DBBDS")=rsStudents("DtDBBDS")
			session("RegdNo")=rsStudents("RegistrationNo")
			Session("academicyear")=rsStudents("year")		
			Session("comments")=rsStudents("remarks")
			
'===============================================================================================			
'on 29th Aug 2012
			Session("rABrotherName") 		= 	rsStudents("ABrotherName") 
			session("rABrotherScholarno") 	= 	rsStudents("ABrotherSchno") 
			session("rABFromYear") 			= 	rsStudents("ABFromYear") 
			session("rABToYear") 			= 	rsStudents("ABToYear")  
			Session("rABrotherClass") 		= 	rsStudents("ABLastClass")  
			
			Session("rABrotherName1") 		= 	rsStudents("ABrotherName1")  
			session("rABrotherScholarno1") 	=	rsStudents("ABrotherSchno1") 
			session("rABFromYear1") 		= 	rsStudents("ABFromYear1") 
			session("rABToYear") 			= 	rsStudents("ABToYear1")  
			Session("rABrotherClass1") 		= 	rsStudents("ABLastClass1") 
			
			Session("rASisterName") 		= 	rsStudents("ASisterName")  
			session("rASisterScholarno") 	= 	rsStudents("ASisterSchno") 
			session("rASFromYear") 			= 	rsStudents("ASFromYear")  
			session("rASToYear") 			= 	rsStudents("ASToYear")  
			Session("rASisterClass") 		= 	rsStudents("ASLastClass")  

			Session("rASisterName1") 		= 	rsStudents("ASisterName1")  
			session("rASisterScholarno1") 	= 	rsStudents("ASisterSchno1")  
			session("rASFromYear1") 		= 	rsStudents("ASFromYear1") 
			session("rASToYear1") 			= 	rsStudents("ASToYear1")  
			Session("rASisterClass1") 		= 	rsStudents("ASLastClass1") 
'===============================================================================================	

'===============================================================================================	
'on 1-sept-2012
			Session("rFatherSubProfession")	=  rsStudents("Fathersubprofession")
			Session("rMotherSubProfession")	=  rsStudents("Mothersubprofession")

'on 13-Aug-2016
			Session("rFatherOccupation1")	=  rsStudents("Father_SubProfession1")
		
'===============================================================================================				
			
	end if
end if

function WriteSession
	Session("rPassword")=  trim(Request.Form("txtPassword"))
	Session("rfirstName") = trim(Request.Form("txtFirstName"))
	Session("rlastName") = trim(Request.Form("txtLastName"))
	session("ScholarNo") = trim(Request.Form("txtScholarNo"))
	session("HouseNo")=Request.Form("txtScholarNo")
	Session("rsex") = Request.Form("sex_select")
	'Session("rDateApplied") = Now()
	Session("rNationality") = Request.Form("cmbNationality")	
	Session("rReligion") = request.form("cmbReligion")
	Session("rDOB") = Request.Form("txtDOB")
end function	

 if Request.Form("txhControl") = "Next" then
	WriteSession
	'response.Write trim(session("prevlogin")) &trim(session("rLoginID"))
	'response.End
	if trim(session("prevlogin")) <>trim(session("rLoginID")) then
		Dim rsRegistration 
		set rsRegistration = server.CreateObject("ADODB.Recordset")
		
		sstr = "select * from students where loginname = '" & trim(replace(Request.Form("txtlogin"),"'","")) & "'"
		set rsRegistration = conn.execute (sstr)
		
		if (rsRegistration.EOF or rsRegistration.BOF)  then
			WriteSession
			Response.Redirect ("studentreg2_edit.asp")

		else
			WriteSession 
			vleft = -150
			asp_showmessage "Login ID " & Request.Form("txtlogin") & " already exists. Please Choose another ID"		
		end if
		set rsRegistration = nothing
	else
		WriteSession
		Response.Redirect ("studentreg2_edit.asp")
end if
	
end if

%>
<script language="javascript">
function KeyPressCheck(txtfld)
{
alert("Please Click on the Link to select Date");
return false
}

function padout(number) 
{ return (number < 10) ? '0' + number : number; } 
function y2k(number) 
{ return (number < 1000) ? number + 1900 : number; } 

				function validate(aa,bb,cc,dd,ee,ff) { 
					var startday = aa;
					var startmonth = bb;   
					var startyear = cc;    
					var endday = dd;   
					var endmonth = ee;  
					var endyear = ff;  
					 
					if(startday.length ==1)
					{
						startday = "0" + startday;
					}
					if(endday.length ==1)
					{
						endday = "0" + endday;
					}
					unvalidstartdate = startday + '/' + startmonth + '/' + startyear ; 
					unvalidenddate = endday + '/' + endmonth + '/' + endyear ; 

					var startdate = new Date(startyear-0,startmonth-1,startday-0); 
					var enddate = new Date(endyear-0,endmonth-1,endday-0); 

					var validstartdate = padout(startdate.getDate()) + '/' + padout(startdate.getMonth()+1) + '/' + y2k(startdate.getYear()) 
					var validenddate = padout(enddate.getDate()) + '/' + padout(enddate.getMonth()+1) + '/' + y2k(enddate.getYear()) 

					if (unvalidstartdate != validstartdate)
					{ 
						alert('Please Enter Date In DD-MON-YYYY format'); 
						return false; 
						
						//alert('From Date: ' + aa + ' ' + bb + ' ' + cc + ' is invalid'); 
						//return false; 
					} 

					if (unvalidenddate != validenddate)
					{ 
						alert('Please Enter Date In DD-MON-YYYY format'); 
						return false; 
						
						//alert('To Date: ' + dd + ' ' + ee + ' ' + ff + ' is invalid'); 
						//return false; 
					} 

					starttime = Date.UTC(y2k(startdate.getYear()),startdate.getMonth(),startdate.getDate(),0,0,0); 
			/*		endtime = Date.UTC(y2k(enddate.getYear()),enddate.getMonth(),enddate.getDate(),0,0,0); 

					if (starttime <= endtime)
					{ 
						// valid 
					} 
					else 
					{ 
						alert('Start Date is not less than End Date'); 
						return false;
					} 
*/
					currentdate = new Date(); 
					currenttime = Date.UTC(y2k(currentdate.getYear()),currentdate.getMonth(),currentdate.getDate(),0,0,0); 

					if (starttime < currenttime)
					{ 
						// valid 
					} 
					else
					{ 
						alert('Date Of Birth Must Be Less Than Current Date'); 
						return false; 
					} 
					return true; 
					 } 
function ConvertMon(tempF)
{
	var tempFMon;
	tempF=tempF.toUpperCase();
	if(tempF == "JAN" || tempF == "01" || tempF == "1" )
	{
		tempFMon = "01";
	} 
	if(tempF == "FEB" || tempF == "02" || tempF == "2")
	{
		tempFMon = "02";
	} 
	if(tempF == "MAR" || tempF == "03" || tempF == "3")
	{
		tempFMon = "03";
	} 
	if(tempF == "APR" || tempF == "04" || tempF == "4")
	{
		tempFMon = "04";
	} 
	if(tempF == "MAY" || tempF == "05" || tempF == "5")
	{
		tempFMon = "05";
	} 
	if(tempF == "JUN" || tempF == "06" || tempF == "6")
	{
		tempFMon = "06";
	} 
	if(tempF == "JUL" || tempF == "07" || tempF == "7")
	{
		tempFMon = "07";
	} 
	if(tempF == "AUG" || tempF == "08" || tempF == "8")
	{
		tempFMon = "08";
	} 
	if(tempF == "SEP" || tempF == "09" || tempF == "9")
	{
		tempFMon = "09";
	} 
	if(tempF == "OCT" || tempF == "10")
	{
		tempFMon = "10";
	} 
	if(tempF == "NOV" || tempF == "11")
	{
		tempFMon = "11";
	} 
	if(tempF ==	 "DEC" || tempF == "12")
	{
		tempFMon = "12";
	} 
 

	return tempFMon;
}




function trim(par)
{	
	
	y=par.length;
	ret='';
	for (i=0;i<y;i++)
	{
		if (par.charAt(i)!=' ')
		{
			ret=ret+par.charAt(i);
		}
	}
	
	return ret;
	
}

function frmstudentreg1_submit()
{
	if (frmstudentreg1.txtPassword.value=='')
	{
		alert ("Please Enter Password");
		frmstudentreg1.txtPassword.focus();
        return false;
	}
	if (frmstudentreg1.txtConfirmPassword.value=='')
	{
		alert ("Please Confirm your Password");
		frmstudentreg1.txtConfirmPassword.focus();
        return false;
	}
	if (frmstudentreg1.txtPassword.value!=frmstudentreg1.txtConfirmPassword.value)
	{
		alert(" Passwords Do not match. Please Re-enter");
		frmstudentreg1.txtConfirmPassword.value='';
		frmstudentreg1.txtConfirmPassword.focus();
        return false;
	}
	if (frmstudentreg1.txtScholarNo.value == "")
		{
			alert("Please Enter Scholar No.");
			frmstudentreg1.txtScholarNo.focus();
			return false;
		}

	if (isNaN(frmstudentreg1.txtScholarNo.value))
		{
			alert("Please Enter Numeric Value");
			frmstudentreg1.txtScholarNo.value=""
			frmstudentreg1.txtScholarNo.focus();
			return false;
		}
	if (frmstudentreg1.txtFirstName.value=='')
	{
		alert("Please Enter Student First Name");
		frmstudentreg1.txtFirstName.focus();
        return false;
	}
/*	if (frmstudentreg1.txtLastName.value=='')
	{
		alert("Please Enter Student Last Name");
		frmstudentreg1.txtLastName.focus();
        return false;
	}*/
	if (document.frmstudentreg1.txtDOB.value == "")
	{		
		alert("Please select Date of Birth");
		document.frmstudentreg1.txtDOB.focus();		
		return false;
	}
	if (frmstudentreg1.sex_select.value=='')
	{
		alert("Please Select Sex");
		document.frmstudentreg1.sex_select.focus();
        return false;
	}
	if (frmstudentreg1.cmbNationality.value=='')
	{
		alert("Please Select Nationality");
        frmstudentreg1.cmbNationality.focus();
        return false;
    }
    if (frmstudentreg1.cmbReligion.value=='')
	{
		alert("Please Select Religion");
        frmstudentreg1.cmbReligion.focus();
        return false;
    }
    
	
	fromDate = frmstudentreg1.txtDOB.value;
	toDate = frmstudentreg1.txtDOB.value;

					if (fromDate != "")
					{
						if (fromDate.indexOf("-") != -1 || toDate.indexOf("-") != -1)
						{
							tempFDate= fromDate.split("-");
							tempFDate[1] = ConvertMon(tempFDate[1]);
							TempTDate= toDate.split("-");
							TempTDate[1] = ConvertMon(TempTDate[1]);
							if(validate(tempFDate[0],tempFDate[1],tempFDate[2],TempTDate[0],TempTDate[1],TempTDate[2]))
							{
						  
							}
							else
							{
							frmstudentreg1.txtDOB.focus();
							return false;
							}
						}
					else
						{
						if (fromDate.indexOf("-") == -1)
							{
								alert("Please Enter Date in DD-MM-YYYY Format");
								document.frmstudentreg1.txtDOB.focus();
								return false;
							}
						}
					}

	//enabiling all controls	
		disable(false);
		
	document.frmstudentreg1.txhControl.value  = "Next";
	document.frmstudentreg1.submit();
}	
</script>
<!--#include virtual="/html_libs/curlform.asp" -->
<html>
	<head>
		<script language="JavaScript" src="/js_lib/date-picker.js"></script>
		<link rel="stylesheet" href="/html_libs/style.css">
			<SCRIPT ID="clientEventHandlersJS" LANGUAGE="javascript">
<!--
function window_onload() {
}
function disable(val)
{
for (i=0;i<document.frmstudentreg1.elements.length;i++)
		{
		if (document.frmstudentreg1.elements(i).type != "button")
		document.frmstudentreg1.elements(i).disabled=+val;
		}
}

//-->
	</SCRIPT>
	<title><%="Mayoor School, Ajmer : Personal Details Of "%><%=Session("rfirstName")%><%=" "%><%=Session("rlastName")%></title>
	</head>
	<body LANGUAGE="javascript" onLoad="return window_onload()">
		<%
	form_name = "frmstudentreg1"
	form_method = "post":form_title = "Student Registration - Personal Identification Details"
	form_iconsrc = "/images/icon.gif"
	form_action = "studentreg1_edit.asp"
	form_showsubmit = true
	form_showsubmit1 = false
	form_showsubmit2 = false
	form_submitname = "NEXT"
	form_paging = false
	form_firstlink = ""
	form_prevlink = ""
	form_nextlink = ""
	form_lastlink = ""
%>
<Div id='popCal' style='POSITION:absolute;visibility:hidden;border:2px ridge;width:10'>
		<iframe name="popFrame" src="/html_libs/popcjs.htm" frameborder="0" scrolling="no" width="183" height="188"></iframe>
</Div>
		<SCRIPT event="onclick()" for="document">popCal.style.visibility = "hidden";</SCRIPT>
		<%startform()%>
		<table class="formtable" width="70%">
			<input type="hidden" name="txhControl">
			<tr valign="top" align="left">
				<td class="keycell" align="left" valign="middle">
					Login Id<font color="red"><strong></strong></font>
				</td>
				<td width="50%">
					<%=Session("rLoginID")%>
				</td>
				<%if Session("photofile") <> "" then%>
				<td rowspan=5>
						<IMG alt="" height=100 width=80 src="\images\studentphotos\<%=Session("photofile")%>">
				</td>
				<%end if%>
			</tr>
			<tr valign="top" align="left">
				<td class="keycell" align="left" valign="middle">
					Password<FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td width="50%">
					<input type="password" name="txtPassword" style="WIDTH: 290px; HEIGHT: 22px" size="41" value="test" maxlength=40>
				</td>
			</tr>
			<tr valign="top" align="left">
				<td class="keycell" align="left" valign="middle">
					Confirm Password<FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td width="50%">
					<input type="password" name="txtConfirmPassword" style="WIDTH: 290px; HEIGHT: 22px" size="41" value="test" maxlength=40>
				</td>
			</tr>
			<tr valign="middle">
				<td class="keycell" width="50%">
					Scholar No <FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td class="">
					<input type=text name="txtScholarNo" align="right" style="WIDTH: 290px; HEIGHT: 22px" value="<%=session("ScholarNo")%>" maxlength=10 ID="Text4">				
				
				</td>
			</tr>
			<tr valign="top" align="left">
				<td class="keycell" align="left" valign="middle">
					First Name<FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td width="50%">
					<input name="txtFirstName" style="WIDTH: 290px; HEIGHT: 22px" size="41" maxlength=25 value="<%=Session("rfirstName")%>">
				</td>
			</tr>
			<tr valign="top" align="left">
				<td class="keycell" align="left" valign="middle">
					Last Name<FONT color="red"><STRONG></STRONG></FONT>
				</td>
				<td width="50%">
					<input name="txtLastName" style="WIDTH: 290px; HEIGHT: 22px" size="41" maxlength=25 value="<%=Session("rlastName")%>">
				</td>
			</tr>
			<TR valign="top" align="left">
				<TD class="keycell" align="left" valign="middle">
					Date of Birth<font color="red"><strong>*</strong></font>
				</TD>
				<td width="50%">
					<input type="text" style="text-align:center;WIDTH: 100px" name="txtDOB" LANGUAGE="javascript" onKeyPress="return KeyPressCheck(this)"  value="<%=Session("rDOB")%>" ID="Text1">
					<input onClick="popFrame.fPopCalendar(txtDOB,txtDOB,popCal); return false" type="button" value="V" NAME="Button1" ID="Button1">
				
				</td>
						
			</TR>
			<tr valign="top" align="left">
				<td class="keycell" align="left" valign="middle">
					Sex<font color="red"><strong>*</strong></font>
				</td>
				<td width="50%">
					<select name="sex_select" style="WIDTH: 290px; HEIGHT: 22px">
						<option value="">
							Please Select</option>
						<option value="M">
						Male
						<option value="F">
						Female </select>
				</td>
			</tr>
			<TR valign="top" align="left">
				<TD class="keycell" align="left" valign="middle">
					Nationality<FONT color="red"><STRONG>*</STRONG></FONT>
				</TD>
				<TD width="50%">
					<SELECT name="cmbNationality" style="WIDTH: 290px; HEIGHT: 22px">
					<%FillNationality%>
						
					</SELECT>
				</TD>
			</TR>
			<TR valign="top" align="left">
				<TD class="keycell" align="left" valign="middle">
					Religion<FONT color="red"><strong>*</strong></FONT>
				</TD>
				<TD width="50%">
					<SELECT name="cmbReligion" style="WIDTH: 290px; HEIGHT: 22px">
						<%FillReligion%>
					</SELECT>
				</TD>
			</TR>
			
			
			

			
			
			<tr valign="top" align="right">
				<td colSpan="2">
					<font face="Verdana, Arial, Helvetica, sans-serif" size="2">Fields marked with <FONT color="red"><STRONG>*</STRONG></FONT>
							are Mandatory</font>
				</td>
			</tr>
		</table>
		<SCRIPT LANGUAGE="javascript">
<!--
	document.frmstudentreg1.cmbNationality.value ="<%=Session("rNationality")%>";
	document.frmstudentreg1.cmbReligion.value ="<%=Session("rReligion")%>";	
	document.frmstudentreg1.sex_select.value ="<%=session("rsex")%>";	
//-->
		</SCRIPT>
		<%
	'''''''''''''''Close Connection'''''''''''''''	
	CloseDB
	''''''''''''''''''''''''''''''''''''''''''''''
%>
		<%endform()
		if session("mode")="V" then%>
		<script language=javascript>
		disable(true);
		</script>
		<%end if%>
	</body>
</html>
