<!--#include virtual="/asp_lib/DBConnect.asp"-->
<!--#include virtual="/asp_lib/displaymessage.asp"-->
<!--#include virtual="/html_libs/curlform.asp" -->
<!--#include virtual="/asp_lib/displaydate.asp"-->
<%
OpenDB
'response.Write(Session("rIP"))
dim rsFill
set rsFill=server.CreateObject("Adodb.recordset")

dim tempRs
set tempRs=server.CreateObject("adodb.recordset")

'''''''''''''''''''''''''''''''
dim vScholarNo 'b
dim vScholarNo1 'b2
dim vScholarNo2 's
dim vScholarNo3 's2
Sql="select brother_scholar1,brother_scholar2,sister_scholar1,sister_scholar2 from students where student_id= " & Session("StudentID")
tempRs.Open sql,conn,1,3
 if tempRs.EOF =false then

	 vScholarNo =tempRs.Fields("brother_scholar1")'b
	vScholarNo1 =tempRs.Fields("brother_scholar2")'b2
	vScholarNo2 =tempRs.Fields("sister_scholar1") 's
	vScholarNo3 =tempRs.Fields("sister_scholar2")'s2
 end if
tempRs.Close 
'''''''''''''''''''''''''''''''
Sql="select ContributionAmount,Status_Of_Contribution from T_SwimmingPool_Contribution where student_id= " & Session("StudentID")
tempRs.Open sql,conn,1,3
 if tempRs.EOF =false then
	session("ContributionAmount") = trim(tempRs("ContributionAmount"))
	session("StatusOfContr") = trim(tempRs("Status_Of_Contribution"))
 end if
tempRs.Close 
'''''''''''''''''''''''''''''''

if Request.Form("txtBrotherScholar1") <> "" then
vScholarNo=Trim(Request.Form("txtBrotherScholar1"))
Sql="select Name,class_id,section_name from v_Students where ScholarNo='"& vScholarNo & "'"
tempRs.Open sql,conn,1,3
 if tempRs.EOF =false then
		Session("rBrotherName1")=tempRs.Fields("Name")
		Session("rBrotherClass1")=tempRs.Fields("class_id")
		Session("rBrotherSection1")=tempRs.Fields("section_name")
		'vName=tempRs.Fields("Name")
		'Request.Form("txtBrotherScholar1")=tempRs("first_name")
		'vStudentId=rs.Fields("student_id")
		'vClass=rs.Fields("ClassName")
		'vHouse=rs.Fields("HostelName")
		'vSection=rs.Fields("Section_Name")
		'vDob=ndate(rs.Fields("dob"),"%d-%b-%Y")
		'vScholarNo=rs.Fields("ScholarNo")
		'vBloodgroup=rs.Fields("BloodGroup")
		ELSE
	Session("rBrotherName1")="Invalid Roll No. or No Record Found"
	end if
end if
tempRs.Close 

if Request.Form("txtBrotherScholar2") <> "" then
vScholarNo1=Trim(Request.Form("txtBrotherScholar2"))
Sql="select Name,class_id,section_name from v_Students where ScholarNo='"& vScholarNo1 & "'"
tempRs.Open sql,conn,1,3
 if tempRs.EOF =false then
		Session("rBrotherName2")=tempRs.Fields("Name")
		Session("rBrotherClass2")=tempRs.Fields("class_id")
		Session("rBrotherSection2")=tempRs.Fields("section_name")
		ELSE
	Session("rBrotherName2")="Invalid Roll No. or No Record Found"
	end if
end if
tempRs.Close 

if Request.Form("txtSisterScholar1") <> "" then
vScholarNo2=Trim(Request.Form("txtSisterScholar1"))
Sql="select Name,class_id,section_name from v_Students where ScholarNo='"& vScholarNo2 & "'"
tempRs.Open sql,conn,1,3
 if tempRs.EOF =false then
		Session("rSisterName1")=tempRs.Fields("Name")
		Session("rSisterClass1")=tempRs.Fields("class_id")
		
		Session("rSisterSection1")=tempRs.Fields("section_name")
		ELSE
	Session("rSisterName1")="Invalid Roll No. or No Record Found"
	end if
end if
tempRs.Close 

if Request.Form("txtSisterScholar2") <> "" then
vScholarNo3=Trim(Request.Form("txtSisterScholar2"))
Sql="select Name,class_id,section_name from v_Students where ScholarNo='"& vScholarNo3 & "'"
tempRs.Open sql,conn,1,3
 if tempRs.EOF =false then
		Session("rSisterName2")=tempRs.Fields("Name")
		Session("rSisterClass2")=tempRs.Fields("class_id")
		Session("rSisterSection2")=tempRs.Fields("section_name")
	else
		Session("rSisterName2")="Invalid Roll No. or No Record Found"
	end if
end if
tempRs.Close 

private sub FillCountry()
'Filling Designation from master
dim tempRs
set tempRs=server.CreateObject("adodb.recordset")
Sql="Select * from T_Country_Master order by CountryName"
tempRs.Open sql,conn,1,3%>
<option value="" selected>Choose Country</OPTION>

<%do while tempRs.EOF=false%>
	<OPTION VALUE="<%=tempRs("CountryId")%>"><%=tempRs("CountryName")%></OPTION>
<%tempRs.MoveNext
LOOP 
tempRs.Close
end sub


private sub FillClass()
'Filling Designation from master
dim tempRs
set tempRs=server.CreateObject("adodb.recordset")
Sql="select class_id, classname from classes order by class_id desc"
tempRs.Open sql,conn,1,3%>
<%do while tempRs.EOF=false%>
	<OPTION VALUE="<%=tempRs("class_id")%>"><%=tempRs("classname")%></OPTION>
