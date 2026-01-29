<#macro registrationLayout displayInfo=false displayMessage=true displayRealm=true>
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8"/>
    <title>${msg("loginTitle",(realm.displayName!realm.name))}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <#nested "head">
  </head>
  <body>
  </body>
</html>
</#macro>
