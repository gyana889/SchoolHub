<%@ LANGUAGE = VBScript.Encode %>
<!--#include virtual="/asp_lib/DBConnect.asp"-->
<!--#include virtual="/asp_lib/displaymessage.asp"-->
<!--#include virtual="/asp_lib/displaydate.asp"-->
<!--#include virtual="/asp_lib/clearsessionvariables.asp"-->
<%
OpenDB
'soring the class and section and rollno fo comparing
if Request.QueryString("next")="y" then
	session("editschoolid")=session("schoolid")
	session("edityear")=session("academicyear")
end if
err.clear
dim rsFill
set rsFill=server.CreateObject("Adodb.recordset")
'procedure for filling boarding category
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
if Request.Form("txhControl")="Submit" then
	Session("rclass") = Request.Form("cmbclass")	
	Session("rsection") = Request.Form("cmbsection")	
	Session("classjoindate")=Request.Form("txtjoindate")
	Session("AdmissionMonth")=Request.Form("cmbAdmissionMonth")
	Session("Hostelreq")=Request.Form("cmbHostel")
	Session("academicyear")=Request.Form("txtyear")
	session("comments")=trim(Request.Form("txtComments"))
	Session("StudentCategory")=Request.Form("cmbStudentCategory")
	
	session("RegdNo")=Request.Form("txtRegdNo")
	session("ScholarNo")=Request.Form("txtScholarNo")
	session("HouseNo")=Request.Form("txtHouseNo")
	session("OldHouseNo")=Request.Form("txtOldHouseNo")
	session("DBBDS")=Request.Form("txtDBBDS")
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
	session("Rebate")=Request.Form("txtRebate")
	
	Response.Redirect "studentreg_edit_confirm.asp"
end if
if Request.Form("txhControl")="previous" then
	Session("rclass") = Request.Form("cmbclass")
	Session("rsection") = Request.Form("cmbsection")	
	Session("classjoindate")=Request.Form("txtjoindate")
	Session("Hostelreq")=Request.Form("cmbHostel")
	Session("academicyear")=Request.Form("txtyear")
	session("comments")=trim(Request.Form("txtComments"))
	Session("StudentCategory")=Request.Form("cmbStudentCategory")
	session("RegdNo")=Request.Form("txtRegdNo")
	session("ScholarNo")=Request.Form("txtScholarNo")
	session("HouseNo")=Request.Form("txtHouseNo")
	session("OldHouseNo")=Request.Form("txtOldHouseNo")
	session("DBBDS")=Request.Form("txtDBBDS")
	Response.Redirect "studentreg5_edit.asp"
end if
if Request.Form("txhControl")="ClassChange" then
	
	Session("rclass") = Request.Form("cmbclass")	
	Session("rsection") = Request.Form("cmbsection")	
	Session("classjoindate")=Request.Form("txtjoindate")
	Session("Hostelreq")=Request.Form("cmbHostel")
	Session("StudentCategory")=Request.Form("cmbStudentCategory")
	Session("academicyear")=Request.Form("txtyear")
	session("comments")=trim(Request.Form("txtComments"))
	session("ScholarNo")=Request.Form("txtScholarNo")
	session("HouseNo")=Request.Form("txtHouseNo")
	session("OldHouseNo")=Request.Form("txtOldHouseNo")
	session("DBBDS")=Request.Form("txtDBBDS")
	session("RegdNo")=Request.Form("txtRegdNo")

end if

if request.form("txhControl")="goback" then
	
		'if session("ptype") = "2" then
		'Response.Redirect "/modules/studentmgt/registration/studentstempedit/studentreg1_edit.asp"
		'else
		clearsessionvariables
		if session("UserType")="S" then
		Response.Redirect "/modules/studentmgt/registration/StudentsTempEdit/studentreg1_edit.asp?ID="&session("UserId") &"&mode=V&ptype=2&Type=2"
		else
		Response.Redirect "/modules/studentmgt/registration/common_frame.asp?mode=V&file=/modules/studentmgt/registration/StudentsTempEdit/student_view.asp"
		end if
		'end if
		
