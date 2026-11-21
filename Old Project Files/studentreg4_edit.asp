<%@ LANGUAGE = VBScript.Encode %>
<!--#include virtual="/asp_lib/DBConnect.asp"-->
<!--#include virtual="/asp_lib/displaymessage.asp"-->
<!--#include virtual="/html_libs/curlform.asp" -->

<%
OpenDb
'response.Write Session("oUID")
Response.Write Session("AdmissionMonth")
Response.Write Session("academicyear")

dim vNumRow  'Assign this Variable to Show the Number of Subject Lines to be displayed
vNumRow = 10
'Session("TempQ_id") = "" 
if Request.Form("txhControl") = "prev" then 
		Response.Redirect  "studentreg3_edit.asp"
end if

Function GetNextTempSchoolNumber()
	Dim rsTemp
	set rsTemp = server.CreateObject("Adodb.recordset")
	sstr = "select max(Temp_ID) MaxNum from student_schools"
	rsTemp.Open sstr,conn,1,3
	if isnull(rsTemp("MaxNum")) then
		GetNextTempSchoolNumber = 1
	else
		GetNextTempSchoolNumber = Cint(rsTemp("MaxNum"))+1
	end if
End Function
'response.Write session("mode")
if Request.Form("txhControl") = "next" then
	if Session("Mode")<>"V" and norecord <> true then	
		'delete the old records
		sql="delete from student_schools where student_id=" & Session("oUID")
		Conn.execute sql 
	 
	 	'Insert records into Student Academic Report Table
		Session("TempQ_id") = GetNextTempSchoolNumber
		for i = 1 to vNumRow
			if Request.Form("txtFromDate" & i) <> "" then
				sql="insert into student_schools(temp_id,student_id,from_date,to_date,school_name,Address) values(" & session("TempQ_id") & "," & Session("oUID") & "," & Request.Form("txtFromDate" & i) & "," & Request.Form("txtToDate" & i) & ",'" & replace(Request.Form("txtOrganisation" & i),"'","''") & "','" & replace(Request.Form("txtDesignation" & i),"'","") & "')"
				conn.execute sql
			else
				sql="insert into student_schools(temp_id,student_id) values(" & session("TempQ_id") & "," & Session("oUID") & ")"
				conn.execute sql
			end if
		Next			
	end if
  		Response.Redirect "studentreg5_edit.asp"			
end if

%>
<html>
	<head>
		<link rel="stylesheet" href="/html_libs/style.css">
	<title><%="Mayo College, Ajmer : Personal Details Of "%><%=Session("rfirstName")%><%=" "%><%=Session("rlastName")%></title>
	</head>
	<body>
		<%
	form_name = "frmstudentreg4"
	form_method = "post"
	form_title = "Student Previous School Details"
	form_iconsrc = "/images/icon.gif"
	form_action = "studentreg4_edit.asp"
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
	form_showaudit = false
	form_audit_tablename = "STAFF"
	form_audit_rowid = ""
%>
		
		<script language="javascript">
function frmstudentreg4_submit1()
{
		disable(false);
	document.frmstudentreg4.txhControl.value = "prev";
	document.frmstudentreg4.submit();
}

function YearOnBlur(txtfld)
{
if (txtfld.value != "")
	{
		var vDate = new Date();
		var vYear = vDate.getFullYear();
			if (isNaN(txtfld.value) == true)
			{
				alert("Please Enter a Valid Year");
				txtfld.select();
				return false;
			}
			if (txtfld.value.length != 4)
			{
				alert("Year Value should be Four Digits");
				txtfld.select();
				return false;
			}		
			if (txtfld.value > vYear)
			{
				alert("Entered Year is greater than current Year. Please Check");
				txtfld.select();
				return false;
			}		
			
			if (txtfld.value < (vYear - 35) )
			{
				alert("Entered Year is Very Less than the Current Year. Please Check");
				txtfld.select();
				return false;
			}
			
			
	}
}


//call the function 


