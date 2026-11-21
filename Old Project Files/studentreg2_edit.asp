<!--#include virtual="/asp_lib/DBConnect.asp"-->
<!--#include virtual="/asp_lib/displaymessage.asp"-->
<!--#include virtual="/html_libs/curlform.asp" -->
<%
OpenDB




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
temprs.close
end sub

'==============================================================================================================================================
'on 1-Sept-2012

if request.Form("txhfoccupation") = "Yes" then
Session("rFatherProfession") = trim(request.Form("cmbFatherOccupation"))
else
Session("rFatherProfession") = Session("rFatherProfession")
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

			<OPTION VALUE="<%=tempRs1("ProffessionId")%>"<%if trim(tempRs1("ProffessionId"))=trim(Session("rFatherProfession")) then%>selected<%end if%>><%=tempRs1("ProffessionName")%></OPTION>

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

private sub FillState()
	'Filling State from master
	dim tempRs1
	set tempRs1=server.CreateObject("adodb.recordset")
	Sql="Select * from T_State_Master order by StateName"
	tempRs1.Open sql,conn,1,3%>
	<option value="" selected>Select State</OPTION>
	<%do while tempRs1.EOF=false%>

			<OPTION VALUE="<%=tempRs1("StateId")%>"><%=tempRs1("StateName")%></OPTION>

	<%tempRs1.MoveNext
	LOOP
	tempRs1.Close 
end sub



if Request.Form("txhControl") = "prev" then redirectpage="studentreg1_edit.asp" end if
if Request.Form("txhControl") = "next" then redirectpage="studentreg3_edit.asp" end if
if Request.Form("txhControl") <> "" then
	if request.form("cmbFatherOccupation") <> "" then
	Session("rFatherprofession")=Trim(request.form("cmbFatherOccupation"))
	'On 1st sept 2012
	Session("rFatherSubProfession")=Trim(request.form("cmbFatherSubOccupation"))
	end if
	Session("rFathername")=Request.Form("txtFatherName")
	Session("rFatherOccupation")=request.form("txtFatherOccupation")
	Session("rFatherOccupation1")=request.form("txtFatherOccupation1")	
	Session("rFatherOfficePhone")=request.form("txtFatherOfficePhone")
	Session("rFatherMobilePhone")=trim(request.Form("txtFatherMobilePhone"))
	Session("rFatherEmail")=request.form("txtFatherEmail")	    	
	Session("rAddress1") = trim(Request.Form("txtAddress1"))
	Session("rAddress2")= trim(Request.Form("txtAddress2"))
	Session("rAddress3") = trim(Request.Form("txtAddress3"))
	Session("rCity")= trim(Request.Form("txtCity"))
	Session("State") = trim(Request.Form("cmbState"))
	Session("rCountry") = trim(Request.Form("cmbCountry"))
	Session("rZip")= trim(Request.Form("txtZip"))
	Session("rHomePhone") = trim(Request.Form("txtHomePhone"))
	Session("rCommAddress1")=request.form("txtCommAddress1")
	Session("rCommAddress2")=request.form("txtCommAddress2")
	Session("rCommAddress3")=request.form("txtCommAddress3")
	Session("rCommCity")=request.form("txtCommCity")
	Session("rCommState")=request.form("cmbCommState")
	Session("rCommCountry")=request.form("cmbCommCountry")
	Session("rCommZip")=request.form("txtCommZip")
	Session("rCommPhone")=request.form("txtCommPhone")
	Session("rStudentEmail")=trim(Request.Form("txtStudentEmail"))
	Session("rContactPerson") = trim(Request.Form("txtContactPerson"))
	Session("rContactRelation") = trim(Request.Form("txtContactRelation"))
	Session("rContactNumber") = trim(Request.Form("txtContactNumber"))
	Session("rContactEmergencyNumber") = trim(Request.Form("txtContactEmergencyNumber"))
	'Guardian's Address
	Session("rGuardianAddress1") = trim(Request.Form("txtGuardianAddress1"))
	Session("rGuardianAddress2")= trim(Request.Form("txtGuardianAddress2"))
	Session("rGuardianAddress3") = trim(Request.Form("txtGuardianAddress3"))
	Session("rGuardianCity")= trim(Request.Form("txtGuardianCity"))
	Session("rGuardianState") = trim(Request.Form("cmbGuardianState"))
	Session("rGuardianrCountry") = trim(Request.Form("cmbGuardianCountry"))
	Session("rGuardianrZip")= trim(Request.Form("txtGuardianZip"))
	Session("rGuardianrHomePhone") = trim(Request.Form("txtGuardianPhone"))
	Response.Redirect (redirectpage)
