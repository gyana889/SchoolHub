<%@ LANGUAGE = VBScript.Encode %>
<!--#include virtual="/asp_lib/DBConnect.asp"-->
<!--#include virtual="/asp_lib/clearsessionvariables.asp" -->
<!--#include virtual="/asp_lib/page_loading.asp"-->
<%
	opendb
	
   
	Response.Buffer=false
	ClearEditSessionVariables
	if Request.Form("txtSearch") <> "" then
	vSearch = Request.Form("txtSearch")
	else
	vSearch = Request.QueryString("search")
	end if

	mode = ucase(request.querystring("mode")) ' E/e for edit |d/D for delete |v/V for View
	vType = 3 '1 for Junior, 2 for senior, 3 for all
	session("vType")=vType
	session("mode") = mode
	searchstring = vSearch
	recordsperpage = 10
	pagenum = Request.QueryString("page")
	searchidcolumn = "student_id"
	'searchtable = "v_Students_NotFA"	
	searchtable = "v_Students"	
	dim searchcolumnarray(11) 
    searchcolumnarray(0) = "name"
	searchcolumnarray(1) = "scholarno"
	searchcolumnarray(2) = "classname"
	searchcolumnarray(3) = "Fathers_Name"
	searchcolumnarray(4)="fathers_occupation"
	searchcolumnarray(5)="father_profession"	
	searchcolumnarray(6)="communication_phone"
	searchcolumnarray(7)="fathers_mobile_num"
	searchcolumnarray(8)="fathers_office_number"
	searchcolumnarray(9)="mothers_name"
	searchcolumnarray(10) = "HostelName"

	SearchOrderBy = "scholarno"
%>
<!-- #include virtual="/asp_lib/search.asp"-->
<html>
	<head>
		<link rel="stylesheet" href="/html_libs/style.css">
			<script language="Javascript">
	function frmStudentsView_first()
	{
		document.location.href = "student_view_All.asp?page=1&search=<%=server.urlencode(searchstring)%>&mode=<%=mode%>"
	}
	
	function frmStudentsView_next()
	{
		document.location.href = "student_view_All.asp?page=<%=pagenum+1%>&search=<%=server.urlencode(searchstring)%>&mode=<%=mode%>"
	}		
	
	function frmStudentsView_last()
	{
		document.location.href = "student_view_All.asp?page=<%=pagecount%>&search=<%=server.urlencode(searchstring)%>&mode=<%=mode%>"
	}
	function frmStudentsView_prev()
	{
		document.location.href = "student_view_All.asp?page=<%=pagenum-1%>&search=<%=server.urlencode(searchstring)%>&mode=<%=mode%>"
	}
			</script>
		</script>
	</head>
	<body>
		<!-- #include virtual="/html_libs/curlform.asp" -->
		<%

	form_name = "frmStudentsView"
	form_method = "post"
	'form_title_width = 90
	'form_showclose = true
if mode = "V" then
	form_title = "View Student Registration - Select Student"
else
	form_title =  "Edit Student Registration - Select Student"
end if
	form_iconsrc = "/images/icon.gif"
	form_action = "student_view_All.asp"
	form_showsubmit = false
	form_showsubmit1 = false
	form_showsubmit2 = false
	form_submitname = "SEARCH"
	form_paging = true
	form_showaudit = true
	form_audit_tablename = "STUDENTS"
	form_audit_rowid = ""
	if cint(pagenum) > 1 then form_showfirst = true
	if cint(pagenum) > 1 then form_showprev = true
	
	if pagecount>cint(pagenum) then form_shownext = true
	if pagecount>cint(pagenum) then  form_showlast = true
	

