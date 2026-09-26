package com.bn5212.mimic.common;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class ArtifactRootResolverTest {

  @TempDir Path temp;

  @Test
  void resolvesWhenWorkingDirectoryIsBackendModule() throws Exception {
    Path demoRoot = temp.resolve("mimic_midterm_demo");
    Path backend = demoRoot.resolve("backend");
    Files.createDirectories(backend);
    Path artifacts = writeValidArtifacts(demoRoot.resolve("artifacts"));

    Path resolved = ArtifactRootResolver.resolve("../artifacts", backend);
    assertEquals(artifacts.toAbsolutePath().normalize(), resolved);
  }

  @Test
  void resolvesWhenWorkingDirectoryIsDemoRoot() throws Exception {
    Path demoRoot = temp.resolve("mimic_midterm_demo");
    Files.createDirectories(demoRoot.resolve("backend"));
    Path artifacts = writeValidArtifacts(demoRoot.resolve("artifacts"));

    Path resolved = ArtifactRootResolver.resolve("../artifacts", demoRoot);
    assertEquals(artifacts.toAbsolutePath().normalize(), resolved);
  }

  @Test
  void resolvesConfiguredAbsolutePath() throws Exception {
    Path demoRoot = temp.resolve("mimic_midterm_demo");
    Path elsewhere = temp.resolve("elsewhere");
    Files.createDirectories(demoRoot);
    Path artifacts = writeValidArtifacts(elsewhere.resolve("artifacts"));

    Path resolved = ArtifactRootResolver.resolve(artifacts.toString(), demoRoot);
    assertEquals(artifacts.toAbsolutePath().normalize(), resolved);
  }

  @Test
  void rejectsRootsThatOnlyHaveLabeledTrainingTables() throws Exception {
    Path root = temp.resolve("artifacts");
    Files.createDirectories(root);
    Files.writeString(root.resolve("demo_features.csv.gz"), "stay_id,mortality\n1,0\n");
    assertFalse(ArtifactRootResolver.isValidArtifactRoot(root));
  }

  @Test
  void acceptsCompleteContractLayout() throws Exception {
    Path artifacts = writeValidArtifacts(temp.resolve("artifacts"));
    assertTrue(ArtifactRootResolver.isValidArtifactRoot(artifacts));
  }

  private static Path writeValidArtifacts(Path artifacts) throws Exception {
    Files.createDirectories(artifacts.resolve("export"));
    Files.writeString(artifacts.resolve("summary.json"), "{\"cohort\":{\"stays\":1}}");
    for (String task : new String[] {"mortality", "long_stay", "readmission"}) {
      Files.writeString(
          artifacts.resolve("export").resolve(task + ".json"),
          "{\"schema_version\":\"1.0\",\"task\":\"" + task + "\"}");
    }
    return artifacts;
  }
}
