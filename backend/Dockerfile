# Multi-stage build: Maven + JDK 17 compile, then Temurin 17 JRE runtime.
# Build context is the demo repository root (see docker-compose.yml).
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /build
COPY backend/pom.xml .
COPY backend/src ./src
RUN mvn -B -DskipTests package

FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=build /build/target/mimic-demo-backend-*.jar /app/app.jar
# Model JSON is mounted at runtime (summary.json + export/*.json). No raw MIMIC data.
ENV DEMO_ARTIFACT_ROOT=/app/artifacts
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
