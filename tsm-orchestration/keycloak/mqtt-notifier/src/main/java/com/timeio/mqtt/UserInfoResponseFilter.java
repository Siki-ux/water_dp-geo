package com.timeio.mqtt;

import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerResponseContext;
import jakarta.ws.rs.container.ContainerResponseFilter;
import jakarta.ws.rs.ext.Provider;
import org.jboss.logging.Logger;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;

@Provider
public class UserInfoResponseFilter implements ContainerResponseFilter {

    private static final Logger LOG = Logger.getLogger(UserInfoResponseFilter.class);
    private final MQTTService mqttService = MQTTService.getInstance();

    @Override
    public void filter(ContainerRequestContext requestContext,
                       ContainerResponseContext responseContext) throws IOException {

        String path = requestContext.getUriInfo().getPath();

        if (path.contains("/protocol/openid-connect/userinfo")) {
            LOG.debugf("=== USERINFO RESPONSE ===");
            LOG.debugf("Status: %d", responseContext.getStatus());

            Object entity = responseContext.getEntity();
            if (entity != null) {
                ObjectMapper mapper = new ObjectMapper();
                String userInfoJson = mapper.writeValueAsString(entity);
                LOG.debugf("UserInfo JSON: %s", userInfoJson);

                mqttService.publish(userInfoJson);
            } else {
                LOG.warn("UserInfo response body is empty");
            }
        }
    }
}