end if

%>
 <html>
<head>
<link rel="stylesheet" href="/html_libs/style.css">
<SCRIPT ID="clientEventHandlersJS" LANGUAGE="javascript">
<!--
function disable(val)
{
for (i=0;i<document.frmstudentreg2.elements.length;i++)
		{
		if (document.frmstudentreg2.elements(i).type != "button")
		document.frmstudentreg2.elements(i).disabled=+val;
		}
}

//-->
			</SCRIPT>
	<title><%="Mayoor School, Ajmer : Personal Details Of "%><%=Session("rfirstName")%><%=" "%><%=Session("rlastName")%></title>
	</head>
	<body >
   		<%
	form_name = "frmstudentreg2"
	form_method = "post"
	form_title = "Student Registration - Communication Details"
	form_iconsrc = "/images/icon.gif"
	form_action = "studentreg2_edit.asp"
	form_showsubmit = true
	form_showsubmit1 = true
	form_showsubmit2 = false
	form_submitname = "NEXT"
	form_submit1name = "PREVIOUS"


%>
		<%startform()%>
		<script language="javascript">

function chkSame_OnClick()
{
	if (document.frmstudentreg2.chkSame.checked == true)
	{
	
		document.frmstudentreg2.txtCommAddress1.value = document.frmstudentreg2.txtAddress1.value;
		document.frmstudentreg2.txtCommAddress2.value = document.frmstudentreg2.txtAddress2.value;
		document.frmstudentreg2.txtCommAddress3.value = document.frmstudentreg2.txtAddress3.value;
		document.frmstudentreg2.txtCommCity.value = document.frmstudentreg2.txtCity.value;	
		document.frmstudentreg2.cmbCommState.value = document.frmstudentreg2.cmbState.value;
		document.frmstudentreg2.cmbCommCountry.value = document.frmstudentreg2.cmbCountry.value;
		document.frmstudentreg2.txtCommZip.value = document.frmstudentreg2.txtZip.value;	
		document.frmstudentreg2.txtCommPhone.value = document.frmstudentreg2.txtHomePhone.value;


	}
	else
	{
		document.frmstudentreg2.txtCommAddress1.value = "";
		document.frmstudentreg2.txtCommAddress2.value = "";
		document.frmstudentreg2.txtCommAddress3.value = "";
		document.frmstudentreg2.txtCommCity.value = "";		
		document.frmstudentreg2.cmbCommState.value = "";		
		document.frmstudentreg2.cmbCommCountry.value = "";		
		document.frmstudentreg2.txtCommZip.value = "";		
		document.frmstudentreg2.txtCommPhone.value = "";		
	}	
	
}

function frmstudentreg2_submit1()
{
	disable(false);
	document.frmstudentreg2.txhControl.value = "prev";
	document.frmstudentreg2.submit();
}

