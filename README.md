# Water DP - Geospatial Stack

This stack provides the infrastructure for serving map layers and geospatial features.

## 📦 Services
*   **water-dp-geoserver**: GeoServer instance (Port 8080).
*   **water-dp-postgis**: PostGIS database for storing vector data.

## 🚀 Quick Start

1.  **Configure Environment**:
    Ensure `.env` exists with admin credentials.
    ```bash
    cp env.example .env
    ```

2.  **Start Services**:
    ```bash
    docker-compose up -d --build
    ```

3.  **Access**:
    *   GeoServer Admin: [http://localhost:8080/geoserver](http://localhost:8080/geoserver)
    *   Default Credentials: `admin` / `geoserver`

## 🌍 Features
*   **WMS/WFS**: Standard OGC services for maps.
*   **Vector Data**: Stores Rivers, Regions, and Monitoring Stations.
*   **Integration**: Automatically connected to the `water_shared_net` for API access.