%>
		<%startform()%>
		<table class="formtable">
			<%if not rs.EOF then %>
			<tr class="keyrow" valign="top" align="left">
				<td width="20%">
					<font face="Verdana, Arial, Helvetica, sans-serif" size="2">Student Name</font>
				</td>
				<td width="9%">
					<font face="Verdana, Arial, Helvetica, sans-serif" size="2">Scholar No.</font>
				</td>
				<td width="9%">
					<font face="Verdana, Arial, Helvetica, sans-serif" size="2">Class Name</font>
				</td>
				<td width="20%">
					<font face="Verdana, Arial, Helvetica, sans-serif" size="2">Father's Name</font>
				</td>
				<td width="20%">
					<font face="Verdana, Arial, Helvetica, sans-serif" size="2">Mother's Name</font>
				</td>
				<td width="9%">
					<font face="Verdana, Arial, Helvetica, sans-serif" size="2">House</font>
				</td>								
				<td width="9%">
					<font face="Verdana, Arial, Helvetica, sans-serif" size="2">Status</font>
				</td>
				<%if mode <> "V" then%>
				<td width="9%">
					<font face="Verdana, Arial, Helvetica, sans-serif" size="2">Edit</font>
				</td>
				<%end if%>
			</tr>
			<%for i = 1 to recordsperpage%>
			<tr valign="top" align="left">
				<%if mode <> "V" then%>
				<td class="keycell" width="20%">
					<%=rs("name")%>
				</td>
				<td class="normalcell" width="15%">
					<%=rs("scholarno")%>
				</td>
				<td class="normalcell" width="10%">
				
					<%=rs("classname")%> 
					
					<% if not isnull(rs("section_id")) then%>/<%
				
					set temprs=conn.execute("select section_name from t_class_sections where section_id=" & rs("section_id"))
					
					if not temprs.eof then%>
					<%= temprs("section_name")%>
					<%end if%>
					<%end if%>
				</td>
				<td class="normalcell" width="20%">				
					<%=rs("Fathers_Name")%>
				</td>
				<td class="normalcell" width="20%">				
					<%=rs("mothers_Name")%>
				</td>
				<td class="normalcell" width="9%">				
					<%=rs("HostelName")%>
				</td>								
				<td class="normalcell" width="10%">				
					<%=rs("Status")%>
				</td>
					 
				<td class="operationcell" width="8%">
					<div align="center">
						<a target="_parent" href="/modules/studentmgt/registration/StudentsTempEdit/Studentreg1_edit.asp?ID=<%=server.urlencode(rs("student_id"))%>&Type=0&mode=E">
							<img src="/images/edit.gif" width="15" height="15" border="0"></a>
					</div>
				</td>
				<%else%>
				<td class="keycell" width="20%">
					<a target="_blank" href="/modules/studentmgt/registration/StudentsTempEdit/ViewStudentDetails.asp?ID=<%=server.urlencode(rs("student_id"))%>">
						<%=rs("name")%>
					</a>
				</td>
				<td class="normalcell" width="15%">
					<%=rs("scholarno")%>
				</td>
				<td class="normalcell" width="10%">
					<%=rs("classname")%> 
					
					<% if not isnull(rs("section_id")) then%>/<%
					
					set temprs=conn.execute("select section_name from t_class_sections where section_id=" & rs("section_id"))
					
					if not temprs.eof then%>
					<%= temprs("section_name")%>
					<%end if%>
					<%end if%>
				</td>
				
				<td class="normalcell" width="20%">				
					<%=rs("Fathers_Name")%>
				</td>

				<td class="normalcell" width="20%">				
					<%=rs("mothers_Name")%>
				</td>				
				<td class="normalcell" width="9%">				
					<%=rs("HostelName")%>
				</td>								
				
				<td class="normalcell" width="10%">
				
					<%=rs("Status")%>
					</td>
				<%end if%>
			</tr>
			<% 
rs.MoveNext 
if rs.EOF then exit for
next%>
			<tr>
				<td class="bottomrow" width="27%" colspan="6">
					<%=totalrecords%>
					Record(s) Found --> Showing Page
					<%=pagenum%>
					of
					<%=pagecount%>
				</td>
			</tr>
			<%else%>
			<tr>
				<td class="bottomrow" width="27%" colspan="5">
					No Records Were Found
				</td>
			</tr>
			<%end if%>
		</table>
		<%endform()%>
	</body>
</html>
