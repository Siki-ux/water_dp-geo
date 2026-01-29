<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=true displayMessage=true displayRealm=false; section>

    <#if section = "header">
        Welcome to time.IO!
    <#elseif section = "form">
        <#if social?? && social.providers?has_content>
            <div class="social-providers">
                <#list social.providers as p>
                    <a class="social-provider" href="${p.loginUrl}" id="social-${p.alias}">
                        ${p.displayName}
                    </a>
                </#list>
            </div>
        </#if>

        <div class="divider">or log in with credentials</div>

        <form id="kc-form-login" action="${url.loginAction}" method="post">
            <div class="form-group">
                <input id="username" name="username" type="text" placeholder="${msg("username")}"
                       value="${login.username!''}" autofocus />
            </div>
            <div class="form-group">
                <input id="password" name="password" type="password" placeholder="${msg("password")}" />
            </div>
            <div class="form-group">
                <input class="login-btn" type="submit" value="${msg("doLogIn")}" />
            </div>
        </form>

        <div class="kc-form-options">
            <#if realm.resetPasswordAllowed?? && realm.resetPasswordAllowed>
                <a href="${url.loginResetCredentialsUrl}">${msg("doForgotPassword")}</a>
            </#if>
        </div>
    </#if>

</@layout.registrationLayout>
