<!--#include virtual="/asp_lib/DBConnect.asp"-->
<!--#include virtual="/asp_lib/displaymessage.asp"-->
<!--#include virtual="/asp_lib/displaydate.asp"-->
<!--#include virtual="/asp_lib/clearsessionvariables.asp"-->
<Title>Confirm Application Details</Title>
<%
OpenDB
Response.Write Session("vDocs")
'Response.End 
dim rsclasses
set rsclasses = Server.CreateObject("adodb.recordset")
dim rsFun
set rsFun=server.CreateObject("adodb.recordset")
dim tempRs
set tempRs = server.CreateObject("adodb.recordset")
'procedure for filling boarding type

if Request.Form ("CmbClub")<>"" then 
vClubid=Request.Form ("CmbClub")
end if
if Request.Form ("CmbClub2")<>"" then 
vClubid2=Request.Form ("CmbClub2")
end if
if Request.Form ("CmbClub3")<>"" then 
vClubid3=Request.Form ("CmbClub3")
end if


'============================================================================================
'on 29 Aug 2012

vScholarNo =  session("rABrotherScholarno")
vScholarNo1 =  session("rABrotherScholarno1")
vScholarNo2 =  session("rASisterScholarno")
vScholarNo3 =  session("rASisterScholarno1")
if Request.Form("txtABrotherScholar") <> "" then
vScholarNo=Trim(Request.Form("txtABrotherScholar"))
Sql="select Name,class_id,section_name from v_Students where ScholarNo='"& vScholarNo & "'"
'response.Write(sql)
tempRs.Open sql,conn,1,3
 if tempRs.EOF =false then
		Session("rABrotherName")=tempRs.Fields("Name")
		Session("rABrotherClass")=tempRs.Fields("class_id")
		ELSE
	Session("rABrotherName")=""
	Session("rABrotherClass") = ""
	end if
end if
tempRs.Close 

if Request.Form("txtABrotherScholar1") <> "" then
vScholarNo1=Trim(Request.Form("txtABrotherScholar1"))
Sql="select Name,class_id,section_name from v_Students where ScholarNo='"& vScholarNo1 & "'"
'response.Write(sql)
tempRs.Open sql,conn,1,3
 if tempRs.EOF =false then
		Session("rABrotherName1")=tempRs.Fields("Name")
		Session("rABrotherClass1")=tempRs.Fields("class_id")
		ELSE
	Session("rABrotherName1")=""
	Session("rABrotherClass1") = ""
	end if
end if
tempRs.Close 

if Request.Form("txtASisterScholar") <> "" then
vScholarNo2=Trim(Request.Form("txtASisterScholar"))
Sql="select Name,class_id,section_name from v_Students where ScholarNo='"& vScholarNo2 & "'"
'response.Write(sql)
tempRs.Open sql,conn,1,3
 if tempRs.EOF =false then
		Session("rASisterName")=tempRs.Fields("Name")
		Session("rASisterClass")=tempRs.Fields("class_id")
		ELSE
		Session("rASisterName")=""
		Session("rASisterClass")=""
	end if
end if
tempRs.Close 

if Request.Form("txtASisterScholar1") <> "" then
vScholarNo3=Trim(Request.Form("txtASisterScholar1"))
Sql="select Name,class_id,section_name from v_Students where ScholarNo='"& vScholarNo3 & "'"
'response.Write(sql)
tempRs.Open sql,conn,1,3
 if tempRs.EOF =false then
		Session("rASisterName1")=tempRs.Fields("Name")
		Session("rASisterClass1")=tempRs.Fields("class_id")
		ELSE
		Session("rASisterName1")=""
		Session("rASisterClass1")=""
	end if
end if
tempRs.Close 
'============================================================================================



'for filling class name

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

private sub fillFirst()
	sstr = "select * from T_Club_master where clubTypeid in(select clubTypeid from T_class_club where class_id="&Session("rclass")&")order by ClubName"
	rsclasses.Open sstr,Conn,1,3
	
	if not rsclasses.EOF  then
		do while not rsclasses.eof 
		%>
		
		<option value="<%=rsclasses("Clubid")%>" <%if cstr(rsclasses("Clubid"))=cstr(trim((vClubId))) then %>selected<%end if%>><%=rsclasses("Clubname")%></option>
		<%
		rsclasses.movenext
		Loop
	end if
	rsclasses.close