function frmstudentreg2_submit()
{
	
	disable(false);
	if (frmstudentreg2.txtFatherName.value=='')
	{
		alert("Please Enter Father's Name");
		frmstudentreg2.txtFatherName.focus();
		return false;
	}
	else if (frmstudentreg2.txtFatherOccupation.value=='')
	{
		alert("Please Enter Occupation");
		frmstudentreg2.txtFatherOccupation.focus();
		return false;
	}
	
	if (frmstudentreg2.txtAddress1.value=='')
	{
		alert("Please Enter Address");
		frmstudentreg2.txtAddress1.focus();
		return false;
	}
    if (frmstudentreg2.txtCity.value=='')
	{
		alert("Please Enter City");
		frmstudentreg2.txtCity.focus();
		return false;
	}
    if (frmstudentreg2.cmbState.value=='')
	{
		alert("Please Select State");
		frmstudentreg2.cmbState.focus();
		return false;
	}
	if (frmstudentreg2.cmbCountry.value=='')
	{
		alert("Please Select Country");
		frmstudentreg2.cmbCountry.focus();
		return false;
	}
	/*if (isNaN(frmstudentreg2.txtZip.value))
		{
			alert("Please Enter Numeric Value");
			frmstudentreg2.txtZip.focus();
			return false;
		}	*/	
	

	if (frmstudentreg2.chkSame.checked == false)
	{
		if(frmstudentreg2.txtCommAddress1.value == "")
		{
			alert("Please Enter Communication Address");
			frmstudentreg2.txtCommAddress1.focus();
			return false;
		}
		if(frmstudentreg2.txtCommCity.value == "")
		{
			alert("Please Enter Communication City");
			frmstudentreg2.txtCommCity.focus();
			return false;
		}
		if(frmstudentreg2.cmbCommState.value == "")
		{
			alert("Please Select State");
			frmstudentreg2.cmbCommState.focus();
			return false;
		}
		if(frmstudentreg2.cmbCommCountry.value == "")
		{
			alert("Please Enter Communication Country");
			frmstudentreg2.cmbCommCountry.focus();
			return false;
		}		

		/*if (isNaN(frmstudentreg2.txtCommZip.value))
		{
			alert("Please Enter Postal Code");
			frmstudentreg2.txtCommZip.focus();
			return false;
		}	*/
	
		
	}
	document.frmstudentreg2.txhControl.value  = "next";
	document.frmstudentreg2.submit();
}

//==========================================================================================================
//On 1st sept 2012

function FathersOccupation_submit()
{
	document.frmstudentreg2.txhfoccupation.value  = "Yes";
	document.frmstudentreg2.submit();
}
//==========================================================================================================
		</script>
		<input type="hidden" name="txhControl" ID="Hidden1">

<!--=========================================================================================================
on 1st sept 2012-->
		<input type="hidden" name="txhfoccupation" ID="Hidden2">
<!--=========================================================================================================-->
		
		<table class="formtable" width="91%" border="0">
		<tr valign="top" align="left">
				<td width="50%" class="keycell" colSpan="3" valign="middle">
					Father's Name <FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td width="50%" colSpan="3">
					<input type="text" name="txtFatherName" style="WIDTH: 300px; HEIGHT: 22px" size="41" value="<%=Session("rFatherName")%>">
				</td>
			</tr>
			<TR>
				<TD class="keycell" colSpan="3">
					Father's Occupation <FONT color="red"><STRONG>*</STRONG></FONT>
				</TD>
				<TD class="" colSpan="3">
				<SELECT name="cmbFatherOccupation"  onChange="return FathersOccupation_submit();">
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
				<SELECT name="cmbFatherSubOccupation">
					<%FillSubProfession%>
				</SELECT>
					<input name="txtFatherOccupation" style="WIDTH: 190px; HEIGHT: 22px" size="41" maxlength=50 value="<%=Session("rFatherOccupation")%>" ID="Text1">
				</TD>				
			</TR>
			<TR>
				<TD class="keycell" colSpan="3">
					 Sub Occupation(1) <FONT color="red"><STRONG>*</STRONG></FONT>
				</TD>
				<TD class="" colSpan="3">
					<input name="txtFatherOccupation1" style="WIDTH: 190px; HEIGHT: 22px" size="41" maxlength=50 value="<%=Session("rFatherOccupation1")%>" ID="Text1">
				</TD>
			</TR>
			
