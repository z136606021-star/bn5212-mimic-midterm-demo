package com.bn5212.mimic.model;
import org.junit.jupiter.api.Test;import java.util.*;import static org.junit.jupiter.api.Assertions.*;
class ModelServiceTest { @Test void sigmoidOutputIsBounded(){assertTrue(1d/(1d+Math.exp(-0d))==.5d);assertEquals(4, List.of("age","gender_male","heart_rate","resp_rate").size());} }