end sub
private sub FillSecond()
	if trim(vClubId) <>"" then
	sql="select * from T_Club_master where clubId <>"&vClubId&" and clubTypeid in(select clubTypeid from T_class_club where class_id="&Session("rclass")&")order by ClubName"
	rsFun.Open sql,conn,1,3
	if not rsFun.EOF then
		while not rsFun.EOF
			%>
			<option value="<%=rsFun("Clubid")%>" <%if cstr(rsFun("Clubid"))=cstr(trim((vClubId2))) then %>selected<%end if%>><%=rsFun("Clubname")%></option>
			<%
		rsFun.MoveNext
		wend
	end if
	rsFun.Close
	end if
end sub
private sub FillThird()
	if vClubId <>"" and vClubId2 <>"" then
	sql="select * from T_Club_master where clubId <>"&vClubId&" and clubId <>"&vClubId2&" and clubTypeid in(select clubTypeid from T_class_club where class_id="&Session("rclass")&") order by ClubName"
	rsFun.Open sql,conn,1,3
	if not rsFun.EOF then
		while not rsFun.EOF
			%>
			<option value="<%=rsFun("Clubid")%>" <%if cstr(rsFun("Clubid"))=cstr(trim((vClubId3))) then %>selected<%end if%>><%=rsFun("Clubname")%></option>
			<%
		rsFun.MoveNext
		wend
	end if
	rsFun.Close
	end if
end sub
err.clear
if Request.Form("txhControl")="Next" then
	Session("Club1") = Request.Form("cmbClub")
	Session("Club2") = Request.Form("cmbClub2")
	Session("Club3") = Request.Form("cmbClub3")	
	Session("vChValue")=trim(Request.Form("Ch"))

'==============================================================================================
'on 29th Aug 2012
	session("rABrotherScholarno") = trim(Request.Form("txtABrotherScholar"))
	Session("rABrotherName")=trim(Request.Form("txtABrotherName"))
	session("rABFromYear") = trim(Request.Form("cmbABFromYear"))
	session("rABToYear") = trim(Request.Form("cmbABToYear"))
	Session("rABrotherClass")=trim(Request.Form("cmbABClass"))

	session("rABrotherScholarno1") = trim(Request.Form("txtABrotherScholar1"))
	Session("rABrotherName1")=trim(Request.Form("txtABrotherName1"))
	session("rABFromYear1") = trim(Request.Form("cmbABFromYear1"))
	session("rABToYear1") = trim(Request.Form("cmbABToYear1"))
	Session("rABrotherClass1")=trim(Request.Form("cmbABClass1"))

	session("rASisterScholarno") = trim(Request.Form("txtASisterScholar"))
	Session("rASisterName")=trim(Request.Form("txtASisterName"))
	session("rASFromYear") = trim(Request.Form("cmbASFromYear"))
	session("rASToYear") = trim(Request.Form("cmbASToYear"))
	Session("rASisterClass")=trim(Request.Form("cmbASClass"))

	session("rASisterScholarno1") = trim(Request.Form("txtASisterScholar1"))	
	Session("rASisterName1")=trim(Request.Form("txtASisterName1"))
	session("rASFromYear1") = trim(Request.Form("cmbASFromYear1"))
	session("rASToYear1") = trim(Request.Form("cmbASToYear1"))
	Session("rASisterClass1")=trim(Request.Form("cmbASClass1"))
	
'==============================================================================================

	Response.Redirect "studentreg_edit_confirm.asp"
end if
if Request.Form("txhControl")="previous" then
	Session("Club1") = Request.Form("cmbClub")
	Session("Club2") = Request.Form("cmbClub2")
	Session("Club3") = Request.Form("cmbClub3")	
	Session("vChValue")=trim(Request.Form("Ch"))

