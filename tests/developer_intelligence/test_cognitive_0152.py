from sona.developer_intelligence.cognitive import analyze_source


def test_cognitive_engine_is_deterministic_profile_aware_and_capped():
    source = """
func complex(value) {
  if value {
    if value {
      if value {
        if value {
          if value {
            print(value);
            print(value);
            print(value);
          };
        };
      };
    };
  };
};
"""
    first = analyze_source(source, profile="adhd")
    second = analyze_source(source, profile="adhd")
    assert [item.to_dict() for item in first] == [item.to_dict() for item in second]
    ids = {item.diagnostic_id for item in first}
    assert "SONA-COG-001" in ids
    assert "SONA-COG-004" in ids
    assert len(first) <= 4
    assert len(analyze_source(source, profile="standard")) <= 8