<%tempRs.MoveNext
LOOP 
tempRs.Close
end sub

private sub FillMonth()
	sql="select * from T_Month_Master order by MonthId"
	rsFill.Open sql,conn,1,3
	if not rsFill.EOF then
		while not rsFill.EOF
			%>
			<option value="<%=rsFill.Fields(0)%>"><%=rsFill.Fields(1)%></option>
			<%
		rsFill.MoveNext
		wend
	end if
	rsFill.Close
end sub
'procedure for filling admission category 
private sub FillCategory()
	sql="select * from T_Admission_Category"
	rsFill.Open sql,conn,1,3
	if not rsFill.EOF then
		while not rsFill.EOF
			%>
			<option value="<%=rsFill.Fields(0)%>"><%=rsFill.Fields(1)%></option>
			<%
		rsFill.MoveNext
		wend
	end if
	rsFill.Close
end sub
'procedure for filling student category type
private sub FillStudentCategory()
	sql="select * from T_Student_Category"
	rsFill.Open sql,conn,1,3
	if not rsFill.EOF then
		while not rsFill.EOF
			%>
			<option value="<%=rsFill.Fields(0)%>"><%=rsFill.Fields(1)%></option>
			<%
		rsFill.MoveNext
		wend
	end if
	rsFill.Close
end sub

'==============================================================================================================================================
'on 1-Sept-2012

if request.Form("txhmoccupation") = "Yes" then
Session("rMotherProfession") = trim(request.Form("cmbMotherOccupation"))
else
Session("rMotherProfession") = Session("rMotherProfession")
end if
'==============================================================================================================================================


private sub Fillprofession()
	'Filling State from master
	dim tempRs1
	set tempRs1=server.CreateObject("adodb.recordset")
	Sql="Select * from T_Proffession_Master order by ProffessionName"
	tempRs1.Open sql,conn,1,3%>
	<option value="" selected>Select Proffession</OPTION>
	<%do while tempRs1.EOF=false%>

			<OPTION VALUE="<%=tempRs1("ProffessionId")%>"<%if trim(tempRs1("ProffessionId"))=trim(Session("rMotherprofession")) then%>selected<%end if%>><%=tempRs1("ProffessionName")%></OPTION>

	<%tempRs1.MoveNext
	LOOP
	tempRs1.Close 
end sub

'==============================================================================================================================================
'on 1-Sept-2012
private sub FillSubprofession()
	'Filling Sub Profession from master
	dim tempRs1
	set tempRs1=server.CreateObject("adodb.recordset")
	Sql="Select * from T_Proffession_SubMaster order by SubProffessionName"
	tempRs1.Open sql,conn,1,3%>
	<option value="" selected>Select Sub Proffession</OPTION>
	<%do while tempRs1.EOF=false%>
	
	<OPTION VALUE="<%=tempRs1("SubProffessionId")%>"><%=tempRs1("SubProffessionName")%></OPTION>
	<%tempRs1.MoveNext
	LOOP
	tempRs1.Close 
end sub
'==============================================================================================================================================


private sub FillBoarderType()
	sql="select * from T_Boarding_Category"
	rsFill.Open sql,conn,1,3
	if not rsFill.EOF then
		while not rsFill.EOF
			%>
			<option value="<%=rsFill.Fields(0)%>"><%=rsFill.Fields(1)%></option>
			<%
		rsFill.MoveNext
		wend
	end if
	rsFill.Close
end sub


if Request.Form("txhControl") = "prev" then 
	redirectpage="studentreg2_edit.asp"
end if
if Request.Form("txhControl") = "next" then
	 redirectpage="studentreg5_edit.asp"
end if

