<cflock name="FileOperation" timeout="20" throwOnTimeout="true">
<cffile action="write" file="#filePath#" output="#content#">
</cflock>
<!-- application scope is exclusively locked on the cache -->
<cflock type="readonly" scope="application" timeout="10" throwOnTimeout="true">
<cfset myVar = application.cache.getValue("x")>
</cflock>
<cfquery name="variables.qUser" datasource="#request.dsn#">
SELECT FirstName, LastName
FROM Users
WHERE UserID = #request.UserID#
</cfquery>
<cflock scope="application" timeout="2" type="exclusive">
<cfset application.qUser=variables.qUser>
</cflock>