end if	

%>
<html>
	<head>
		<script language="JavaScript" src="/js_lib/date-picker.js"></script>
		<link rel="stylesheet" href="/html_libs/style.css">
	<title><%="Mayo College, Ajmer : Personal Details Of "%><%=Session("rfirstName")%><%=" "%><%=Session("rlastName")%></title>
	</head>
	<body> <!-- #include virtual="/html_libs/curlform.asp" -->
		<%
	form_name = "frmStudentreg6"
	form_method = "post"
	
	form_iconsrc = "/images/icon.gif"
	form_action = "studentreg6_edit.asp"
	
	if session("mode") = "V" then
		form_showsubmit = false
		form_showsubmit1 = false
		form_showsubmit2 = true
		form_submit2name = "BACK"	
		form_title = "Complete Student Registration"
	else	
		form_showsubmit = true
		form_showsubmit1 = true
		form_showsubmit2 = false
		form_submitname = "SUBMIT"
		form_submit1name = "PREVIOUS"
		form_title = "Complete Student Registration"
	end if	
	form_paging = false
	form_firstlink = ""
	form_prevlink = ""
	form_nextlink = ""
	form_lastlink = ""

%>
		<%startform()%>
<SCRIPT LANGUAGE="javascript">
function KeyPressCheck(txtfld)
{
alert("Please Click on the Link to select Date");
return false;
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
						alert('Please Enter Date In dd-MON-YYYY format'); 
						return false; 
					} 

					if (unvalidenddate != validenddate)
					{ 
						alert('Please Enter Date In dd-MON-YYYY format'); 
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

function cmbclass_onchange() {
	if (frmStudentreg6.txtyear.value == "" || isNaN(frmStudentreg6.txtyear.value))
		{
			alert("Please Enter Academic Year in Four Digit Format");
			frmStudentreg6.txtyear.value="";
			frmStudentreg6.txtyear.focus();
			return false;
		}
	document.frmStudentreg6.txhControl.value = "ClassChange";
	document.frmStudentreg6.submit();
}
function cmbsection_onchange() 
{
	if (frmStudentreg6.txtyear.value == "" || isNaN(frmStudentreg6.txtyear.value))
		{
			alert("Please Enter Academic Year in Four Digit Format");
			frmStudentreg6.txtyear.value="";
			frmStudentreg6.txtyear.focus();
			return false;
		}
	if (frmStudentreg6.cmbclass.value == "")
		{
			alert("Please Select Class");
			frmStudentreg6.cmbclass.focus();
			return false;
		}
	document.frmStudentreg6.txhControl.value = "ClassChange";
	document.frmStudentreg6.submit();
}
function frmStudentreg6_submit()
{
disable(false);
	if (frmStudentreg6.txtyear.value == "" || isNaN(frmStudentreg6.txtyear.value))
		{
			alert("Please Enter Academic Year in Four Digit Format");
			frmStudentreg6.txtyear.value="";
			frmStudentreg6.txtyear.focus();
			return false;
		}

	
		if (frmStudentreg6.txtRegdNo.value == "")
		{
			alert("Please Enter Registration No.");
			frmStudentreg6.txtRegdNo.focus();
			return false;
		}	
		
		if (frmStudentreg6.txtHouseNo.value == "")
		{
			alert("Please Enter House No");
			frmStudentreg6.txtHouseNo.focus();
			return false;
		}	
		
	document.frmStudentreg6.txhControl.value = "Submit";
	document.frmStudentreg6.submit();
}

function frmStudentreg6_submit1()
{
disable(false);
	document.frmStudentreg6.txhControl.value = "previous";
	document.frmStudentreg6.submit();
}
function frmStudentreg6_submit2()
{
disable(false);
	document.frmStudentreg6.txhControl.value = "goback";
	document.frmStudentreg6.submit();

}
function disable(val)
{
for (i=0;i<document.frmStudentreg6.elements.length;i++)
		{
		if (document.frmStudentreg6.elements(i).type != "button")
		document.frmStudentreg6.elements(i).disabled=+val;
		}
}

</script>
<Div id='popCal' style='POSITION:absolute;visibility:hidden;border:2px ridge;width:10'>
		<iframe name="popFrame" src="/html_libs/popcjs.htm" frameborder="0" scrolling="no" width="183" height="188"></iframe>
</Div>
		<SCRIPT event="onclick()" for="document">popCal.style.visibility = "hidden";</SCRIPT>
		
<table width="100%" class="formtable">
			<input type="hidden" name="txhControl" value=""></input>
			<tr class="keyrow">
<td colspan=4 align=center><b><font size="2">Current School Details</font></b></td>
</tr>
			<!--<tr>
				<td class="keycell" colspan="1">
					Academic Year <FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td width="50%">
						<input type="text" style="WIDTH: 200px" name="txtyear" value="<%=Session("academicyear")%>" maxlength=4>
				</td>
			</tr>-->
			
			<tr valign="middle">
				<td class="keycell" width="50%">
					Registration No <FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td class="normalcell">
					<input type=text name="txtRegdNo" align="right" style="width=250;" value="<%=session("RegdNo")%>" maxlength=10>				
				
				</td>
			</tr>
				
			
			<tr valign="middle">
				<td class="keycell" width="50%">
					House No <FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td class="normalcell">
					<input type=text name="txtHouseNo" align="right" style="width=250;" value="<%=session("HouseNo")%>" maxlength=15 ID="Text5">				
				
				</td>
			</tr>
			<tr valign="middle">
				<td class="keycell" width="50%">
					Old House No 
				</td>
				<td class="normalcell">
					<input type=text name="txtOldHouseNo" align="right" style="width=250;" value="<%=session("OldHouseNo")%>" maxlength=15 ID="Text5">				
				
				</td>
			</tr>
			<tr>
				<td class="keycell" colspan="1">
					Date Of DBBDS <FONT color="red"><STRONG></STRONG></FONT>
				</td>
				<td width="50%">
					<input type="text" style="text-align:center;WIDTH: 100px" name="txtDBBDS" value="<%=Ndate(Session("DBBDS"),"%d-%b-%Y") %>" LANGUAGE="javascript" onkeypress="return KeyPressCheck(this)"  ID="Text1">
					<input onclick="popFrame.fPopCalendar(txtDBBDS,txtDBBDS,popCal); return false" type="button" value="V" NAME="Button1" ID="Button1">
				
				</td>
			</tr>
						<tr valign="middle">
				<td class="keycell" width="50%">
					Comments
				</td>
				<td class="normalcell">
					<textarea name="txtComments" cols="30" rows="4"><%=session("comments")%></textarea>
				</td>
			</tr>
			<tr>
				<td align="right" colspan="6" style="WIDTH: 25%">
					<font face="Verdana, Arial, Helvetica, sans-serif" size="2">Fields marked with <font color="red" size="3"><strong>*</strong></font> 
							are mandatory</font>
				</td>
			</tr>
		</table>
		<script>
		<!--
		document.frmStudentreg6.cmbHostel.value="<%=Cdbl(Session("hostelreq"))%>"
		document.frmStudentreg6.cmbStudentCategory.value="<%=cdbl(Session("StudentCategory"))%>"
		document.frmStudentreg6.cmbAdmissionMonth.value="<%=cint(Session("AdmissionMonth"))%>"
		
		
		-->
		</script>
		<%CloseDB%>
		<%endform()
		if session("mode")="V" then%>
		<script language=javascript>
		disable(true);
		</script>
		<%end if%>

	</body>
</html>
