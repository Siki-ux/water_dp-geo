<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=true displayMessage=true displayRealm=false; section>

<head>
  <style>
    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      overflow: hidden;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
      background-color: #5FB4C0;
      animation: bgCycle 20s ease-in-out infinite;
    }

    @keyframes bgCycle {
      0% { background-color: #5FB4C0; }
      33% { background-color: #0071BC; }
      66% { background-color: #004F9F; }
      100% { background-color: #5FB4C0; }
    }

    section.fullscreen {
      position: relative;
      width: 100%;
      height: 100vh;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .orbital-waves {
      position: absolute;
      top: -30%;
      left: 50%;
      transform: translateX(-50%);
      width: 325vh;
      height: 325vh;
      z-index: 0;
      pointer-events: none;
    }

    .orbital-waves span {
      position: absolute;
      width: 100%;
      height: 100%;
      border-radius: 45%;
      animation: rotateWave 25s linear infinite;
    }

    .orbital-waves span:nth-child(1) {
      background: rgba(0, 113, 188, 0.2);
      animation-duration: 35s;
    }

    .orbital-waves span:nth-child(2) {
      background: rgba(0, 79, 159, 0.2);
      animation-duration: 50s;
    }

    .orbital-waves span:nth-child(3) {
      background: rgba(95, 180, 192, 0.2);
      animation-duration: 70s;
    }

    @keyframes rotateWave {
      0% { transform: translateX(-50%) rotate(0deg); }
      100% { transform: translateX(-50%) rotate(360deg); }
    }

    .wave-layer {
      position: absolute;
      width: 200%;
      height: 12em;
      background: rgba(255, 255, 255, 0.2);
      border-radius: 1000% 1000% 0 0;
      bottom: 0;
      left: 0;
      z-index: 0;
      animation: wave 12s -3s linear infinite;
      opacity: 0.8;
    }

    .wave-layer:nth-of-type(2) {
      bottom: -1.25em;
      animation: wave 18s linear reverse infinite;
    }

    .wave-layer:nth-of-type(3) {
      bottom: -2.5em;
      animation: wave 20s -1s reverse infinite;
    }

    @keyframes wave {
      0%, 100% { transform: translateX(1); }
      25% { transform: translateX(-25%); }
      50% { transform: translateX(-50%); }
      75% { transform: translateX(-25%); }
    }

    .login-container {
      position: relative;
      z-index: 1;
      width: 100%;
      max-width: 420px;
      margin: 0 auto;
      padding: 2.5rem 2rem;
      background: rgba(255, 255, 255, 0.95);
      border-radius: 12px;
      box-shadow: 0 0 20px rgba(0, 0, 0, 0.2);
      text-align: center;
    }

    .logo-container {
      margin-bottom: 1rem;
    }

    .logo-container img {
      width: 160px;
      height: auto;
    }

    .welcome-text {
      font-size: 1.4rem;
      font-weight: 500;
      margin-bottom: 2rem;
      color: #004F9F;
    }

    .kc-message {
      padding: 0.75rem;
      margin-bottom: 1.5rem;
      border-radius: 6px;
      font-weight: 500;
      text-align: center;
    }

    .kc-message.error {
      background-color: #ffd6d6;
      color: #990000;
      border: 1px solid #cc0000;
    }

    .kc-message.warning {
      background-color: #fff4d6;
      color: #996600;
      border: 1px solid #cc9900;
    }

    .kc-message.success {
      background-color: #d6ffd6;
      color: #006600;
      border: 1px solid #00cc00;
    }

    .social-providers {
      margin-bottom: 2rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .social-provider {
      padding: 0.75rem;
      background: #004F9F;
      color: #fff;
      text-decoration: none;
      border-radius: 6px;
      font-weight: bold;
    }

    .divider {
      display: flex;
      align-items: center;
      text-align: center;
      color: #666;
      margin: 2rem 0 1.5rem;
    }

    .divider::before,
    .divider::after {
      content: '';
      flex: 1;
      height: 1px;
      background: #ccc;
    }

    .divider:not(:empty)::before {
      margin-right: .75em;
    }

    .divider:not(:empty)::after {
      margin-left: .75em;
    }

    .form-group {
      margin-bottom: 1rem;
    }

    input[type="text"],
    input[type="password"] {
      width: 90%;
      padding: 0.65rem;
      border-radius: 6px;
      border: 1px solid #ccc;
      font-size: 1rem;
    }

    .login-btn {
      width: 90%;
      padding: 0.75rem;
      background: #0071BC;
      color: white;
      font-weight: bold;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 1rem;
    }

    .login-btn:hover {
      background: #004F9F;
    }

    .kc-form-options {
      margin-top: 1rem;
      font-size: 0.9rem;
    }

    @media (max-width: 500px) {
      .login-container {
        margin: 0 1rem;
        padding: 2rem 1.2rem;
      }

      .logo-container img {
        width: 130px;
      }

      .welcome-text {
        font-size: 1.1rem;
      }
    }
  </style>
</head>

<body>

  <section class="fullscreen">

    <!-- Background decorations -->
    <div class="orbital-waves">
      <span></span>
      <span></span>
      <span></span>
    </div>

    <div class="wave-layer"></div>
    <div class="wave-layer"></div>
    <div class="wave-layer"></div>

    <!-- Login box -->
    <div class="login-container">
      <div class="logo-container">
        <img src="${url.resourcesPath}/logo.svg" alt="Logo" />
      </div>

      <div class="welcome-text">Welcome to time.IO!</div>

      <#if message?has_content>
        <div class="kc-message ${message.type}">
          ${message.summary}
        </div>
      </#if>

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
    </div>

  </section>
</body>

</@layout.registrationLayout>