function frmstudentreg4_submit()
{
		disable(false);
	var i;
	var j;
	var n = 1;
	var fromDate,tempFDate,toDate,TempTDate,tempFMon,tempTmon;	
	theDate = new Date();
	<%for i = 1 to vNumRow%>
	if (frmstudentreg4.txtFromDate<%=i%>.value != "" || frmstudentreg4.txtToDate<%=i%>.value != "" || frmstudentreg4.txtOrganisation<%=i%>.value != "" || frmstudentreg4.txtDesignation<%=i%>.value != "")
	{
		if (frmstudentreg4.txtFromDate<%=i%>.value == "" || isNaN(frmstudentreg4.txtFromDate<%=i%>.value))
		{
			alert("Please Enter From Year In 4 Digit Format");
			frmstudentreg4.txtFromDate<%=i%>.focus();
			return false;
		}
		if (frmstudentreg4.txtToDate<%=i%>.value == "" || isNaN(frmstudentreg4.txtToDate<%=i%>.value))
		{
			alert("Please Enter To Year In 4 Digit Format");
			frmstudentreg4.txtToDate<%=i%>.focus();
			return false;
		}
			
		if (trim(frmstudentreg4.txtOrganisation<%=i%>.value) == "")
		{
			alert("Please Enter School Name.");
			frmstudentreg4.txtOrganisation<%=i%>.focus();
			return false;
		}		
		if (trim(frmstudentreg4.txtDesignation<%=i%>.value) == "")
		{
			alert("Please Enter Address.");
			frmstudentreg4.txtDesignation<%=i%>.focus();
			return false;
		}
		if (frmstudentreg4.txtFromDate<%=i%>.value != "" && frmstudentreg4.txtToDate<%=i%>.value != "")
		{
			if (parseInt(frmstudentreg4.txtFromDate<%=i%>.value) > parseInt(frmstudentreg4.txtToDate<%=i%>.value))
			{
			alert("From Year Can Not Be Greater Than To Year");
			frmstudentreg4.txtFromDate<%=i%>.focus();
			return false;
			}
		}				
	}
	<%next%>
	
	<%for j = 1 to vNumRow%>
	if (frmstudentreg4.txtFromDate<%=j%>.value != "" && frmstudentreg4.txtToDate<%=j%>.value != "" && frmstudentreg4.txtOrganisation<%=j%>.value != "" && frmstudentreg4.txtDesignation<%=j%>.value != "")
	{
		n = n + 1;
	}
	<%next%>
	
	document.frmstudentreg4.txhControl.value  = "next";
	document.frmstudentreg4.submit();
}	
function trim(par)
{	
	y=par.length;
	//alert(y);
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

function disable(val)
{
for (i=0;i<document.frmstudentreg4.elements.length;i++)
		{
		if (document.frmstudentreg4.elements(i).type != "button")
		document.frmstudentreg4.elements(i).disabled=+val;
		}
}

		</script>

		<%startform()
		sstr = "select * from student_schools where student_id = " & Session("oUID") & " order by from_date desc"
			set rs = Conn.execute(sstr)		
				if (Session("oUID") = "") or rs.eof  then
				%> 
		<table class="formtable" width="80%">
			
			<tr class="keyrow" valign="middle" align="left">
				<td  >
					<div align="center">
						Sl. No.
					</div>
				</td>
				<td>
					<div align="center">
						From Year
					</div>
				</td>
				<td  >
					<div align="center">
						To Year
					</div>
				</td>
				<td >
					<div>
						School Name
					</div>
				</td>
				<td >
					<div>
						Address
					</div>
				</td>

			</tr>
			<%for i = 1 to vNumRow
				%>
			<tr valign="middle" align="left">
				<td class="keycell">
					<div align="right">
						<%=i%>
					</div>
				</td>
				<div align="center">
				<td  class="keycell">
						<input type="text" style="text-align:center;WIDTH: 60px" name = "txtFromDate<%=i%>">
				</td>
				
				</div>	
				<div align="center">
				<td  class="keycell">
						<input type="text" style="text-align:center;WIDTH: 60px" name = "txtToDate<%=i%>">
				</td>
				
				</div>
				<td  class="keycell">
					<div align="center">
						<input type="text" name="txtOrganisation<%=i%>" size="30" maxlength="40" value="">
					</div>
				</td>
				<td  class="keycell">
					<div align="center">
						<input type="text" name="txtDesignation<%=i%>" size="25" maxlength="40" value="">
					</div>
				</td>
				
			</tr>
			<%next%>
			<input type="hidden" name="txhControl">
		</table>
		<%else
		%>
		<table class="formtable" width="91%">
			
			<tr class="keyrow" valign="middle" align="left">
				<td  >
					<div align="center">
						Sl. No.
					</div>
				</td>
				<td  >
					<div align="center">
						From Year
					</div>
				</td>
				<td  >
					<div align="center">
						To Year
					</div>
				</td>
				<td >
					<div align="center">
						School Name
					</div>
				</td>
				<td >
					<div align="center">
						Address
					</div>
				</td>

			</tr>
			<%
			if not rs.eof then
				norecord=true
				rs.movefirst
				m = 1
				do while not rs.eof
				'if isnull(rs("from_date")) then
				'	Session("TFromDate") = ""
				'	Session("TToDate") = ""
				'else
					Session("TFromDate") = rs("from_date")
					Session("TToDate") = rs("to_date")
				'end if 
				
			%>
			<tr valign="middle" align="left">
				<td class="keycell" >
					<div align="right">
						<%=m%>
					</div>
				</td>
				
				<div align="center">
				<td  class="keycell">
						<input type="text" style="text-align:center;WIDTH: 60px" name = "txtFromDate<%=m%>" value="<%=Session("TFromDate")%>">
				</td>
				
				</div>	
				<div align="center">
				<td  class="keycell">
						<input type="text" style="text-align:center;WIDTH: 60px" name = "txtToDate<%=m%>" value="<%=Session("TToDate")%>">
				</td>
				
				</div>
				<td  class="keycell">
					<div align="center">
						<input type="text" name="txtOrganisation<%=m%>" size="30" maxlength="50" value="<%=rs("school_name")%>">
					</div>
				</td>
				<td  class="keycell">
					<div align="center">
						<input type="text" name="txtDesignation<%=m%>" size="25" maxlength="50" value="<%=rs("Address")%>">
					</div>
				</td>
				
			</tr>
			<%
			rs.movenext
			m = m + 1
			Loop
			end if
			%>
			<input type="hidden" name="txhControl" ID="Hidden1">
		</table>
		<%end if%>
		<SCRIPT LANGUAGE="javascript">
<!--

//-->
		</SCRIPT>
		<%endform()%>
		<%CloseDb
		if session("mode")="V" then%>
		<script language=javascript>
		disable(true);
		</script>
		<%end if%>
	</body>
</html>
