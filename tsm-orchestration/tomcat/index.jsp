<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>TSM FROST-Server</title>
    </head>
    <body>
        <div id="main-container">
            <h1 id="title">STA<br>Endpoints</h1>
            <ul class="endpoint-list">
                <%
                    String webappsDir = "/usr/local/tomcat/webapps/";
                    String scheme = request.getScheme();
                    String serverName = request.getServerName();
                    int serverPort = request.getServerPort();
                    java.io.File[] webapps = new java.io.File(webappsDir).listFiles();

                    int datasourceNumber = 0;
                    for (java.io.File webapp : webapps) {
                        if (webapp.isDirectory() && !webapp.getName().equals("ROOT")) {
                            datasourceNumber += 1;
                            String webappName = webapp.getName();
                            int firstIdx = webappName.indexOf("_");
                            int secondIdx = webappName.indexOf("_", firstIdx + 1);
                            String groupName, projectName, endpointDisplayName;
                            if (secondIdx == -1) {
                                groupName = webappName.substring(0, firstIdx);
                                endpointDisplayName = groupName;
                            } else {
                                groupName = webappName.substring(0, firstIdx);
                                projectName = webappName.substring(firstIdx + 1, secondIdx);
                                endpointDisplayName = groupName + " " + projectName;
                            }
                            String webappURL = String.format(
                                "%s://%s:%s/sta/%s/v1.1",
                                scheme, serverName, serverPort, webappName
                            );
                %>
                <li class="endpoint-item-wrapper" style="animation-duration: <%= (datasourceNumber + 3) * 0.1 %>s;">
                    <a href="<%=webappURL%>">
                        <div class="endpoint-item">
                            <span class="endpoint-title"><%=endpointDisplayName%></span>
                            <span class="endpoint-subtitle"><%=webappName%></span>
                        </div>
                    </a>
                </li>
                <%
                        }
                    }
                    if (datasourceNumber == 0) {
                %>
                <span id="no-endpoints-text">No endpoints available.</span>
                <%
                    }
                %>
            </ul>
        </div>
        <style>
            body {
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 0;
                padding: 0;
                overflow: hidden;
                font-size: 1.5em;
                font-family: Tahoma, Verdana, Arial, sans-serif;
            }

            #main-container {
                width: 80%;
                display: flex;
                animation: fadeIn .4s ease-out;
                position: relative;
            }

            #main-container::after {
                content: " ";
                display: block;
                background-image: linear-gradient(to top, rgba(255,255,255, 1), rgba(255,255,255, 0));
                height: 100px;
                width: 100%;
                pointer-events: none;
                position: absolute;
                bottom: 20px;
                right: 20px;
            }

            #title {
                font-size: 1.5em;
                margin-top: 1.5em;
                text-transform: uppercase;
                font-weight: 100;
                text-align: center;
                letter-spacing: 1px;
            }

            .endpoint-list {
                height: 80vh;
                list-style-type: none;
                overflow-y: auto;
                overflow-x: hidden;
                padding: 0;
            }

            .endpoint-item-wrapper {
                display: absolute;
                margin: .3em 1em;
                background-image: linear-gradient(to right, rgba(0,0,50,0.05), rgba(0,0,50,0));
                border-radius: .4em;
                transition: all .1s;
                animation: cardFadeIn 1s ease-out;
            }

            .endpoint-item-wrapper:last-of-type {
                margin-bottom: 60px;
            }

            .endpoint-item-wrapper:hover {
                background-image: linear-gradient(to right, rgba(0,0,50,0.1), rgba(0,0,50,0));
                transform: scale(1.025);
            }

            .endpoint-item-wrapper a {
                text-decoration: none;
                color: #333;
            }

            .endpoint-item {
                padding: 1.5em;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }

            .endpoint-title {
                text-transform: uppercase;
                font-weight: 600;
            }

            .endpoint-subtitle {
                color: #555;
                font-size: .7em;
                text-overflow: ellipsis;
                overflow: hidden;
                white-space: nowrap;
            }

            #no-endpoints-text {
                text-align: left;
                font-weight: 600;
                top: 2em;
                position: relative;
            }

            /* keyframes */

            @keyframes cardFadeIn {
                0% {left: 1em; opacity: 0;}
                50% {left: .9em; opacity: 0;}
                100% {left: 0em; opacity: 1;}
            }

            @keyframes fadeIn {
                0% { opacity: 0;}
                100% { opacity: 1;}
            }

            /* mobile breakpoints */

            @media (max-width: 1000px) {
                #main-container {
                    flex-direction: column;
                }
            }

            @media (min-width: 1000px) {
                #title {
                    margin-right: 2em;
                    text-align: right;
                }

                .endpoint-list {
                    border-left: 2px solid #eee;
                    padding-left: 2em;
                }

                #no-endpoints-text {
                    padding-left: 2em;
                }
            }
        </style>
    </body>
</html>