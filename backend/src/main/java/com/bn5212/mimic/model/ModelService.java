package com.bn5212.mimic.model;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class ModelService {
  private final Map<String, ModelContract> models = new HashMap<>();

  public ModelService(ObjectMapper mapper, Path artifactRoot) {
    for (String task : List.of("mortality", "long_stay", "readmission")) {
      try {
        ModelContract model = mapper.readValue(
            artifactRoot.resolve("export").resolve(task + ".json").toFile(),
            ModelContract.class);
        if (model.valid() && task.equals(model.task)) {
          models.put(task, model);
        }
      } catch (Exception ignored) {
        // Missing or invalid contracts leave the service not ready.
      }
    }
  }

  public boolean ready() {
    return models.size() == 3;
  }

  public Map<String, Object> predict(String task, Map<String, Double> input) {
    ModelContract model = models.get(task);
    if (model == null) {
      throw new IllegalStateException("Model artifact is unavailable");
    }
    for (String key : input.keySet()) {
      if (!model.features.contains(key)) {
        throw new IllegalArgumentException("Unknown feature: " + key);
      }
    }
    double z = model.intercept;
    List<Map<String, Object>> contributors = new ArrayList<>();
    for (int i = 0; i < model.features.size(); i++) {
      String feature = model.features.get(i);
      Double value = input.get(feature);
      double raw = value == null || !Double.isFinite(value) ? model.medians.get(i) : value;
      double contribution = ((raw - model.means.get(i)) / model.scales.get(i)) * model.coefficients.get(i);
      z += contribution;
      contributors.add(Map.of(
          "feature", feature,
          "direction", contribution > 0 ? "higher" : "lower",
          "contribution", Math.round(contribution * 1000d) / 1000d));
    }
    double score = 1d / (1d + Math.exp(-z));
    contributors.sort((a, b) -> Double.compare(
        Math.abs((double) b.get("contribution")),
        Math.abs((double) a.get("contribution"))));
    return Map.of(
        "ranking_score", Math.round(score * 10000d) / 10000d,
        "risk_band", score >= 0.66 ? "higher" : score >= 0.33 ? "middle" : "lower",
        "top_contributors", contributors.subList(0, Math.min(4, contributors.size())));
  }
}