'==============================================================================================

	session("rABrotherScholarno") = trim(Request.Form("txtABrotherScholar"))
	Session("rABrotherName")=trim(Request.Form("txtABrotherName"))
	session("rABFromYear") = trim(Request.Form("cmbABFromYear"))
	session("rABToYear") = trim(Request.Form("cmbABToYear"))
	Session("rABrotherClass")=trim(Request.Form("cmbABClass"))

	session("rABrotherScholarno1") = trim(Request.Form("txtABrotherScholar1"))
	Session("rABrotherName1")=trim(Request.Form("txtABrotherName1"))
	session("rABFromYear1") = trim(Request.Form("cmbABFromYear1"))
	session("rABToYear1") = trim(Request.Form("cmbABToYear1"))
	Session("rABrotherClass1")=trim(Request.Form("cmbABClass1"))

	session("rASisterScholarno") = trim(Request.Form("txtASisterScholar"))
	Session("rASisterName")=trim(Request.Form("txtASisterName"))
	session("rASFromYear") = trim(Request.Form("cmbASFromYear"))
	session("rASToYear") = trim(Request.Form("cmbASToYear"))
	Session("rASisterClass")=trim(Request.Form("cmbASClass"))

	session("rASisterScholarno1") = trim(Request.Form("txtASisterScholar1"))	
	Session("rASisterName1")=trim(Request.Form("txtASisterName1"))
	session("rASFromYear1") = trim(Request.Form("cmbASFromYear1"))
	session("rASToYear1") = trim(Request.Form("cmbASToYear1"))
	Session("rASisterClass1")=trim(Request.Form("cmbASClass1"))
'==============================================================================================

	Response.Redirect "studentreg5_edit.asp"
end if

if request.form("txhControl")="goback" then
	
		'if session("ptype") = "2" then
		'Response.Redirect "/modules/studentmgt/registration/studentstempedit/studentreg1_edit.asp"
		'else
		clearsessionvariables
		Response.Redirect "/modules/studentmgt/registration/common_frame.asp?mode=V&file=/modules/studentmgt/registration/preapplication/applicant_view.asp"
		'end if
		
end if	

%>
<html>
	<head>
		<script language="JavaScript" src="/js_lib/date-picker.js"></script>
		
		<link rel="stylesheet" href="/html_libs/style.css">
	</head>
	<body> <!-- #include virtual="/html_libs/curlform.asp" -->
		<%
	form_name = "frmStudentreg6"
	form_method = "post"
	
	form_iconsrc = "/images/icon.gif"
	form_action = "StudentregActivity.asp"
	
	if session("mode") = "V" then
	form_showsubmit = false
	form_showsubmit1 = false
	form_showsubmit2 = true
	form_submit2name = "BACK"	
	form_title = "Complete Application Details"
	else	
	form_showsubmit = true
	form_showsubmit1 = true
	form_showsubmit2 = false
	
	form_submitname = "NEXT"
	form_submit1name = "PREVIOUS"
	form_title = "Complete Application Details"
	end if	
	form_paging = false
	form_firstlink = ""
	form_prevlink = ""
	form_nextlink = ""
	form_lastlink = ""

%>
		<%startform()%>
<SCRIPT LANGUAGE="javascript">
function frmStudentreg6_submit()
{
	
				
	
	document.frmStudentreg6.txhControl.value = "Next";
	document.frmStudentreg6.submit();
}
function frmStudentreg6_submit1()
{

	document.frmStudentreg6.txhControl.value = "previous";
	document.frmStudentreg6.submit();
}
function frmStudentreg6_submit2()
{
	document.frmStudentreg6.txhControl.value = "goback";
	document.frmStudentreg6.submit();

}


//==============================================================================================
//on 29th Aug 2012

function txtScholarNo_onblur()
{
	if (frmStudentreg6.txtABrotherScholar.value!= "")
	{
		document.frmStudentreg6.submit();		
	}

}


function txtScholarNo1_onblur()
{
	if (frmStudentreg6.txtABrotherScholar1.value!= "")
	{
		document.frmStudentreg6.submit();		
	}
}

function txtScholarNo2_onblur()
{
	if (frmStudentreg6.txtASisterScholar.value!= "")
	{
		document.frmStudentreg6.submit();		
	}
}