if Request.Form("txhControl") <> "" then

	if request.form("cmbMotherOccupation") <> "" then
	Session("rMotherprofession")=trim(Request.Form("cmbMotherOccupation"))
	'on 1st sept 2012
	Session("rMotherSubProfession")=Trim(request.form("cmbMotherSubOccupation"))
	end if
	Session("rMothername")=trim(Request.Form("txtMotherName"))
	Session("rMotherOccupation")=trim(Request.Form("txtMotherOccupation"))
	Session("rMotherOfficePhone")=trim(request.Form("txtMotherOfficePhone"))
	Session("rMotherMobilePhone")=trim(request.Form("txtMotherMobilePhone"))
	Session("rMotherEmail")=trim(request.Form("txtMotherEmail"))
	     
	Session("rBrotherScholar1")=trim(Request.Form("txtBrotherScholar1"))
    Session("rBrotherName1")=trim(Request.Form("txtBrotherName1"))
    Session("rBrotherAge1")=trim(Request.Form("txtBrotherHouseNo1"))
    Session("rBrotherClass1")=trim(Request.Form("cmbbClass1"))
    Session("rBrothersection1")=trim(Request.Form("cmbbSection1"))
    Session("rBrotherRemarks1")=trim(Request.Form("txtBRemarks1"))
    Session("rBrotherScholar2")=trim(Request.Form("txtBrotherScholar2"))
	Session("rBrotherName2")=trim(Request.Form("txtBrotherName2"))
    Session("rBrotherAge2")=trim(Request.Form("txtBrotherHouseNo2"))
    Session("rBrotherClass2")=trim(Request.Form("cmbbClass2"))
    Session("rBrothersection2")=trim(Request.Form("cmbbSection2"))
    Session("rBrotherRemarks2")=trim(Request.Form("txtBRemarks2"))
    Session("rSisterScholar1")=trim(Request.Form("txtSisterScholar1"))
    Session("rSisterName1")=trim(Request.Form("txtSisterName1"))
    Session("rSisterAge1")=trim(Request.Form("txtSisterHouseNo1"))
    Session("rsisterClass1")=trim(Request.Form("cmbsClass1"))
    Session("rsistersection1")=trim(Request.Form("cmbsSection1"))
    Session("rsisterRemarks1")=trim(Request.Form("txtsRemarks1"))
    Session("rSisterScholar2")=trim(Request.Form("txtSisterScholar2"))
    Session("rSisterName2")=trim(Request.Form("txtSisterName2"))
    Session("rSisterAge2")=trim(Request.Form("txtSisterHouseNo2"))
    Session("rsisterClass2")=trim(Request.Form("cmbsClass2"))
    Session("rsistersection2")=trim(Request.Form("cmbsSection2"))
    Session("rsisterRemarks2")=trim(Request.Form("txtsRemarks2"))
    'relation details
	Session("rPerson1")=trim(Request.Form("txtPerson1"))
    Session("rRelation1")=trim(Request.Form("txtRelation1"))
	Session("rYear1")=trim(Request.Form("txtYear1"))
	Session("rPerson2")=trim(Request.Form("txtPerson2"))
    Session("rRelation2")=trim(Request.Form("txtRelation2"))
	Session("rYear2")=trim(Request.Form("txtYear2"))
	Session("rPerson3")=trim(Request.Form("txtPerson3"))
    Session("rRelation3")=trim(Request.Form("txtPerson3"))
	Session("rYear3")=trim(Request.Form("txtYear3"))
	'School Details
	Session("rclass") = Request.Form("cmbclass")
		
	Session("rsection") = Request.Form("cmbsection")
	Session("rIP") = Request.Form("cmbIP")
		
	Session("classjoindate")=Request.Form("txtjoindate")
	session("RegdNo")=Request.Form("txtRegdNo")
	'Session("AdmissionMonth")=Request.Form("cmbAdmissionMonth")
	Session("AdmissionMonth")=month(Request.Form("txtjoindate")) 'should in ID
	Session("Hostelreq")=Request.Form("cmbHostel")
	'Session("academicyear")=Request.Form("txtyear")
	'Session("academicyear")=year(Request.Form("txtjoindate"))
	Session("StudentCategory")=Request.Form("cmbStudentCategory")
	
	if Request.Form("chkSC") <> "" then
	Session("CategorySC")="Y"
	else
	Session("CategorySC")="N"
	end if 
	
	if Request.Form("chkOB") <> "" then
	Session("CategoryOB")="Y"
	else
	Session("CategoryOB")="N"
	end if 
	
	if Request.Form("chkBR") <> "" then
	Session("CategoryBR")="Y"
	else
	Session("CategoryBR")="N"
	end if 
	
	if Request.Form("chkGS") <> "" then
	Session("CategoryGS")="Y"
	else
	Session("CategoryGS")="N"
	end if 
	
	if Request.Form("chkNR") <> "" then
	Session("CategoryNR")="Y"
	else
	Session("CategoryNR")="N"
	end if
	
	if Request.Form("chkSIS") <> "" then
	Session("CategorySIS")="Y"
	else
	Session("CategorySIS")="N"
	end if  
	
	if Request.Form("chkWD") <> "" then
	Session("CategoryWD")="Y"
	else
	Session("CategoryWD")="N"
	end if  
	
	if Request.Form("chkDS") <> "" then
	Session("CategoryDS")="Y"
	else
	Session("CategoryDS")="N"
	end if  

	if Request.Form("chkRTE") <> "" then
	Session("CategoryRTE")="Y"
	else
	Session("CategoryRTE")="N"
	end if  
	
	session("Rebate")=Request.Form("txtRebate")
	
	if trim(Request.Form("txt_Amount")) = "" then
		session("ContributionAmount")=0
	else
		session("ContributionAmount")=trim(Request.Form("txt_Amount"))
	end if
	
	session("StatusOfContr")=trim(Request.Form("cmbStatusContr"))

	Response.Redirect (redirectpage)
end if%>

<html>
	<head>
		<link rel="stylesheet" href="/html_libs/style.css">
	<title><%="Mayo College, Ajmer : Personal Details Of "%><%=Session("rfirstName")%><%=" "%><%=Session("rlastName")%></title>
	</head>
	<body LANGUAGE="javascript">
		<%
	form_name = "frmstudentreg3"
	form_method = "post"
	form_title = "Student Registration - Parent's & Family Details"
	form_iconsrc = "/images/icon.gif"
	form_action = "studentreg3_edit.asp"
	form_showsubmit = true
	form_showsubmit1 = true
	form_showsubmit2 = false
	form_submitname = "NEXT"
	form_submit1name = "PREVIOUS"
	form_paging = false
	form_firstlink = ""
	form_prevlink = ""
	form_nextlink = ""
	form_lastlink = ""

%>
		<%startform()%>
		<script language="javascript">
function KeyPressCheck(txtfld)
{
alert("Please Click on the Link to select Date");
return false;
}


