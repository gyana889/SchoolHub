<!--#include virtual="/asp_lib/DbConnect.asp"-->
<!--#include virtual="/html_libs/curlform.asp" -->
<!--#include virtual="/asp_lib/displaydate.asp"-->

<%
	OpenDB
	
	'Response.Write Session("AdmissionMonth")
'Response.Write Session("academicyear")
if Request.Form("txhControl")="prev" then

	session("achievements") = Request.Form("txtAchievements")	
	session("hobbies")=Request.Form("txtHobbies")	
	session("Interest")=Request.Form("txtInterest")	
	session("other")=Request.Form("txtOther")	
	Response.Redirect "studentreg3_edit.asp"
end if
	
if request.form("txhControl")="next" then
	session("achievements") = Request.Form("txtAchievements")	
	session("hobbies")=Request.Form("txtHobbies")	
	session("Interest")=Request.Form("txtInterest")	
	session("other")=Request.Form("txtOther")	
	'Response.Redirect "studentreg6_edit.asp?next=y"	
	Response.Redirect "StudentregActivity.asp"
end if

if request.form("txhControl")="goback" then
	response.write "ok"
	response.end
		clearsessionvariables
		if session("UserType")="S" then
		Response.Redirect "/modules/studentmgt/registration/StudentsTempEdit/studentreg1_edit.asp?ID="&session("UserId") &"&mode=V&ptype=2&Type=2"
		else
		Response.Redirect "/modules/studentmgt/registration/common_frame.asp?mode=V&file=/modules/studentmgt/registration/StudentsTempEdit/student_view.asp"
		end if
end if	



%>

<html>
	<head>
		<script language="JavaScript" src="/js_lib/date-picker.js"></script>
	<script language=javascript>
		function disable(val)
		{
		for (i=0;i<document.frmstudentreg5.elements.length;i++)
				{
				if (document.frmstudentreg5.elements(i).type != "button")
				document.frmstudentreg5.elements(i).disabled=+val;
				}
		}
	</script>
		<link rel="stylesheet" href="/html_libs/style.css">
	<title><%="Mayoor School, Ajmer : Personal Details Of "%><%=Session("rfirstName")%><%=" "%><%=Session("rlastName")%></title>
	</head>
	<body>
		<%
	form_name = "frmstudentreg5":	form_method = "post":form_title = "Student Registration : Extra Curricular Details"
	form_iconsrc = "/images/icon.gif"
	form_action = "studentreg5_edit.asp"
if session("mode") = "V" then
	form_showsubmit2 = false
	form_submit2name = "GOBACK"
else
	form_showsubmit = true
	form_showsubmit1 = true
	form_submitname = "Next"
	form_submit1name = "PREVIOUS"
end if
	

%>
		<%startform()%>

		<table class="formtable" width="91%">
			<input type="hidden" name="txhControl">
			<input type="hidden" name="txhControl1">


			