function txtScholarNo3_onblur()
{
	if (frmStudentreg6.txtASisterScholar1.value!= "")
	{
		document.frmStudentreg6.submit();		
	}
}

//==============================================================================================

    </script>
		
<table class="formtable" width="91%">
			<input type="hidden" name="txhControl" value=""></input>
			<tr>
				<td class="keycell" align="center" width="50%" colspan="3">
					CCA CLUB
				</td>
			</tr>
			<tr>
				<td class="keycell" width="50%" colspan="1">
					First Choice <FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td align="left" valign="top"  colspan="2">
					<select name="cmbClub" style="WIDTH: 120px; HEIGHT: 22px" language="javascript" onChange="javascript:frmStudentreg6.submit()">
						<option value="">Please Select</option>
						<%fillFirst%>
					</select>
				</td>
			</tr>
			<tr>
				<td class="keycell" width="50%" colspan="1">
					Second Choice <FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td align="left" valign="top"  colspan="2">
					<select name="cmbClub2" style="WIDTH: 120px; HEIGHT: 22px" language="javascript" onChange="javascript:frmStudentreg6.submit()">
						<option value="">Please Select</option>
						<%fillSecond%>
					</select>
				</td>
			</tr>
			<tr>
				<td class="keycell" width="50%" colspan="1">
					Second Choice <FONT color="red"><STRONG>*</STRONG></FONT>
				</td>
				<td align="left" valign="top"  colspan="2">
					<select name="cmbClub3" style="WIDTH: 120px; HEIGHT: 22px" language="javascript" onChange="javascript:frmStudentreg6.submit()">
						<option value="">Please Select</option>
						<%fillThird%>
					</select>
				</td>
			</tr>
			<tr>
				<td class="keycell" align="center" width="50%" colspan="3">
					Activity Interest
				</td>
				
			</tr>	
					
			<%
			set rsDoc = server.CreateObject("ADODB.Recordset")
			rsDoc.CursorLocation=3
			set rsStDoc = server.CreateObject("ADODB.Recordset")
			rsStDoc.CursorLocation=3
			
			
			myQl="select * from T_Activity_Master"
			rsDoc.Open myQl,conn,1,3
			count=cint(rsDoc.RecordCount)					
			rsDoc.MoveFirst%>
			<input type = "hidden" name = "vDoc" value = "<%=count%>">
			<%while not rsDoc.EOF
							
			%>
			
			<tr valign="top" align="left">
			
			
				<td class="keycell" width="2%">						
					<input type="checkbox" name="Ch" value="<%=rsDoc("Activityid")%>" >
				<font face="Verdana, Arial, Helvetica, sans-serif" size="2"><%=rsDoc("Activityname")%></font>
				</td>
											
				
										
			</tr>
			<%	
			rsStDoc.Close				
			rsDoc.MoveNext
			wend
			rsDoc.Close
			%>
				
				<%'-----------------------------------%>
			
			
			</tr>
		</table>
