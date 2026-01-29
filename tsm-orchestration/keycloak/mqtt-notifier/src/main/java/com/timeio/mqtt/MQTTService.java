package com.timeio.mqtt;

import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.jboss.logging.Logger;

public class MQTTService {
    private static final Logger LOG = Logger.getLogger(MQTTService.class);

    private static final String MQTT_BROKER = System.getenv().getOrDefault("MQTT_BROKER", "tcp://mqtt-broker:1883");
    private static final String MQTT_USER = System.getenv().getOrDefault("MQTT_USER", "mqtt");
    private static final String MQTT_PASSWORD = System.getenv().getOrDefault("MQTT_PASSWORD", "mqtt");
    private static final String MQTT_TOPIC = System.getenv().getOrDefault("MQTT_TOPIC", "user_login");
    private static final int MQTT_QOS = Integer.parseInt(System.getenv().getOrDefault("MQTT_QOS", "2"));

    private static final MQTTService INSTANCE = new MQTTService();

    private MqttClient mqttClient;

    private MQTTService() {
        try {
            mqttClient = new MqttClient(MQTT_BROKER, MqttClient.generateClientId(), new MemoryPersistence());
            MqttConnectOptions options = new MqttConnectOptions();
            options.setUserName(MQTT_USER);
            options.setPassword(MQTT_PASSWORD.toCharArray());
            options.setAutomaticReconnect(true);
            options.setCleanSession(true);

            mqttClient.setCallback(new MqttCallbackExtended() {
                public void connectComplete(boolean reconnect, String brokerURI) {
                    LOG.debugf("MQTT connected%s: %s", reconnect ? " (Reconnect)" : "", brokerURI);
                }
                public void connectionLost(Throwable cause) {
                    LOG.warn("MQTT connection lost", cause);
                }
                public void messageArrived(String topic, MqttMessage message) {}
                public void deliveryComplete(IMqttDeliveryToken token) {}
            });
            mqttClient.connect(options);
            LOG.info("Connection to MQTT-Broker established");
        } catch (Exception e) {
            LOG.error("Error when connecting to MQTT-Broker", e);
        }
    }

    public static MQTTService getInstance() {
        return INSTANCE;
    }

    public void publish(String payload) {
        try {
            if (mqttClient != null && mqttClient.isConnected()) {
                MqttMessage message = new MqttMessage(payload.getBytes());
                message.setQos(MQTT_QOS);
                mqttClient.publish(MQTT_TOPIC, message);
                LOG.debugf("MQTT message sent to topic '%s': %s", MQTT_TOPIC, payload);
            } else {
                LOG.warn("MQTT-Client not connected, message not sent");
            }
        } catch (Exception e) {
            LOG.error("Error while sending MQTT Message", e);
        }
    }
}