function cmbclass_onchange() 
{
/*	if (frmstudentreg3.txtyear.value == "" || isNaN(frmstudentreg3.txtyear.value))
		{
			alert("Please Enter Academic Year in Four Digit Format");
			frmstudentreg3.txtyear.value="";
			frmstudentreg3.txtyear.focus();
			return false;
		}*/
	document.frmstudentreg3.txhControl.value = "ClassChange";
	document.frmstudentreg3.submit();
}
function cmbsection_onchange() 
{
	/*if (frmstudentreg3.txtyear.value == "" || isNaN(frmstudentreg3.txtyear.value))
		{
			alert("Please Enter Academic Year in Four Digit Format");
			frmstudentreg3.txtyear.value="";
			frmstudentreg3.txtyear.focus();
			return false;
		}*/
	if (frmstudentreg3.cmbclass.value == "")
		{
			alert("Please Select Class");
			frmstudentreg3.cmbclass.focus();
			return false;
		}
	document.frmstudentreg3.txhControl.value = "ClassChange";
	document.frmstudentreg3.submit();
}


		
function frmstudentreg3_submit1()
{
	disable(false);
	
	document.frmstudentreg3.txhControl.value = "prev";
	document.frmstudentreg3.submit();
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

function frmstudentreg3_submit()
{
	disable(false);


	if (trim(frmstudentreg3.txtMotherName.value)=="")
	{
		alert("Please Enter Mother's Name");
		frmstudentreg3.txtMotherName.value="";
		frmstudentreg3.txtMotherName.focus();
		return false;
	}
		if (document.frmstudentreg3.cmbsection.value == "")
	{
		window.alert("Please Select Section");
		document.frmstudentreg3.cmbsection.focus();
		return false;
	}
	if (document.frmstudentreg3.cmbclass.value == "")
	{
		window.alert("Please Select Class");
		document.frmstudentreg3.cmbclass.focus();
		return false;
	}

		/*if (frmstudentreg3.txtjoindate.value == "")
		{
			alert("Please Enter Admission Date");
			frmstudentreg3.txtjoindate.focus();
			return false;
		}*/
		
	if (trim(frmstudentreg3.txtRegdNo.value == ""))
		{
			alert("Please Enter Registration No.");
			frmstudentreg3.txtRegdNo.focus();
			return false;
		}			

		if (frmstudentreg3.cmbHostel.value == "")
		{
			alert("Please Select Live in Out side Hostel");
			frmstudentreg3.cmbHostel.focus();
			return false;
		}	
		
		if (frmstudentreg3.cmbStudentCategory.value == "")
		{
			alert("Please Select Student Category");
			frmstudentreg3.cmbStudentCategory.focus();
			return false;
		}	
		if (isNaN(frmstudentreg3.txtRebate.value) == true)
		{
			alert("Please Enter Numeric Value");
			frmstudentreg3.txtRebate.value=""
			frmstudentreg3.txtRebate.focus();
			return false;
		}
	document.frmstudentreg3.txhControl.value  = "next";
	document.frmstudentreg3.submit();
}	

function disable(val)
{
for (i=0;i<document.frmstudentreg3.elements.length;i++)
		{
		if (document.frmstudentreg3.elements(i).type != "button")
		document.frmstudentreg3.elements(i).disabled=+val;
		}
}

function txtScholarNo_onblur()
{
	/*if (trim(frmstudentreg3.txtBrotherScholar1.value)=="")
	{
		alert("Please Enter Scholar No.");
		frmstudentreg3.txtBrotherScholar1.value="";
		frmstudentreg3.txtBrotherScholar1.focus();
        return false;
	}*/
	if (trim(frmstudentreg3.txtBrotherScholar1.value)!= " ")
	{
		document.frmstudentreg3.submit();
		//return true;
	}

}

function txtScholarNo1_onblur()
{
	/*if (trim(frmstudentreg3.txtBrotherScholar1.value)=="")
	{
		alert("Please Enter Scholar No.");
		frmstudentreg3.txtBrotherScholar1.value="";
		frmstudentreg3.txtBrotherScholar1.focus();
        return false;
	}*/
	if (trim(frmstudentreg3.txtBrotherScholar2.value)!="")
	{
		document.frmstudentreg3.submit();
	}
}

function txtScholarNo2_onblur()
{
	/*if (trim(frmstudentreg3.txtBrotherScholar1.value)=="")
	{
		alert("Please Enter Scholar No.");
		frmstudentreg3.txtBrotherScholar1.value="";
		frmstudentreg3.txtBrotherScholar1.focus();
        return false;
	}*/
	if (trim(frmstudentreg3.txtSisterScholar1.value)!="")
	{
		document.frmstudentreg3.submit();
	}
}

function txtScholarNo3_onblur()
{
	/*if (trim(frmstudentreg3.txtBrotherScholar1.value)=="")
	{
		alert("Please Enter Scholar No.");
		frmstudentreg3.txtBrotherScholar1.value="";
		frmstudentreg3.txtBrotherScholar1.focus();
        return false;
	}*/
	if (trim(frmstudentreg3.txtSisterScholar2.value)!="")
	{
		document.frmstudentreg3.submit();
	}
}

//==========================================================================================================
//On 1st sept 2012

function MothersOccupation_submit()
{
	document.frmstudentreg3.txhmoccupation.value  = "Yes";
	document.frmstudentreg3.submit();
}
//==========================================================================================================

</script>
<Div id='popCal' style='POSITION:absolute;visibility:hidden;border:2px ridge;width:10'>
<iframe name="popFrame" src="/html_libs/popcjs.htm" frameborder="0" scrolling="no" width="183" height="188"></iframe>
</Div>
<SCRIPT event="onclick()" for="document">popCal.style.visibility = "hidden";</SCRIPT>
<table class="formtable" width="91%">
		<input type="hidden" name="txhControl">
<!--=========================================================================================================
on 1st sept 2012-->
		<input type="hidden" name="txhmoccupation" ID="Hidden2">
<!--=========================================================================================================-->
		
			<!--<tr valign="top" align="left">
				<td class="keycell" colspan=2>
				Parent Login Id
				</td>
				<td width="50%" colspan=2>
					<%=session("pLogin")%>
				</td>
			</tr>-->
			
			<tr valign="top" align="left">
				<td width="50%" class="keycell" colSpan="3">
					Mother's Name <FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td colSpan="3">
					<input type="text" name="txtMotherName" style="WIDTH: 305px; HEIGHT: 22px" maxlength=50 size="41" value="<%=Session("rMotherName")%>" ID="Text5">
				</td>
			</tr>
			
			<TR>
				<TD class="keycell" colSpan="3" >
					Mother's Occupation
				</TD>
				<TD class="" colSpan="3">
					<SELECT name="cmbMotherOccupation" onChange="return MothersOccupation_submit();">
					<%FillProfession%>
				</SELECT>
				</TD>
			</TR>
			
<!--=================================================================================================================
on 1-Sept-2012 -->
			<TR>
				<TD class="keycell" colSpan="3">
					 Sub Occupation <FONT color="red"><STRONG>*</STRONG></FONT>
				</TD>
				<TD class="" colSpan="3">
				<SELECT name="cmbMotherSubOccupation">
					<%FillSubProfession%>
				</SELECT>
					<input name="txtMotherOccupation" style="WIDTH: 190px; HEIGHT: 22px" size="41" maxlength=50 value="<%=Session("rMotherOccupation")%>" ID="Text2">
				</TD>				
			</TR>
<!--=================================================================================================================-->

						
			<tr>
				<td class="keycell" colSpan="2" width="30%">
					Mother's Office Ph.
				</td>
				<TD class="" width="20%">
					<INPUT name="txtMotherOfficePhone" maxlength=20 style="WIDTH: 100px; HEIGHT: 22px" value="<%=Session("rMotherOfficePhone")%>" ID="Text7">
				</TD>
				<td class="keycell" colSpan="2" width="30%">
					Mother's Mobile 
				</td>
				<TD width="20%">
					<input style="WIDTH: 100px; HEIGHT: 22px" name="txtMotherMobilePhone" maxlength=20 value="<%=Session("rMotherMobilePhone")%>" ID="Text8">
				</TD>
			</tr>

			<TR>
				<TD class="keycell" colSpan="3" width="50%">
					Mother's Email
				</TD>
				<TD class="" colSpan="3" width="50%">
					<input name="txtMotherEmail" style="WIDTH: 305px; HEIGHT: 22px" MaxLength=50 size="41" value="<%=Session("rMotherEmail")%>" ID="Text9">
				</TD>
			</TR>
			<tr>
			
				<td class="keycell" colSpan="1" width="16%">Scholar No </td>
				<TD class="keycell" colSpan="1" width="30%">
					Brother's Name
				</TD>
		       	<TD class="keycell" colSpan="1" width="16%">
					Class 
				</TD>
				<TD class="keycell" colSpan="1" width="16%">
				Section 
				</TD>
			
			</tr>
			<tr>
				
				<td  colSpan="1"  width="16%">
					<input type="text" name="txtBrotherScholar1" style="WIDTH: 100px; HEIGHT: 22px" value="<%=vScholarNo%>" LANGUAGE=javascript onBlur="return txtScholarNo_onblur()" maxlength=5>	
					</td>
				<TD colSpan="1" width="30%">
					<input type="text" name="txtBrotherName1" style="WIDTH: 200px; HEIGHT: 22px" maxlength=50 value="<%=Session("rBrotherName1")%>" ID="Text10">
				</td>
				<TD colSpan="1" width="16%">
				<!-- <input type="text" name="txtBrotherClass1" style="WIDTH: 100px; HEIGHT: 22px" value="<%=Session("rBrotherClass1")%>">	-->
					 <select name="cmbbClass1" style="WIDTH: 80px; HEIGHT: 22px">
						<option value = "">Class</option>
						<%FillClass%>
				        </select> 
				</td>
				<TD colSpan="1" width="16%">
				
				<!-- <input type="text" name="txtBrotherSection1" style="WIDTH: 100px; HEIGHT: 22px" value="<%=Session("rBrotherSection1")%>"> --> 
						 <select name="cmbbSection1" style="WIDTH: 80px; HEIGHT: 22px">
						<option value = "" selected>Section</option>
						<option value="A"<%if trim(session("rbrothersection1"))="A" then%>selected<%end if%>>A</option>
						<option value="B"<%if trim(session("rbrothersection1"))="B" then%>selected<%end if%>>B</option>
						<option value="C"<%if trim(session("rbrothersection1"))="C" then%>selected<%end if%>>C</option>
						<option value="D"<%if trim(session("rbrothersection1"))="D" then%>selected<%end if%>>D</option>
						<option value="E"<%if trim(session("rbrothersection1"))="E" then%>selected<%end if%>>E</option>
						<option value="SCIENCE"<%if trim(session("rbrothersection1"))="SCIENCE" then%>selected<%end if%>>SCIENCE</option>
						<option value="Commerce"<%if trim(session("rbrothersection1"))="Commerce" then%>selected<%end if%>>Commerce</option>
						<option value="ARTS"<%if trim(session("rbrothersection1"))="ARTS" then%>selected<%end if%>>ARTS</option>
				         </select>	
				</td>
				
			</tr>
			<tr>
				<td  colSpan="1"  width="16%">
					<input type="text" name="txtBrotherScholar2" style="WIDTH: 100px; HEIGHT: 22px" value="<%=vScholarNo1%>" onBlur="return txtScholarNo1_onblur()" maxlength=5>	
				</td>
				<TD colSpan="1" width="30%">
					<input type="text" name="txtBrotherName2" style="WIDTH: 200px; HEIGHT: 22px" maxlength=50 value="<%=Session("rBrotherName2")%>" ID="Text12">
				</td>
				<TD colSpan="1" width="16%">	
					<select name="cmbbClass2" style="WIDTH: 80px; HEIGHT: 22px">
						<option value = "">Class</option>
						<%FillClass%>
				        </select>
				 </td>
				<TD colSpan="1" width="16%">		
					<select name="cmbbSection2" style="WIDTH: 80px; HEIGHT: 22px">
						<option value = "" selected>Section</option>
						<option value="A"<%if trim(session("rbrothersection2"))="A" then%>selected<%end if%>>A</option>
						<option value="B"<%if trim(session("rbrothersection2"))="B" then%>selected<%end if%>>B</option>
						<option value="C"<%if trim(session("rbrothersection2"))="C" then%>selected<%end if%>>C</option>
						<option value="D"<%if trim(session("rbrothersection2"))="D" then%>selected<%end if%>>D</option>
						<option value="E"<%if trim(session("rbrothersection2"))="E" then%>selected<%end if%>>E</option>
						<option value="SCIENCE"<%if trim(session("rbrothersection2"))="SCIENCE" then%>selected<%end if%>>SCIENCE</option>
						<option value="Commerce"<%if trim(session("rbrothersection2"))="Commerce" then%>selected<%end if%>>Commerce</option>
						<option value="ARTS"<%if trim(session("rbrothersection2"))="ARTS" then%>selected<%end if%>>ARTS</option>
				        </select>
				 </td>
				

			</tr>
			<tr>
				<td class="keycell" colSpan="1" width="16%">Scholar No </td>
		       	<TD class="keycell" colSpan="1" width="30%">
					Sister's Name
				</td>
				<TD class="keycell" colSpan="1" width="16%">
					Class 
				</TD>
				<TD class="keycell" colSpan="1" width="16%">
				Section 
				</TD>
				
			</tr>
			<tr>
				<td  colSpan="1"  width="16%">
					<input type="text" name="txtSisterScholar1" style="WIDTH: 100px; HEIGHT: 22px" value="<%=vScholarNo2%>" onBlur="return txtScholarNo2_onblur()" maxlength=5>	
				</td>	
				<TD colSpan="1" width="30%">
					<input type="text" name="txtSisterName1" style="WIDTH: 200px; HEIGHT: 22px" maxlength=50 value="<%=Session("rSisterName1")%>" ID="Text14">
				</td>
				<TD colSpan="1" width="16%">	
					<select name="cmbsClass1" style="WIDTH: 80px; HEIGHT: 22px">
						<option value = "">Class</option>
						<%FillClass%>
				        </select>
				</td>
				<TD colSpan="1" width="16%">		
				<select name="cmbsSection1" style="WIDTH: 80px; HEIGHT: 22px">
						<option value = "" selected>Section</option>
						<option value="A"<%if trim(session("rsistersection1"))="A" then%>selected<%end if%>>A</option>
						<option value="B"<%if trim(session("rsistersection1"))="B" then%>selected<%end if%>>B</option>
						<option value="C"<%if trim(session("rsistersection1"))="C" then%>selected<%end if%>>C</option>
						<option value="D"<%if trim(session("rsistersection1"))="D" then%>selected<%end if%>>D</option>
						<option value="E"<%if trim(session("rsistersection1"))="E" then%>selected<%end if%>>E</option>
						<option value="SCIENCE"<%if trim(session("rsistersection1"))="SCIENCE" then%>selected<%end if%>>SCIENCE</option>
						<option value="Commerce"<%if trim(session("rsistersection1"))="Commerce" then%>selected<%end if%>>Commerce</option>
						<option value="ARTS"<%if trim(session("rsistersection1"))="ARTS" then%>selected<%end if%>>ARTS</option>
				        </select>
				 </td>
				

			</tr>
			<tr>
				<td  colSpan="1"  width="16%">	
				<input type="text" name="txtSisterScholar2" style="WIDTH: 100px; HEIGHT: 22px" value="<%=vScholarNo3%>" onBlur="return txtScholarNo3_onblur()" maxlength=5>	
				</td>
				<TD colSpan="1" width="30%">
					<input type="text" name="txtSisterName2" style="WIDTH: 200px; HEIGHT: 22px" maxlength=50 value="<%=Session("rSisterName2")%>" ID="Text16">
				</td>
				<TD colSpan="1" width="16%">	
					<select name="cmbsClass2" style="WIDTH: 80px; HEIGHT: 22px">
						<option value = "">Class</option>
						<%FillClass %>
				        </select>
				</td>
				<TD colSpan="1" width="16%">		
				<select name="cmbsSection2" style="WIDTH: 80px; HEIGHT: 22px">
						<option value = "" selected>Section</option>
						<option value="A"<%if trim(session("rsistersection2"))="A" then%>selected<%end if%>>A</option>
						<option value="B"<%if trim(session("rsistersection2"))="B" then%>selected<%end if%>>B</option>
						<option value="C"<%if trim(session("rsistersection2"))="C" then%>selected<%end if%>>C</option>
						<option value="D"<%if trim(session("rsistersection2"))="D" then%>selected<%end if%>>D</option>
						<option value="E"<%if trim(session("rsistersection2"))="E" then%>selected<%end if%>>E</option>
							<option value="SCIENCE"<%if trim(session("rsistersection2"))="SCIENCE" then%>selected<%end if%>>SCIENCE</option>
						<option value="Commerce"<%if trim(session("rsistersection2"))="Commerce" then%>selected<%end if%>>Commerce</option>
						<option value="ARTS"<%if trim(session("rsistersection2"))="ARTS" then%>selected<%end if%>>ARTS</option>
				        </select>
				 </td>
				

			</tr>
			<tr>
				<td class="keycell" colspan="3" width="50%">
				Category 
				</td>
				<td class="normalcell" colspan="3" width="50%">
					<INPUT type="checkbox" name=chkNR value="NR" <%if trim(session("CategoryNR"))="Y" then%> checked <%end if%> width="15%">NR
					<INPUT type="checkbox" name=chkSc value="SC" <%if trim(session("CategorySC"))="Y" then%> checked <%end if%> width="15%">SC
					<INPUT type="checkbox" name=chkBR value="BR" <%if trim(session("CategoryBR"))="Y" then%> checked <%end if%> width="15%">BR
					<INPUT type="checkbox" name=chkSIS value="SIS" <%if trim(session("CategorySIS"))="Y" then%> checked <%end if%> width="15%">SIS
					<INPUT type="checkbox" name=chkWD value="WD" <%if trim(session("CategoryWD"))="Y" then%> checked <%end if%> width="15%">WD
					<INPUT type="checkbox" name=chkOB value="OB" <%if trim(session("CategoryOB"))="Y" then%> checked <%end if%> width="15%">OB
					<INPUT type="checkbox" name=chkGS value="GS" <%if trim(session("CategoryGS"))="Y" then%> checked <%end if%> width="15%">GS
					<INPUT type="checkbox" name=chkDS value="Ds" <%if trim(session("CategoryDS"))="Y" then%> checked <%end if%> width="15%">DS
					<INPUT type="checkbox" name=chkRTE value="RTE" <%if trim(session("CategoryRTE"))="Y" then%> checked <%end if%> width="15%">RTE
				</td>
			</tr>	
			<tr>
				<td class="keycell" colspan="2" width="30%">
				Rebate
				</td>
				<td align="left" valign="top" colspan="1" width="20%">
					<INPUT type="text" name=txtRebate align="right" style="width=100px;" value="<%=session("Rebate")%>">
				</td>
				<td class="keycell" width="30%"  colspan="2">
					Registration No <FONT color="red"><STRONG></STRONG></FONT>
				</td>
				<td class="normalcell"  colspan="1" width="20%">
					<input type=text name="txtRegdNo" align="right" style="width=100px;" value="<%=session("RegdNo")%>" maxlength=10>				
				
				</td>
			</tr>	
			<tr>
				<td class="keycell" width="50%" colspan="3" width="30%">
					Class/Section <FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td align="left" valign="top" width="20%" colspan="3">
					<select name="cmbclass" style="WIDTH: 80px; HEIGHT: 22px" LANGUAGE=javascript onChange="return cmbclass_onchange()">
						<option value="" selected>Class</option>
						<%
						dim rsclasses
						set rsclasses = Server.CreateObject("adodb.recordset")
						sstr = "select * from classes order by classname"
						rsclasses.Open sstr,Conn,1,3
						if not rsclasses.eof then
						do while not rsclasses.eof 
						%>
						<option value="<%=rsclasses("class_id")%>" <%if cint(Session("rclass"))=cint(rsclasses("class_id")) then%> selected <%end if%>><%=rsclasses("classname")%></option>
						<%
							rsclasses.movenext
							Loop
						end if
						rsclasses.close
						%>
					</select>
					
					<select name="cmbsection" style="WIDTH: 80px; HEIGHT: 22px" LANGUAGE=javascript onChange="return cmbsection_onchange()">
						<option value="">Section</option>
			<%	if trim(session("rclass")) <> "" then
			set rcs =server.CreateObject("adodb.recordset")
				sql="select * from t_class_sections where class_id="& cint(session("rclass"))
				rcs.Open sql,conn
				if not rcs.EOF then
				set temprs=server.CreateObject ("adodb.recordset")
				sql="select * from t_class_sections where class_id=" &session("rclass")
				'Response.Write sql
				temprs.Open sql,conn
					if not temprs.EOF then%>
					
						<%do while not temprs.eof %>
						<option value="<%=temprs("section_id")%>" <%if cstr(temprs("section_id"))=cstr(session("rsection")) then%>selected<%end if%>><%=temprs("section_name")%></option>
						<%temprs.movenext
						Loop
					 end if
				end if
				end if%>
				</select>
				<%	if trim(session("rclass")) =14  or trim(session("rclass"))=15 then%>
					<select name="cmbIP" >
				<option value = "Y"<%if trim(Session("rIP"))="Y" then%>selected<%end if%>>With IP</option>
				<option value = "N"<%if trim(Session("rIP"))="N" then%>selected<%end if%>>Without IP</option>
				</select>
				<%end if%>
				</td>
			</tr>
			
			<tr>		
				<td class="keycell" colspan="2" >
					Date Of Admission <FONT color="red"><STRONG></STRONG></FONT>
				</td>
				<td colspan="2">
					<input type="text" style="text-align:center;WIDTH: 100px" name="txtjoindate" LANGUAGE="javascript" onKeyPress="return KeyPressCheck(this)" value="<%=Ndate(Session("classjoindate"),"%d-%b-%Y") %>" ID="Text1">
					<input onClick="popFrame.fPopCalendar(txtjoindate,txtjoindate,popCal); return false" type="button" value="V" NAME="Button1" ID="Button1">
				
				</td>
				
				<!--
				<td class="keycell" colspan="2" width="30%">
					Admission Month/Year <FONT color="red"><STRONG></STRONG></FONT>
				</td>
				<td align="left" valign="top" colspan="1" width="20%">
					<select name="cmbAdmissionMonth" style="WIDTH: 80px; HEIGHT: 22px" ID="Select1">
					<option value="" selected>Month</option>
						<%FillMonth%>
					</select>
					<input type="text" style="WIDTH: 40px; HEIGHT: 22px" name="txtyear" value="<%=Session("academicyear")%>" maxlength=4>
				</td>-->
			</tr>
			
			<tr>
				<td class="keycell" colspan="2" width="30%">
					Live in Outside Hostel? <FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				
				<td align="left" valign="top" colspan="1" width="20%">
					
					<select name="cmbHostel" >
					
						<option value=""<%if Session("Hostelreq")="" then%>selected<%end if%>>Select</option>
						<option value="Y"<%if trim(Session("Hostelreq"))="Y" then %>selected<%end if%>>Yes</option>
						<option value="N"<%if Session("Hostelreq")="N" then%>selected<%end if%>>No</option>
					</select>
				</td>
				<td class="keycell" colspan="2" width="30%">Student Category<FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td align="left" valign="top" colspan="1" width="20%">
					<select name="cmbStudentCategory" style="WIDTH: 100px; HEIGHT: 22px" ID="Select4">
						<option value="">Category</option>
						<%FillStudentCategory%>
					</select>
				</td>
			</tr>

			<tr>
				<td class="keycell" colspan="2" id=text2 name=text2 width="30%">
					Swimming Pool Contribution Amount
				</td>
				<td align="left" valign="top" colspan="1"  width="20%">
	            	<input type="text" name="txt_Amount" id="txt_Amount" value="<%=session("ContributionAmount")%>" />
				</td  width="25%">

				<td class="keycell" colspan="2">
					Status Of Contribution
				</td>

				<td align="left" valign="top" colspan="1" width="25%"> 
					<select name="cmbStatusContr" style="WIDTH: 100px; HEIGHT: 22px">
						<option value="Y" <%if trim(session("StatusOfContr")) = "Y" then%> selected <%end if%>>Yes</option>
						<option value="N" <%if trim(session("StatusOfContr")) = "N" then%> selected <%end if%>>No</option>
					</select>
				</td>
			</tr>
			
			<tr class="keyrow">
				<td colspan="6">Relationship Details </td>
			</tr>
			<tr>
				<TD class="keycell" colspan="3" width="50%">
					Forth Generation Name
				</td>
				<TD class="keycell" colspan="2" width="30%">
					Relation
				</td>
				 <TD class="keycell" colspan="1" width="20%">
					Year
				</td>
			</tr>
			<tr>
				<TD colspan="3" width="50%">
					<input type="text" name="txtPerson1" style="WIDTH: 200px; HEIGHT: 22px" maxlength=50 size="41" value="<%=Session("rPerson1")%>" ID="Text18">
				</td>
			    
				<TD colspan="2" width="30%">
					<input type="text" name="txtRelation1" style="WIDTH: 200px; HEIGHT: 22px" maxlength=50 size="41" value="<%=Session("rRelation1")%>" ID="Text19">
				</td>
			   
				<TD colspan="1" width="20%">
					<input type="text" name="txtYear1" style="WIDTH: 50px; HEIGHT: 22px" maxlength=4 size="41" value="<%=Session("rYear1")%>" ID="Text20">
				</td>
			</tr>
			<tr>
				<TD class="keycell" colspan="3" width="50%">
					Fifth Generation Name
				</td>
				<TD class="keycell" colspan="2" width="30%">
					Relation
				</td>
				 <TD class="keycell" colspan="1" width="20%">
					Year
				</td>
			</tr>
			<tr>
				
				<TD colspan="3" width="50%">
					<input type="text" name="txtPerson2" style="WIDTH: 200px; HEIGHT: 22px" maxlength=50 size="41" value="<%=Session("rPerson2")%>" ID="Text21">
				</td>
			    
				<TD colspan="2" width="30%">
					<input type="text" name="txtRelation2" style="WIDTH: 200px; HEIGHT: 22px" maxlength=50 size="41" value="<%=Session("rRelation2")%>" ID="Text22">
				</td>
			    
				<TD colspan="1" width="20%">
					<input type="text" name="txtYear2" style="WIDTH: 50px; HEIGHT: 22px" maxlength=4 size="41" value="<%=Session("rYear2")%>" ID="Text23">
				</td>
			</tr>
			
			<TR>
				<TD align="right" colSpan="6">
					<font face="Verdana, Arial, Helvetica, sans-serif" size="2">Fields marked with <font color="red" size="3"><strong>*</strong></font>
							are mandatory</font>
				</TD>
			</TR>
		</table>
		<SCRIPT LANGUAGE="javascript">
			<!--
				document.frmstudentreg3.cmbbClass1.value ="<%=Session("rBrotherClass1")%>";
				document.frmstudentreg3.cmbbClass2.value ="<%=Session("rbrotherClass2")%>";
				document.frmstudentreg3.cmbsClass1.value ="<%=Session("rsisterClass1")%>";
				document.frmstudentreg3.cmbsClass2.value ="<%=Session("rsisterClass2")%>";
				
			document.frmstudentreg3.cmbHostel.value="<%=Session("hostelreq")%>"
		document.frmstudentreg3.cmbStudentCategory.value="<%=cdbl(Session("StudentCategory"))%>"
		//document.frmstudentreg3.cmbAdmissionMonth.value="<%=cint(Session("AdmissionMonth"))%>"
		
		
		
			//-->
			</SCRIPT>
		<%endform()
		if session("mode")="V" then%>
		<script language=javascript>
		disable(true);
		</script>
		<%end if%>
	</body>
</html>


