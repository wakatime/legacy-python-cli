<%@ Page Language="CustomLanguage" AutoEventWireup="true" CodeFile="Custom.aspx" Inherits="_Default" %>

<!DOCTYPE html>
<script src="//code.jquery.com/jquery-1.11.0.min.js"></script>
<script src="//code.jquery.com/jquery-migrate-1.2.1.min.js"></script>
<script type="text/javascript">
    $(document).ready(function () {
        $('#SomeID').removeAttr('id');
    });
</script>


<html id="SomeID"  runat="server" xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title></title>
</head>
<body>
    <form id="form1" runat="server">
    <div>
    </div>
    </form>
</body>
</html>
