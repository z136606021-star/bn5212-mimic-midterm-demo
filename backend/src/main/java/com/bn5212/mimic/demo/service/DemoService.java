package com.bn5212.mimic.demo.service;

import com.bn5212.mimic.demo.dto.PredictRequest;
import com.bn5212.mimic.model.ModelService;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class DemoService {
  private final ObjectMapper mapper;
  private final ModelService model;
  private final Path root;

  public DemoService(ObjectMapper mapper, ModelService model, Path artifactRoot) {
    this.mapper = mapper;
    this.model = model;
    this.root = artifactRoot;
  }

  @SuppressWarnings("unchecked")
  public Map<String, Object> summary() {
    try {
      return mapper.readValue(root.resolve("summary.json").toFile(), Map.class);
    } catch (Exception e) {
      throw new IllegalStateException("Demo artifacts are not prepared");
    }
  }

  public List<Map<String, Object>> tasks() {
    return List.of(
        Map.of(
            "id", "mortality",
            "title", "In-hospital mortality",
            "question", "Can first-24-hour information identify higher-risk ICU stays?",
            "label", "hospital_expire_flag",
            "window", "First 24 hours after ICU admission",
            "type", "prediction"),
        Map.of(
            "id", "long_stay",
            "title", "Prolonged ICU stay",
            "question", "Will this ICU stay exceed three days?",
            "label", "ICU LOS > 3 days",
            "window", "First 24 hours after ICU admission",
            "type", "prediction"),
        Map.of(
            "id", "readmission",
            "title", "30-day readmission",
            "question", "Is another admission observed within 30 days after discharge?",
            "label", "next admission within 30 days",
            "window", "First 24 hours after ICU admission",
            "type", "prediction"),
        Map.of(
            "id", "missingness",
            "title", "Missing-data robustness",
            "question", "How does performance change when observed values are masked?",
            "label", "mortality / long-stay performance",
            "window", "Evaluation-only perturbation",
            "type", "robustness"));
  }

  public Map<String, Object> predict(PredictRequest req) {
    if (req.features() == null) {
      throw new IllegalArgumentException("Java online inference requires an explicit feature map");
    }
    Map<String, Object> result = new HashMap<>(model.predict(req.task(), req.features()));
    result.put("task", req.task());
    result.put("source", "manual teaching input");
    result.put("disclaimer", "Preliminary course demo; not a diagnosis or calibrated clinical probability.");
    return result;
  }
}
