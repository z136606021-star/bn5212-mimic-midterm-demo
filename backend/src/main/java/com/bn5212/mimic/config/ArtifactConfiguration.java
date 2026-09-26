package com.bn5212.mimic.config;

import com.bn5212.mimic.common.ArtifactRootResolver;
import java.nio.file.Path;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ArtifactConfiguration {

  @Bean
  Path artifactRoot(@Value("${mimic.artifact-root:../artifacts}") String configuredRoot) {
    return ArtifactRootResolver.resolve(configuredRoot);
  }
}