<!--==============================================================================================
on 29th Aug 2012-->

		<table class="formtable" width="91%">
			<tr>
				<td class="keycell" align="left"  style="width:100%" colspan="3">
					<b><u>Alumni Entry</u></b>
				</td>
			</tr>	

			<tr>			
				<TD class="keycell" colSpan="1" width="15%">Scholar No </TD>
   				<td class="keycell" colSpan="1" width="30%">Brother's Name</td>
			   	<TD class="keycell" colSpan="1" width="20%">From Year</TD>
				<TD class="keycell" colSpan="1" width="20%">To Year</TD>				
			   	<TD class="keycell" colSpan="1" width="15%">Last Class</TD>
			</tr>

			<tr>				
				<td  colSpan="1"  width="15%">
					<input type="text" name="txtABrotherScholar"  value="<%=vScholarNo%>" LANGUAGE=javascript onBlur="return txtScholarNo_onblur()" maxlength=5 style="WIDTH: 100px; HEIGHT: 22px">	
				</td>
				<TD colSpan="1" width="30%">
					<input type="text" name="txtABrotherName" value="<%=Session("rABrotherName")%>" style="WIDTH: 200px; HEIGHT: 22px">
				</td>
				<TD colSpan="1" width="20%">
					 <select name="cmbABFromYear" style="WIDTH: 100px; HEIGHT: 22px">
						<option value = "">Year</option>
						<option value = "1990">1990</option>
						<option value = "1992">1992</option>
						<option value = "1993">1993</option>
						<option value = "1994">1994</option>
						<option value = "1995">1995</option>
						<option value = "1996">1996</option>
						<option value = "1997">1997</option>
						<option value = "1998">1998</option>
						<option value = "1999">1999</option>
						<option value = "2000">2000</option>
						<option value = "2001">2001</option>
						<option value = "2002">2002</option>
						<option value = "2003">2003</option>
						<option value = "2004">2004</option>
						<option value = "2005">2005</option>
						<option value = "2006">2006</option>
						<option value = "2007">2007</option>
						<option value = "2008">2008</option>
						<option value = "2009">2009</option>
						<option value = "2010">2010</option>
						<option value = "2011">2011</option>
						<option value = "2012">2012</option>
						<option value = "2013">2013</option>
						<option value = "2014">2014</option>
						<option value = "2015">2015</option>
						<option value = "2016">2016</option>
						<option value = "2017">2017</option>
						<option value = "2018">2018</option>
						<option value = "2019">2019</option>
						<option value = "2020">2020</option>
						<option value = "2021">2021</option>
						<option value = "2022">2022</option>
						<option value = "2023">2023</option>
						<option value = "2024">2024</option>
						<option value = "2025">2025</option>						
				        </select> 
				</td>

				<TD colSpan="1" width="20%">
					 <select name="cmbABToYear" style="WIDTH: 100px; HEIGHT: 22px">
						<option value = "">Year</option>
						<option value = "1990">1990</option>
						<option value = "1992">1992</option>
						<option value = "1993">1993</option>
						<option value = "1994">1994</option>
						<option value = "1995">1995</option>
						<option value = "1996">1996</option>
						<option value = "1997">1997</option>
						<option value = "1998">1998</option>
						<option value = "1999">1999</option>
						<option value = "2000">2000</option>
						<option value = "2001">2001</option>
						<option value = "2002">2002</option>
						<option value = "2003">2003</option>
						<option value = "2004">2004</option>
						<option value = "2005">2005</option>
						<option value = "2006">2006</option>
						<option value = "2007">2007</option>
						<option value = "2008">2008</option>
						<option value = "2009">2009</option>
						<option value = "2010">2010</option>
						<option value = "2011">2011</option>
						<option value = "2012">2012</option>
						<option value = "2013">2013</option>
						<option value = "2014">2014</option>
						<option value = "2015">2015</option>
						<option value = "2016">2016</option>
						<option value = "2017">2017</option>
						<option value = "2018">2018</option>
						<option value = "2019">2019</option>
						<option value = "2020">2020</option>
						<option value = "2021">2021</option>
						<option value = "2022">2022</option>
						<option value = "2023">2023</option>
						<option value = "2024">2024</option>
						<option value = "2025">2025</option>						
				        </select> 
				</td>

				<TD colSpan="1" width="15%">
					 <select name="cmbABClass" id="cmbABClass" style="WIDTH: 80px; HEIGHT: 22px">
						<option value = "">Class</option>
						<%FillClass%>
				        </select> 
				</td>
			</tr>

			<tr>				
				<td  colSpan="1"  width="15%">
					<input type="text" name="txtABrotherScholar1"  value="<%=vScholarNo1%>" LANGUAGE=javascript onBlur="return txtScholarNo1_onblur()" maxlength=5 style="WIDTH: 100px; HEIGHT: 22px">	
				</td>
				<TD colSpan="1" width="30%">
					<input type="text" name="txtABrotherName1" value="<%=Session("rABrotherName1")%>" style="WIDTH: 200px; HEIGHT: 22px">
				</td>
				<TD colSpan="1" width="20%">
					 <select name="cmbABFromYear1" style="WIDTH: 100px; HEIGHT: 22px">
						<option value = "">Year</option>
						<option value = "1990">1990</option>
						<option value = "1992">1992</option>
						<option value = "1993">1993</option>
						<option value = "1994">1994</option>
						<option value = "1995">1995</option>
						<option value = "1996">1996</option>
						<option value = "1997">1997</option>
						<option value = "1998">1998</option>
						<option value = "1999">1999</option>
						<option value = "2000">2000</option>
						<option value = "2001">2001</option>
						<option value = "2002">2002</option>
						<option value = "2003">2003</option>
						<option value = "2004">2004</option>
						<option value = "2005">2005</option>
						<option value = "2006">2006</option>
						<option value = "2007">2007</option>
						<option value = "2008">2008</option>
						<option value = "2009">2009</option>
						<option value = "2010">2010</option>
						<option value = "2011">2011</option>
						<option value = "2012">2012</option>
						<option value = "2013">2013</option>
						<option value = "2014">2014</option>
						<option value = "2015">2015</option>
						<option value = "2016">2016</option>
						<option value = "2017">2017</option>
						<option value = "2018">2018</option>
						<option value = "2019">2019</option>
						<option value = "2020">2020</option>
						<option value = "2021">2021</option>
						<option value = "2022">2022</option>
						<option value = "2023">2023</option>
						<option value = "2024">2024</option>
						<option value = "2025">2025</option>						
				        </select> 
				</td>

				<TD colSpan="1" width="20%">
					 <select name="cmbABToYear1" style="WIDTH: 100px; HEIGHT: 22px">
						<option value = "">Year</option>
						<option value = "1990">1990</option>
						<option value = "1992">1992</option>
						<option value = "1993">1993</option>
						<option value = "1994">1994</option>
						<option value = "1995">1995</option>
						<option value = "1996">1996</option>
						<option value = "1997">1997</option>
						<option value = "1998">1998</option>
						<option value = "1999">1999</option>
						<option value = "2000">2000</option>
						<option value = "2001">2001</option>
						<option value = "2002">2002</option>
						<option value = "2003">2003</option>
						<option value = "2004">2004</option>
						<option value = "2005">2005</option>
						<option value = "2006">2006</option>
						<option value = "2007">2007</option>
						<option value = "2008">2008</option>
						<option value = "2009">2009</option>
						<option value = "2010">2010</option>
						<option value = "2011">2011</option>
						<option value = "2012">2012</option>
						<option value = "2013">2013</option>
						<option value = "2014">2014</option>
						<option value = "2015">2015</option>
						<option value = "2016">2016</option>
						<option value = "2017">2017</option>
						<option value = "2018">2018</option>
						<option value = "2019">2019</option>
						<option value = "2020">2020</option>
						<option value = "2021">2021</option>
						<option value = "2022">2022</option>
						<option value = "2023">2023</option>
						<option value = "2024">2024</option>
						<option value = "2025">2025</option>						
				        </select> 
				</td>

				<TD colSpan="1" width="15%">
					 <select name="cmbABClass1" id="cmbABClass1" style="WIDTH: 80px; HEIGHT: 22px">
						<option value = "">Class</option>
						<%FillClass%>
				        </select> 
				</td>
			</tr>

			<tr>			
				<TD class="keycell" colSpan="1" width="15%">Scholar No </TD>
   				<td class="keycell" colSpan="1" width="30%">Sister's Name</td>
			   	<TD class="keycell" colSpan="1" width="20%">From Year</TD>
				<TD class="keycell" colSpan="1" width="20%">To Year</TD>				
			   	<TD class="keycell" colSpan="1" width="15%">Last Class</TD>
			</tr>

			<tr>				
				<td  colSpan="1"  width="15%">
					<input type="text" name="txtASisterScholar"  value="<%=vScholarNo2%>" LANGUAGE=javascript onBlur="return txtScholarNo2_onblur()" maxlength=5 style="WIDTH: 100px; HEIGHT: 22px">	
				</td>
				<TD colSpan="1" width="30%">
					<input type="text" name="txtASisterName" value="<%=Session("rASisterName")%>" style="WIDTH: 200px; HEIGHT: 22px">
				</td>
				<TD colSpan="1" width="20%">
					 <select name="cmbASFromYear" style="WIDTH: 100px; HEIGHT: 22px">
						<option value = "">Year</option>
						<option value = "1990">1990</option>
						<option value = "1992">1992</option>
						<option value = "1993">1993</option>
						<option value = "1994">1994</option>
						<option value = "1995">1995</option>
						<option value = "1996">1996</option>
						<option value = "1997">1997</option>
						<option value = "1998">1998</option>
						<option value = "1999">1999</option>
						<option value = "2000">2000</option>
						<option value = "2001">2001</option>
						<option value = "2002">2002</option>
						<option value = "2003">2003</option>
						<option value = "2004">2004</option>
						<option value = "2005">2005</option>
						<option value = "2006">2006</option>
						<option value = "2007">2007</option>
						<option value = "2008">2008</option>
						<option value = "2009">2009</option>
						<option value = "2010">2010</option>
						<option value = "2011">2011</option>
						<option value = "2012">2012</option>
						<option value = "2013">2013</option>
						<option value = "2014">2014</option>
						<option value = "2015">2015</option>
						<option value = "2016">2016</option>
						<option value = "2017">2017</option>
						<option value = "2018">2018</option>
						<option value = "2019">2019</option>
						<option value = "2020">2020</option>
						<option value = "2021">2021</option>
						<option value = "2022">2022</option>
						<option value = "2023">2023</option>
						<option value = "2024">2024</option>
						<option value = "2025">2025</option>						
				        </select> 
				</td>

				<TD colSpan="1" width="20%">
					 <select name="cmbASToYear" style="WIDTH: 100px; HEIGHT: 22px">
						<option value = "">Year</option>
						<option value = "1990">1990</option>
						<option value = "1992">1992</option>
						<option value = "1993">1993</option>
						<option value = "1994">1994</option>
						<option value = "1995">1995</option>
						<option value = "1996">1996</option>
						<option value = "1997">1997</option>
						<option value = "1998">1998</option>
						<option value = "1999">1999</option>
						<option value = "2000">2000</option>
						<option value = "2001">2001</option>
						<option value = "2002">2002</option>
						<option value = "2003">2003</option>
						<option value = "2004">2004</option>
						<option value = "2005">2005</option>
						<option value = "2006">2006</option>
						<option value = "2007">2007</option>
						<option value = "2008">2008</option>
						<option value = "2009">2009</option>
						<option value = "2010">2010</option>
						<option value = "2011">2011</option>
						<option value = "2012">2012</option>
						<option value = "2013">2013</option>
						<option value = "2014">2014</option>
						<option value = "2015">2015</option>
						<option value = "2016">2016</option>
						<option value = "2017">2017</option>
						<option value = "2018">2018</option>
						<option value = "2019">2019</option>
						<option value = "2020">2020</option>
						<option value = "2021">2021</option>
						<option value = "2022">2022</option>
						<option value = "2023">2023</option>
						<option value = "2024">2024</option>
						<option value = "2025">2025</option>						
				        </select> 
				</td>

				<TD colSpan="1" width="15%">
					 <select name="cmbASClass" id="cmbASClass" style="WIDTH: 80px; HEIGHT: 22px">
						<option value = "">Class</option>
						<%FillClass%>
				        </select> 
				</td>
			</tr>

			<tr>				
				<td  colSpan="1"  width="15%">
					<input type="text" name="txtASisterScholar1"  value="<%=vScholarNo3%>" LANGUAGE=javascript onBlur="return txtScholarNo3_onblur()" maxlength=5 style="WIDTH: 100px; HEIGHT: 22px">	
				</td>
				<TD colSpan="1" width="30%">
					<input type="text" name="txtASisterName1" value="<%=Session("rASisterName1")%>" style="WIDTH: 200px; HEIGHT: 22px">
				</td>
				<TD colSpan="1" width="20%">
					 <select name="cmbASFromYear1" style="WIDTH: 100px; HEIGHT: 22px">
						<option value = "">Year</option>
						<option value = "1990">1990</option>
						<option value = "1992">1992</option>
						<option value = "1993">1993</option>
						<option value = "1994">1994</option>
						<option value = "1995">1995</option>
						<option value = "1996">1996</option>
						<option value = "1997">1997</option>
						<option value = "1998">1998</option>
						<option value = "1999">1999</option>
						<option value = "2000">2000</option>
						<option value = "2001">2001</option>
						<option value = "2002">2002</option>
						<option value = "2003">2003</option>
						<option value = "2004">2004</option>
						<option value = "2005">2005</option>
						<option value = "2006">2006</option>
						<option value = "2007">2007</option>
						<option value = "2008">2008</option>
						<option value = "2009">2009</option>
						<option value = "2010">2010</option>
						<option value = "2011">2011</option>
						<option value = "2012">2012</option>
						<option value = "2013">2013</option>
						<option value = "2014">2014</option>
						<option value = "2015">2015</option>
						<option value = "2016">2016</option>
						<option value = "2017">2017</option>
						<option value = "2018">2018</option>
						<option value = "2019">2019</option>
						<option value = "2020">2020</option>
						<option value = "2021">2021</option>
						<option value = "2022">2022</option>
						<option value = "2023">2023</option>
						<option value = "2024">2024</option>
						<option value = "2025">2025</option>						
				        </select> 
				</td>

				<TD colSpan="1" width="20%">
					 <select name="cmbASToYear1" style="WIDTH: 100px; HEIGHT: 22px">
						<option value = "">Year</option>
						<option value = "1990">1990</option>
						<option value = "1992">1992</option>
						<option value = "1993">1993</option>
						<option value = "1994">1994</option>
						<option value = "1995">1995</option>
						<option value = "1996">1996</option>
						<option value = "1997">1997</option>
						<option value = "1998">1998</option>
						<option value = "1999">1999</option>
						<option value = "2000">2000</option>
						<option value = "2001">2001</option>
						<option value = "2002">2002</option>
						<option value = "2003">2003</option>
						<option value = "2004">2004</option>
						<option value = "2005">2005</option>
						<option value = "2006">2006</option>
						<option value = "2007">2007</option>
						<option value = "2008">2008</option>
						<option value = "2009">2009</option>
						<option value = "2010">2010</option>
						<option value = "2011">2011</option>
						<option value = "2012">2012</option>
						<option value = "2013">2013</option>
						<option value = "2014">2014</option>
						<option value = "2015">2015</option>
						<option value = "2016">2016</option>
						<option value = "2017">2017</option>
						<option value = "2018">2018</option>
						<option value = "2019">2019</option>
						<option value = "2020">2020</option>
						<option value = "2021">2021</option>
						<option value = "2022">2022</option>
						<option value = "2023">2023</option>
						<option value = "2024">2024</option>
						<option value = "2025">2025</option>
				        </select> 
				</td>

				<TD colSpan="1" width="15%">
					 <select name="cmbASClass1" id="cmbASClass1" style="WIDTH: 80px; HEIGHT: 22px">
						<option value = "">Class</option>
						<%FillClass%>
				        </select> 
				</td>
			</tr>
<!--==============================================================================================-->

			
			<TR>
				<TD align="right" colSpan="6" height="19">
					<font face="Verdana, Arial, Helvetica, sans-serif" size="2">Fields marked with <font color="red" size="3"><strong>*</strong></font>
							are mandatory</font>
				</TD>
			</TR>
		</table>
			
		
		<%CloseDB%>
		<SCRIPT LANGUAGE="javascript">
		//==============================================================================================
		//on 29th Aug 2012

			document.frmStudentreg6.cmbABClass.value ="<%=Session("rABrotherClass")%>";
			document.frmStudentreg6.cmbABClass1.value ="<%=Session("rABrotherClass1")%>";
			document.frmStudentreg6.cmbASClass.value ="<%=Session("rASisterClass")%>";
			document.frmStudentreg6.cmbASClass1.value ="<%=Session("rASisterClass1")%>";
		//==============================================================================================


		</script>
		<%endform()%>

	</body>
</html>