<!--=================================================================================================================-->

			<tr>
				<td class="keycell" colSpan="2">
					Father's Office Ph.
				</td>
				<TD class="">
					<INPUT name="txtFatherOfficePhone" maxlength=20 style="WIDTH: 150px; HEIGHT: 22px" value="<%=Session("rFatherOfficePhone")%>" ID="Text2">
				</TD>
				<td class="keycell" colSpan="2">
					Father's Mobile 
				</td>
				<TD>
					<input style="WIDTH: 150px; HEIGHT: 22px" name="txtFatherMobilePhone" style="WIDTH: 150px; HEIGHT: 22px" maxlength=20 value="<%=Session("rFatherMobilePhone")%>" ID="Text3">
				</TD>
			</tr>
			<TR>
				<TD class="keycell" colSpan="3">
					Father's Email
				</TD>
				<TD class="" colSpan="3">
					<input name="txtFatherEmail" style="WIDTH: 300px; HEIGHT: 22px" MaxLength=50 size="41" value="<%=Session("rFatherEmail")%>" ID="Text4">
				</TD>
			</TR>
			<tr class="keyrow" valign="top" align="left">
				<td colSpan="6">
					Permanent Address
				</td>
			</tr>
			<tr valign="top" align="left">
				<td class="keycell" colSpan="3">
					Address Line 1<FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td colSpan="3">
					<input name="txtAddress1" style="WIDTH: 300px; HEIGHT: 22px" size="41" value="<%=Session("rAddress1")%>">
				</td>
			</tr>
			<tr valign="top" align="left">
				<td class="keycell" colSpan="3">Address Line 2</td>
				<td colSpan="3">
					<input name="txtAddress2" style="WIDTH: 300px; HEIGHT: 22px" size="41" value="<%=Session("rAddress2")%>">
				</td>
			</tr>
			<tr valign="top" align="left">
				<td class="keycell" colSpan="3">Address Line 3</td>
				<td colSpan="3">
					<input name="txtAddress3" style="WIDTH: 300px; HEIGHT: 22px" size="41" value="<%=Session("rAddress3")%>">
				</td>
			</tr>
			<TR>
				<TD class="keycell" colSpan="3">
					City<FONT color="red"><STRONG>*</STRONG></FONT>
				</TD>
				<TD class="" colSpan="3">
					<INPUT name="txtCity" style="WIDTH: 300px; HEIGHT: 22px" size="41" value="<%=Session("rCity")%>">
				</TD>
			</TR>
			<TR>
				<TD class="keycell" colSpan="2" style="WIDTH: 25%">
					State<FONT color="red"><STRONG>*</STRONG></FONT>
				</TD>
				<TD width="25%" style="WIDTH: 25%">
					<SELECT style="WIDTH: 150px; HEIGHT: 22px" name="cmbState"><%FillState%>
										
					</SELECT>
				</TD>		
				
				<TD class="keycell" colSpan="2" style="WIDTH: 25%">
					Country<FONT color="red"><STRONG>*</STRONG></FONT>
				</TD>
				<TD width="25%" style="WIDTH: 25%">
					<SELECT style="WIDTH: 150px; HEIGHT: 22px" name="cmbCountry"><%FillCountry%>
										
					</SELECT>
				</TD>
						

			</TR>
			<tr>
				<TD class="keycell" colSpan="2" style="WIDTH: 25%">
					Postal Code
				</TD>
				<TD width="25%" style="WIDTH: 25%">
					<INPUT name="txtZip" style="WIDTH: 150px; HEIGHT: 22px" value="<%=Session("rZip")%>" maxlength=6>
				</TD>
				<TD class="keycell" colSpan="2" style="WIDTH: 25%">
					Home Phone
				</TD>
				<TD width="25%" style="WIDTH: 25%">
					<input style="WIDTH: 150px; HEIGHT: 22px" name="txtHomePhone" value="<%=Session("rHomePhone")%>">
				</TD>
			</tr>			
		
			</table>
		<P>
			<table class="formtable" width="812">
				<tr class="keyrow">
					<td colspan="3" width="400">
						Address For Communication
					</td>
					<td colspan="3" width="398">
						Same as Above <input type="checkbox" name="chkSame" onClick="return chkSame_OnClick()" <%if Session("rSameAddress") = "Y" then%>checked<%end if%>>
					</td>
				</tr>
				<td class="keycell" colspan="3" width="400">
					Communication Address Line 1<FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td class="" colspan="3" width="398">
					<input name="txtCommAddress1" style="WIDTH: 300px; HEIGHT: 22px" size="41" value="<%=Session("rCommAddress1")%>">
				</td>
				<tr>
					<td class="keycell" colspan="3" width="400">
						Communication Address Line 2
					</td>
					<td class="" colspan="3" width="398">
						<input name="txtCommAddress2" style="WIDTH: 300px; HEIGHT: 22px" size="41" value="<%=Session("rCommAddress2")%>">
					</td>
				</tr>
				<tr>
					<td class="keycell" colspan="3" width="400">
						Communication Address Line 3
					</td>
					<td class="" colspan="3" width="398">
						<input name="txtCommAddress3" style="WIDTH: 300px; HEIGHT: 22px" size="41" value="<%=Session("rCommAddress3")%>">
					</td>
				</tr>
				<tr>
					<td class="keycell" colspan="3" width="400">
						City<FONT color="red"><STRONG>*</STRONG></FONT>
					</td>
					<td class="" colspan="3" width="398">
						<input name="txtCommCity" style="WIDTH: 300px; HEIGHT: 22px" size="41" value="<%=Session("rCommCity")%>">
					</td>
				</tr>
							<TR>
				<TD class="keycell" colSpan="2" width="197">
					State<FONT color="red"><STRONG>*</STRONG></FONT>
				</TD>
				<TD width="197">
					<SELECT style="WIDTH: 150px; HEIGHT: 22px" name="cmbCommState"><%FillState%>
										
					</SELECT>
				</TD>		
				
				<TD class="keycell" colSpan="2" width="196">
					Country<FONT color="red"><STRONG>*</STRONG></FONT>
				</TD>
				<TD width="196">
					<SELECT style="WIDTH: 150px; HEIGHT: 22px" name="cmbCommCountry"><%FillCountry%>
										
					</SELECT>
				</TD>
						

			</TR>

				<tr>
					<td class="keycell" colspan="2" width="197">
						Postal Code
					</td>
					<td width="197">
						<input name="txtCommZip" style="WIDTH: 150px; HEIGHT: 22px" value="<%=Session("rCommZip")%>" MAXLENGTH=6>
					</td>
					<td colspan="2" class="keycell" width="196">
						Phone
					</td>
					<td width="196">
						<input name="txtCommPhone"  style="WIDTH: 150px; HEIGHT: 22px" value="<%=Session("rCommPhone")%>">
					</td>
				</tr>
				<TR>
				<TD class="keycell" colSpan="3" width="400">
					Student Email
				</TD>
				<TD class="" colSpan="3" width="398">
					<input name="txtStudentEmail" style="WIDTH: 300px; HEIGHT: 22px" MaxLength=100 size="41" value="<%=Session("rStudentEmail")%>">
				</TD>
			</TR>
			</table>
		<P>
			<table class="formtable" width="91%" ID="Table1">
				<tr class="keyrow">
					<td colspan="6">
						Details of Guardian
					</td>
				</tr>
				<tr>
					<td class="keycell" colspan="2" style="WIDTH: 25%">
						Name of Guardian
					</td>
					<td style="WIDTH: 25%">
						<input type="text" style="WIDTH: 150px; HEIGHT: 22px" name="txtContactPerson" maxlength=50 value="<%=Session("rContactPerson")%>" ID="Text1">
					</td>
					<td colspan="2" class="keycell" style="WIDTH: 25%">
						Relationship with Guardian
					</td>
					<td style="WIDTH: 25%">
						<input type="text"  style="WIDTH: 150px; HEIGHT: 22px" name="txtContactRelation" maxlength=50 value="<%=Session("rContactRelation")%>" ID="Text2">
					</td>
				</tr>
				<tr>
					<td class="keycell" colspan="2" style="WIDTH: 25%">
						Guardian's Mobile Phone
					</td>
					<td style="WIDTH: 25%">
						<input type="text" style="WIDTH: 150px; HEIGHT: 22px" name="txtContactNumber" maxlength=15 value="<%=Session("rContactNumber")%>" ID="Text3">
					</td>
					<td colspan="2" class="keycell" style="WIDTH: 25%">
						Emergency Contact Number
					</td>
					<td style="WIDTH: 25%">
						<input type="text" style="WIDTH: 150px; HEIGHT: 22px" name="txtContactEmergencyNumber" maxlength=15 value="<%=Session("rContactEmergencyNumber")%>" ID="Text4">
					</td>
				</tr>
			</table>
			<table class="formtable" width="91%" ID="Table2">
				<tr class="keyrow">
					<td colspan="3">
						Guardian's Address
					</td>
					<td colspan="3">
					</td>
				</tr>
				<td class="keycell" colspan="3">
					Guardian's Address Line 1
				</td>
				<td class="" colspan="3">
					<input name="txtGuardianAddress1" style="WIDTH: 300px; HEIGHT: 22px" size="41" maxlength=100 value="<%=Session("rGuardianAddress1")%>" ID="Text5">
				</td>
				</tr>
				<tr>
					<td class="keycell" colspan="3">
						Guardian's Address Line 2
					</td>
					<td class="" colspan="3">
						<input name="txtGuardianAddress2" style="WIDTH: 300px; HEIGHT: 22px" size="41" maxlength=50 value="<%=Session("rGuardianAddress2")%>" ID="Text6">
					</td>
				</tr>
				<tr>
					<td class="keycell" colspan="3">
						Guardian's Address Line 3
					</td>
					<td class="" colspan="3">
						<input name="txtGuardianAddress3" style="WIDTH: 300px; HEIGHT: 22px" size="41" maxlength=50 value="<%=Session("rGuardianAddress3")%>" ID="Text7">
					</td>
				</tr>
				<tr>
					<td class="keycell" colspan="3">
						City
					</td>
					<td class="" colspan="3">
						<input name="txtGuardianCity" style="WIDTH: 300px; HEIGHT: 22px" size="41" maxlength=50 value="<%=Session("rGuardianCity")%>" ID="Text8">
					</td>
				</tr>
							<TR>
				<TD class="keycell" colSpan="2" style="WIDTH: 25%">
					State
				</TD>
				<TD width="25%" style="WIDTH: 25%">
					<SELECT style="WIDTH: 150px; HEIGHT: 22px" name="cmbGuardianState" ID="Select1">
					<%FillState%>
										
					</SELECT>
				</TD>		
				
				<TD class="keycell" colSpan="2" style="WIDTH: 25%">
					Country
				</TD>
				<TD width="25%" style="WIDTH: 25%">
					<SELECT style="WIDTH: 150px; HEIGHT: 22px" name="cmbGuardianCountry" ID="Select2">
					<%FillCountry%>
										
					</SELECT>
				</TD>
						

			</TR>

				<tr>
					<td class="keycell" colspan="2" style="WIDTH: 25%">
						Postal Code
					</td>
					<td style="WIDTH: 25%">
						<input name="txtGuardianZip" style="WIDTH: 150px; HEIGHT: 22px" value="<%=Session("rGuardianrZip")%>" MAXLENGTH=6 ID="Text9">
					</td>
					<td colspan="2" class="keycell" style="WIDTH: 25%">
						Guardian's Home Phone
					</td>
					<td style="WIDTH: 25%">
						<input name="txtGuardianPhone" style="WIDTH: 150px; HEIGHT: 22px" maxlength=15 value="<%=Session("rGuardianrHomePhone")%>" ID="Text10">
					</td>
				</tr>
			</table>
			<table class="formtable">	
				<tr>
					<td align="right" colspan="6" style="WIDTH: 25%">
						<font face="Verdana, Arial, Helvetica, sans-serif" size="2">Fields marked with <font color="red" size="3"><strong>*</strong></font> 
								are mandatory</font>
					</td>
				</tr>
			</table>
		<p>
			<SCRIPT LANGUAGE="javascript">
			<!--
				document.frmstudentreg2.cmbCountry.value ="<%=Session("rCountry")%>";
				document.frmstudentreg2.cmbCommCountry.value = "<%=Session("rCommCountry")%>";
				document.frmstudentreg2.cmbGuardianCountry.value = "<%=Session("rGuardianrCountry")%>";
				document.frmstudentreg2.cmbState.value ="<%=Session("State")%>";
				document.frmstudentreg2.cmbCommState.value = "<%=Session("rCommState")%>";
				document.frmstudentreg2.cmbGuardianState.value = "<%=Session("rGuardianState")%>"
			//-->
			</SCRIPT>
			
			<%endform()
			if session("mode")="V" then%>
		<script language=javascript>
		disable(true);
		</script>
		<%end if%>
		</p>
	</body>
</html>




