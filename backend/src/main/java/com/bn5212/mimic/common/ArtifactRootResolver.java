package com.bn5212.mimic.common;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/**
 * Resolves the demo {@code artifacts/} directory from either the repository root
 * or the Maven {@code backend/} module working directory.
 * <p>
 * Only {@code summary.json} and {@code export/*.json} model contracts are required.
 * Training tables such as {@code demo_features.csv.gz} (which contain outcome labels)
 * are never used for path validation or loading.
 */
public final class ArtifactRootResolver {

  private static final List<String> MODEL_TASKS = List.of("mortality", "long_stay", "readmission");

  private ArtifactRootResolver() {}

  public static Path resolve(String configuredRoot) {
    return resolve(configuredRoot, Path.of("").toAbsolutePath().normalize());
  }

  public static Path resolve(String configuredRoot, Path workingDirectory) {
    Objects.requireNonNull(workingDirectory, "workingDirectory");
    Path cwd = workingDirectory.toAbsolutePath().normalize();

    Set<Path> candidates = new LinkedHashSet<>();
    if (configuredRoot != null && !configuredRoot.isBlank()) {
      Path configured = Path.of(configuredRoot);
      candidates.add(configured.isAbsolute() ? configured.normalize() : cwd.resolve(configured).normalize());
    }
    candidates.add(cwd.resolve("artifacts").normalize());
    candidates.add(cwd.resolve("..").resolve("artifacts").normalize());
    Path parent = cwd.getParent();
    if (parent != null) {
      candidates.add(parent.resolve("artifacts").normalize());
    }

    for (Path candidate : candidates) {
      if (isValidArtifactRoot(candidate)) {
        return candidate;
      }
    }

    return candidates.stream().findFirst().orElse(cwd.resolve("artifacts").normalize());
  }

  public static boolean isValidArtifactRoot(Path root) {
    if (root == null || !Files.isDirectory(root)) {
      return false;
    }
    if (!Files.isRegularFile(root.resolve("summary.json"))) {
      return false;
    }
    Path exportDir = root.resolve("export");
    if (!Files.isDirectory(exportDir)) {
      return false;
    }
    for (String task : MODEL_TASKS) {
      if (!Files.isRegularFile(exportDir.resolve(task + ".json"))) {
        return false;
      }
    }
    return true;
  }
}
