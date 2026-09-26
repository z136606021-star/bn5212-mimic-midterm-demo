package com.bn5212.mimic.demo.dto; import jakarta.validation.constraints.*; import java.util.Map;
public record PredictRequest(@NotBlank String task,@Min(0) Integer sample_index,Map<String,Double> features) {}
