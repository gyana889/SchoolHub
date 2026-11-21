<%@ LANGUAGE = VBScript.Encode %>
<%
if Request.Form("txhControl") = "" then
	session("frompage") = Request.ServerVariables ("HTTP_REFERER")	
end if	
%>
<%
if Request.Form("txhControl") = "yes" then
	Response.Redirect "studentreg_edit_submit.asp"
end if

if Request.Form("txhControl") = "no" then
	Response.Redirect session("frompage")
end if

%>
<html>
<head>
<link rel="stylesheet" href="/html_libs/style.css">
</head>
<body>
<!-- #include virtual="/html_libs/curlform.asp" -->
<%
	form_name = "frmConfirm"
	form_method = "post"
	form_title = "Confirm Student Registration (Edit)"
	form_iconsrc = "/images/icon.gif"
	form_action = "studentreg_edit_confirm.asp"
	form_showsubmit = true
	form_showsubmit1 = true
	form_submitname = "NO"
	form_submit1name = "YES"
%>
<%startform()%>
<SCRIPT LANGUAGE="javascript">

<!--

function frmConfirm_submit1()
{
	document.frmConfirm.txhControl.value = "yes";
	document.frmConfirm.submit();
}

function frmConfirm_submit()
{
	document.frmConfirm.txhControl.value = "no";
	document.frmConfirm.submit();
}

//-->
		</SCRIPT>
		<table width="100%" class=formtable>
			<input type="hidden" name="txhControl" value="">
			<input type="hidden" name="txhID" value="<%=Request.QueryString("ID")%>">
			<tr valign="top" align="center">
				<td colspan="2">
					<div align="center">
						<font face="Verdana, Arial, Helvetica, sans-serif" size="2"><font size="4">
								<br>
								Please Confirm Update ? </font>
							<br>
						</font>
					</div>
				</td>
			</tr>
		</table>
		<%endform()%>
	</body>
</html>