<!--			<tr class=keyrow>
			<td class="keycell" width="50%" colspan="4"><center><b>Previous School Details </b></center></td>
			</tr>
			<tr>
				<td class="keycell" width="50%" colspan="2">
					School Name
				</td>
				<td class="normalcell width="50%" colspan=2>
				<input name=txtschoolname maxlength=50 value="<%=session("prevschoolname")%>" style="width:250px">
				</td>
			</tr>
			<tr>
				<td class="keycell" width="50%" colspan="2">
					Address
				</td>
				<td class="normalcell width="50%" colspan=2>
				<textarea name=txtschooladdress rows=3 style="width:250px"><%=session("prevschooladdress")%></textarea>
				</td>
			</tr>
			<tr>
				<td class="keycell" width="50%" colspan="2">
					From Date
				</td>
				<td class="normalcell width="50%" colspan=2>
						<input type="text" style="text-align:center;WIDTH: 200px" name="txtfromDate" LANGUAGE="javascript" onkeypress="return KeyPressCheck(this)" value="<%=Ndate(Session("prevfromDate"),"%d-%b-%Y") %>">
						<A href="javascript:show_calendar('frmstudentreg5.txtfromDate');"><IMG height="22" src="/images/calendar.gif" width="24" border="0"></A>
				</td>
			</tr>
			<tr>
				<td class="keycell" width="50%" colspan="2">
					To Date
				</td>
				
				<td class="normalcell width="50%" colspan=2>
						<input type="text" style="text-align:center;WIDTH: 200px" name="txttoDate" LANGUAGE="javascript" onkeypress="return KeyPressCheck(this)" value="<%=Ndate(Session("prevtoDate"),"%d-%b-%Y") %>">
						<A href="javascript:show_calendar('frmstudentreg5.txttoDate');"><IMG height="22" src="/images/calendar.gif" width="24" border="0"></A>
				</td>
			</tr>
			<tr>
				<td class="keycell" width="50%" colspan="2">
					Previous Class Attenended
				</td>
				<td class="normalcell width="50%" colspan=2>
				<input name=txtprevclass value="<%=session("prevschoolclass")%>" style="WIDTH: 200px">
				</td>
			</tr>
			<tr>
				<td class="keycell" colspan="2">
					Medium of Instruction 
				</td>
				<td width="50%">
					<select name="cmbMedium" style="WIDTH: 200px; HEIGHT: 22px">
						<option value="">
							Please Select</option>
							<option value="English" <%if trim(Session("MedInst"))="English" then Response.write "selected" end if%>>English</option>
							<option value="Hindi" <%if trim(Session("MedInst"))="Hindi" then Response.write "selected" end if%>>Hindi</option>
							</select>
				</td>
			</tr>
-->			
			
			<tr class=keyrow>
			<td class="keycell" width="50%" colspan="4"><center><b>Extra Curricular Activities </b></center></td>
			</tr>
			
            <tr>
				<td class="keycell" width="50%" colspan="2">
					Achievements
				</td>
				<td class="normalcell" width="50%" colspan=2>
				<textarea name=txtAchievements rows=12  style="width:550px" cols="40"><%=session("achievements")%></textarea>
				</td>
			</tr>
			<tr>
				<td class="keycell" width="50%" colspan="2">
					Hobbies
				</td>
				<td class="normalcell" width="50%" colspan=2>
				<textarea name=txtHobbies rows=4  style="width:550px" cols="40"><%=session("hobbies")%></textarea>
				</td>
			</tr>
			<tr>
				<td class="keycell" width="50%" colspan="2">
					Special Interest
				</td>
				<td class="normalcell" width="50%" colspan=2>
				<textarea name=txtInterest rows=4  style="width:550px" cols="20"><%=session("Interest")%></textarea>
				</td>
			</tr>
			<tr>
				<td class="keycell" width="50%" colspan="2">
					Other Information
				</td>
				<td class="normalcell" width="50%" colspan=2>
				<textarea name=txtOther rows=4  style="width:550px" cols="20"><%=session("other")%></textarea>
				</td>
			</tr> 
		</table>
		<%endform()
		if session("mode")="V" then%>
		<script language=javascript>
		disable(true);
		</script>
		<%end if%>
<script language="javascript">
function frmstudentreg5_submit1()
{
	disable(false);
	document.frmstudentreg5.txhControl.value = "prev";
	document.frmstudentreg5.submit();
}

function frmstudentreg5_submit()
{
	disable(false);
	document.frmstudentreg5.txhControl.value = "next";
	document.frmstudentreg5.submit();
}

function frmstudentreg5_submit2()
{
	window.navigate("/modules/studentmgt/registration/common_frame.asp?mode=V&file=/modules/studentmgt/registration/StudentsTempEdit/student_view.asp");
	//document.frmstudentreg5.txhControl.value = "goback";
	
	//document.frmstudentreg5.submit();

}

</script>
</body>
</html>
